# Participant Visibility Matrix

| Participant | Internal | Agency | Client | Passenger | Supplier | Platform | System | Posting rule |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Platform | No | No | No | No | No | Yes | No | Protected governance only; no Agency impersonation |
| Agency | Yes | Yes | Yes | Yes | Yes | No | No | Active same-Agency membership required |
| Client Portal | No | No | Yes | No | No | No | No | Active Client mapping, participation, and entity ownership |
| Passenger Portal | No | No | No | Yes | No | No | No | Active Passenger mapping, participation, and entity ownership |
| Supplier | No | No | No | No | Yes | No | No | Manual evidence only |
| Airline | No | No | No | No | Yes | No | No | Manual evidence only; no airline integration |
| System | Yes | No | No | No | No | No | Yes | Internal deterministic event producer |

## Participant Identity

A participant stores type, identity reference where applicable, display label,
role, permissions, visibility, and active status. Portal participants also
store the mapped Client or Passenger. Supplier and Airline participants store
non-secret operational references only.

Participant records do not create identities, memberships, Portal mappings,
supplier credentials, or airline credentials. Deactivated or revoked identity
links are rejected by the authentication and Portal context boundary before a
message route is reached.

## Thread Scope

Participants belong to one Agency and one thread. A participant from another
thread or Agency cannot be used as sender or recipient. Visibility must be
allowed by both participant type and thread. Search and detail projections
apply the same matrix.
