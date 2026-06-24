# Phase 27.2 — Assistance Assessment Driven SSR Recommendation

Phase 27.2 changes mobility assistance from code-first data entry to assessment-first recommendation. Staff answer operational questions first; the system suggests an SSR/service code, and staff can confirm or override it with a reason.

## Implemented

- Mobility assistance builder section renamed around “Assistance assessment”.
- Passenger context tags:
  - PRM / reduced mobility
  - SRC / senior citizen
  - temporary injury
  - medical condition
  - blind or visually impaired
  - deaf or hard of hearing
  - cognitive / neurodivergent assistance
  - pregnancy
  - child / young passenger support
  - unaccompanied minor
  - other
- Functional assessment fields drive the suggested SSR/service code.
- Suggested SSR/service code shows code, explanation, and confidence.
- Staff confirmation supports use-suggested, override, and manual review.
- Override reason is required when confirmed code differs from the suggested code.
- Own mobility device and battery details remain supplementary and conditional.

## Recommendation Rules

- `WCHR`: passenger can walk short distances and climb stairs, but needs wheelchair for airport distance.
- `WCHS`: passenger can walk short distances but cannot climb aircraft stairs or needs assistance to the aircraft door.
- `WCHC`: passenger cannot walk, cannot self-transfer, needs assistance into the aircraft seat, or needs aisle chair.
- `MAAS`: passenger needs navigation/escort support only and no wheelchair is indicated.
- `MEDA`: medical context or medical assistance indicators are selected.
- `BLND` / `DEAF`: visual/hearing impairment is selected and no wheelchair is indicated.
- `manual_review`: information is insufficient or conflicting.

## Payload Shape

Mobility service detail payloads now use:

- `assessment_version: "v2_assessment_driven"`
- `passenger_context_tags`
- `passenger_context_notes`
- `functional_assessment`
- `suggested_ssr_code`
- `suggested_ssr_reason`
- `recommendation_confidence`
- `confirmed_ssr_code`
- `override_reason`
- `final_assistance_label`
- `own_mobility_device`
- `own_device_details`
- `battery_details`

## Compatibility

- Older `assistance_code` / `wheelchair_type` payloads still display as legacy payloads.
- Intake conversion now creates mobility payloads as `manual_review` assessment-driven records when details are unavailable.
- No migration is required.

## Known Limits

- No airline-specific SSR validation.
- No centralized reference taxonomy.
- No automated SSR transmission to airline, GDS, NDC, or portal systems.
- No pricing or airline integration.
