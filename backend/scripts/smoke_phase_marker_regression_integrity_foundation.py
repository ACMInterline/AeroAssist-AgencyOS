#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from build_phase import (
    CURRENT_BUILD_PHASE,
    InvalidPhaseIdentifier,
    compare_phase_identifiers,
    parse_phase_identifier,
    phase_is_at_least,
    phase_is_exact,
)
from phase_assertions import application_phase_is_at_least, assert_application_phase_at_least
from smoke_booking_pnr_foundation import get


MINIMUM_PHASE = "phase_56_5_1_regression_integrity_foundation"
ROOT = Path(__file__).resolve().parents[2]


def assert_comparison(left: str, right: str, expected: int) -> None:
    actual = compare_phase_identifiers(left, right)
    if actual != expected:
        raise AssertionError(f"Expected comparison {left!r} to {right!r} to be {expected}, got {actual}.")


def verify_phase_utility() -> None:
    assert_comparison(
        "phase_55_9_airline_intelligence_scale_release_readiness_foundation",
        "phase_56_0_canonical_journey_itinerary_representation_foundation",
        -1,
    )
    assert_comparison(
        "phase_56_3_journey_comparison_client_presentation_foundation",
        "phase_56_4_offer_delivery_client_interaction_foundation",
        -1,
    )
    assert_comparison(
        "phase_56_4_offer_delivery_client_interaction_foundation",
        MINIMUM_PHASE,
        -1,
    )
    assert_comparison("phase_56_9_future_foundation", "phase_56_10_future_foundation", -1)
    assert_comparison("phase_56_3_alpha_foundation", "phase_56_3_beta_foundation", 0)
    if not phase_is_exact(MINIMUM_PHASE, MINIMUM_PHASE):
        raise AssertionError("Exact phase equality failed.")
    if phase_is_exact("phase_56_3_alpha_foundation", "phase_56_3_beta_foundation"):
        raise AssertionError("Exact equality ignored a phase suffix difference.")
    if not phase_is_at_least(MINIMUM_PHASE, "phase_55_9_historical_foundation"):
        raise AssertionError("A newer current phase did not satisfy a historical minimum.")
    if phase_is_at_least("phase_55_9_historical_foundation", MINIMUM_PHASE):
        raise AssertionError("An older current phase satisfied a newer minimum.")
    if not application_phase_is_at_least(
        "phase_56_5_2_legacy_regression_suite_migration",
        MINIMUM_PHASE,
        source="focused helper check",
    ):
        raise AssertionError("The shared smoke helper rejected a newer application phase.")
    if application_phase_is_at_least(
        "phase_56_4_offer_delivery_client_interaction_foundation",
        MINIMUM_PHASE,
        source="focused helper check",
    ):
        raise AssertionError("The shared smoke helper accepted an older application phase.")
    try:
        application_phase_is_at_least("phase_unknown", MINIMUM_PHASE, source="focused helper check")
    except AssertionError as exc:
        if "focused helper check" not in str(exc):
            raise AssertionError("The shared smoke helper omitted its readable source context.") from exc
    else:
        raise AssertionError("The shared smoke helper accepted a malformed application phase.")
    for invalid in ["phase_unknown", "phase_56_foundation", "56_5_1_foundation", "phase_56_5_1"]:
        try:
            parse_phase_identifier(invalid)
        except InvalidPhaseIdentifier:
            continue
        raise AssertionError(f"Malformed phase identifier was accepted: {invalid!r}")


def verify_static_registration() -> None:
    assert_application_phase_at_least(CURRENT_BUILD_PHASE, MINIMUM_PHASE, source="canonical build phase")
    server_text = (ROOT / "backend/server.py").read_text(encoding="utf-8")
    for text in [
        "from build_phase import CURRENT_BUILD_PHASE",
        '"phase_marker_regression_integrity_foundation"',
        '"current_build_phase_centralized": True',
    ]:
        if text not in server_text:
            raise AssertionError(f"Server phase registration is incomplete: missing {text}")


def verify_runtime_registration() -> None:
    health = get("/api/health")
    readiness = get("/api/readiness")
    assert_application_phase_at_least(health.get("phase"), MINIMUM_PHASE, source="health")
    assert_application_phase_at_least(readiness.get("phase"), MINIMUM_PHASE, source="readiness")
    section = readiness.get("phase_marker_regression_integrity_foundation") or {}
    for key in [
        "current_build_phase_centralized",
        "numeric_phase_comparison_enabled",
        "historical_minimum_phase_assertions_enabled",
        "historical_provenance_preserved",
    ]:
        if section.get(key) is not True:
            raise AssertionError(f"Regression-integrity readiness flag is missing: {key}")
    if section.get("readiness_required") is not False:
        raise AssertionError("Phase-marker regression integrity must remain a diagnostic readiness section.")
    capability_phases = {
        "airline_master_profile_intelligence_foundation": "phase_55_1_airline_master_profile_intelligence_foundation",
        "airline_policy_evidence_source_governance_foundation": "phase_55_2_airline_policy_evidence_source_governance_foundation",
        "airline_knowledge_versioning_change_detection_foundation": "phase_55_3_airline_knowledge_versioning_change_detection_foundation",
        "airline_service_coverage_gap_management_foundation": "phase_55_4_airline_service_coverage_gap_management_foundation",
        "airline_distribution_pss_gds_ndc_capability_intelligence_foundation": "phase_55_5_airline_distribution_pss_gds_ndc_capability_intelligence_foundation",
        "interline_codeshare_operating_carrier_intelligence_foundation": "phase_55_6_interline_codeshare_operating_carrier_intelligence_foundation",
        "airline_fare_family_rbd_baggage_brand_intelligence_foundation": "phase_55_7_airline_fare_family_rbd_baggage_brand_intelligence_foundation",
        "airline_contact_communication_intelligence_foundation": "phase_55_8_airline_contact_communication_intelligence_foundation",
        "airline_intelligence_scale_release_readiness_foundation": "phase_55_9_airline_intelligence_scale_release_readiness_foundation",
        "canonical_journey_itinerary_representation_foundation": "phase_56_0_canonical_journey_itinerary_representation_foundation",
        "journey_segment_authoring_intelligent_import_workspace_foundation": "phase_56_1_journey_segment_authoring_intelligent_import_workspace_foundation",
        "journey_option_fare_brand_composition_workspace_foundation": "phase_56_2_journey_option_fare_brand_composition_workspace_foundation",
        "journey_comparison_client_presentation_foundation": "phase_56_3_journey_comparison_client_presentation_foundation",
        "offer_delivery_client_interaction_foundation": "phase_56_4_offer_delivery_client_interaction_foundation",
    }
    for section_name, expected_phase in capability_phases.items():
        actual_phase = (readiness.get(section_name) or {}).get("capability_phase")
        if actual_phase != expected_phase:
            raise AssertionError(
                f"Readiness capability provenance mismatch for {section_name}: {actual_phase!r}"
            )


def main() -> None:
    verify_phase_utility()
    verify_static_registration()
    verify_runtime_registration()
    print("Phase 56.5.1 phase marker and regression integrity foundation smoke passed.")


if __name__ == "__main__":
    main()
