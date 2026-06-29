# Special Services Unified Facade

Phase 36.4.5 adds `SpecialServicesUnifiedFacade` as a compatibility layer over the existing special-services foundation.

## Purpose

The supplementary blueprint describes separate medical, cargo/restricted item, VIP/corporate, passenger-service, exception-rule, SSR/OSI, and compliance modules. AgencyOS already has the canonical pieces:

- `PassengerServiceRequest`
- `request_pets`
- `request_special_items`
- `trip_service_items`
- Service Catalogue mappings
- `AirlineRulesCore`
- `UnifiedExceptionRule`
- `SpecialServicesService`
- `ExceptionEngineService`
- `SsrOsiGeneratorService`
- `RulesAndServicesRegistry`

The facade adopts the unified workflow idea without duplicating those modules.

## Facade Methods

- `list_services_for_trip(agency_id, trip_id)`
- `list_services_for_booking(agency_id, booking_record_id)`
- `normalize_service_context(payload)`
- `generate_ssr_osi_preview(context)`
- `evaluate_service_context(context)`

## Boundaries

The facade does not create live supplier requests, execute GDS/NDC commands, auto-approve airline policies, or replace existing request/trip/service models. It gives future UI work one stable compatibility surface while the current Phase 36.0 and Phase 36.2.5 foundations remain canonical.
