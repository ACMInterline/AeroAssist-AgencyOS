from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from database import Database
from models import (
    AirlineDistributionSummary,
    AirlineGroupRelationship,
    AirlineHubAssignment,
    AirlineIdentityAlias,
    AirlineMasterProfile,
    AirlineMasterProfileCreate,
    AirlineMasterProfileUpdate,
    AirlineOperationalClassification,
    AirlineProfileEvidenceLink,
    AirlineProfileRevision,
    AirlineServiceDeskSummary,
    AuditEvent,
)


PHASE_LABEL = "phase_55_9_airline_intelligence_scale_release_readiness_foundation"

PROFILE_COLLECTION = "airline_master_profiles"
ALIAS_COLLECTION = "airline_identity_aliases"
RELATIONSHIP_COLLECTION = "airline_group_relationships"
HUB_COLLECTION = "airline_hub_assignments"
CLASSIFICATION_COLLECTION = "airline_operational_classifications"
DISTRIBUTION_COLLECTION = "airline_distribution_summaries"
SERVICE_DESK_COLLECTION = "airline_service_desk_summaries"
EVIDENCE_COLLECTION = "airline_profile_evidence_links"
REVISION_COLLECTION = "airline_profile_revisions"

PROFILE_COLLECTIONS = [
    PROFILE_COLLECTION,
    ALIAS_COLLECTION,
    RELATIONSHIP_COLLECTION,
    HUB_COLLECTION,
    CLASSIFICATION_COLLECTION,
    DISTRIBUTION_COLLECTION,
    SERVICE_DESK_COLLECTION,
    EVIDENCE_COLLECTION,
    REVISION_COLLECTION,
]

PUBLIC_REVIEW_STATUSES = {"approved", "published"}
CONFIDENCE_WEIGHTS = {"low": 25, "medium": 55, "high": 80, "official_source": 95}


class AirlineMasterProfileError(ValueError):
    pass


def normalize_identity(value: Any) -> str:
    return " ".join(str(value or "").strip().upper().split())


def payload_dict(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json", exclude_unset=True)
    return dict(payload or {})


def effective_now(record: dict[str, Any], today: date | None = None) -> bool:
    today = today or datetime.now(timezone.utc).date()
    effective_from = record.get("effective_from")
    effective_to = record.get("effective_to")
    if isinstance(effective_from, str):
        effective_from = date.fromisoformat(effective_from[:10])
    if isinstance(effective_to, str):
        effective_to = date.fromisoformat(effective_to[:10])
    return not ((effective_from and effective_from > today) or (effective_to and effective_to < today))


class AirlineMasterProfileIntelligenceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def safety_flags(self) -> dict[str, bool]:
        return {
            "canonical_airline_identity_reused": True,
            "duplicate_airline_catalogue_disabled": True,
            "raw_source_truth_preserved": True,
            "conflicting_evidence_preserved": True,
            "effective_dating_enabled": True,
            "revision_history_enabled": True,
            "agency_read_only": True,
            "internal_notes_restricted": True,
            "client_safe_projection_enabled": True,
            "automatic_production_seeding_disabled": True,
            "external_api_calls_disabled": True,
            "provider_execution_disabled": True,
            "ai_disabled": True,
            "metadata_only": True,
        }

    async def resolve_canonical_airline(self, identifier: str) -> dict[str, Any] | None:
        airline = await self.db.collection("airline_profiles").find_one({"id": identifier})
        normalized = normalize_identity(identifier)
        if airline is None and normalized:
            airline = await self.db.collection("airline_profiles").find_one({"airline_code": normalized})
        if airline is None and normalized:
            airline = await self.db.collection("airline_profiles").find_one({"icao_code": normalized})
        if airline is None and normalized:
            alias = await self.db.collection(ALIAS_COLLECTION).find_one({"normalized_alias": normalized})
            if alias:
                airline = await self.db.collection("airline_profiles").find_one({"id": alias["canonical_airline_id"]})
        return airline

    async def list_profiles(
        self,
        *,
        search: str | None = None,
        review_status: str | None = None,
        agency_safe: bool = False,
    ) -> list[dict[str, Any]]:
        airlines = await self.db.collection("airline_profiles").find_many()
        profiles = await self.db.collection(PROFILE_COLLECTION).find_many()
        by_airline = {item["canonical_airline_id"]: item for item in profiles}
        query = normalize_identity(search)
        results: list[dict[str, Any]] = []
        for airline in airlines:
            profile = by_airline.get(airline["id"])
            if agency_safe and (not profile or profile.get("review_status") not in PUBLIC_REVIEW_STATUSES or not effective_now(profile)):
                continue
            if review_status and (profile or {}).get("review_status") != review_status:
                continue
            haystack = " ".join(
                normalize_identity(value)
                for value in [airline.get("airline_code"), airline.get("icao_code"), airline.get("airline_name"), (profile or {}).get("commercial_name")]
            )
            if query and query not in haystack:
                continue
            results.append(await self.build_profile_view(airline, profile, agency_safe=agency_safe))
        return sorted(results, key=lambda item: (item["identity"].get("commercial_name") or "", item["identity"].get("iata_code") or ""))

    async def get_profile(self, identifier: str, *, agency_safe: bool = False) -> dict[str, Any]:
        airline = await self.resolve_canonical_airline(identifier)
        if airline is None:
            raise AirlineMasterProfileError("Canonical airline identity was not found.")
        profile = await self.db.collection(PROFILE_COLLECTION).find_one({"canonical_airline_id": airline["id"]})
        if agency_safe and (not profile or profile.get("review_status") not in PUBLIC_REVIEW_STATUSES or not effective_now(profile)):
            raise AirlineMasterProfileError("No approved or published airline profile is available.")
        return await self.build_profile_view(airline, profile, agency_safe=agency_safe)

    async def build_profile_view(
        self,
        airline: dict[str, Any],
        profile: dict[str, Any] | None,
        *,
        agency_safe: bool,
    ) -> dict[str, Any]:
        airline_id = airline["id"]
        intelligence = await self.db.collection("airline_intelligence_profiles").find_one({"airline_id": airline_id})
        if intelligence is None and airline.get("airline_code"):
            intelligence = await self.db.collection("airline_intelligence_profiles").find_one({"iata_code": airline["airline_code"]})
        aliases = await self._related(ALIAS_COLLECTION, airline_id, agency_safe)
        relationships = await self._related(RELATIONSHIP_COLLECTION, airline_id, agency_safe)
        hubs = await self._related(HUB_COLLECTION, airline_id, agency_safe)
        classifications = await self._related(CLASSIFICATION_COLLECTION, airline_id, agency_safe)
        distributions = await self._related(DISTRIBUTION_COLLECTION, airline_id, agency_safe)
        service_desks = await self._related(SERVICE_DESK_COLLECTION, airline_id, agency_safe)
        evidence = await self._related(EVIDENCE_COLLECTION, airline_id, agency_safe)
        revisions = [] if agency_safe else await self.db.collection(REVISION_COLLECTION).find_many({"canonical_airline_id": airline_id})

        identity = {
            "canonical_airline_id": airline_id,
            "legal_name": (intelligence or {}).get("legal_name") or airline.get("airline_name"),
            "commercial_name": (profile or {}).get("commercial_name") or airline.get("airline_name"),
            "iata_code": airline.get("airline_code"),
            "icao_code": airline.get("icao_code") or (intelligence or {}).get("icao_code"),
            "accounting_prefix_code": (profile or {}).get("accounting_prefix_code") or (intelligence or {}).get("numeric_code"),
            "country_of_registration": airline.get("country") or (intelligence or {}).get("base_country"),
            "operating_status": airline.get("status"),
            "airline_type": (profile or {}).get("airline_type") or "unknown",
            "active_status": (profile or {}).get("active_status") or airline.get("status") or "unknown",
        }
        score = self.calculate_completeness(identity, profile, aliases, relationships, hubs, classifications, distributions, service_desks, evidence)
        confidence = self.calculate_confidence(profile, evidence, score["score"])
        operational_summary = await self._operational_summary(airline_id, airline, relationships, hubs, classifications, distributions, service_desks)
        result = {
            "identity": identity,
            "profile": self._safe_record(profile, agency_safe),
            "legacy_intelligence_profile": self._safe_record(intelligence, agency_safe),
            "aliases": aliases,
            "relationships": relationships,
            "hub_assignments": hubs,
            "operational_classifications": classifications,
            "distribution_summaries": distributions,
            "service_desk_summaries": service_desks,
            "evidence": evidence,
            "revision_history": sorted(revisions, key=lambda item: item.get("version", 0), reverse=True),
            "completeness": score,
            "confidence": confidence,
            "operational_summary": operational_summary,
            "client_safe_identity": self.client_safe_identity(identity, operational_summary, confidence),
            "unknown_fields": score["missing_fields"],
            "manual_review_required": bool(score["missing_fields"] or confidence["conflicting_evidence_count"]),
            **self.safety_flags(),
        }
        return result

    async def _related(self, collection: str, airline_id: str, agency_safe: bool) -> list[dict[str, Any]]:
        items = await self.db.collection(collection).find_many({"canonical_airline_id": airline_id})
        if agency_safe:
            items = [item for item in items if item.get("review_status", "approved") in PUBLIC_REVIEW_STATUSES and effective_now(item)]
        return [self._safe_record(item, agency_safe) for item in items]

    def _safe_record(self, record: dict[str, Any] | None, agency_safe: bool) -> dict[str, Any] | None:
        if record is None or not agency_safe:
            return record
        restricted = {
            "internal_notes",
            "source_metadata_json",
            "before_snapshot",
            "after_snapshot",
            "actor_user_id",
        }
        safe = {key: value for key, value in record.items() if key not in restricted}
        if "source_collection" in safe:
            safe["source_reference_restricted"] = True
            safe.pop("source_collection", None)
            safe.pop("source_record_id", None)
        return safe

    def calculate_completeness(
        self,
        identity: dict[str, Any],
        profile: dict[str, Any] | None,
        aliases: list[dict[str, Any]],
        relationships: list[dict[str, Any]],
        hubs: list[dict[str, Any]],
        classifications: list[dict[str, Any]],
        distributions: list[dict[str, Any]],
        service_desks: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
    ) -> dict[str, Any]:
        checks = {
            "legal_name": identity.get("legal_name"),
            "commercial_name": identity.get("commercial_name"),
            "iata_code": identity.get("iata_code"),
            "icao_code": identity.get("icao_code"),
            "accounting_prefix_code": identity.get("accounting_prefix_code"),
            "country_of_registration": identity.get("country_of_registration"),
            "operating_status": identity.get("operating_status"),
            "airline_type": identity.get("airline_type") not in {None, "", "unknown"},
            "governance_profile": profile,
            "aliases": aliases,
            "relationships": relationships,
            "hubs": hubs,
            "operational_classification": classifications,
            "distribution_summary": distributions,
            "service_desk_summary": service_desks,
            "evidence": evidence,
            "effective_date": (profile or {}).get("effective_from"),
            "review_status": (profile or {}).get("review_status") in PUBLIC_REVIEW_STATUSES,
            "last_verified_at": (profile or {}).get("last_verified_at"),
            "source_references": (profile or {}).get("source_reference_ids"),
        }
        missing = [key for key, value in checks.items() if not value]
        score = round((len(checks) - len(missing)) * 100 / len(checks))
        return {"score": score, "completed_fields": len(checks) - len(missing), "total_fields": len(checks), "missing_fields": missing}

    def calculate_confidence(self, profile: dict[str, Any] | None, evidence: list[dict[str, Any]], completeness: int) -> dict[str, Any]:
        base = CONFIDENCE_WEIGHTS.get((profile or {}).get("confidence", "low"), 25)
        verified = len([item for item in evidence if item.get("evidence_status") in {"verified", "approved", "published"}])
        conflicts = len([item for item in evidence if item.get("conflict_status") not in {None, "none", "resolved"}])
        score = max(0, min(100, round(base * 0.55 + completeness * 0.25 + min(verified, 5) * 5 - conflicts * 10)))
        level = "high" if score >= 75 else "medium" if score >= 50 else "low"
        return {"score": score, "level": level, "verified_evidence_count": verified, "conflicting_evidence_count": conflicts}

    async def _operational_summary(
        self,
        airline_id: str,
        airline: dict[str, Any],
        relationships: list[dict[str, Any]],
        hubs: list[dict[str, Any]],
        classifications: list[dict[str, Any]],
        distributions: list[dict[str, Any]],
        service_desks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        capability_rows = await self.db.collection("airline_capability_matrix").find_many({"airline_code": airline.get("airline_code")})
        contacts = await self.db.collection("airline_contacts").find_many({"airline_id": airline_id})
        routes = await self.db.collection("airline_routes").find_many({"airline_id": airline_id})
        return {
            "alliance": airline.get("alliance"),
            "relationship_count": len(relationships),
            "primary_hubs": [item.get("airport_code") for item in hubs if item.get("assignment_type") == "primary_hub"],
            "focus_cities": [item.get("airport_code") for item in hubs if item.get("assignment_type") == "focus_city"],
            "classifications": sorted({value for item in classifications for value in item.get("classifications", [])}),
            "route_regions": sorted({value for item in classifications for value in item.get("route_regions", [])}),
            "distribution_known": bool(distributions),
            "service_desks_known": [item.get("desk_type") for item in service_desks if item.get("available") is True],
            "contact_count": len(contacts),
            "route_count": len(routes),
            "capability_record_count": len(capability_rows),
            "policy_link": f"/agency/airline-policy-library?airline={airline.get('airline_code') or ''}",
            "capability_link": f"/agency/capability-matrix?airline={airline.get('airline_code') or ''}",
        }

    def client_safe_identity(self, identity: dict[str, Any], operational_summary: dict[str, Any], confidence: dict[str, Any]) -> dict[str, Any]:
        return {
            "canonical_airline_id": identity.get("canonical_airline_id"),
            "commercial_name": identity.get("commercial_name"),
            "iata_code": identity.get("iata_code"),
            "icao_code": identity.get("icao_code"),
            "country_of_registration": identity.get("country_of_registration"),
            "operating_status": identity.get("operating_status"),
            "alliance": operational_summary.get("alliance"),
            "evidence_freshness": confidence.get("level"),
        }

    async def create_profile(self, payload: AirlineMasterProfileCreate, user: dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        airline = await self.resolve_canonical_airline(data["canonical_airline_id"])
        if airline is None:
            raise AirlineMasterProfileError("A profile can only enrich an existing canonical airline identity.")
        existing = await self.db.collection(PROFILE_COLLECTION).find_one({"canonical_airline_id": airline["id"]})
        if existing:
            raise AirlineMasterProfileError("An enriched profile already exists for this canonical airline.")
        data["canonical_airline_id"] = airline["id"]
        created = await self.db.collection(PROFILE_COLLECTION).insert_one(AirlineMasterProfile(**data).model_dump(mode="json"))
        await self._write_revision(created, None, created, "created", user, "Initial enriched airline profile.")
        await self._audit("airline_master_profile.created", created["id"], user, {"canonical_airline_id": airline["id"]})
        return await self.get_profile(airline["id"])

    async def update_profile(self, identifier: str, payload: AirlineMasterProfileUpdate, user: dict[str, Any], reason: str | None = None) -> dict[str, Any]:
        airline = await self.resolve_canonical_airline(identifier)
        if airline is None:
            raise AirlineMasterProfileError("Canonical airline identity was not found.")
        before = await self.db.collection(PROFILE_COLLECTION).find_one({"canonical_airline_id": airline["id"]})
        if before is None:
            raise AirlineMasterProfileError("Enriched airline profile was not found.")
        updates = payload_dict(payload)
        updates["version"] = int(before.get("version") or 1) + 1
        after = await self.db.collection(PROFILE_COLLECTION).update_one({"id": before["id"]}, updates)
        if after is None:
            raise AirlineMasterProfileError("Enriched airline profile could not be updated.")
        await self._write_revision(after, before, after, "updated", user, reason)
        await self._audit("airline_master_profile.updated", after["id"], user, {"changed_fields": sorted(updates)})
        return await self.get_profile(airline["id"])

    async def create_alias(self, identifier: str, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        airline = await self._require_airline(identifier)
        data = payload_dict(payload)
        data.update({"canonical_airline_id": airline["id"], "normalized_alias": normalize_identity(data.get("alias"))})
        if not data["normalized_alias"]:
            raise AirlineMasterProfileError("Alias is required.")
        duplicate = await self.db.collection(ALIAS_COLLECTION).find_one({"normalized_alias": data["normalized_alias"]})
        if duplicate:
            raise AirlineMasterProfileError("This alias is already mapped and requires duplicate-candidate review.")
        created = await self.db.collection(ALIAS_COLLECTION).insert_one(AirlineIdentityAlias(**data).model_dump(mode="json"))
        await self._audit("airline_master_profile.alias_created", created["id"], user, {"canonical_airline_id": airline["id"]})
        return created

    async def create_relationship(self, identifier: str, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        return await self._create_related(identifier, payload, AirlineGroupRelationship, RELATIONSHIP_COLLECTION, "relationship", user)

    async def create_hub(self, identifier: str, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        data["airport_code"] = normalize_identity(data.get("airport_code"))
        return await self._create_related(identifier, data, AirlineHubAssignment, HUB_COLLECTION, "hub", user)

    async def create_classification(self, identifier: str, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        return await self._create_related(identifier, payload, AirlineOperationalClassification, CLASSIFICATION_COLLECTION, "classification", user)

    async def create_distribution(self, identifier: str, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        return await self._create_related(identifier, payload, AirlineDistributionSummary, DISTRIBUTION_COLLECTION, "distribution", user)

    async def create_service_desk(self, identifier: str, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        return await self._create_related(identifier, payload, AirlineServiceDeskSummary, SERVICE_DESK_COLLECTION, "service_desk", user)

    async def create_evidence_link(self, identifier: str, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        return await self._create_related(identifier, payload, AirlineProfileEvidenceLink, EVIDENCE_COLLECTION, "evidence", user)

    async def _create_related(self, identifier: str, payload: dict[str, Any], model: Any, collection: str, event: str, user: dict[str, Any]) -> dict[str, Any]:
        airline = await self._require_airline(identifier)
        data = payload_dict(payload)
        data["canonical_airline_id"] = airline["id"]
        created = await self.db.collection(collection).insert_one(model(**data).model_dump(mode="json"))
        await self._audit(f"airline_master_profile.{event}_created", created["id"], user, {"canonical_airline_id": airline["id"]})
        return created

    async def _require_airline(self, identifier: str) -> dict[str, Any]:
        airline = await self.resolve_canonical_airline(identifier)
        if airline is None:
            raise AirlineMasterProfileError("Canonical airline identity was not found.")
        return airline

    async def _write_revision(
        self,
        profile: dict[str, Any],
        before: dict[str, Any] | None,
        after: dict[str, Any],
        change_type: str,
        user: dict[str, Any],
        reason: str | None,
    ) -> None:
        changed = sorted(key for key in after if key not in {"updated_at"} and (before or {}).get(key) != after.get(key))
        revision = AirlineProfileRevision(
            canonical_airline_id=profile["canonical_airline_id"],
            profile_id=profile["id"],
            version=int(profile.get("version") or 1),
            change_type=change_type,
            changed_fields=changed,
            before_snapshot=before or {},
            after_snapshot=after,
            change_reason=reason,
            actor_user_id=user.get("id"),
        )
        await self.db.collection(REVISION_COLLECTION).insert_one(revision.model_dump(mode="json"))

    async def _audit(self, event_type: str, entity_id: str, user: dict[str, Any], metadata: dict[str, Any]) -> None:
        event = AuditEvent(
            actor_user_id=user.get("id"),
            event_type=event_type,
            entity_type="airline_master_profile_intelligence",
            entity_id=entity_id,
            summary=event_type.replace(".", " ").replace("_", " ").title(),
            metadata=metadata,
        )
        await self.db.collection("audit_events").insert_one(event.model_dump(mode="json"))

    async def duplicate_candidates(self) -> list[dict[str, Any]]:
        airlines = await self.db.collection("airline_profiles").find_many()
        aliases = await self.db.collection(ALIAS_COLLECTION).find_many()
        candidates: list[dict[str, Any]] = []
        values: dict[str, list[dict[str, Any]]] = {}
        for airline in airlines:
            for value in [airline.get("airline_code"), airline.get("icao_code"), airline.get("airline_name")]:
                normalized = normalize_identity(value)
                if normalized:
                    values.setdefault(normalized, []).append({"canonical_airline_id": airline["id"], "source": "canonical_identity", "value": value})
        for alias in aliases:
            values.setdefault(alias["normalized_alias"], []).append({"canonical_airline_id": alias["canonical_airline_id"], "source": "alias", "value": alias["alias"]})
        for key, matches in values.items():
            airline_ids = sorted({item["canonical_airline_id"] for item in matches})
            if len(airline_ids) > 1:
                candidates.append({"normalized_identity": key, "canonical_airline_ids": airline_ids, "matches": matches, "resolution_status": "manual_review_required"})
        return candidates

    async def coverage(self) -> dict[str, Any]:
        airlines = await self.db.collection("airline_profiles").find_many()
        profiles = await self.db.collection(PROFILE_COLLECTION).find_many()
        evidence = await self.db.collection(EVIDENCE_COLLECTION).find_many()
        status_counts: dict[str, int] = {}
        for profile in profiles:
            status = profile.get("review_status") or "unknown"
            status_counts[status] = status_counts.get(status, 0) + 1
        return {
            "canonical_airline_count": len(airlines),
            "enriched_profile_count": len(profiles),
            "approved_or_published_count": len([item for item in profiles if item.get("review_status") in PUBLIC_REVIEW_STATUSES]),
            "missing_enriched_profile_count": max(0, len(airlines) - len(profiles)),
            "evidence_link_count": len(evidence),
            "conflicting_evidence_count": len([item for item in evidence if item.get("conflict_status") not in {None, "none", "resolved"}]),
            "duplicate_candidate_count": len(await self.duplicate_candidates()),
            "review_status_counts": status_counts,
        }

    async def response(self, *, search: str | None = None, review_status: str | None = None, agency_safe: bool = False) -> dict[str, Any]:
        items = await self.list_profiles(search=search, review_status=review_status, agency_safe=agency_safe)
        coverage = (
            {"visible_profile_count": len(items), "approved_or_published_count": len(items)}
            if agency_safe
            else await self.coverage()
        )
        return {"phase": PHASE_LABEL, "items": items, "count": len(items), "coverage": coverage, **self.safety_flags()}
