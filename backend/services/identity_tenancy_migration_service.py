from __future__ import annotations

from collections import defaultdict
from typing import Any

from database import Database
from security import normalize_email


ANALYZED_COLLECTIONS = (
    "auth_identities",
    "agency_staff_memberships",
    "portal_access_mappings",
    "client_profiles",
    "passenger_profiles",
    "client_passenger_relationships",
    "client_master_records",
    "passenger_master_records",
    "client_passenger_links",
    "client_portal_access_profiles",
)


class IdentityTenancyMigrationError(ValueError):
    pass


def _record_ref(record: dict[str, Any]) -> dict[str, Any]:
    return {
        key: record.get(key)
        for key in ("id", "agency_id", "status", "portal_status")
        if record.get(key) is not None
    }


def _normalized(value: Any) -> str | None:
    if not value:
        return None
    try:
        return normalize_email(str(value))
    except (TypeError, ValueError):
        return None


async def analyze_identity_tenancy_migration(
    db: Database,
    *,
    agency_id: str | None = None,
    apply: bool = False,
) -> dict[str, Any]:
    if apply:
        raise IdentityTenancyMigrationError(
            "Write mode is intentionally unavailable. Reconciliation requires a separately reviewed, "
            "single-agency plan with confirmation, audit evidence, and a rollback manifest."
        )

    records: dict[str, list[dict[str, Any]]] = {}
    for collection in ANALYZED_COLLECTIONS:
        tenant_filter = {"agency_id": agency_id} if agency_id and collection != "auth_identities" else None
        records[collection] = await db.collection(collection).find_many(tenant_filter)

    identities = records["auth_identities"]
    identities_by_id = {item["id"]: item for item in identities}
    identities_by_email: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for identity in identities:
        normalized = _normalized(identity.get("normalized_email") or identity.get("email"))
        if normalized:
            identities_by_email[normalized].append(identity)

    clients = records["client_profiles"]
    passengers = records["passenger_profiles"]
    clients_by_id = {item["id"]: item for item in clients}
    passengers_by_id = {item["id"]: item for item in passengers}
    issues: list[dict[str, Any]] = []

    active_mappings_by_identity: dict[str, list[dict[str, Any]]] = defaultdict(list)
    active_mappings_by_subject: dict[tuple[str, str, str], list[dict[str, Any]]] = (
        defaultdict(list)
    )
    mappings_by_id = {
        str(item["id"]): item
        for item in records["portal_access_mappings"]
        if item.get("id")
    }
    for mapping in records["portal_access_mappings"]:
        mapping_status = mapping.get("status") or mapping.get("portal_status")
        identity_id = mapping.get("auth_identity_id")
        if not identity_id:
            email = _normalized(mapping.get("user_email"))
            suggestions = [
                _record_ref(identity)
                for identity in identities_by_email.get(email or "", [])
                if identity.get("identity_type") in {"client_portal", "passenger_portal"}
            ]
            issues.append(
                {
                    "issue_type": "legacy_email_portal_mapping",
                    "severity": "warning",
                    "record": _record_ref(mapping),
                    "email_match_is_authoritative": False,
                    "suggested_identity_candidates": suggestions,
                    "ambiguous": len(suggestions) != 1,
                    "remediation": "Review and create an explicit AuthIdentity-to-subject mapping.",
                }
            )
            continue
        identity = identities_by_id.get(identity_id)
        if mapping_status == "active":
            active_mappings_by_identity[str(identity_id)].append(mapping)
            subject_type = str(mapping.get("subject_type") or "")
            subject_id = str(
                mapping.get("client_profile_id")
                or mapping.get("client_id")
                or mapping.get("passenger_profile_id")
                or ""
            )
            if subject_type and subject_id:
                active_mappings_by_subject[
                    (str(mapping.get("agency_id") or ""), subject_type, subject_id)
                ].append(mapping)
        if mapping_status == "active" and (
            not identity or identity.get("status") != "active"
        ):
            issues.append(
                {
                    "issue_type": "inactive_identity_active_portal_mapping",
                    "severity": "critical",
                    "record": _record_ref(mapping),
                    "auth_identity_id": identity_id,
                    "identity_status": (identity or {}).get("status", "missing"),
                    "remediation": "Revoke the mapping or reactivate the identity after operator review.",
                }
            )
        if mapping_status == "active":
            subject_type = mapping.get("subject_type")
            subject_id = (
                mapping.get("client_profile_id") or mapping.get("client_id")
                if subject_type == "client"
                else mapping.get("passenger_profile_id")
                if subject_type == "passenger"
                else None
            )
            subject = (
                clients_by_id.get(subject_id)
                if subject_type == "client"
                else passengers_by_id.get(subject_id)
                if subject_type == "passenger"
                else None
            )
            if (
                subject is None
                or subject.get("agency_id") != mapping.get("agency_id")
                or subject.get("status") in {"archived", "quarantined", "duplicate_merged"}
            ):
                issues.append(
                    {
                        "issue_type": "invalid_active_portal_subject_link",
                        "severity": "critical",
                        "record": _record_ref(mapping),
                        "auth_identity_id": identity_id,
                        "subject_type": subject_type,
                        "subject_id": subject_id,
                        "subject_record": _record_ref(subject) if subject else None,
                        "remediation": "Revoke the invalid active mapping and create a reviewed same-Agency replacement.",
                    }
                )
        if (
            mapping_status == "active"
            and identity
            and (
                (
                    mapping.get("subject_type") == "client"
                    and identity.get("identity_type") != "client_portal"
                )
                or (
                    mapping.get("subject_type") == "passenger"
                    and identity.get("identity_type") != "passenger_portal"
                )
            )
        ):
            issues.append(
                {
                    "issue_type": "portal_identity_subject_type_mismatch",
                    "severity": "critical",
                    "record": _record_ref(mapping),
                    "auth_identity_id": identity_id,
                    "identity_type": identity.get("identity_type"),
                    "subject_type": mapping.get("subject_type"),
                    "remediation": "Revoke the mapping and create a reviewed mapping with the matching Portal identity type.",
                }
            )

    for identity_id, mappings in active_mappings_by_identity.items():
        if len(mappings) > 1:
            issues.append(
                {
                    "issue_type": "ambiguous_active_portal_mappings",
                    "severity": "critical",
                    "auth_identity_id": identity_id,
                    "mapping_candidates": [_record_ref(item) for item in mappings],
                    "cross_agency": len(
                        {str(item.get("agency_id") or "") for item in mappings}
                    )
                    > 1,
                    "automatic_subject_selection_disabled": True,
                    "remediation": "Review all candidate subjects and revoke conflicting mappings without deleting evidence.",
                }
            )

    for subject_key, mappings in active_mappings_by_subject.items():
        if len(mappings) > 1:
            issues.append(
                {
                    "issue_type": "duplicate_active_portal_subject_mapping",
                    "severity": "critical",
                    "agency_id": subject_key[0],
                    "subject_type": subject_key[1],
                    "subject_id": subject_key[2],
                    "mapping_candidates": [_record_ref(item) for item in mappings],
                    "automatic_subject_selection_disabled": True,
                    "remediation": "Review and revoke duplicate active subject mappings without deleting evidence.",
                }
            )

    for membership in records["agency_staff_memberships"]:
        if membership.get("status") != "active":
            continue
        identity_id = membership.get("identity_id")
        identity = identities_by_id.get(str(identity_id)) if identity_id else None
        if not identity_id or not identity or identity.get("status") != "active":
            issues.append(
                {
                    "issue_type": "active_membership_without_active_identity",
                    "severity": "critical" if identity_id else "warning",
                    "record": _record_ref(membership),
                    "auth_identity_id": identity_id,
                    "identity_status": (identity or {}).get("status", "missing"),
                    "remediation": "Link the membership to one reviewed active staff identity or revoke the membership.",
                }
            )

    for profile in records["client_portal_access_profiles"]:
        if profile.get("portal_status") not in {"invited", "active"}:
            continue
        mapping_id = profile.get("source_portal_mapping_id")
        mapping = mappings_by_id.get(str(mapping_id)) if mapping_id else None
        mapping_status = (
            mapping.get("status") or mapping.get("portal_status")
            if mapping
            else None
        )
        if (
            not mapping
            or mapping.get("agency_id") != profile.get("agency_id")
            or mapping.get("subject_type") != "client"
            or mapping_status != "active"
        ):
            issues.append(
                {
                    "issue_type": "legacy_active_portal_profile_without_active_mapping",
                    "severity": "critical",
                    "record": _record_ref(profile),
                    "source_portal_mapping_id": mapping_id,
                    "mapping_record": _record_ref(mapping) if mapping else None,
                    "authorization_effect": False,
                    "remediation": "Archive the legacy active state or link it to one reviewed active Client Portal mapping.",
                }
            )

    for record in records["client_master_records"]:
        source_id = record.get("source_client_profile_id")
        source = clients_by_id.get(source_id) if source_id else None
        status = (
            "missing_source_reference"
            if not source_id
            else "unresolved_source_reference"
            if not source
            else "cross_agency_source_collision"
            if source.get("agency_id") != record.get("agency_id")
            else "canonical_overlap"
        )
        issues.append(
            {
                "issue_type": f"client_master_{status}",
                "severity": "critical" if status == "cross_agency_source_collision" else "warning",
                "record": _record_ref(record),
                "source_client_profile_id": source_id,
                "canonical_record": _record_ref(source) if source else None,
                "remediation": "Treat ClientProfile as authoritative and retain this record as a compatibility projection.",
            }
        )

    for record in records["passenger_master_records"]:
        source_id = record.get("source_passenger_profile_id")
        source = passengers_by_id.get(source_id) if source_id else None
        status = (
            "missing_source_reference"
            if not source_id
            else "unresolved_source_reference"
            if not source
            else "cross_agency_source_collision"
            if source.get("agency_id") != record.get("agency_id")
            else "canonical_overlap"
        )
        issues.append(
            {
                "issue_type": f"passenger_master_{status}",
                "severity": "critical" if status == "cross_agency_source_collision" else "warning",
                "record": _record_ref(record),
                "source_passenger_profile_id": source_id,
                "canonical_record": _record_ref(source) if source else None,
                "remediation": "Treat PassengerProfile as authoritative and retain this record as a compatibility projection.",
            }
        )

    relationship_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for relationship in records["client_passenger_relationships"]:
        key = (
            str(relationship.get("agency_id") or ""),
            str(relationship.get("client_id") or ""),
            str(relationship.get("passenger_id") or ""),
        )
        relationship_groups[key].append(relationship)
    for key, group in relationship_groups.items():
        if len(group) > 1:
            issues.append(
                {
                    "issue_type": "duplicate_client_passenger_relationship",
                    "severity": "warning",
                    "agency_id": key[0],
                    "client_profile_id": key[1],
                    "passenger_profile_id": key[2],
                    "relationship_ids": sorted(str(item["id"]) for item in group),
                    "remediation": "Review duplicate canonical relationships without deleting historical evidence.",
                }
            )

    legacy_links_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for link in records["client_passenger_links"]:
        if link.get("source_relationship_id"):
            legacy_links_by_source[str(link["source_relationship_id"])].append(link)
    for source_id, links in legacy_links_by_source.items():
        if len(links) > 1:
            issues.append(
                {
                    "issue_type": "duplicate_legacy_relationship_projection",
                    "severity": "warning",
                    "source_relationship_id": source_id,
                    "legacy_link_ids": sorted(str(item["id"]) for item in links),
                    "remediation": "Keep one canonical relationship and reconcile compatibility projections.",
                }
            )

    client_email_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for client in clients:
        normalized = _normalized(client.get("primary_email"))
        if normalized:
            client_email_groups[normalized].append(client)
    for normalized, group in client_email_groups.items():
        agencies = {str(item.get("agency_id")) for item in group}
        if len(agencies) > 1:
            issues.append(
                {
                    "issue_type": "cross_agency_client_email_collision",
                    "severity": "information",
                    "normalized_email": normalized,
                    "client_candidates": [_record_ref(item) for item in group],
                    "authorization_effect": False,
                    "remediation": "Do not use email to infer tenant or portal scope.",
                }
            )
        same_agency_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in group:
            same_agency_groups[str(item.get("agency_id"))].append(item)
        for tenant, candidates in same_agency_groups.items():
            if len(candidates) > 1:
                issues.append(
                    {
                        "issue_type": "ambiguous_client_email_match",
                        "severity": "warning",
                        "agency_id": tenant,
                        "normalized_email": normalized,
                        "client_candidates": [_record_ref(item) for item in candidates],
                        "authorization_effect": False,
                        "remediation": "Require explicit operator selection; never auto-link.",
                    }
                )

    issues.sort(
        key=lambda item: (
            str(item.get("issue_type") or ""),
            str((item.get("record") or {}).get("agency_id") or item.get("agency_id") or ""),
            str((item.get("record") or {}).get("id") or ""),
        )
    )
    by_type: dict[str, int] = defaultdict(int)
    by_severity: dict[str, int] = defaultdict(int)
    for issue in issues:
        by_type[str(issue["issue_type"])] += 1
        by_severity[str(issue["severity"])] += 1

    return {
        "mode": "dry_run",
        "dry_run": True,
        "writes_performed": 0,
        "agency_scope": agency_id,
        "automatic_subject_selection_disabled": True,
        "email_authorization_disabled": True,
        "write_mode_available": False,
        "requirements_for_future_write_mode": [
            "explicit confirmation",
            "one agency at a time",
            "deterministic reconciliation",
            "audit evidence",
            "rollback manifest",
            "no automatic ambiguous subject selection",
        ],
        "collection_counts": {
            collection: len(items) for collection, items in records.items()
        },
        "summary": {
            "issue_count": len(issues),
            "by_type": dict(sorted(by_type.items())),
            "by_severity": dict(sorted(by_severity.items())),
        },
        "issues": issues,
    }
