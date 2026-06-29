# Current Model Inventory

This inventory maps current FastAPI/Pydantic model classes and Mongo-compatible collection names to the blueprint terminology. Status values are **canonical**, **transitional**, or **legacy-compatible**.

| Model/classes | Collection(s) | Purpose | Tenant scope | Relationships | Blueprint equivalent | Status |
|---|---|---|---|---|---|---|
| `Agency`, `AgencyWorkspace` | `agencies`, `agency_workspaces` | Agency tenant and workspace identity | Platform / agency | Staff, branding, websites, operations | Agency/company | Canonical |
| `AgencyStaffMembership`, `Invitation`, auth/session models | `agency_staff_memberships`, `invitations`, auth collections | Staff access and invitations | Agency / platform | Users to agencies | Staff/user accounts | Canonical |
| `ClientProfile` | `client_profiles` | Payer/requester/account profile | Agency | Relationships to passengers, requests | CRM client | Canonical |
| `PassengerProfile` | `passenger_profiles` | Traveler/beneficiary registry | Agency | Client relationships, request passengers | Passenger registry | Canonical |
| `ClientPassengerRelationship` | `client_passenger_relationships` | Client-passenger permissions/relationship | Agency | Client + passenger | Client traveler linkage | Canonical |
| `RequestIntake` | `request_intakes` | Public/portal/staff intake records | Optional agency | Converts to `TravelRequest` | Intake/request submission | Canonical |
| `TravelRequest` | `travel_requests` | Operational request/work demand | Agency | Client, passengers, segments, services, optional trip | Request/case | Canonical |
| `RequestPassenger` | `request_passengers` | Passenger snapshot in request | Agency | Request + passenger | Request traveler | Canonical |
| `RequestSegment` | `request_segments` | Segment-first itinerary request structure | Agency | Request, future trip segment | Itinerary segment | Canonical |
| `RequestedService` | `requested_services` | Requested assistance/service | Agency | Request, passengers, segments | Service request | Transitional toward Phase 34 catalogue-backed applicability |
| `RequestPassengerSegmentService` | `request_passenger_segment_services` | Explicit passenger+segment service applicability with service catalogue/family metadata | Agency/workspace | Request, service, passenger, segment | Service applicability | Canonical foundation |
| `RequestCaseFlag` | `request_case_flags` | Derived and manual operational flags/risk/attention markers | Agency/workspace | Request, normalized children | Case flags | Canonical foundation |
| `RequestPet`, `RequestPetSegmentTransport` | `request_pets`, `request_pet_segment_transport` | Pet/service animal request and segment transport applicability | Agency/workspace | Request, passenger, segment | Pet transport | Canonical foundation |
| `RequestSpecialItem`, `RequestSpecialItemSegment` | `request_special_items`, `request_special_item_segments` | Special item and segment transport applicability | Agency/workspace | Request, passenger, segment | Special baggage/items | Canonical foundation |
| `TripDossier`, `TripPassenger`, `TripSegment`, `TripServiceItem`, `TripTimelineEvent` | `trip_dossiers`, `trip_passengers`, `trip_segments`, `trip_service_items`, `trip_timeline_events` | Operational trip dossier shell and copied request context | Agency/workspace | Linked requests, copied passengers, copied segments, copied service scopes, future bookings/offers | Trip/dossier | Canonical foundation |
| Offer models | `offers`, `offer_*` collections | Manual offer foundation | Agency | Request, passengers, routes, fares, services | Offer/comparison | Legacy-compatible foundation |
| Offer builder workspace models | `offer_workspaces`, `offer_options`, `offer_routing_options`, `offer_builder_segments`, `offer_fare_bundles`, `offer_pricing_lines`, `offer_comparison_snapshots` | Rule-aware offer workspace, option builder, pricing summaries, internal comparison snapshots, and recommendation flags | Agency | Requests, trips, offer option children, airline rules/service evaluations | Offer workspace/comparison matrix | Canonical foundation |
| Offer acceptance and booking readiness models | `offer_acceptances`, `trip_accepted_offer_snapshots`, `booking_readiness_packages` | Accepted option lifecycle, trip accepted-offer snapshot, and readiness-only booking handoff package | Agency | Offer workspaces/options, requests, trip dossiers, rules/service feasibility snapshots | Offer acceptance/booking readiness | Canonical foundation |
| Booking/ticket/EMD models | `bookings`, `booking_passengers`, `booking_segments`, `ticket_records`, `emd_records` | Booking and document mirror/tracking | Agency | Requests/bookings/passengers/segments | Booking/GDS mirror | Transitional |
| Invoice/payment models | `invoices`, `invoice_line_items`, `payment_records` | Finance tracking | Agency | Booking/client | Invoice/payment | Transitional |
| Refund/exchange models | `refund_exchange_*` collections | Refund/exchange case tracking | Agency | Bookings/tickets/messages/timeline | Claims/service cases | Canonical for refund/exchange, partial for generic claims |
| Document models | `document_templates`, `rendered_documents`, `document_exports`, `document_deliveries`, `document_storage_records` | Templates, render snapshots, exports, delivery attempts | Agency | Requests/offers/bookings/invoices | Documents/templates | Canonical foundation |
| `RequestMessage`, `RequestTask`, timeline models | `request_messages`, `request_tasks`, timeline collections | Communications, staff tasks, activity | Agency | Request | Communications/tasks/activity | Canonical request-level foundation |
| Airline intelligence models | `airline_profiles`, `airline_knowledge_items`, `airline_procedures`, `airline_emd_rule_notes`, `agency_airline_overrides` | Airline policy/decision support | Global + agency overrides | Airlines, sources, overrides | Airline policies | Canonical foundation |
| Phase 36 airline intelligence foundation models | `airline_intelligence_profiles`, `airline_contacts`, `airline_fleet_types`, `aircraft_tail_numbers`, `aircraft_configurations`, `aircraft_seatmaps`, `airline_routes`, `airline_fare_families`, `airline_rbd_matrix_rows`, `airline_fare_rules`, `airline_ancillaries`, `airline_interline_agreements`, `airline_distribution_profiles`, `airline_pss_parameters`, `airline_gds_parameters`, `airline_exception_rules` | Typed platform-owned airline operating, commercial, distribution, and fleet foundation data | Global/platform | Existing `airline_profiles`, reference airline records, future offers/bookings | Unified airline intelligence | Additive foundation |
| `AirlineRulesCore` | `airline_rules_core` | Single platform-owned airline rules core for special services and future feasibility checks | Global/platform | Airline profile/reference, exception rules, service requests | Airline rules source of truth | Canonical foundation |
| `UnifiedExceptionRule` | `unified_exception_rules` | Targeted category/airline/route/aircraft exception rules evaluated safely | Global/platform | Airline rules core, passenger service requests, simulator | Policy exception rules | Canonical foundation |
| `PassengerServiceRequest` | `passenger_service_requests` | Agency-owned operational bridge for passenger special services, evaluation results, documents, warnings, and SSR/OSI previews | Agency | Request/trip/booking/passenger/segment | Passenger special service request | Canonical bridge |
| `GlobalReferenceRecord` | `global_reference_records` | Controlled master lookup domains | Global, agency-ready | Reference domains, request/builders/documents | Reference data | Canonical foundation |
| `ReferenceDomainMetadata` | `reference_domain_metadata` | Platform-owned domain labels, categories, sort order, active status, and future schema metadata | Platform | Global reference records, platform console | Reference domain governance | Canonical foundation |
| `ReferenceDataSuggestion` | `reference_data_suggestions` | Agency-submitted reference additions/corrections awaiting platform review | Agency submission, platform review | Global reference records, agencies, reviewers | Reference governance suggestions | Canonical foundation |
| `ReferenceImportBatch` | `reference_import_batches` | Manual CSV import validation/import audit trail | Platform | Global reference records, audit events | Reference governance import | Canonical foundation |
| Reference enrichment import reports | `reference_import_batches.error_report_json.enrichment` | Enrichment pack dry-run/commit reports, warnings, missing links, and update mode metadata | Platform | Global reference records, audit events, reference pack templates | Reference enrichment import | Additive foundation |
| `ServiceCatalogueRecord` | `service_catalogue` | Service catalogue lookup with SSR/scoping/policy metadata | Global | Requested services, future segment applicability, airline policy checks | Service catalogue | Canonical foundation |
| `GlobalFieldDefinition` | `global_field_definitions` | Platform-owned canonical field library | Global/platform | Form profiles, intakes, requests, future offers | Field library/schema governance | Canonical foundation |
| `AgencyFormProfile`, `AgencyFormFieldSetting` | `agency_form_profiles`, `agency_form_field_settings` | Agency display profiles and field menu settings | Agency/workspace | Global field definitions, request/public/admin forms | Form profile/display configuration | Canonical foundation |
| Branding/logo/media models | `agency_branding_settings`, `agency_branding_assets`, `agency_website_media_assets` | Controlled branding and public-safe assets | Agency | Website/public renderer | Branding/media | Canonical |
| Website/CMS models | `agency_website_settings`, `agency_website_pages` | Public website settings/pages/sections | Agency | Branding/media/intakes | Public CMS | Canonical |
| Portal models | `portal_access_mappings`, `portal_action_events`, `document_acknowledgements` | Controlled client portal visibility/actions | Agency/client | Client, documents, actions | Portal/client accounts | Transitional |
| `AuditEvent` | `audit_events` | Security/operations audit log | Agency optional | Any entity | Activity/audit | Canonical |

## Notes

- Current stack remains FastAPI/Pydantic, repository-backed Mongo/in-memory database, React frontend, and Docker deployment.
- Collection names are not destructively renamed for blueprint alignment.
- Segment-scoped request service, pet, and special item classes are now populated by Phase 34 normalization.
- Trip dossier classes now support manual trip creation, request-to-trip conversion, request linking, copied request child records, and trip timelines while preserving request independence.
- Reference Data is platform-owned global master data; agency suggestions improve it only after platform review.
- Reference Data is intentionally separate from Airline Intelligence policy rules; it supplies lookup values and service catalogue metadata, not airline-specific acceptance decisions.
- Phase 36.0 adds the shared Rules & Services foundation: platform owns global airline rules and exception records, while agencies consume/evaluate them in request and trip workflows.
- Phase 36.1 adds additive offer workspaces and internal comparison matrices without destructively renaming the legacy Phase 4 offer collections.
- Phase 36.2 adds accepted-offer snapshots and booking readiness packages; these are readiness-only records and do not create live bookings, PNRs, tickets, EMDs, invoices, payments, or supplier actions.
- SSR/OSI output is deterministic preview text for staff review; it is not ticketing, booking execution, or an AI reasoning engine.
- Future policy learning should mirror the suggestion workflow through agency-local overrides, evidence, and reviewed promotion to global policy rules.
- Field profiles are agency-owned display configuration over platform-owned canonical fields; custom agency questions must remain in `agency_custom_fields`.
