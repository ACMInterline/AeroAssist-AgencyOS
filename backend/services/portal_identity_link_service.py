from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from database import Database
from models import AuditEvent, PortalAccessMapping, PortalAccessMappingCreate, now_utc
from persistence_query import MAXIMUM_QUERY_LIMIT, PaginationRequest
from persistence_repository import PersistenceRepository
from security import normalize_email


UNLINKED_PORTAL_MESSAGE = "Your portal account is not linked to a profile yet."
ACTIVE_PORTAL_STATUSES = {"active"}


class PortalIdentityLinkError(ValueError):
    pass


class PortalIdentityLinkConflict(PortalIdentityLinkError):
    pass


class PortalIdentityLinkNotFound(PortalIdentityLinkError):
    pass


def safe_portal_mapping(mapping: Mapping[str, Any]) -> dict[str, Any]:
    client_id = mapping.get("client_profile_id") or mapping.get("client_id")
    return {
        "id": mapping.get("id"),
        "agency_id": mapping.get("agency_id"),
        "auth_identity_id": mapping.get("auth_identity_id"),
        "subject_type": mapping.get("subject_type"),
        "client_profile_id": client_id,
        "passenger_profile_id": mapping.get("passenger_profile_id"),
        "status": mapping.get("status") or mapping.get("portal_status"),
        "portal_status": mapping.get("portal_status") or mapping.get("status"),
        "display_name": mapping.get("display_name"),
        "created_at": mapping.get("created_at"),
        "created_by": mapping.get("created_by"),
        "updated_at": mapping.get("updated_at"),
        "updated_by": mapping.get("updated_by"),
        "revoked_at": mapping.get("revoked_at"),
        "revoked_by": mapping.get("revoked_by"),
        "replacement_mapping_id": mapping.get("replacement_mapping_id"),
        "active_subject_key": mapping.get("active_subject_key"),
        "linkage_version": mapping.get("linkage_version"),
        "last_login_at": mapping.get("last_login_at"),
    }


def safe_portal_subject(subject_type: str, subject: Mapping[str, Any]) -> dict[str, Any]:
    if subject_type == "client":
        fields = (
            "id",
            "display_name",
            "legal_name",
            "client_type",
            "status",
            "portal_status",
            "preferred_language",
            "default_currency",
        )
    else:
        fields = (
            "id",
            "display_name",
            "first_name",
            "middle_name",
            "last_name",
            "passenger_type",
            "status",
            "primary_language",
        )
    return {key: subject.get(key) for key in fields if key in subject}


async def _write_audit(
    db: Database,
    mapping: Mapping[str, Any],
    event_type: str,
    actor_id: str | None,
    summary: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    await db.collection("audit_events").insert_one(
        AuditEvent(
            agency_id=mapping.get("agency_id"),
            actor_user_id=actor_id,
            event_type=event_type,
            entity_type="portal_access_mapping",
            entity_id=str(mapping.get("id")),
            summary=summary,
            metadata=metadata or {},
        ).model_dump(mode="json")
    )


async def _identity(db: Database, identity_id: str) -> dict[str, Any]:
    identity = await db.collection("auth_identities").find_one({"id": identity_id})
    if not identity:
        raise PortalIdentityLinkNotFound("Auth identity not found.")
    if identity.get("status") != "active":
        raise PortalIdentityLinkConflict("Portal identity must be active.")
    return identity


async def _subject(
    db: Database,
    agency_id: str,
    subject_type: str,
    client_profile_id: str | None,
    passenger_profile_id: str | None,
) -> dict[str, Any]:
    if subject_type == "client":
        collection_name = "client_profiles"
        subject_id = client_profile_id
        expected_identity_type = "client_portal"
    elif subject_type == "passenger":
        collection_name = "passenger_profiles"
        subject_id = passenger_profile_id
        expected_identity_type = "passenger_portal"
    else:
        raise PortalIdentityLinkError("Portal subject type must be client or passenger.")
    if not subject_id:
        raise PortalIdentityLinkError(f"{subject_type}_profile_id is required.")
    subject = await db.collection(collection_name).find_one(
        {"agency_id": agency_id, "id": subject_id}
    )
    if not subject or subject.get("status") in {"archived", "quarantined", "duplicate_merged"}:
        raise PortalIdentityLinkNotFound(
            f"Active {subject_type} profile was not found in this agency."
        )
    return {
        "record": subject,
        "subject_id": subject_id,
        "identity_type": expected_identity_type,
    }


async def create_portal_mapping(
    db: Database,
    agency_id: str,
    payload: PortalAccessMappingCreate,
    actor_id: str,
) -> dict[str, Any]:
    identity = await _identity(db, payload.auth_identity_id)
    subject_type = (
        payload.subject_type.value
        if hasattr(payload.subject_type, "value")
        else str(payload.subject_type)
    )
    subject = await _subject(
        db,
        agency_id,
        subject_type,
        payload.client_profile_id,
        payload.passenger_profile_id,
    )
    predecessor = None
    if payload.replaces_mapping_id:
        predecessor = await db.collection("portal_access_mappings").find_one(
            {"agency_id": agency_id, "id": payload.replaces_mapping_id}
        )
        if not predecessor:
            raise PortalIdentityLinkNotFound("Replacement predecessor mapping not found.")
        predecessor_status = predecessor.get("status") or predecessor.get("portal_status")
        if predecessor_status != "revoked":
            raise PortalIdentityLinkConflict(
                "Replacement predecessor must be explicitly revoked first."
            )
        if predecessor.get("replacement_mapping_id"):
            raise PortalIdentityLinkConflict(
                "Replacement predecessor already names a replacement mapping."
            )
        predecessor_subject_id = (
            predecessor.get("client_profile_id")
            or predecessor.get("client_id")
            or predecessor.get("passenger_profile_id")
        )
        if (
            predecessor.get("auth_identity_id") != identity["id"]
            and predecessor_subject_id != subject["subject_id"]
        ):
            raise PortalIdentityLinkConflict(
                "Replacement must retain either the reviewed identity or the reviewed subject."
            )
    if identity.get("identity_type") != subject["identity_type"]:
        raise PortalIdentityLinkConflict(
            f"{subject_type.title()} mapping requires a {subject['identity_type']} identity."
        )
    existing_page = await PersistenceRepository(db).find_platform_records(
        collection_name="portal_access_mappings",
        filters={"auth_identity_id": identity["id"], "status": "active"},
        sort_field="created_at",
        sort_direction="asc",
        pagination=PaginationRequest.build(limit=2),
    )
    if existing_page.items:
        raise PortalIdentityLinkConflict(
            "This identity already has an active portal mapping. Revoke it before creating a replacement."
        )
    subject_filter = {
        "agency_id": agency_id,
        "subject_type": subject_type,
        "status": "active",
        f"{subject_type}_profile_id": subject["subject_id"],
    }
    if await db.collection("portal_access_mappings").find_one(subject_filter):
        raise PortalIdentityLinkConflict(
            "This profile already has an active portal mapping."
        )
    mapping = PortalAccessMapping(
        agency_id=agency_id,
        auth_identity_id=identity["id"],
        subject_type=subject_type,
        client_profile_id=payload.client_profile_id,
        passenger_profile_id=payload.passenger_profile_id,
        status="active",
        portal_status="active",
        created_by=actor_id,
        updated_by=actor_id,
        active_mapping_key=identity["id"],
        active_subject_key=f"{subject_type}:{subject['subject_id']}",
        identity_email_snapshot=identity.get("email"),
        user_email=identity.get("email"),
        display_name=payload.display_name or subject["record"].get("display_name"),
    )
    created = await db.collection("portal_access_mappings").insert_one(
        mapping.model_dump(mode="json")
    )
    if predecessor:
        linked_predecessor = await db.collection("portal_access_mappings").update_one(
            {
                "agency_id": agency_id,
                "id": predecessor["id"],
                "status": "revoked",
                "replacement_mapping_id": None,
            },
            {
                "replacement_mapping_id": created["id"],
                "updated_by": actor_id,
            },
        )
        if not linked_predecessor:
            tombstone = f"revoked+{created['id']}@invalid.aeroassist.local"
            await db.collection("portal_access_mappings").update_one(
                {"agency_id": agency_id, "id": created["id"], "status": "active"},
                {
                    "status": "revoked",
                    "portal_status": "revoked",
                    "revoked_at": now_utc(),
                    "revoked_by": actor_id,
                    "updated_by": actor_id,
                    "revocation_reason": "Replacement predecessor linkage failed.",
                    "active_mapping_key": f"revoked:{created['id']}",
                    "active_subject_key": f"revoked:{created['id']}",
                    "user_email": tombstone,
                },
            )
            raise PortalIdentityLinkConflict(
                "Replacement predecessor changed before linkage could be recorded."
            )
    await _write_audit(
        db,
        created,
        "portal_mapping.created",
        actor_id,
        f"Linked a portal identity to a {subject_type} profile.",
        {
            "subject_type": subject_type,
            "subject_id": subject["subject_id"],
            "auth_identity_id": identity["id"],
            "replaces_mapping_id": payload.replaces_mapping_id,
        },
    )
    return created


async def activate_invited_portal_mapping(
    db: Database,
    invitation: Mapping[str, Any],
    identity: Mapping[str, Any],
    actor_id: str | None,
    display_name: str | None = None,
) -> dict[str, Any]:
    subject_type = (
        "passenger"
        if invitation.get("invitation_type") == "passenger_portal"
        else "client"
    )
    payload = PortalAccessMappingCreate(
        auth_identity_id=str(identity["id"]),
        subject_type=subject_type,
        client_profile_id=invitation.get("target_client_id"),
        passenger_profile_id=invitation.get("target_passenger_id"),
        display_name=display_name,
    )
    if subject_type == "client":
        legacy_page = await PersistenceRepository(db).find_agency_records(
            collection_name="portal_access_mappings",
            agency_id=str(invitation["agency_id"]),
            filters={
                "client_id": invitation.get("target_client_id"),
                "portal_status": "invited",
            },
            sort_field="created_at",
            sort_direction="asc",
            pagination=PaginationRequest.build(limit=MAXIMUM_QUERY_LIMIT),
        )
        invitation_email = normalize_email(str(invitation["invited_email"]))
        legacy_candidates = [
            item
            for item in legacy_page.items
            if not item.get("auth_identity_id")
            and item.get("user_email")
            and normalize_email(str(item["user_email"])) == invitation_email
        ]
        if len(legacy_candidates) > 1:
            raise PortalIdentityLinkConflict(
                "Multiple legacy invitation mappings require operator review."
            )
        if legacy_candidates:
            return await _activate_legacy_invitation_mapping(
                db,
                invitation,
                identity,
                legacy_candidates[0],
                actor_id,
                display_name,
            )
    return await create_portal_mapping(
        db,
        str(invitation["agency_id"]),
        payload,
        actor_id or str(identity["id"]),
    )


async def _activate_legacy_invitation_mapping(
    db: Database,
    invitation: Mapping[str, Any],
    identity: Mapping[str, Any],
    legacy_mapping: Mapping[str, Any],
    actor_id: str | None,
    display_name: str | None,
) -> dict[str, Any]:
    reviewed_identity = await _identity(db, str(identity["id"]))
    subject = await _subject(
        db,
        str(invitation["agency_id"]),
        "client",
        str(invitation["target_client_id"]),
        None,
    )
    if reviewed_identity.get("identity_type") != subject["identity_type"]:
        raise PortalIdentityLinkConflict(
            "Client mapping requires a client_portal identity."
        )
    active_identity_page = await PersistenceRepository(db).find_platform_records(
        collection_name="portal_access_mappings",
        filters={"auth_identity_id": reviewed_identity["id"], "status": "active"},
        sort_field="created_at",
        sort_direction="asc",
        pagination=PaginationRequest.build(limit=2),
    )
    if active_identity_page.items:
        raise PortalIdentityLinkConflict(
            "This identity already has an active portal mapping."
        )
    active_subject = await db.collection("portal_access_mappings").find_one(
        {
            "agency_id": invitation["agency_id"],
            "subject_type": "client",
            "client_profile_id": invitation["target_client_id"],
            "status": "active",
        }
    )
    if active_subject:
        raise PortalIdentityLinkConflict(
            "This profile already has an active portal mapping."
        )
    actor = actor_id or str(reviewed_identity["id"])
    updated = await db.collection("portal_access_mappings").update_one(
        {
            "agency_id": invitation["agency_id"],
            "id": legacy_mapping["id"],
            "portal_status": "invited",
            "auth_identity_id": None,
        },
        {
            "auth_identity_id": reviewed_identity["id"],
            "subject_type": "client",
            "client_profile_id": invitation["target_client_id"],
            "client_id": invitation["target_client_id"],
            "status": "active",
            "portal_status": "active",
            "created_by": legacy_mapping.get("created_by") or actor,
            "updated_by": actor,
            "active_mapping_key": reviewed_identity["id"],
            "active_subject_key": f"client:{invitation['target_client_id']}",
            "identity_email_snapshot": reviewed_identity.get("email"),
            "user_email": reviewed_identity.get("email"),
            "display_name": display_name
            or legacy_mapping.get("display_name")
            or subject["record"].get("display_name"),
            "linkage_version": "explicit_identity_v1",
        },
    )
    if not updated:
        raise PortalIdentityLinkConflict(
            "Legacy invitation mapping changed before activation."
        )
    await _write_audit(
        db,
        updated,
        "portal_mapping.legacy_invitation_activated",
        actor,
        "Activated a reviewed legacy Client Portal invitation as an explicit identity link.",
        {
            "auth_identity_id": reviewed_identity["id"],
            "client_profile_id": invitation["target_client_id"],
            "authorization_by_email": False,
        },
    )
    return updated


async def revoke_portal_mapping(
    db: Database,
    agency_id: str,
    mapping_id: str,
    actor_id: str,
    reason: str,
) -> dict[str, Any]:
    mapping = await db.collection("portal_access_mappings").find_one(
        {"agency_id": agency_id, "id": mapping_id}
    )
    if not mapping:
        raise PortalIdentityLinkNotFound("Portal mapping not found.")
    current_status = mapping.get("status") or mapping.get("portal_status")
    if current_status == "revoked":
        return mapping
    if current_status != "active":
        raise PortalIdentityLinkConflict("Only an active portal mapping can be revoked.")
    # The tombstones keep pre-existing unique email and active-key indexes
    # additive while allowing an explicitly authorized replacement mapping.
    tombstone = f"revoked+{mapping_id}@invalid.aeroassist.local"
    updated = await db.collection("portal_access_mappings").update_one(
        {"agency_id": agency_id, "id": mapping_id, "status": "active"},
        {
            "status": "revoked",
            "portal_status": "revoked",
            "revoked_at": now_utc(),
            "revoked_by": actor_id,
            "updated_by": actor_id,
            "revocation_reason": reason,
            "active_mapping_key": f"revoked:{mapping_id}",
            "active_subject_key": f"revoked:{mapping_id}",
            "user_email": tombstone,
        },
    )
    if not updated:
        raise PortalIdentityLinkConflict("Portal mapping changed before revocation.")
    await _write_audit(
        db,
        updated,
        "portal_mapping.revoked",
        actor_id,
        "Revoked an explicit portal identity link.",
        {"reason": reason},
    )
    return updated


async def resolve_portal_identity_context(
    db: Database,
    auth_identity_id: str,
    *,
    required: bool = True,
) -> dict[str, Any] | None:
    page = await PersistenceRepository(db).find_platform_records(
        collection_name="portal_access_mappings",
        filters={"auth_identity_id": auth_identity_id, "status": "active"},
        sort_field="created_at",
        sort_direction="asc",
        pagination=PaginationRequest.build(limit=2),
    )
    mappings = page.items
    if not mappings:
        if required:
            raise PortalIdentityLinkNotFound(UNLINKED_PORTAL_MESSAGE)
        return None
    if len(mappings) != 1:
        raise PortalIdentityLinkConflict(
            "Portal identity has multiple active mappings and requires operator review."
        )
    mapping = mappings[0]
    subject_type = mapping.get("subject_type")
    subject = await _subject(
        db,
        str(mapping["agency_id"]),
        str(subject_type),
        mapping.get("client_profile_id") or mapping.get("client_id"),
        mapping.get("passenger_profile_id"),
    )
    identity = await _identity(db, auth_identity_id)
    if identity.get("identity_type") != subject["identity_type"]:
        raise PortalIdentityLinkConflict("Portal identity type does not match its linked subject.")
    agency = await db.collection("agencies").find_one({"id": mapping["agency_id"]})
    if not agency:
        raise PortalIdentityLinkNotFound("Portal agency not found.")
    workspace = await db.collection("agency_workspaces").find_one(
        {"agency_id": mapping["agency_id"]}
    )
    return {
        "mapping": mapping,
        "account": mapping,
        "agency": agency,
        "workspace": workspace,
        "subject_type": subject_type,
        "subject": subject["record"],
        "client": subject["record"] if subject_type == "client" else None,
        "passenger": subject["record"] if subject_type == "passenger" else None,
    }
