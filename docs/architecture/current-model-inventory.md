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
| `RequestPassengerSegmentService` | `request_passenger_segment_services` | Explicit passenger+segment service applicability | Agency | Request, service, passenger, segment | Service applicability | Foundation |
| `RequestCaseFlag` | `request_case_flags` | Operational flags/risk/attention markers | Agency | Request | Case flags | Foundation |
| `RequestPet`, `RequestPetSegmentTransport` | `request_pets`, `request_pet_segment_transport` | Pet/service animal request and segment transport applicability | Agency | Request, passenger, segment | Pet transport | Foundation |
| `RequestSpecialItem`, `RequestSpecialItemSegment` | `request_special_items`, `request_special_item_segments` | Special item and segment applicability | Agency | Request, passenger, segment | Special baggage/items | Foundation |
| `TripDossier`, `TripPassenger`, `TripSegment` | `trip_dossiers`, `trip_passengers`, `trip_segments` | Canonical trip dossier placeholders | Agency | Requests, passengers, segments, future bookings/offers | Trip/dossier | Foundation |
| Offer models | `offers`, `offer_*` collections | Manual offer foundation | Agency | Request, passengers, routes, fares, services | Offer/comparison | Legacy-compatible foundation |
| Booking/ticket/EMD models | `bookings`, `booking_passengers`, `booking_segments`, `ticket_records`, `emd_records` | Booking and document mirror/tracking | Agency | Requests/bookings/passengers/segments | Booking/GDS mirror | Transitional |
| Invoice/payment models | `invoices`, `invoice_line_items`, `payment_records` | Finance tracking | Agency | Booking/client | Invoice/payment | Transitional |
| Refund/exchange models | `refund_exchange_*` collections | Refund/exchange case tracking | Agency | Bookings/tickets/messages/timeline | Claims/service cases | Canonical for refund/exchange, partial for generic claims |
| Document models | `document_templates`, `rendered_documents`, `document_exports`, `document_deliveries`, `document_storage_records` | Templates, render snapshots, exports, delivery attempts | Agency | Requests/offers/bookings/invoices | Documents/templates | Canonical foundation |
| `RequestMessage`, `RequestTask`, timeline models | `request_messages`, `request_tasks`, timeline collections | Communications, staff tasks, activity | Agency | Request | Communications/tasks/activity | Canonical request-level foundation |
| Airline intelligence models | `airline_profiles`, `airline_knowledge_items`, `airline_procedures`, `airline_emd_rule_notes`, `agency_airline_overrides` | Airline policy/decision support | Global + agency overrides | Airlines, sources, overrides | Airline policies | Canonical foundation |
| `GlobalReferenceRecord` | `global_reference_records` | Controlled master lookup domains | Global, agency-ready | Reference domains, request/builders/documents | Reference data | Canonical foundation |
| `ServiceCatalogueRecord` | `service_catalogue` | Service catalogue lookup with SSR/scoping/policy metadata | Global | Requested services, future segment applicability, airline policy checks | Service catalogue | Canonical foundation |
| Branding/logo/media models | `agency_branding_settings`, `agency_branding_assets`, `agency_website_media_assets` | Controlled branding and public-safe assets | Agency | Website/public renderer | Branding/media | Canonical |
| Website/CMS models | `agency_website_settings`, `agency_website_pages` | Public website settings/pages/sections | Agency | Branding/media/intakes | Public CMS | Canonical |
| Portal models | `portal_access_mappings`, `portal_action_events`, `document_acknowledgements` | Controlled client portal visibility/actions | Agency/client | Client, documents, actions | Portal/client accounts | Transitional |
| `AuditEvent` | `audit_events` | Security/operations audit log | Agency optional | Any entity | Activity/audit | Canonical |

## Notes

- Current stack remains FastAPI/Pydantic, repository-backed Mongo/in-memory database, React frontend, and Docker deployment.
- Collection names are not destructively renamed for blueprint alignment.
- Trip dossier and segment-scoped applicability classes are additive placeholders for future UI/API phases.
- Reference Data is intentionally separate from Airline Intelligence policy rules; it supplies lookup values and service catalogue metadata, not airline-specific acceptance decisions.
