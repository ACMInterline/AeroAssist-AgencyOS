from __future__ import annotations

from typing import Any

from database import Database
from models import AirlineOperationalIntelligenceArchitecture


PHASE_LABEL = "phase_42_0_document_workspace_foundation"
ARCHITECTURE_COLLECTION = "airline_operational_intelligence_architecture"
ARCHITECTURE_REFERENCE = "phase_50_0_airline_operational_intelligence_engine_architecture_foundation"

PASSENGER_SERVICE_OPERATIONS_PRINCIPLE = (
    "Passenger -> Need -> Service Requirement -> Airline Capability -> Operational Feasibility -> "
    "Pricing / Conditions -> Recommendation -> Fulfilment"
)

LINKED_EXISTING_FOUNDATIONS = [
    "Airline policy ingestion foundation",
    "Airline intelligence data packs",
    "Airline intelligence knowledge versioning",
    "Airline intelligence agency consumption bridge",
    "Canonical service taxonomy",
    "SSR/OSI and EMD/RFIC/RFISC service mechanics mapping",
    "Ancillary pricing schema and exception engine",
    "Policy comparison and service advisor",
    "Offer builder policy advisor integration",
    "Passenger workspace",
    "SSR/OSI future operational workspace",
    "Ticket workspace",
    "EMD workspace",
    "Booking workspace",
    "Offer workspace",
]

FUTURE_AOIE_PHASES = [
    "50.0 Airline Operational Intelligence Engine Architecture Foundation",
    "50.1 Airline Knowledge Acquisition Workspace",
    "50.2 Airline Policy Text Parser Foundation",
    "50.3 Airline Service Rule Normalisation Foundation",
    "50.4 Airline Knowledge Version Review Foundation",
    "50.5 Airline Capability Matrix Foundation",
    "50.6 Passenger Service Feasibility Assessment Foundation",
    "50.7 Airline-Itinerary Recommendation Foundation",
    "50.8 Total Journey Cost Comparison Foundation",
    "50.9 Offer Builder AOIE Integration Foundation",
]

EXCLUDED_SCOPE = [
    "AI generation",
    "airline scraping",
    "automatic web crawling",
    "live airline APIs",
    "provider integrations",
    "pricing engine execution",
    "itinerary search",
    "booking execution",
    "ticket issuance",
    "EMD issuance",
    "recommendation automation",
    "background workers",
]


class AirlineOperationalIntelligenceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def ensure_architecture_record(self) -> dict[str, Any]:
        existing = await self.db.collection(ARCHITECTURE_COLLECTION).find_one({"architecture_reference": ARCHITECTURE_REFERENCE})
        if existing:
            return self._projection(existing)
        record = AirlineOperationalIntelligenceArchitecture(
            id=ARCHITECTURE_REFERENCE,
            architecture_reference=ARCHITECTURE_REFERENCE,
            architecture_status="foundation",
            architecture_version="50.0",
            principle=PASSENGER_SERVICE_OPERATIONS_PRINCIPLE,
            purpose=(
                "AOIE defines the future intelligence layer that coordinates governed airline knowledge into "
                "human-reviewed answers about what is possible, allowed, priced, risky, and recommended for a "
                "passenger service case."
            ),
            operational_platform_scope=(
                "The Operational Platform records what is happening across requests, passengers, trips, offers, "
                "bookings, tickets, EMDs, documents, and future SSR/OSI workspaces."
            ),
            intelligence_engine_scope=(
                "AOIE will coordinate existing airline policy, taxonomy, mechanics, pricing, comparison, offer advisor, "
                "and workspace metadata into future decision-support views. It does not duplicate those foundations."
            ),
            knowledge_acquisition_scope=(
                "Future acquisition workspaces will stage human-provided airline knowledge, source references, and "
                "review metadata without scraping, crawling, provider calls, or AI generation."
            ),
            knowledge_normalisation_scope=(
                "Future normalisation phases will map airline text and service conditions into canonical service, "
                "mechanics, RFIC/RFISC, applicability, exception, and pricing metadata."
            ),
            knowledge_versioning_scope=(
                "AOIE consumes governed knowledge-version records so changes can be compared against last-approved "
                "airline knowledge versions."
            ),
            knowledge_approval_scope=(
                "Human review and approval remain mandatory before intelligence metadata can be considered safe for "
                "agency visibility or future operational decision support."
            ),
            operational_feasibility_scope=(
                "Future feasibility views will compare passenger needs, service requirements, airline capabilities, "
                "documents, approvals, deadlines, SSR/OSI needs, EMD/RFIC/RFISC requirements, and risk indicators."
            ),
            airline_recommendation_scope=(
                "Future recommendation phases may rank airline-itinerary options for human review, but Phase 50.0 "
                "does not execute or automate recommendations."
            ),
            offer_optimisation_scope=(
                "Future offer integration will compare total journey costs, ancillary fees, feasibility, risk, and "
                "service quality before presenting evidence to offer builders."
            ),
            excluded_scope=EXCLUDED_SCOPE,
            linked_existing_foundations=LINKED_EXISTING_FOUNDATIONS,
            linked_future_phases=FUTURE_AOIE_PHASES,
            notes=(
                "AOIE is the second brain of AeroAssist. Phase 50.0 is architecture and governance only; it creates "
                "metadata describing how future intelligence phases should coordinate existing foundations."
            ),
        )
        stored = await self.db.collection(ARCHITECTURE_COLLECTION).insert_one(record.model_dump(mode="json"))
        return self._projection(stored)

    async def list_architecture(self) -> list[dict[str, Any]]:
        await self.ensure_architecture_record()
        records = await self.db.collection(ARCHITECTURE_COLLECTION).find_many()
        records.sort(key=lambda item: str(item.get("architecture_version") or ""), reverse=True)
        return [self._projection(item) for item in records]

    async def get_architecture(self, architecture_id: str | None = None) -> dict[str, Any]:
        await self.ensure_architecture_record()
        filters = {"id": architecture_id} if architecture_id else {"architecture_reference": ARCHITECTURE_REFERENCE}
        record = await self.db.collection(ARCHITECTURE_COLLECTION).find_one(filters)
        if not record:
            record = await self.db.collection(ARCHITECTURE_COLLECTION).find_one({"architecture_reference": ARCHITECTURE_REFERENCE})
        return self._projection(record or {})

    async def platform_response(self) -> dict[str, Any]:
        architecture = await self.get_architecture()
        items = await self.list_architecture()
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "architecture": architecture,
            "summary": self.summary_from_items(items),
            "sections": self.sections_from_architecture(architecture),
            "read_only": True,
            "metadata_only": True,
            "architecture_only": True,
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str) -> dict[str, Any]:
        architecture = await self.get_architecture()
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "architecture": self._agency_projection(architecture),
            "summary": self.summary_from_items([architecture]),
            "sections": self.sections_from_architecture(architecture),
            "read_only": True,
            "metadata_only": True,
            "architecture_only": True,
            **self.safety_flags(),
        }

    async def summary(self) -> dict[str, Any]:
        items = await self.list_architecture()
        return {
            "phase": PHASE_LABEL,
            **self.summary_from_items(items),
            "read_only": True,
            "metadata_only": True,
            "architecture_only": True,
            **self.safety_flags(),
        }

    def summary_from_items(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        active = [item for item in items if item.get("architecture_status") == "foundation"]
        return {
            "architecture_record_count": len(items),
            "foundation_record_count": len(active),
            "linked_existing_foundation_count": len(LINKED_EXISTING_FOUNDATIONS),
            "future_aoie_phase_count": len(FUTURE_AOIE_PHASES),
            "excluded_scope_count": len(EXCLUDED_SCOPE),
            "passenger_service_operations_principle": PASSENGER_SERVICE_OPERATIONS_PRINCIPLE,
            "next_intelligence_phase": "Phase 50.1 - Airline Knowledge Acquisition Workspace",
            "next_operational_phase": "Phase 42.0 - Document Workspace Foundation",
        }

    def sections_from_architecture(self, architecture: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {"key": "passenger_service_operations_principle", "label": "Passenger Service Operations Principle", "body": architecture.get("principle")},
            {"key": "operational_platform_vs_intelligence_engine", "label": "Operational Platform vs Intelligence Engine", "body": f"{architecture.get('operational_platform_scope')} {architecture.get('intelligence_engine_scope')}"},
            {"key": "knowledge_acquisition", "label": "Knowledge Acquisition", "body": architecture.get("knowledge_acquisition_scope")},
            {"key": "knowledge_normalisation", "label": "Knowledge Normalisation", "body": architecture.get("knowledge_normalisation_scope")},
            {"key": "versioning_and_human_approval", "label": "Versioning and Human Approval", "body": f"{architecture.get('knowledge_versioning_scope')} {architecture.get('knowledge_approval_scope')}"},
            {"key": "airline_capability_matrix", "label": "Airline Capability Matrix", "body": "Future AOIE phases will map airline capabilities against canonical services, mechanics, conditions, and operational constraints."},
            {"key": "passenger_service_feasibility", "label": "Passenger Service Feasibility", "body": architecture.get("operational_feasibility_scope")},
            {"key": "airline_itinerary_recommendation", "label": "Airline-Itinerary Recommendation", "body": architecture.get("airline_recommendation_scope")},
            {"key": "total_journey_cost_comparison", "label": "Total Journey Cost Comparison", "body": "Future AOIE phases will compare airfare, ancillary fees, penalties, service quality, operational risk, documents, and deadlines as metadata for human review."},
            {"key": "future_offer_builder_integration", "label": "Future Offer Builder Integration", "body": architecture.get("offer_optimisation_scope")},
            {"key": "excluded_scope", "label": "Excluded Scope", "body": ", ".join(architecture.get("excluded_scope") or EXCLUDED_SCOPE)},
        ]

    def safety_flags(self) -> dict[str, bool]:
        return {
            "ai_generation_disabled": True,
            "airline_scraping_disabled": True,
            "automatic_web_crawling_disabled": True,
            "live_airline_apis_disabled": True,
            "provider_integrations_disabled": True,
            "pricing_engine_execution_disabled": True,
            "itinerary_search_disabled": True,
            "booking_execution_disabled": True,
            "ticket_issuance_disabled": True,
            "emd_issuance_disabled": True,
            "recommendation_automation_disabled": True,
            "background_workers_disabled": True,
            "automation_disabled": True,
            "external_api_calls_disabled": True,
        }

    def _projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected.update(
            {
                "phase": PHASE_LABEL,
                "display_name": "Airline Operational Intelligence Engine",
                "abbreviation": "AOIE",
                "metadata_only": True,
                "architecture_only": True,
                "coordinates_existing_foundations": True,
                "duplicates_existing_foundations": False,
                "passenger_service_operations_system": True,
                **self.safety_flags(),
            }
        )
        return projected

    def _agency_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = self._projection(item)
        projected["read_only"] = True
        return projected
