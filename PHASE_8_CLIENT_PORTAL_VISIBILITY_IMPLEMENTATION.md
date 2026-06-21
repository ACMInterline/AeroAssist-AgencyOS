# Phase 8 Client Portal Visibility Implementation

Phase 8 adds the read-only client portal visibility foundation for AeroAssist AgencyOS. It is intentionally a portal preview and data-safety layer, not production authentication, request submission, offer acceptance, document sharing, PDF export, email delivery, or payment processing.

## Scope Implemented

- Portal access mapping records that connect a demo portal email to one agency client.
- Read-only `/api/portal` backend router for the current mapped client.
- Client profile, passenger, request, offer, booking, document, invoice, and payment visibility endpoints.
- Client/passenger relationship enforcement using active relationships with `can_view=true`.
- Client-scoped entity enforcement for requests, offers, bookings, rendered documents, invoices, and payments.
- Explicit portal-safe response projections to avoid raw internal records.
- Client-visible-only request messages, request tasks, request timeline events, offer price lines, invoice line items, and rendered documents.
- Branded portal layout using the agency workspace brand snapshot.
- Frontend portal routes for dashboard, profile, passengers, requests, offers, bookings, documents, invoices, and payments.
- Seeded demo portal accounts for the individual and organization sample clients.

## Models Added

- `PortalAccessMapping`

The mapping stores `agency_id`, `client_id`, `user_email`, `portal_status`, `display_name`, and `last_login_at`. It is a development foundation for client portal identity mapping and should be replaced or hardened when production auth is introduced.

## Backend Endpoints Added

- `GET /api/portal/me`
- `GET /api/portal/dashboard`
- `GET /api/portal/profile`
- `GET /api/portal/passengers`
- `GET /api/portal/passengers/{passenger_id}`
- `GET /api/portal/requests`
- `GET /api/portal/requests/{request_id}`
- `GET /api/portal/offers`
- `GET /api/portal/offers/{offer_id}`
- `GET /api/portal/bookings`
- `GET /api/portal/bookings/{booking_id}`
- `GET /api/portal/documents`
- `GET /api/portal/documents/{document_id}`
- `GET /api/portal/invoices`
- `GET /api/portal/invoices/{invoice_id}`
- `GET /api/portal/payments`

## Frontend Routes Added

- `/portal`
- `/portal/profile`
- `/portal/passengers`
- `/portal/passengers/:passengerId`
- `/portal/requests`
- `/portal/requests/:requestId`
- `/portal/offers`
- `/portal/offers/:offerId`
- `/portal/bookings`
- `/portal/bookings/:bookingId`
- `/portal/documents`
- `/portal/documents/:documentId`
- `/portal/invoices`
- `/portal/invoices/:invoiceId`
- `/portal/payments`

## Visibility Rules

- The portal context is resolved from one active `PortalAccessMapping`.
- Every portal query is scoped to the mapped `agency_id` and `client_id`.
- Passenger records are returned only through active client/passenger relationships where `can_view=true`.
- Request details include only passengers the client can view.
- Request messages, tasks, and timeline events are included only when marked `client_visible`.
- Offer price lines and invoice line items are included only when `client_visible` is true.
- Rendered documents are included only when `client_visible=true` and not archived.
- Internal fields such as internal notes, reconciliation notes, raw sent snapshots, raw booking snapshots, passenger medical notes, passport numbers, and airline intelligence internals are not returned by portal endpoints.

## Demo Access

Phase 8 uses development-only demo headers:

```bash
X-Demo-Role: portal_client
X-Demo-Client-Email: anna.client@example.com
```

Seeded portal emails:

- `anna.client@example.com`
- `travel@orbitex.example.com`

These headers are not production authentication. They exist only so the portal surface can be exercised locally while the data contracts and visibility rules are being shaped.

## Known Limitations

- No production client login, password, SSO, MFA, invite, token, or session management.
- No public document links, PDF downloads, email sending, or share workflow.
- No offer acceptance or rejection workflow.
- No request submission or client editing workflow.
- No online payment checkout or payment gateway integration.
- No client-facing airline intelligence UI.
- No client upload or document collection workflow.

## Validation

- `python3 -m py_compile backend/*.py backend/routers/*.py backend/services/*.py`
- `npm run build`
- `git diff --check`
- Local HTTP smoke against `/api/portal` for both seeded portal accounts.
- Cross-client detail checks returned `404` for passenger, request, offer, booking, document, and invoice detail records.
- Portal JSON smoke checked for internal field names including `internal_notes`, `reconciliation_notes`, `airline_knowledge`, `medical_notes_internal`, `travel_document_notes`, `passport_number`, `sent_snapshot`, and `booking_snapshot`.

## Recommended Next Phase

The next phase should add production-grade portal identity and invitation flows, or expand portal workflows into controlled request submission and document exchange. Offer acceptance, payment checkout, public links, and PDF export should remain separate explicit phases because each adds external side effects and security concerns.
