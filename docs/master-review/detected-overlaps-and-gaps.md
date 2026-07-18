# Detected Overlaps and Gaps

## Interpretation

This register is factual Stage A evidence, not a Phase 1-57 classification or a refactoring recommendation.

- **Confirmed** means an exact source-level condition was found.
- **Structural** means parallel concepts or incomplete governance coverage exist, but may be intentional compatibility architecture.
- **Static-only** means runtime behavior may resolve the apparent gap.

## Confirmed Clean Checks

- No duplicate FastAPI method/path registrations were found across 2,163 operations.
- All 235 router modules are represented in the assembled FastAPI app.
- No exact duplicate model class names were found.
- No exact duplicate service class names were found.
- All 142 smoke scripts are registered in `backend/scripts/smoke_inventory.json`, and every inventory entry has a script.
- Every one of the 3,347 startup index specifications maps to an inventoried collection name.
- No routed frontend page with a direct/imported API reference was wholly unmatched to a backend route family.

## Route Overlaps

### Frontend duplicate registrations (confirmed)

Fourteen paths are declared both in the route map and in an earlier exact matcher. In every case the same component is selected, so the current effect is redundant precedence-sensitive routing rather than divergent rendering:

| Path | Component |
|---|---|
| `/agency/airline-service-advisor` | `AirlineServiceAdvisorPage` |
| `/agency/booking-workspaces` | `BookingWorkspaceMetadataPage` |
| `/agency/clients` | `AgencyClientMasterPage` |
| `/agency/gds-parser` | `GdsParserPage` |
| `/agency/offer-policy-advisor` | `AgencyOfferPolicyAdvisorPage` |
| `/agency/passengers` | `AgencyPassengerMasterPage` |
| `/agency/policy-comparison` | `AgencyPolicyComparisonPage` |
| `/agency/refunds-exchanges` | `RefundExchangeCasesPage` |
| `/agency/refunds-exchanges/new` | `RefundExchangeCaseCreatePage` |
| `/agency/service-mechanics` | `AgencyServiceMechanicsPage` |
| `/agency/service-taxonomy` | `AgencyServiceTaxonomyPage` |
| `/agency/trips` | `TripsPage` |
| `/portal/refunds-exchanges` | `PortalRefundExchangeCasesPage` |
| `/portal/requests/new` | `PortalRequestCreatePage` |

Exact source lines are in `frontend-route-inventory.csv` under `route_map` and `ordered_exact_match`.

### Backend routes without a static frontend caller (static-only)

Twenty-two operations have no API literal in pages, shared components, or frontend client modules. They cluster into intentionally internal/diagnostic endpoints and operations not surfaced by the current UI:

- health/readiness/audit diagnostics in `backend/server.py` and `backend/routers/platform.py`;
- protected observability and release-gate diagnostics;
- five platform client/passenger subrecord mutations;
- two airline policy extraction-run reads;
- two airline procedure/EMD-note updates;
- reference bootstrap and seed mutations;
- demo-login and change-password endpoints.

This is not proof that all 22 need pages. The exact rows are marked `no_static_frontend_api_reference` in `backend-route-inventory.csv`.

## Frontend Gaps

### Page modules without `App.jsx` registration (confirmed)

The following files are imported by neither the route map nor an ordered matcher:

- `frontend/src/pages/agency/BookingWorkspacesPage.jsx`
- `frontend/src/pages/agency/ClientsPage.jsx`
- `frontend/src/pages/agency/OfferDetailPage.jsx`
- `frontend/src/pages/agency/OffersPage.jsx`
- `frontend/src/pages/agency/PassengersPage.jsx`

Some have newer replacements (`BookingWorkspaceMetadataPage`, `AgencyClientMasterPage`, `AgencyPassengerMasterPage`, and offer workspace pages). Their presence is therefore an overlap/cleanup candidate, not evidence that the active route is missing.

Seventeen active route rows have partial static API matches because one call is composed through a helper or nested template expression. Their matched calls and unresolved expression are retained in `frontend-route-inventory.csv`; no total frontend/backend mismatch was found.

## Model and Persistence Overlaps

### Coexisting operational generations (structural)

The repository intentionally or compatibly carries multiple record families for several domains:

| Domain | Coexisting models/collections | Evidence |
|---|---|---|
| Passenger | `PassengerProfile`, `PassengerMasterRecord`, `PassengerWorkspace` | `backend/models.py:1137`, `:1367`, `:13052` |
| Request | `TravelRequest`, `TravelRequestWorkspace` | `backend/models.py:1886`, `:12921` |
| Trip | `TripDossier`, `TripWorkspace` | `backend/models.py:2123`, `:13372` |
| Offer | `OfferWorkspace` / `offer_workspaces`, `OfferWorkspaceV2` / `offer_workspaces_v2` | `backend/models.py:3557`, `:13519`; `backend/services/offer_workspace_service.py:17` |
| Booking | `BookingWorkspace`, `BookingRecord`, and later standalone `Booking` records | `backend/models.py:4049`, `:4190`, `:20456` |
| Ticket | `TicketWorkspace` / `ticket_workspaces`, `TicketRecord` / `ticket_records` | `backend/models.py:13739`, `:20622` |
| EMD | `EmdWorkspace` / `emd_workspaces`, `EMDRecord` / `emd_records` | `backend/models.py:13994`, `:20758` |
| Documents | operational `DocumentWorkspace` plus render/package/share/storage models | `backend/models.py:14507` and the Phase 36.5 document services |

Compatibility lookups are explicit in services such as `backend/services/ticket_workspace_service.py` and `backend/services/booking_workspace_service.py`. Stage A does not decide which generation is canonical; it records the overlap for later review.

### Likely stale collection mapping (confirmed source mismatch)

`backend/services/airline_contact_communication_intelligence_service.py:153` maps `ssr_osi_workspace_id` to `ssr_osi_operational_workspaces`, and `_integration_snapshot` uses that value in `db.collection(...)` at line 709. The registered/indexed operational collection is `ssr_osi_workspaces` in `backend/database.py:606` and `backend/services/ssr_osi_workspace_service.py:22`.

The current code degrades a missing lookup to a manual-review warning, but valid SSR/OSI workspace links can therefore resolve against the wrong collection name in this integration path.

### Ownership coverage (structural)

Of 503 discovered collection names:

- 397 are in `AGENCY_OWNED_COLLECTIONS`;
- 49 are in `COLLECTION_OWNERSHIP_REGISTRY`;
- 45 appear in both;
- 102 appear in neither explicit ownership registry.

The unclassified set includes global auth, airline intelligence, policy, reference, and capability collections, plus the stale SSR/OSI name above. This does not imply missing indexes or unsafe access by itself; it means ownership is inferred from service behavior rather than declared in either current registry. Filter `model-and-collection-inventory.csv` for `ownership_type=not_in_governed_query_registry` for the complete set.

### Models with no static symbol consumer (static-only)

Twenty-nine definitions have no token-level reference outside their declaration. They include legacy airline master/fleet/distribution schemas, several update payloads, and utility schemas:

`AdmRiskEvent`, `AiTraceEvent`, `AircraftConfiguration`, `AircraftSeatmap`, `AircraftTailNumber`, `AirlineAncillary`, `AirlineBrandAsset`, `AirlineContact`, `AirlineDistributionProfile`, `AirlineExceptionRule`, `AirlineFareRule`, `AirlineFleetType`, `AirlineGdsParameters`, `AirlineInterlineAgreement`, `AirlinePssParameters`, `AirlineRbdMatrixRow`, `AirlineRoute`, `AirlineServicePriceQuoteScenarioUpdate`, `ApiMessage`, `ClientPassengerMasterLinkUpdate`, `ClientPortalAccessProfileUpdate`, `DemoLoginRequest`, `PassengerKnownDocumentUpdate`, `PassengerOperationalPreferenceUpdate`, `PassengerServiceHistoryUpdate`, `PassengerServiceRequestUpdate`, `PlatformUserCreate`, `TripLinkRequestPayload`, and `WorkspaceStatus`.

String-based/reflection consumers are not detectable statically, so these are review candidates rather than proven dead code.

## Service Overlaps

No service class name is duplicated. Seventeen public helper names recur across service modules, including `payload_dict`, `enum_value`, `normalize_airline_code`, `normalize_taxonomy_code`, `clean_updates`, `visible_scoped`, `actor_from_user`, and `utc_now`. These are mostly small normalization/projection helpers. Full module membership is in `service-inventory.csv`; Stage A does not recommend consolidation.

## Documentation Gaps

### Stale readiness route (confirmed)

`docs/architecture/ticket-workspace-foundation.md:84` documents `/api/health/ready`, but no such route exists. Current readiness routes are `/api/readiness` and protected `/api/system/readiness` in `backend/server.py`.

The other unmatched documented API strings are `/api/admin*` and `/api/agent*`, which occur as prohibited route examples and are correctly absent.

All implemented API operations are covered by at least one documented route family. Six implemented UI roots lack a matching route string in the documentation corpus: `/`, `/login`, `/invite/accept`, and the three `/site/{...}` public website patterns.

## Smoke, CI, and Index Registration Gaps

- Smoke scripts missing inventory registration: **0**.
- Inventory entries missing scripts: **0**.
- Startup indexes without a corresponding inventoried collection: **0**.
- CI workflow files inventoried: **4**.

The smoke and CI inventory reports declarations and metadata only; Stage A did not execute all 142 smokes or CI workflows.
