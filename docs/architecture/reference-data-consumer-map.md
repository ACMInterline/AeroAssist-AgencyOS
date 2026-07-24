# Reference Data Consumer Map

The machine-readable registry is
`backend/services/reference_domain_usage_service.py`. It covers every registered
reference domain and the canonical service catalogue. Entries are sorted by
domain key and declare models, fields, routes, selectors, workflows, risk, and
migration status.

| Domain | Primary models/collections | Canonical fields | Frontend selector |
|---|---|---|---|
| passenger_types | PassengerProfile, RequestPassenger | passenger_type_code_id/code/label | PtcSelect |
| countries | PassengerProfile, RequestPassenger | nationality/residence/passport IDs and snapshots | CountrySelect |
| languages | PassengerProfile | primary_language_reference_id/code/label | ReferenceSelect |
| document_types | PassengerProfile, Document/Request compatibility | travel_document_type_id/code/label | ReferenceSelect |
| airports | RequestSegment, TripSegment, Offer segments | origin/destination IDs and snapshots | AirportAutocomplete |
| airlines | RequestSegment, Trip/Offer compatibility | carrier and preferred/excluded IDs and snapshots | AirlineAutocomplete |
| cabin_classes | Request V4 trip/segments | cabin ID/code/label | ReferenceSelect |
| currencies | Request V4, Offer, Invoice compatibility | currency ID/code/label | CurrencySelect |
| pet_species | RequestPet | species_reference_id/key/label | ReferenceSelect |
| pet_breeds | RequestPet | breed_reference_id/key/label | ReferenceSelect |
| container_types | RequestPet | container_type_reference_id/code/label | ReferenceSelect |
| special_item_categories | RequestSpecialItem | item_category_reference_id/code/label | ReferenceSelect |
| service_catalogue | PassengerServiceRequest and Request services | service catalogue ID/key/snapshot | existing service controls |

Domains without a registered operational consumer remain explicit
`consumer_wiring_pending` entries rather than disappearing from the registry.

## Usage Counts and Deactivation

Per-record usage checks scan only registered consumer fields with a bounded
limit. Counts distinguish active and historical records and produce one of
`high`, `historical_only`, or `none` deactivation risk. The Platform console
shows these counts before lifecycle actions. Active usage requires an explicit
forced override reason and audit event.

The registry is descriptive and protective. It does not activate a workflow,
enforce airline policy, calculate a price, or migrate data.
