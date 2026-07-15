#!/usr/bin/env python3
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from database import AGENCY_OWNED_COLLECTIONS, Database
from models import (
    DocumentPackage,
    JourneyOfferAcceptanceHandoff,
    JourneyOfferClientDecision,
    JourneyOfferClientInteraction,
    JourneyOfferClientQuestion,
    JourneyOfferDelivery,
    JourneyOfferDeliveryAuditEvent,
    JourneyOfferDeliveryRecipient,
    JourneyOfferDeliveryVersion,
    JourneyOfferDocumentPackageLink,
    JourneyOfferWarningAcknowledgement,
    OfferAcceptance,
    OfferWorkspace,
)
from routers import (
    agency_offer_deliveries,
    platform_offer_delivery_diagnostics,
    portal_offer_deliveries,
)
from services.offer_delivery_client_interaction_service import (
    AUDIT_COLLECTION,
    DELIVERY_COLLECTIONS,
    DELIVERY_COLLECTION,
    DOCUMENT_LINK_COLLECTION,
    ImmutableJourneyOfferDeliveryVersionError,
    OfferDeliveryClientInteractionService,
    JourneyOfferDeliveryError,
    PHASE_LABEL,
    VERSION_COLLECTION,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, request


EXPECTED_PHASE = "phase_56_4_offer_delivery_client_interaction_foundation"
ROOT = Path(__file__).resolve().parents[2]
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}


def require_text(path: Path, text: str) -> None:
    if text not in path.read_text(encoding="utf-8"):
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def restricted_key_found(value: object) -> bool:
    restricted = {
        "agency_id", "internal_notes", "internal_summary", "internal_payload",
        "source_provenance", "source_references", "source_urls", "source_locations",
        "raw_payload", "supplier_cost", "internal_cost", "margin", "credentials", "secret",
    }
    if isinstance(value, dict):
        return any(key in restricted or key.startswith("internal_") or restricted_key_found(item) for key, item in value.items())
    if isinstance(value, list):
        return any(restricted_key_found(item) for item in value)
    return False


def verify_static_contracts() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected Phase 56.4 marker: {PHASE_LABEL}")
    if not all([
        agency_offer_deliveries.router,
        platform_offer_delivery_diagnostics.router,
        portal_offer_deliveries.router,
    ]):
        raise AssertionError("Offer delivery routers did not import.")

    expected_collections = set(DELIVERY_COLLECTIONS)
    if len(expected_collections) != 10 or not expected_collections.issubset(set(AGENCY_OWNED_COLLECTIONS)):
        raise AssertionError("Phase 56.4 collections are incomplete or not agency-owned.")
    models = [
        JourneyOfferDelivery,
        JourneyOfferDeliveryVersion,
        JourneyOfferDeliveryRecipient,
        JourneyOfferClientInteraction,
        JourneyOfferClientDecision,
        JourneyOfferClientQuestion,
        JourneyOfferWarningAcknowledgement,
        JourneyOfferDocumentPackageLink,
        JourneyOfferAcceptanceHandoff,
        JourneyOfferDeliveryAuditEvent,
    ]
    if any("metadata_only" not in model.model_fields for model in models):
        raise AssertionError("Phase 56.4 metadata-only model defaults are incomplete.")
    if not JourneyOfferDeliveryVersion.model_fields["physical_deletion_disabled"].default:
        raise AssertionError("Released delivery version deletion is not disabled by default.")
    if not JourneyOfferAcceptanceHandoff.model_fields["automatic_booking_disabled"].default:
        raise AssertionError("Acceptance handoff does not disable automatic booking.")
    if not all([OfferWorkspace, OfferAcceptance, DocumentPackage]):
        raise AssertionError("Canonical Offer, Offer Acceptance, or Document ownership is unavailable.")
    if "offer_id" not in JourneyOfferDelivery.model_fields or "presentation_snapshot_id" not in JourneyOfferDelivery.model_fields:
        raise AssertionError("Delivery does not reference canonical Offer and Phase 56.3 snapshot ownership.")

    models_text = (ROOT / "backend/models.py").read_text(encoding="utf-8")
    for declaration in [
        "class OfferWorkspace(BaseDocument):",
        "class OfferAcceptance(BaseDocument):",
        "class DocumentPackage(BaseDocument):",
    ]:
        if models_text.count(declaration) != 1:
            raise AssertionError(f"Canonical ownership declaration was duplicated: {declaration}")

    database_text = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "journey_offer_deliveries_code_unique",
        "journey_offer_deliveries_presentation_lookup",
        "journey_offer_delivery_versions_number_unique",
        "journey_offer_delivery_recipients_version_status_lookup",
        "journey_offer_delivery_recipients_passenger_lookup",
        "journey_offer_client_interactions_recipient_lookup",
        "journey_offer_client_decisions_status_lookup",
        "journey_offer_client_questions_status_lookup",
        "journey_offer_warning_acknowledgements_unique",
        "journey_offer_document_package_links_package_lookup",
        "journey_offer_acceptance_handoffs_decision_unique",
        "journey_offer_delivery_audit_events_timeline_lookup",
    ]:
        if index_name not in database_text:
            raise AssertionError(f"Missing Mongo index registration: {index_name}")

    service_text = (ROOT / "backend/services/offer_delivery_client_interaction_service.py").read_text(encoding="utf-8").lower()
    for forbidden in [
        "requests.get(", "requests.post(", "httpx.", "openai", "selenium", "playwright",
        "backgroundtasks", "celery", "stripe", "scrape(", "public_share_token",
    ]:
        if forbidden in service_text:
            raise AssertionError(f"Delivery service contains forbidden execution semantics: {forbidden}")
    for required in [
        "offeracceptanceservice", "documentrenderservice", "portal_user_id",
        "recipient_not_authorized", "delivery_version_immutable", "client_payload_internal_field_detected",
        "automatic_booking_disabled", "public_share_links_disabled", "anonymous_access_disabled",
    ]:
        if required not in service_text:
            raise AssertionError(f"Delivery service missing required contract: {required}")

    require_text(ROOT / "frontend/src/App.jsx", '"/agency/offer-deliveries"')
    require_text(ROOT / "frontend/src/App.jsx", '"/platform/offer-delivery-diagnostics"')
    require_text(ROOT / "frontend/src/App.jsx", '"/portal/travel-options"')
    require_text(ROOT / "frontend/src/lib/moduleCatalog.js", 'label: "Offer Delivery"')
    require_text(ROOT / "frontend/src/lib/moduleCatalog.js", 'surface_type: "contextual_tool"')
    require_text(ROOT / "frontend/src/lib/moduleCatalog.js", 'navigation_visibility: "contextual"')
    require_text(ROOT / "frontend/src/layouts/AgencyLayout.jsx", 'item.navigation_visibility !== "contextual"')
    require_text(ROOT / "frontend/src/pages/agency/OfferWorkspaceDetailPage.jsx", "OfferDeliveryPanel")
    require_text(ROOT / "frontend/src/pages/agency/OfferWorkspaceDetailPage.jsx", "Delivery & Responses")
    require_text(ROOT / "frontend/src/components/offers/OfferDeliveryPanel.jsx", "Offer context required")
    require_text(ROOT / "frontend/src/components/offers/OfferDeliveryPanel.jsx", "offer_id: offerContextId")
    require_text(ROOT / "frontend/src/pages/agency/OfferDeliveryContextPage.jsx", "Back to Offer Workspace")
    require_text(ROOT / "frontend/src/pages/agency/ClientDetailPage.jsx", 'href="/agency/offers"')
    require_text(ROOT / "frontend/src/pages/agency/PassengerDetailPage.jsx", 'href="/agency/offers"')
    require_text(ROOT / "frontend/src/pages/platform/OfferDeliveryDiagnosticsPage.jsx", "Governance view only")
    require_text(ROOT / "frontend/src/pages/portal/PortalOfferDeliveryDetailPage.jsx", "Acknowledge")
    require_text(ROOT / "frontend/src/layouts/ClientPortalLayout.jsx", "Travel Options")
    require_text(ROOT / "docs/architecture/offer-delivery-client-interaction-foundation.md", "Delivery And Immutable Versions")
    require_text(ROOT / "docs/architecture/product-surface-workspace-governance.md", "Product Surface Review Gate")
    require_text(ROOT / "backend/routers/portal_offer_deliveries.py", "Depends(portal_context)")
    require_text(ROOT / "backend/routers/portal_offer_deliveries.py", "safe_response")

    ordinary_surfaces = [
        ROOT / "frontend/src/components/offers/OfferDeliveryPanel.jsx",
        ROOT / "frontend/src/pages/agency/OfferDeliveryContextPage.jsx",
        ROOT / "frontend/src/pages/portal/PortalOfferDeliveriesPage.jsx",
        ROOT / "frontend/src/pages/portal/PortalOfferDeliveryDetailPage.jsx",
    ]
    for path in ordinary_surfaces:
        content = path.read_text(encoding="utf-8")
        if "Journey Offer Delivery" in content:
            raise AssertionError(f"Forbidden user-facing delivery terminology remains in {path.relative_to(ROOT)}")
    router_text = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in [
        "backend/routers/agency_offer_deliveries.py",
        "backend/routers/portal_offer_deliveries.py",
        "backend/routers/platform_offer_delivery_diagnostics.py",
    ])
    if "/api/public" in router_text or "anonymous" in router_text.lower():
        raise AssertionError("Phase 56.4 introduced an anonymous public route or access mode.")


async def expect_error(call, code: str) -> None:
    try:
        await call
    except JourneyOfferDeliveryError as exc:
        if exc.code != code:
            raise AssertionError(f"Expected {code}, received {exc.code}") from exc
    else:
        raise AssertionError(f"Expected guarded error {code}")


async def seed_source(db: Database) -> None:
    now = datetime.now(timezone.utc).isoformat()
    await db.collection("client_profiles").insert_one({
        "id": "client-a", "agency_id": "agency-a", "display_name": "Alex Client",
        "email": "alex@example.test", "status": "active", "created_at": now, "updated_at": now,
    })
    for suffix in ["a", "b", "c"]:
        await db.collection("portal_access_mappings").insert_one({
            "id": f"portal-{suffix}", "agency_id": "agency-a", "client_id": "client-a",
            "user_email": f"client-{suffix}@example.test", "display_name": f"Client {suffix.upper()}",
            "portal_status": "active", "created_at": now, "updated_at": now,
        })
    await db.collection("journey_comparison_presentations").insert_one({
        "id": "presentation-a", "agency_id": "agency-a", "journey_id": "journey-a",
        "composition_id": "composition-a", "offer_id": "offer-a", "trip_id": "trip-a",
        "status": "client_ready", "audience_type": "client", "language_code": "en",
        "currency_code": "EUR", "title": "Internal title", "client_title": "Sofia to New York options",
        "client_intro_text": "Review these itinerary options and tell us how you would like to proceed.",
        "internal_notes": "CLIENT-LEAK-SENTINEL", "metadata": {"client_id": "client-a"},
        "created_at": now, "updated_at": now,
    })
    client_payload = {
        "presentation": {"title": "Sofia to New York options", "status": "client_ready"},
        "configuration": {"show_connections": True, "show_baggage": True, "show_flexibility": True},
        "options": [{
            "id": "option-projection-a", "composition_option_id": "composition-option-a",
            "title": "Frankfurt connection", "currency_code": "EUR", "total_price": 650,
            "total_elapsed_minutes": 780, "stop_count": 1, "warning_codes": ["schedule_subject_to_change"],
        }],
        "segments": [
            {"id": "segment-a", "option_projection_id": "option-projection-a", "segment_order": 1,
             "origin_airport_code": "SOF", "destination_airport_code": "FRA", "marketing_carrier_code": "LH",
             "departure_local": "2028-04-01T07:00:00+03:00", "arrival_local": "2028-04-01T08:30:00+02:00"},
            {"id": "segment-b", "option_projection_id": "option-projection-a", "segment_order": 2,
             "origin_airport_code": "FRA", "destination_airport_code": "JFK", "marketing_carrier_code": "LH",
             "departure_local": "2028-04-01T10:30:00+02:00", "arrival_local": "2028-04-01T13:20:00-04:00"},
        ],
        "connections": [{
            "id": "connection-a", "option_projection_id": "option-projection-a", "airport_code": "FRA",
            "connection_minutes": 120, "minimum_connection_status": "unknown", "warning_codes": [],
        }],
        "fare_brands": [{
            "id": "fare-projection-a", "option_projection_id": "option-projection-a", "brand_name": "Flex",
            "booking_class": "Y", "price": 650, "currency_code": "EUR", "baggage_summary": "1 checked bag",
            "change_summary": "Changes permitted with fare difference", "refund_summary": "Conditional refund",
            "warning_codes": [],
        }],
        "service_suitability": [{
            "id": "service-a", "option_projection_id": "option-projection-a", "service_code": "WCHC",
            "suitability_status": "conditional", "client_safe_summary": "Airline confirmation is required.",
            "warning_codes": ["airline_confirmation_required"], "blocking_indicator": False,
        }],
        "comparison": {"lowest_price_option_id": "option-projection-a", "preferred_option_id": "option-projection-a"},
        "content_blocks": [{"id": "content-a", "title": "Important", "client_text": "Times are local."}],
        "internal_notes": "CLIENT-LEAK-SENTINEL",
        "source_references": [{"source": "restricted"}],
    }
    await db.collection("journey_presentation_snapshots").insert_one({
        "id": "presentation-snapshot-a", "agency_id": "agency-a", "presentation_id": "presentation-a",
        "version_number": 1, "snapshot_status": "finalized", "client_safe_payload": client_payload,
        "internal_payload": {"internal_notes": "CLIENT-LEAK-SENTINEL"},
        "source_hash": "a" * 64, "finalized": True, "finalized_at": now,
        "created_at": now, "updated_at": now,
    })
    await db.collection("offer_workspaces").insert_one({
        "id": "offer-a", "agency_id": "agency-a", "offer_reference": "OFF-A",
        "offer_title": "Canonical offer", "offer_status": "draft", "created_at": now, "updated_at": now,
    })
    await db.collection("offer_options").insert_one({
        "id": "offer-option-a", "agency_id": "agency-a", "workspace_id": "offer-a",
        "composition_option_id": "composition-option-a", "label": "Frankfurt connection",
        "metadata": {"composition_option_id": "composition-option-a"}, "created_at": now, "updated_at": now,
    })


class FakeAcceptanceService:
    async def accept_offer_option(self, agency_id, workspace_id, option_id, user, payload):
        if (agency_id, workspace_id, option_id) != ("agency-a", "offer-a", "offer-option-a"):
            raise AssertionError("Acceptance handoff did not preserve canonical Offer mapping.")
        return {
            "acceptance": {"id": "canonical-acceptance-a", "workspace_id": workspace_id, "option_id": option_id},
            "booking_readiness": None,
        }


async def verify_service_behavior() -> None:
    db = Database()
    await seed_source(db)
    service = OfferDeliveryClientInteractionService(db)
    user = {"id": "agent-a", "email": "agent-a@example.test"}
    await expect_error(
        service.create_from_presentation(
            "agency-a", "presentation-a", {"client_id": "client-a", "offer_id": "offer-other"}, user
        ),
        "OFFER_PRESENTATION_MISMATCH",
    )
    created = await service.create_from_presentation("agency-a", "presentation-a", {
        "client_id": "client-a", "offer_id": "offer-a", "title": "Your travel options",
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
    }, user)
    delivery = created["delivery"]
    version = created["versions"][0]
    if not created.get("created") or version.get("immutable") or version.get("status") != "draft":
        raise AssertionError("Draft delivery creation from Phase 56.3 snapshot failed.")
    if version.get("source_snapshot_hash") != "a" * 64 or len(version.get("payload_hash") or "") != 64:
        raise AssertionError("Delivery version did not preserve its source snapshot hash and deterministic payload hash.")
    duplicate = await service.create_from_presentation("agency-a", "presentation-a", {"client_id": "client-a"}, user)
    if not duplicate.get("idempotent") or duplicate.get("created") is not False:
        raise AssertionError("Delivery creation is not idempotent per client and source snapshot.")
    await expect_error(service.get_delivery("agency-b", delivery["id"]), "AGENCY_ISOLATION_VIOLATION")

    client_preview = await service.preview_client("agency-a", delivery["id"])
    if restricted_key_found(client_preview["client_safe_payload"]) or "CLIENT-LEAK-SENTINEL" in str(client_preview):
        raise AssertionError("Client delivery preview leaked internal or source content.")
    if client_preview["client_safe_payload"].get("terms", {}).get("booking_is_not_created_automatically") is not True:
        raise AssertionError("Client delivery terms do not preserve the non-booking boundary.")

    await expect_error(
        service.create_recipient("agency-a", delivery["id"], {
            "portal_user_id": "unmapped-portal-user", "display_name": "Unknown recipient",
        }, user),
        "RECIPIENT_NOT_AUTHORIZED",
    )

    recipients = []
    for suffix in ["a", "b", "c"]:
        result = await service.create_recipient("agency-a", delivery["id"], {
            "portal_user_id": f"portal-{suffix}", "display_name": f"Client {suffix.upper()}",
            "email_reference": f"client-{suffix}@example.test",
        }, user)
        recipients.append(result["recipient"])
    invalid = await service.validate_version("agency-a", delivery["id"], version["id"])
    if not invalid.get("can_release") or invalid.get("blocking_count") != 0:
        raise AssertionError(f"Valid delivery was blocked from release: {invalid.get('findings')}")
    released = await service.release_version("agency-a", delivery["id"], version["id"], {"release_notes": "Agent approved."}, user)
    if released["version"].get("status") != "released" or released["version"].get("immutable") is not True:
        raise AssertionError("Explicit immutable release failed.")
    try:
        await service.release_version("agency-a", delivery["id"], version["id"], {}, user)
    except ImmutableJourneyOfferDeliveryVersionError:
        pass
    else:
        raise AssertionError("Released delivery version could be released again.")
    await expect_error(
        service.update_delivery("agency-a", delivery["id"], {"currency_code": "USD"}, user),
        "DELIVERY_VERSION_IMMUTABLE",
    )

    contexts = [{"account": {"id": f"portal-{suffix}", "agency_id": "agency-a", "client_id": "client-a"}} for suffix in ["a", "b", "c"]]
    portal_list = await service.portal_list(contexts[0])
    if portal_list.get("count") != 1 or portal_list.get("authenticated") is not True:
        raise AssertionError("Authenticated recipient delivery listing failed.")
    portal_detail = await service.portal_detail(contexts[0], delivery["id"], record_open=True)
    if restricted_key_found(portal_detail["client_safe_payload"]) or "CLIENT-LEAK-SENTINEL" in str(portal_detail) or portal_detail.get("anonymous_access_disabled") is not True:
        raise AssertionError("Portal detail is not recipient-safe.")
    await expect_error(
        service.portal_detail({"account": {"id": "intruder", "agency_id": "agency-a", "client_id": "client-a"}}, delivery["id"]),
        "RECIPIENT_NOT_AUTHORIZED",
    )

    option_id = portal_detail["client_safe_payload"]["options"][0]["id"]
    fare_id = portal_detail["client_safe_payload"]["fare_brands"][0]["id"]
    warning_codes = [item["code"] for item in portal_detail["client_safe_payload"]["warnings"] if item.get("required")]
    await service.portal_record_interaction(contexts[0], delivery["id"], {
        "interaction_type": "preferred_option_selected", "option_id": option_id,
    })
    for code in warning_codes:
        await service.portal_acknowledge_warning(contexts[0], delivery["id"], {
            "warning_code": code, "acknowledgement_text": "Reviewed and understood.",
        })
    question = await service.portal_submit_question(contexts[0], delivery["id"], {"message_text": "Can you confirm wheelchair handling?"})
    reply = await service.reply_question("agency-a", delivery["id"], question["question"]["id"], {"message_text": "The airline confirmation remains pending."}, user)
    if reply.get("message_sent") is not False:
        raise AssertionError("Question reply incorrectly implied external messaging.")

    accept_payload = {
        "decision_type": "accept", "selected_option_id": option_id, "selected_fare_brand_id": fare_id,
        "acknowledged_warning_codes": warning_codes, "terms_acknowledged": True,
        "client_comment": "Please proceed with agency processing.",
    }
    preview = await service.portal_decision_preview(contexts[0], delivery["id"], accept_payload)
    if not preview.get("can_submit") or preview.get("canonical_acceptance_created") is not False:
        raise AssertionError(f"Valid client acceptance preview failed: {preview.get('findings')}")
    accepted = await service.portal_submit_decision(contexts[0], delivery["id"], accept_payload)
    if accepted["decision"].get("handoff_status") != "pending_agency_action" or accepted.get("booking_created") is not False:
        raise AssertionError("Client acceptance did not remain a guarded handoff request.")
    await expect_error(
        service.portal_submit_decision(contexts[0], delivery["id"], accept_payload),
        "DECISION_ALREADY_SUBMITTED",
    )
    declined = await service.portal_submit_decision(contexts[1], delivery["id"], {
        "decision_type": "decline", "client_comment": "Not suitable.",
    })
    changed = await service.portal_submit_decision(contexts[2], delivery["id"], {
        "decision_type": "request_changes", "client_comment": "Please provide a shorter connection.",
    })
    if declined["decision"]["decision_type"] != "decline" or changed["decision"]["decision_type"] != "request_changes":
        raise AssertionError("Decline or request-changes decision recording failed.")

    accept_decision = accepted["decision"]
    handoff_preview = await service.acceptance_handoff_preview("agency-a", delivery["id"], {"decision_id": accept_decision["id"]}, user)
    if not handoff_preview.get("can_apply") or handoff_preview["preview"].get("offer_option_id") != "offer-option-a":
        raise AssertionError(f"Canonical acceptance handoff mapping failed: {handoff_preview.get('findings')}")
    service.acceptance = FakeAcceptanceService()
    handoff = await service.acceptance_handoff_apply("agency-a", delivery["id"], {"decision_id": accept_decision["id"]}, user)
    if handoff["handoff"].get("canonical_acceptance_id") != "canonical-acceptance-a" or handoff.get("booking_created") is not False:
        raise AssertionError("Explicit canonical acceptance handoff failed.")
    idempotent_handoff = await service.acceptance_handoff_apply("agency-a", delivery["id"], {"decision_id": accept_decision["id"]}, user)
    if not idempotent_handoff.get("idempotent"):
        raise AssertionError("Acceptance handoff was not idempotent.")

    document_preview = await service.document_handoff_preview("agency-a", delivery["id"], {"delivery_version_id": version["id"]})
    if not document_preview.get("can_apply") or document_preview["preview"].get("rendered") is not False:
        raise AssertionError("Immutable document source handoff preview failed.")
    document = await service.document_handoff_apply("agency-a", delivery["id"], {"delivery_version_id": version["id"]}, user)
    if document.get("rendered") is not False or document.get("sent") is not False:
        raise AssertionError("Document linkage crossed into rendering or sending.")
    duplicate_document = await service.document_handoff_apply("agency-a", delivery["id"], {"delivery_version_id": version["id"]}, user)
    if not duplicate_document.get("idempotent"):
        raise AssertionError("Document package linkage was not idempotent.")
    downloaded = await service.portal_record_document_download(contexts[0], delivery["id"], document["document_link"]["id"])
    if downloaded.get("file_transfer_performed") is not False:
        raise AssertionError("Document download metadata implied file transfer.")

    await db.collection(VERSION_COLLECTION).update_one({"id": version["id"]}, {"expires_at": datetime.now(timezone.utc) - timedelta(minutes=1)})
    expired_preview = await service.portal_decision_preview(contexts[0], delivery["id"], accept_payload)
    if expired_preview.get("can_submit") or "DELIVERY_EXPIRED" not in {item.get("code") for item in expired_preview.get("findings", [])}:
        raise AssertionError("Expired delivery was not blocked by decision preview.")
    await db.collection(VERSION_COLLECTION).update_one({"id": version["id"]}, {"expires_at": datetime.now(timezone.utc) + timedelta(days=1)})
    replacement = (await service.create_version("agency-a", delivery["id"], {}, user))["version"]
    superseded = await service.supersede_version("agency-a", delivery["id"], version["id"], {"superseded_by_version_id": replacement["id"]}, user)
    if superseded["version"].get("status") != "superseded":
        raise AssertionError("Version supersession did not preserve historical state.")
    await expect_error(service._require_actionable_version("agency-a", delivery, version["id"]), "DELIVERY_VERSION_SUPERSEDED")

    audit = await service.list_audit_events("agency-a", delivery["id"])
    timeline = await db.collection("operational_timelines").find_many({"agency_id": "agency-a"})
    summary = await service.summarize_readiness("agency-a")
    if len(audit) < 8 or not timeline:
        raise AssertionError("Delivery audit or operational timeline history is incomplete.")
    for key in [
        "delivery_count", "version_count", "immutable_version_count", "recipient_count", "interaction_count",
        "decision_count", "question_count", "acknowledgement_count", "document_count", "acceptance_handoff_count",
        "audit_event_count", "expired_count", "revoked_count", "superseded_count", "blocking_warning_count",
    ]:
        if not isinstance(summary.get(key), int):
            raise AssertionError(f"Readiness counter missing: {key}")
    for key, value in service.safety_flags().items():
        if value is not True:
            raise AssertionError(f"Safety flag is not enabled: {key}")

    revoked = await service.revoke_delivery("agency-a", delivery["id"], user)
    if revoked["delivery"].get("status") != "revoked":
        raise AssertionError("Delivery revocation failed.")
    current = await db.collection(DELIVERY_COLLECTION).find_one({"id": delivery["id"]})
    await expect_error(service._require_actionable_version("agency-a", current, version["id"]), "DELIVERY_REVOKED")
    if not await db.collection(DOCUMENT_LINK_COLLECTION).find_one({"agency_id": "agency-a", "delivery_id": delivery["id"]}):
        raise AssertionError("Document package link was not retained after revocation.")
    if not await db.collection(AUDIT_COLLECTION).find_one({"agency_id": "agency-a", "delivery_id": delivery["id"], "event_type": "revoked"}):
        raise AssertionError("Revocation audit event was not retained.")


def verify_live_api() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}; expected {EXPECTED_PHASE}")
    readiness = get("/api/readiness")
    section = readiness.get("offer_delivery_client_interaction_foundation") or {}
    for key in OfferDeliveryClientInteractionService(Database()).safety_flags():
        if section.get(key) is not True:
            raise AssertionError(f"Offer delivery readiness flag missing: {key}={section.get(key)}")
    for key in [
        "delivery_count", "version_count", "immutable_version_count", "recipient_count", "interaction_count",
        "decision_count", "question_count", "acknowledgement_count", "document_count", "acceptance_handoff_count",
        "audit_event_count", "expired_count", "revoked_count", "superseded_count", "blocking_warning_count",
    ]:
        if not isinstance(section.get(key), int):
            raise AssertionError(f"Offer delivery readiness counter missing: {key}")
    if section.get("readiness_required") is not False:
        raise AssertionError("Offer delivery readiness must remain diagnostic-only.")

    paths = get("/openapi.json").get("paths") or {}
    route_contract = [
        ("/api/agencies/{agency_id}/offer-deliveries", "get"),
        ("/api/agencies/{agency_id}/offer-deliveries", "post"),
        ("/api/agencies/{agency_id}/offer-deliveries/from-presentation/{presentation_id}", "post"),
        ("/api/agencies/{agency_id}/offer-deliveries/from-offer/{offer_id}", "post"),
        ("/api/agencies/{agency_id}/offer-deliveries/{delivery_id}/recipients", "post"),
        ("/api/agencies/{agency_id}/offer-deliveries/{delivery_id}/versions/{version_id}/validate", "post"),
        ("/api/agencies/{agency_id}/offer-deliveries/{delivery_id}/versions/{version_id}/release", "post"),
        ("/api/agencies/{agency_id}/offer-deliveries/{delivery_id}/acceptance-handoff/preview", "post"),
        ("/api/agencies/{agency_id}/offer-deliveries/{delivery_id}/acceptance-handoff/apply", "post"),
        ("/api/agencies/{agency_id}/offer-deliveries/{delivery_id}/document-handoff/apply", "post"),
        ("/api/platform/offer-delivery-diagnostics", "get"),
        ("/api/platform/offer-delivery-diagnostics/deliveries/{delivery_id}", "get"),
        ("/api/portal/offer-deliveries", "get"),
        ("/api/portal/offer-deliveries/{delivery_id}", "get"),
        ("/api/portal/offer-deliveries/{delivery_id}/open", "post"),
        ("/api/portal/offer-deliveries/{delivery_id}/selection", "post"),
        ("/api/portal/offer-deliveries/{delivery_id}/warnings/acknowledge", "post"),
        ("/api/portal/offer-deliveries/{delivery_id}/questions", "post"),
        ("/api/portal/offer-deliveries/{delivery_id}/decisions/preview", "post"),
        ("/api/portal/offer-deliveries/{delivery_id}/decisions", "post"),
        ("/api/portal/offer-deliveries/{delivery_id}/documents", "get"),
    ]
    for path, method in route_contract:
        assert_openapi_path(paths, path, method)

    platform = get("/api/platform/offer-delivery-diagnostics", OWNER_HEADERS)
    if platform.get("read_only") is not True or platform.get("platform_diagnostics_read_only") is not True:
        raise AssertionError("Platform delivery diagnostics are not read-only.")
    filters = get("/api/platform/offer-delivery-diagnostics/filters", OWNER_HEADERS)
    if filters.get("read_only") is not True or "accept" not in filters.get("filters", {}).get("decision_types", []):
        raise AssertionError("Platform governed filters are incomplete.")
    request("GET", "/api/platform/offer-delivery-diagnostics", None, AGENCY_AGENT_HEADERS, expect=403)


def main() -> None:
    verify_static_contracts()
    asyncio.run(verify_service_behavior())
    verify_live_api()
    print("Phase 56.4 offer delivery and client interaction smoke passed.")


if __name__ == "__main__":
    main()
