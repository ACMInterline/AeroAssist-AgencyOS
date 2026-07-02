from __future__ import annotations

import re
from typing import Any

from database import Database
from models import (
    OfferPolicyAdvisorAirlineRow,
    OfferPolicyAdvisorContext,
    OfferPolicyAdvisorContextStatus,
    OfferPolicyAdvisorDecisionNote,
    OfferPolicyAdvisorSavedSnapshot,
    OfferPolicyAdvisorWarning,
    OfferPolicyAdvisorWarningSource,
    PolicyComparisonGeneratedFrom,
    PolicyComparisonWarningLevel,
)
from services.ancillary_pricing_service import AncillaryPricingService
from services.offer_builder_service import OfferBuilderService
from services.policy_comparison_service import PolicyComparisonService
from services.service_mechanics_service import ServiceMechanicsService


PHASE_LABEL = "phase_37_2_offer_policy_advisor_integration_foundation"

CONTEXT_COLLECTION = "offer_policy_advisor_contexts"
AIRLINE_ROW_COLLECTION = "offer_policy_advisor_airline_rows"
WARNING_COLLECTION = "offer_policy_advisor_warnings"
DECISION_NOTE_COLLECTION = "offer_policy_advisor_decision_notes"
SAVED_SNAPSHOT_COLLECTION = "offer_policy_advisor_saved_snapshots"


def payload_dict(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json", exclude_unset=True)
    return dict(payload or {})


def enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def normalize_taxonomy_code(value: Any) -> str | None:
    text = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return text or None


def normalize_airline_code(value: Any) -> str | None:
    text = str(value or "").strip().upper()
    return text or None


def compact_unique(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def warning_level(value: Any) -> str:
    value = enum_value(value) or PolicyComparisonWarningLevel.INFO.value
    return value if value in {item.value for item in PolicyComparisonWarningLevel} else PolicyComparisonWarningLevel.INFO.value


class OfferPolicyAdvisorService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.policy_comparison = PolicyComparisonService(db)
        self.service_mechanics = ServiceMechanicsService(db)
        self.ancillary_pricing = AncillaryPricingService(db)

    async def summary(self, agency_id: str | None = None) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "context_count": len(await self.list_contexts(agency_id=agency_id)),
            "airline_row_count": len(await self.list_airline_rows(agency_id=agency_id)),
            "warning_count": len(await self.list_warnings(agency_id=agency_id)),
            "decision_note_count": len(await self.list_decision_notes(agency_id=agency_id)),
            "saved_snapshot_count": len(await self.list_saved_snapshots(agency_id=agency_id)),
            "deterministic_offer_advisor_integration_enabled": True,
            "auto_recommendation_disabled": True,
            "provider_execution_disabled": True,
            "emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "agency_global_mutation_blocked": True,
            "diagnostic": "Offer policy advisor context is metadata-only and does not auto-select airlines, change offer pricing, book, issue, charge, contact providers, invoice, or settle.",
        }

    async def list_contexts(
        self,
        *,
        agency_id: str | None = None,
        offer_workspace_id: str | None = None,
        offer_option_id: str | None = None,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if offer_workspace_id:
            filters["offer_workspace_id"] = offer_workspace_id
        if offer_option_id:
            filters["offer_option_id"] = offer_option_id
        items = await self.db.collection(CONTEXT_COLLECTION).find_many(filters or None)
        return sorted(items, key=lambda item: str(item.get("created_at") or ""), reverse=True)

    async def get_context(self, context_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        filters = {"id": context_id}
        if agency_id:
            filters["agency_id"] = agency_id
        return await self.db.collection(CONTEXT_COLLECTION).find_one(filters)

    async def build_context(self, agency_id: str, payload: Any, user: dict | None = None) -> dict[str, Any]:
        data = self._normalize_payload(payload_dict(payload))
        workspace_id = data["offer_workspace_id"]
        workspace = await self.db.collection("offer_workspaces").find_one({"agency_id": agency_id, "id": workspace_id})
        if not workspace:
            raise ValueError("Offer workspace not found.")

        options = await self._context_options(agency_id, workspace_id, data.get("offer_option_id"))
        option_ids = [item["id"] for item in options]
        segments = [
            item
            for item in await self.db.collection("offer_builder_segments").find_many({"agency_id": agency_id})
            if item.get("option_id") in option_ids
        ]
        services = await self._workspace_services(agency_id, workspace)
        domain_code, family_code, variant_code = self._taxonomy_from_context(data, services)
        airline_codes = self._airlines_from_context(data, options, segments)
        route_context = {**self._route_context(segments), **(data.get("route_context_json") or {})}
        passenger_context = {**self._passenger_context(workspace, services), **(data.get("passenger_context_json") or {})}
        service_context = {**self._service_context(services), **(data.get("service_context_json") or {})}
        taxonomy_refs = await self._taxonomy_refs(domain_code, family_code, variant_code)

        mechanics_lookup = {}
        initial_warnings: list[dict[str, Any]] = []
        for airline_code in airline_codes:
            lookup = await self.service_mechanics.lookup(
                airline_code=airline_code,
                domain_code=domain_code,
                family_code=family_code,
                variant_code=variant_code,
                agency_id=agency_id,
            )
            mechanics_lookup[airline_code] = lookup
            for message in lookup.get("warnings") or []:
                initial_warnings.append(
                    {
                        "airline_code": airline_code,
                        "warning_type": "service_mechanics_lookup",
                        "message": message,
                        "warning_level": PolicyComparisonWarningLevel.INFO.value,
                        "source": OfferPolicyAdvisorWarningSource.SERVICE_MECHANICS.value,
                    }
                )

        if not options:
            initial_warnings.append(
                {
                    "warning_type": "offer_option_missing",
                    "message": "No offer option is linked to this advisor context.",
                    "warning_level": PolicyComparisonWarningLevel.WARNING.value,
                    "source": OfferPolicyAdvisorWarningSource.CONTEXT.value,
                }
            )
        if not segments:
            initial_warnings.append(
                {
                    "warning_type": "offer_segments_missing",
                    "message": "No offer segments are available for route-specific advisor context.",
                    "warning_level": PolicyComparisonWarningLevel.WARNING.value,
                    "source": OfferPolicyAdvisorWarningSource.CONTEXT.value,
                }
            )

        context = OfferPolicyAdvisorContext(
            agency_id=agency_id,
            offer_workspace_id=workspace_id,
            offer_option_id=data.get("offer_option_id"),
            context_name=data.get("context_name") or f"Advisor context for {workspace.get('title') or workspace_id}",
            airline_codes=airline_codes,
            domain_code=domain_code,
            family_code=family_code,
            variant_code=variant_code,
            service_mechanics_lookup_json=mechanics_lookup,
            taxonomy_refs_json=taxonomy_refs,
            offer_workspace_summary_json=self._workspace_summary(workspace),
            offer_option_summary_json=self._option_summary_payload(options),
            route_context_json=route_context,
            passenger_context_json=passenger_context,
            service_context_json=service_context,
            source_links_json=self._source_links(workspace, options, segments, services),
            warning_count=len(initial_warnings),
            manual_review_required=bool(initial_warnings),
            created_by_user_id=(user or {}).get("id"),
        )
        stored_context = await self.db.collection(CONTEXT_COLLECTION).insert_one(context.model_dump(mode="json"))
        warnings = [
            await self._create_warning(agency_id, stored_context, warning)
            for warning in initial_warnings
        ]
        return {
            "context": {**stored_context, "warning_count": len(warnings), "manual_review_required": bool(warnings)},
            "airline_rows": [],
            "warnings": warnings,
            **self._safety_flags(),
        }

    async def evaluate_context(self, agency_id: str, context_id: str, payload: Any | None = None, user: dict | None = None) -> dict[str, Any] | None:
        context = await self.get_context(context_id, agency_id)
        if not context:
            return None
        data = self._normalize_payload(payload_dict(payload))
        airline_codes = data.get("airline_codes") or context.get("airline_codes") or ["UNKNOWN"]
        route_context = {**(context.get("route_context_json") or {}), **(data.get("route_context_json") or {})}
        passenger_context = {**(context.get("passenger_context_json") or {}), **(data.get("passenger_context_json") or {})}
        service_context = {**(context.get("service_context_json") or {}), **(data.get("service_context_json") or {})}

        advisor_payload = {
            "scenario_name": f"Offer advisor {context.get('context_name') or context_id}",
            "airline_codes": airline_codes,
            "domain_code": context.get("domain_code"),
            "family_code": context.get("family_code"),
            "variant_code": context.get("variant_code"),
            "passenger_age": passenger_context.get("passenger_age"),
            "passenger_type": passenger_context.get("passenger_type"),
            "route_type": route_context.get("route_type"),
            "direct_vs_connecting": route_context.get("direct_vs_connecting"),
            "origin_airport": route_context.get("origin_airport"),
            "destination_airport": route_context.get("destination_airport"),
            "origin_country": route_context.get("origin_country"),
            "destination_country": route_context.get("destination_country"),
            "cabin": route_context.get("cabin") or passenger_context.get("cabin"),
            "segment_count": route_context.get("segment_count"),
            "direction_count": route_context.get("direction_count"),
            "requested_service_context_json": {
                **service_context,
                "offer_policy_advisor_context_id": context_id,
                "offer_workspace_id": context.get("offer_workspace_id"),
                "offer_option_id": context.get("offer_option_id"),
            },
        }
        advisor = await self.policy_comparison.evaluate_advisor(advisor_payload, user, agency_id=agency_id)
        quote_results_by_airline = await self._evaluate_quotes(context, airline_codes, route_context, passenger_context, service_context, user)
        comparison_snapshot = advisor.get("comparison_snapshot") or {}
        advisor_result = advisor.get("result") or {}
        scenario = advisor.get("scenario") or {}

        rows = []
        warnings = []
        mechanics_lookup = context.get("service_mechanics_lookup_json") or {}
        for row in advisor.get("advisory_rows") or []:
            airline_code = normalize_airline_code(row.get("airline_code")) or "UNKNOWN"
            quote_result = quote_results_by_airline.get(airline_code, {})
            offer_row = OfferPolicyAdvisorAirlineRow(
                agency_id=agency_id,
                context_id=context_id,
                offer_workspace_id=context["offer_workspace_id"],
                offer_option_id=context.get("offer_option_id"),
                airline_code=airline_code,
                domain_code=row.get("domain_code") or context.get("domain_code"),
                family_code=row.get("family_code") or context.get("family_code"),
                variant_code=row.get("variant_code") or context.get("variant_code"),
                policy_comparison_snapshot_id=comparison_snapshot.get("id"),
                policy_comparison_row_id=row.get("id"),
                advisor_result_id=advisor_result.get("id"),
                quote_result_id=(quote_result.get("result") or {}).get("id"),
                service_mechanics_lookup_json=mechanics_lookup.get(airline_code) or {},
                ancillary_pricing_quote_json=quote_result,
                taxonomy_refs_json=context.get("taxonomy_refs_json") or {},
                warning_level=warning_level(row.get("warning_level")),
                operational_complexity_score=row.get("operational_complexity_score"),
                manual_contact_required=bool(row.get("manual_contact_required")),
                emd_required=bool(row.get("emd_required")),
                pricing_summary=row.get("pricing_summary"),
                advisor_summary=advisor_result.get("explanation"),
                row_json=row,
            )
            stored_row = await self.db.collection(AIRLINE_ROW_COLLECTION).insert_one(offer_row.model_dump(mode="json"))
            rows.append(stored_row)
            for message in (row.get("row_json") or {}).get("warnings", []):
                warnings.append(
                    await self._create_warning(
                        agency_id,
                        context,
                        {
                            "airline_code": airline_code,
                            "warning_type": "policy_comparison_row",
                            "message": message,
                            "warning_level": row.get("warning_level") or PolicyComparisonWarningLevel.INFO.value,
                            "source": OfferPolicyAdvisorWarningSource.POLICY_COMPARISON.value,
                            "source_record_id": row.get("id"),
                        },
                    )
                )
            for message in ((quote_result.get("result") or {}).get("warnings") or []):
                warnings.append(
                    await self._create_warning(
                        agency_id,
                        context,
                        {
                            "airline_code": airline_code,
                            "warning_type": "ancillary_pricing_quote",
                            "message": message,
                            "warning_level": PolicyComparisonWarningLevel.WARNING.value,
                            "source": OfferPolicyAdvisorWarningSource.ANCILLARY_PRICING.value,
                            "source_record_id": (quote_result.get("result") or {}).get("id"),
                        },
                    )
                )

        for message in advisor_result.get("operational_warnings") or []:
            warnings.append(
                await self._create_warning(
                    agency_id,
                    context,
                    {
                        "warning_type": "service_advisor_result",
                        "message": message,
                        "warning_level": PolicyComparisonWarningLevel.WARNING.value,
                        "source": OfferPolicyAdvisorWarningSource.SERVICE_ADVISOR.value,
                        "source_record_id": advisor_result.get("id"),
                    },
                )
            )

        quote_result_ids = compact_unique([(quote.get("result") or {}).get("id") for quote in quote_results_by_airline.values()])
        all_warnings = await self.list_warnings(agency_id=agency_id, context_id=context_id)
        all_rows = await self.list_airline_rows(agency_id=agency_id, context_id=context_id)
        updates = {
            "context_status": OfferPolicyAdvisorContextStatus.EVALUATED.value,
            "airline_codes": airline_codes,
            "policy_comparison_snapshot_id": comparison_snapshot.get("id"),
            "advisor_scenario_id": scenario.get("id"),
            "advisor_result_id": advisor_result.get("id"),
            "quote_result_ids": quote_result_ids,
            "route_context_json": route_context,
            "passenger_context_json": passenger_context,
            "service_context_json": service_context,
            "row_count": len(all_rows),
            "warning_count": len(all_warnings),
            "manual_review_required": self._manual_review_required(rows, all_warnings),
        }
        updated_context = await self.db.collection(CONTEXT_COLLECTION).update_one({"agency_id": agency_id, "id": context_id}, updates)
        return {
            "context": updated_context,
            "advisor": advisor,
            "airline_rows": rows,
            "warnings": warnings,
            "quote_results": list(quote_results_by_airline.values()),
            **self._safety_flags(),
        }

    async def attach_artifacts(self, agency_id: str, context_id: str, payload: Any) -> dict[str, Any] | None:
        context = await self.get_context(context_id, agency_id)
        if not context:
            return None
        data = payload_dict(payload)
        updates = {
            key: value
            for key, value in {
                "context_status": OfferPolicyAdvisorContextStatus.ATTACHED.value,
                "policy_comparison_snapshot_id": data.get("policy_comparison_snapshot_id") or context.get("policy_comparison_snapshot_id"),
                "advisor_scenario_id": data.get("advisor_scenario_id") or context.get("advisor_scenario_id"),
                "advisor_result_id": data.get("advisor_result_id") or context.get("advisor_result_id"),
                "quote_result_ids": data.get("quote_result_ids") or context.get("quote_result_ids") or [],
            }.items()
            if value is not None
        }
        updated_context = await self.db.collection(CONTEXT_COLLECTION).update_one({"agency_id": agency_id, "id": context_id}, updates)
        return {"context": updated_context, **self._safety_flags()}

    async def create_decision_note(self, agency_id: str, context_id: str, payload: Any, user: dict | None = None) -> dict[str, Any] | None:
        context = await self.get_context(context_id, agency_id)
        if not context:
            return None
        data = payload_dict(payload)
        note = OfferPolicyAdvisorDecisionNote(
            agency_id=agency_id,
            context_id=context_id,
            offer_workspace_id=context["offer_workspace_id"],
            offer_option_id=data.get("offer_option_id") or context.get("offer_option_id"),
            airline_code=normalize_airline_code(data.get("airline_code")),
            note_title=data["note_title"],
            note_body=data["note_body"],
            note_status=enum_value(data.get("note_status")) or "recorded",
            policy_comparison_snapshot_id=context.get("policy_comparison_snapshot_id"),
            advisor_result_id=context.get("advisor_result_id"),
            created_by_user_id=(user or {}).get("id"),
            metadata_json=data.get("metadata_json") or {},
        )
        stored_note = await self.db.collection(DECISION_NOTE_COLLECTION).insert_one(note.model_dump(mode="json"))
        return {"decision_note": stored_note, **self._safety_flags()}

    async def create_saved_snapshot(self, agency_id: str, context_id: str, payload: Any) -> dict[str, Any] | None:
        context = await self.get_context(context_id, agency_id)
        if not context:
            return None
        data = payload_dict(payload)
        rows = await self.list_airline_rows(agency_id=agency_id, context_id=context_id)
        warnings = await self.list_warnings(agency_id=agency_id, context_id=context_id)
        notes = await self.list_decision_notes(agency_id=agency_id, context_id=context_id)
        snapshot = OfferPolicyAdvisorSavedSnapshot(
            agency_id=agency_id,
            context_id=context_id,
            offer_workspace_id=context["offer_workspace_id"],
            offer_option_id=context.get("offer_option_id"),
            snapshot_name=data.get("snapshot_name") or f"Offer advisor snapshot {context.get('context_name') or context_id}",
            policy_comparison_snapshot_id=context.get("policy_comparison_snapshot_id"),
            advisor_scenario_id=context.get("advisor_scenario_id"),
            advisor_result_id=context.get("advisor_result_id"),
            quote_result_ids=context.get("quote_result_ids") or [],
            airline_row_ids=[item["id"] for item in rows],
            warning_ids=[item["id"] for item in warnings],
            decision_note_ids=[item["id"] for item in notes],
            snapshot_json={
                "context": context,
                "airline_rows": rows,
                "warnings": warnings,
                "decision_notes": notes,
                "metadata_json": data.get("metadata_json") or {},
                "metadata_only": True,
            },
        )
        stored_snapshot = await self.db.collection(SAVED_SNAPSHOT_COLLECTION).insert_one(snapshot.model_dump(mode="json"))
        return {"saved_snapshot": stored_snapshot, **self._safety_flags()}

    async def list_airline_rows(
        self,
        *,
        agency_id: str | None = None,
        context_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_agency_records(AIRLINE_ROW_COLLECTION, agency_id=agency_id, context_id=context_id, offer_workspace_id=offer_workspace_id)

    async def list_warnings(
        self,
        *,
        agency_id: str | None = None,
        context_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_agency_records(WARNING_COLLECTION, agency_id=agency_id, context_id=context_id, offer_workspace_id=offer_workspace_id)

    async def list_decision_notes(
        self,
        *,
        agency_id: str | None = None,
        context_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_agency_records(DECISION_NOTE_COLLECTION, agency_id=agency_id, context_id=context_id, offer_workspace_id=offer_workspace_id)

    async def list_saved_snapshots(
        self,
        *,
        agency_id: str | None = None,
        context_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_agency_records(SAVED_SNAPSHOT_COLLECTION, agency_id=agency_id, context_id=context_id, offer_workspace_id=offer_workspace_id)

    async def _list_agency_records(
        self,
        collection_name: str,
        *,
        agency_id: str | None = None,
        context_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if context_id:
            filters["context_id"] = context_id
        if offer_workspace_id:
            filters["offer_workspace_id"] = offer_workspace_id
        items = await self.db.collection(collection_name).find_many(filters or None)
        return sorted(items, key=lambda item: str(item.get("created_at") or ""), reverse=True)

    async def _create_warning(self, agency_id: str, context: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        warning = OfferPolicyAdvisorWarning(
            agency_id=agency_id,
            context_id=context["id"],
            offer_workspace_id=context["offer_workspace_id"],
            offer_option_id=context.get("offer_option_id"),
            airline_code=normalize_airline_code(data.get("airline_code")),
            warning_level=warning_level(data.get("warning_level")),
            warning_type=data.get("warning_type") or "advisor_warning",
            message=data.get("message") or "Manual review required.",
            source=enum_value(data.get("source")) or OfferPolicyAdvisorWarningSource.CONTEXT.value,
            source_record_id=data.get("source_record_id"),
            human_review_required=True,
        )
        return await self.db.collection(WARNING_COLLECTION).insert_one(warning.model_dump(mode="json"))

    async def _context_options(self, agency_id: str, workspace_id: str, option_id: str | None) -> list[dict[str, Any]]:
        if option_id:
            option = await self.db.collection("offer_options").find_one({"agency_id": agency_id, "workspace_id": workspace_id, "id": option_id})
            if not option:
                raise ValueError("Offer option not found.")
            return [option]
        return await self.db.collection("offer_options").find_many({"agency_id": agency_id, "workspace_id": workspace_id})

    async def _workspace_services(self, agency_id: str, workspace: dict[str, Any]) -> list[dict[str, Any]]:
        return await OfferBuilderService(self.db)._workspace_services(agency_id, workspace)

    async def _taxonomy_refs(self, domain_code: str, family_code: str, variant_code: str | None) -> dict[str, Any]:
        domain = await self.db.collection("canonical_service_domains").find_one({"code": domain_code})
        family = await self.db.collection("canonical_service_families").find_one({"domain_code": domain_code, "code": family_code})
        variant = None
        if variant_code:
            variant = await self.db.collection("canonical_service_variants").find_one({"domain_code": domain_code, "family_code": family_code, "code": variant_code})
        return {
            "domain": {"code": domain_code, "id": (domain or {}).get("id"), "name": (domain or {}).get("name")},
            "family": {"code": family_code, "id": (family or {}).get("id"), "name": (family or {}).get("name")},
            "variant": {"code": variant_code, "id": (variant or {}).get("id"), "name": (variant or {}).get("name")} if variant_code else None,
        }

    async def _evaluate_quotes(
        self,
        context: dict[str, Any],
        airline_codes: list[str],
        route_context: dict[str, Any],
        passenger_context: dict[str, Any],
        service_context: dict[str, Any],
        user: dict | None,
    ) -> dict[str, dict[str, Any]]:
        quote_results = {}
        for airline_code in airline_codes:
            payload = {
                "airline_code": airline_code,
                "domain_code": context.get("domain_code"),
                "family_code": context.get("family_code"),
                "variant_code": context.get("variant_code"),
                "scenario_name": f"Offer advisor quote {context.get('context_name') or context['id']} {airline_code}",
                "passenger_age": passenger_context.get("passenger_age"),
                "passenger_type": passenger_context.get("passenger_type"),
                "route_type": route_context.get("route_type"),
                "direct_vs_connecting": route_context.get("direct_vs_connecting"),
                "origin_airport": route_context.get("origin_airport"),
                "destination_airport": route_context.get("destination_airport"),
                "origin_country": route_context.get("origin_country"),
                "destination_country": route_context.get("destination_country"),
                "cabin": route_context.get("cabin") or passenger_context.get("cabin"),
                "segment_count": route_context.get("segment_count"),
                "direction_count": route_context.get("direction_count"),
                "currency": (context.get("offer_workspace_summary_json") or {}).get("currency"),
                "context_json": {
                    "offer_policy_advisor_context_id": context["id"],
                    "offer_workspace_id": context.get("offer_workspace_id"),
                    "offer_option_id": context.get("offer_option_id"),
                    "service_context_json": service_context,
                },
            }
            quote_results[airline_code] = await self.ancillary_pricing.evaluate(payload, user, agency_id=context["agency_id"])
        return quote_results

    def _normalize_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(data)
        if "airline_codes" in normalized and normalized["airline_codes"] is not None:
            normalized["airline_codes"] = compact_unique([normalize_airline_code(item) for item in normalized.get("airline_codes") or []])
        for key in ["domain_code", "family_code", "variant_code"]:
            if key in normalized:
                normalized[key] = normalize_taxonomy_code(normalized.get(key))
        for key, value in list(normalized.items()):
            normalized[key] = enum_value(value)
        return normalized

    def _taxonomy_from_context(self, data: dict[str, Any], services: list[dict[str, Any]]) -> tuple[str, str, str | None]:
        if data.get("domain_code") and data.get("family_code"):
            return data["domain_code"], data["family_code"], data.get("variant_code")
        service = services[0] if services else {}
        service_code = normalize_taxonomy_code(service.get("service_key") or service.get("service_type") or service.get("service_code"))
        category = normalize_taxonomy_code(service.get("service_catalogue_category") or service.get("category"))
        if service_code in {"wchr", "wchs", "wchc", "wcbd", "wcbw", "wcmp"}:
            return "mobility", "wheelchair", service_code
        if service_code in {"petc", "avih"}:
            return "pet_transport", "pet_in_cabin" if service_code == "petc" else "pet_in_hold", service_code
        return data.get("domain_code") or category or "other", data.get("family_code") or service_code or "general", data.get("variant_code")

    def _airlines_from_context(self, data: dict[str, Any], options: list[dict[str, Any]], segments: list[dict[str, Any]]) -> list[str]:
        explicit = compact_unique([normalize_airline_code(item) for item in data.get("airline_codes") or []])
        if explicit:
            return explicit
        codes = []
        for option in options:
            codes.append(option.get("main_airline_code"))
        for segment in segments:
            codes.extend([segment.get("marketing_airline_code"), segment.get("operating_airline_code")])
        return compact_unique([normalize_airline_code(item) for item in codes]) or ["UNKNOWN"]

    def _route_context(self, segments: list[dict[str, Any]]) -> dict[str, Any]:
        ordered = sorted(segments, key=lambda item: (int(item.get("sequence") or 0), str(item.get("departure_at") or "")))
        if not ordered:
            return {"segment_count": 0, "direction_count": 1}
        cabins = compact_unique([item.get("cabin_class") for item in ordered])
        return {
            "origin_airport": ordered[0].get("origin_airport"),
            "destination_airport": ordered[-1].get("destination_airport"),
            "segment_count": len(ordered),
            "direction_count": 1,
            "direct_vs_connecting": "direct" if len(ordered) == 1 else "connecting",
            "route_type": "unknown",
            "cabin": cabins[0] if cabins else None,
            "marketing_airlines": compact_unique([item.get("marketing_airline_code") for item in ordered]),
        }

    def _passenger_context(self, workspace: dict[str, Any], services: list[dict[str, Any]]) -> dict[str, Any]:
        client_summary = workspace.get("client_summary_json") or {}
        service_metadata = (services[0].get("metadata_json") or {}) if services else {}
        return {
            "passenger_type": service_metadata.get("passenger_type") or "adult",
            "passenger_count": client_summary.get("passenger_count"),
        }

    def _service_context(self, services: list[dict[str, Any]]) -> dict[str, Any]:
        service = services[0] if services else {}
        service_code = service.get("service_key") or service.get("service_type") or service.get("service_code")
        return {
            "service_code": service_code,
            "service_label": service.get("service_label"),
            "service_count": len(services),
            "services": services,
        }

    def _workspace_summary(self, workspace: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": workspace.get("id"),
            "title": workspace.get("title"),
            "request_id": workspace.get("request_id"),
            "trip_id": workspace.get("trip_id"),
            "status": workspace.get("status"),
            "currency": workspace.get("currency"),
            "client_summary_json": workspace.get("client_summary_json") or {},
        }

    def _option_summary_payload(self, options: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "option_count": len(options),
            "options": [
                {
                    "id": option.get("id"),
                    "label": option.get("label"),
                    "status": option.get("status"),
                    "main_airline_code": option.get("main_airline_code"),
                    "provider_name": option.get("provider_name"),
                    "pricing_summary_json": option.get("pricing_summary_json") or {},
                }
                for option in options
            ],
        }

    def _source_links(
        self,
        workspace: dict[str, Any],
        options: list[dict[str, Any]],
        segments: list[dict[str, Any]],
        services: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        links = [{"type": "offer_workspace", "id": workspace.get("id")}]
        links.extend({"type": "offer_option", "id": item.get("id")} for item in options)
        links.extend({"type": "offer_builder_segment", "id": item.get("id")} for item in segments)
        links.extend({"type": "service_context", "id": item.get("id")} for item in services if item.get("id"))
        return links

    def _manual_review_required(self, rows: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> bool:
        if warnings:
            return True
        return any(
            row.get("manual_contact_required")
            or row.get("warning_level") in {PolicyComparisonWarningLevel.WARNING.value, PolicyComparisonWarningLevel.BLOCKER.value}
            for row in rows
        )

    def _safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "auto_recommendation_disabled": True,
            "recommendations_disabled": True,
            "provider_execution_disabled": True,
            "emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "offer_pricing_unchanged": True,
            "live_booking_disabled": True,
        }
