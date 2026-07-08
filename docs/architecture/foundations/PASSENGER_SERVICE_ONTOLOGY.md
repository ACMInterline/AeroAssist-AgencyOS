# Passenger Service Ontology

The Passenger Service Ontology defines the operational chain that AeroAssist uses for passenger service work.

## Hierarchy

Passenger
-> Need
-> Service Requirement
-> Operational Service
-> SSR / OSI
-> Approval
-> Document
-> EMD
-> Ticket / Booking
-> Travel Readiness

## Meaning

Passenger is the person whose journey must be completed.

Need is the reason ordinary travel shopping is not enough. It may involve mobility, medical, animal transport, baggage, seating, documents, approval, airport handling, aircraft, cabin, timing, connection, fare, or airline-specific conditions.

Service Requirement is the structured expression of that need.

Operational Service is the agency-manageable service record that links the requirement to airline handling, documents, EMDs, approvals, tickets, timelines, and workflow stages.

SSR / OSI records carry airline communication and handling metadata.

Approval records show whether airline, airport, authority, supplier, or internal review has accepted the service condition.

Document records show evidence, forms, certificates, receipts, confirmations, waivers, and readiness artifacts.

EMD records represent ancillary or service payment metadata when applicable.

Ticket / Booking records represent the travel document and reservation context. They support the service case but do not replace passenger need as the root.

Travel Readiness is the operational state where required service, evidence, payment artifacts, booking artifacts, documents, and review notes indicate that the passenger can proceed.

## AOIE Connection

AOIE reads passenger service requirements from this ontology and compares them with structured airline operational knowledge. Future recommendation phases must preserve this direction: Passenger Need first, airline and itinerary options second.
