# Passenger Portal Contract

## Purpose

The Passenger Portal is a narrow self-service projection for one canonical
`PassengerProfile`. It is not a reduced Client account and does not inherit
Client-wide access.

Access requires an active `PortalAccessMapping` linking the authenticated
identity directly to one Passenger in the same Agency. Revoked, unlinked,
email-only, cross-Agency, or ambiguous mappings are rejected.

## Visible Records

A Passenger may view only:

- Trips containing an exact `TripPassenger` link to that Passenger;
- the Passenger's own Trip passenger row, services, pets, and special items;
- Booking Records linked to that Trip, with passenger-scoped embedded content;
- Tickets and EMDs whose canonical passenger link matches exactly;
- customer-visible Documents linked to that Passenger or to an authorized
  record without a conflicting passenger link;
- Passenger-visible Timeline events and Notification projections;
- Communication Threads where the Passenger is an explicit participant and
  the entity link is within the Passenger's scope;
- released travel options addressed to that exact Passenger, read-only;
- the Passenger's canonical travel profile.

The Passenger cannot see another traveler's Ticket, EMD, Document, service,
pet, special item, or embedded booking data merely because both travelers
share a Trip.

## Allowed Actions

The Passenger may:

- update allowlisted travel-profile preferences, assistance information,
  loyalty references, document-country/expiry summaries, and emergency
  contact data on `PassengerProfile`;
- upload an allowed file only for a Passenger-linked Document Workspace that
  explicitly requests it;
- reply in an authorized Passenger-visible Communication Thread.

Passenger access does not include Client-wide Requests, finance, Client
profile data, Offer acceptance, Client approvals, or other passengers.
Documents remain read-only except for an explicit requested-upload state.

## Sensitive Data

The projection does not return passport numbers, known-traveler numbers,
medical raw data, internal notes, supplier costs, margins, provider payloads,
credentials, or internal communication. Full identity and document changes
remain governed Agency operations.

## Compatibility And Reconciliation

Legacy Passenger workspaces and relationship-derived visibility can be read
only through documented compatibility adapters. They are not authorization
truth. Missing canonical links are reported for manual reconciliation by the
dry-run Portal migration analyzer; no automatic migration is available.
