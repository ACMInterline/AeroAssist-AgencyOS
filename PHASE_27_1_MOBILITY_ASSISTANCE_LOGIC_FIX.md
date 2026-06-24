# Phase 27.1 — Mobility Assistance Logic And Builder UX Correction

Phase 27.1 corrects the mobility assistance service model in the Operational Request Builder V1.

## Corrected Mobility Logic

- `assistance_code` now captures the required airport/airline assistance:
  - `WCHR`: can walk and use stairs; wheelchair needed for airport distance.
  - `WCHS`: can walk short distances; cannot use stairs.
  - `WCHC`: cannot walk; full assistance to/from aircraft seat.
  - `meet_and_assist`: meet and assist only; wheelchair may not be required.
  - `unknown` / `to_be_assessed`: staff assessment required.
- Transfer/boarding details are separate optional clarifiers:
  - `can_transfer_to_aircraft_seat`
  - `can_walk_short_distance`
  - `needs_aisle_chair`
  - `needs_lift_or_stair_assistance`
- Own mobility device details are conditional on `own_mobility_device`.
- Battery fields show only for `electric_wheelchair_powerchair` and `mobility_scooter`.

## UI Correction

- The mobility section is split into:
  - Assistance required
  - Operational details
  - Own mobility device
  - Battery details when relevant
- Removed new UI usage of the incorrect old fields:
  - `wheelchair_type`
  - `can_walk_stairs`
  - `assistance_level`
  - unconditional `battery_wheelchair`

## Compatibility

- Existing saved payloads are still displayed defensively where old fields exist.
- No migration is required.
- Intake conversion now initializes mobility service payloads with `assistance_code=unknown` and `own_mobility_device=unknown`.

## Known Limits

- No airline-specific validation.
- No reference-data-driven mobility taxonomy.
- No pricing, airline integration, or automated delivery.
