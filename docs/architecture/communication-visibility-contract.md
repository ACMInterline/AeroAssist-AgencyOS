# Communication Visibility Contract

## Values

| Visibility | Intended audience | Never implies |
|---|---|---|
| `internal` | Authorized Agency operations staff | Client, passenger, supplier, or Platform visibility |
| `agency` | Authorized Agency staff | Portal or supplier visibility |
| `client` | Explicitly linked Client Portal participant and Agency staff | Passenger-wide, supplier, or internal finance access |
| `passenger` | Explicitly linked Passenger Portal participant and Agency staff | Client account-wide, supplier, or internal access |
| `supplier` | Governed manual supplier/airline participant and Agency staff | Provider delivery or internal finance access |
| `platform` | Authorized Platform governance | Agency staff impersonation or Portal visibility |
| `system` | Internal system evidence | Any external visibility |

## Enforcement

Visibility is checked at four boundaries:

1. Thread allowlist.
2. Participant permission and participant type.
3. Message or attachment visibility.
4. Reader projection.

Agency access still requires active membership and a matching immutable
`agency_id`. Platform roles do not silently become Agency participants. Portal
access additionally requires active identity mapping, matching subject type,
thread participation, and ownership of at least one referenced entity.

## Non-Leakage Rules

- Client Portal never sees internal notes, supplier exchanges, cost, margin,
  reconciliation, or system entries.
- Passenger Portal never receives Client account-wide information merely
  because a passenger belongs to that Client.
- Supplier and airline participants never receive Agency-internal finance or
  operations notes.
- Platform governance reads are protected and read-only.
- Search uses the same Agency and visibility projection as ordinary reads and
  is bounded to 100 results.
- Recipient IDs, attachment IDs, and entity references must belong to the same
  Agency and thread.

Hidden frontend navigation is not authorization. Every boundary is enforced
server-side.
