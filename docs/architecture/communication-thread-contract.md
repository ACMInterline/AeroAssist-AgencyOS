# Communication Thread Contract

## Ownership

`CommunicationThread` is the conversation aggregate.
`CommunicationMessage`, `CommunicationParticipant`, and
`CommunicationAttachment` are governed children. New writes use
`OperationalCollaborationService`.

The canonical persistence chain is:

`communication_threads -> communication_messages ->
communication_attachments / communication_participants`

Each posted message creates linked operational timeline and audit evidence.
Notifications are derived separately.

## Thread Rules

- A thread belongs to exactly one Agency.
- A thread must reference at least one existing same-Agency business entity.
- One thread may reference Request, Offer, accepted Offer evidence, Trip,
  Booking, Ticket, EMD, Passenger Service, Document, Invoice, Payment,
  Supplier Cost, Refund, Exchange, After-Sales Case, or Task records.
- Related records stay in one thread; adapters must not create a second
  conversation tree for each page.
- Thread visibility is an allowlist for child messages and attachments.
- Supported states are `open`, `closed`, and `archived`.
- Closed threads reject new messages. Archived threads cannot be changed.
- Thread creation is idempotent when a context key is supplied.

## Message Rules

Each message records sender participant, sender type, recipients, message type,
plain text, optional rich text, attachment references, visibility, delivery
status, timestamps, audit ID, and timeline ID.

- Posted messages cannot be deleted.
- An edit requires a reason and preserves the prior body, edit timestamp,
  actor, reason, and content hash.
- An idempotency key cannot be reused with different content.
- Internal notes are messages with `message_type=internal_note` and
  `visibility=internal`.
- Portal replies are recorded as received evidence.
- Agency supplier/client/passenger messages default to `not_sent` or
  `recorded`; provider delivery cannot be asserted.
- Message bodies are not copied into notification projections.

## Compatibility Adapters

Request message, Portal message, after-sales communication, refund/exchange
message, and offer-question routes may retain their historical response
shapes. Their supported new writes must resolve a canonical thread and message.
Existing legacy rows remain read-only compatibility history.

No migration, deletion, provider delivery, or background dispatch is part of
this contract.
