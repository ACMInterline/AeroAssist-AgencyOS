# Product Surface And Workspace Governance

## Purpose

This policy establishes the permanent Product Surface Review Gate for AeroAssist. It keeps operational ownership clear, limits unnecessary navigation, and prevents an internal engine or metadata model from becoming a duplicate user workflow.

## Workspace Ownership

One operational object has one primary workspace. The primary Agency workspaces are Client, Passenger, Request, Trip, Offer, Booking, Ticket, EMD, and Document. Each owns its object's lifecycle, navigation context, and user-facing history.

An engine, service, projection, evaluator, or diagnostic does not automatically require a top-level page. A capability that supports an existing operational object must normally appear as a tab, panel, step, or contextual action in the owning workspace. Its backend service and internal compatibility identifiers may remain modular.

Separate pages are justified only when at least one of these conditions applies:

- the surface serves a different actor, such as the authenticated Client Portal;
- the surface provides Platform governance or diagnostics;
- the record has a truly independent lifecycle and canonical owner;
- the surface represents a materially different operational object.

## Offer Lifecycle

Offer Workspace is the canonical commercial owner. Its Agency lifecycle is Overview, Client & Passengers, Itinerary Builder, Itinerary Options & Fare Brands, Airline Suitability, Offer Comparison, Client Preview, Delivery & Responses, and History.

Phase 56 services remain modular engines. Itinerary Builder, Itinerary Options & Fare Brands, Offer Comparison, and Offer Delivery are contextual tools owned by Offer Workspace. They must not appear as independent primary Agency navigation entries. A compatibility deep route may render the same reusable component, but it must require Offer context and guide the user back to the owning Offer Workspace.

The authenticated Portal offer-review experience remains separate because it serves the client. Offer Delivery Diagnostics remains separate because it is a read-only Platform governance surface.

## Terminology

Ordinary Agency and Client Portal UI uses travel-industry vocabulary:

- `JourneyRepresentation` is shown as Itinerary.
- Journey authoring is shown as Itinerary Builder.
- Journey option composition is shown as Itinerary Options & Fare Brands.
- Journey comparison presentation is shown as Offer Comparison.
- Journey offer delivery is shown as Offer Delivery.
- Journey segment is shown as Flight Segment or Itinerary Segment according to context.

Internal names may remain in classes, collections, API compatibility routes, and explicit technical diagnostics. Terms such as projection, representation, composition, payload, source hash, metadata-only, and handoff must not appear in ordinary Agency or Client UI outside a clearly identified technical-details view.

## Product Surface Review Gate

Every future phase must answer these questions before adding a route, page, or module entry:

1. What existing workspace owns this capability?
2. Is a new top-level menu item necessary?
3. Could this be a tab, panel, step, or contextual action?
4. Does it create or imply a duplicate lifecycle?
5. Does it increase unnecessary navigation?
6. Is the terminology understood by travel agents?
7. Does it preserve the passenger-needs-first principle?

The implementation must classify new surfaces as `primary_workspace`, `contextual_tool`, `platform_diagnostic`, or `client_portal`. Only `primary_workspace` records belong in main Agency navigation. Smoke coverage must verify ownership, classification, visible terminology, and contextual routing for material new surfaces.

## Route Rules

Contextual tools use canonical `/agency/*` and `/api/agencies/{agency_id}/*` families and preserve the owning record ID. Platform diagnostics use `/platform/*` and `/api/platform/*`. Client experiences use the authenticated `/portal/*` and `/api/portal/*` families. A contextual tool must not create an anonymous public route, parallel Offer API, or alternate lifecycle root.

## Phase 56.4 Decision

Phase 56.4 retains immutable delivery versions, authorized recipients, client-safe content, decisions, acknowledgements, questions, expiry, revocation, supersession, document links, Offer Acceptance integration, audit history, timeline integration, Portal review, and Platform diagnostics. The Agency experience is consolidated into Offer Workspace under Delivery & Responses. Delivery statuses remain subordinate to canonical Offer status.
