# MongoDB Security, Backup, and Disaster Recovery Foundation

## Scope

Phase 56.5.5 hardens the existing MongoDB 7 and Hostinger Docker Compose deployment. It adds authenticated production configuration, a least-privilege application user, internal-only database networking, timestamped logical backups, integrity manifests, retention controls, guarded restore planning, and disposable restore rehearsals.

It does not migrate or touch the live volume, deploy production changes, restore production automatically, change application collections, or alter product behavior.

## Threat Model

The foundation addresses accidental public database exposure, unauthenticated production access, weak or committed credentials, incomplete backups, silent archive corruption, destructive restore mistakes, unbounded retention deletion, and recovery procedures that exist only as operator memory. Host compromise, malicious root access, off-site storage, hardware failure, and managed secret-store integration remain operational concerns outside the repository.

## Production Architecture

- MongoDB has no production host-port mapping and is reachable through the private Compose network.
- The backend connects with a dedicated application identity granted `readWrite` only on `MONGO_DATABASE`.
- Administrative credentials initialize an empty volume and are reserved for controlled administration and restore operations.
- Compose explicitly masks administrative variables in the backend container; only MongoDB and host-side guarded operator tooling receive them.
- The application builds an authenticated URI from environment values when `MONGODB_URL` is blank. Credentials are percent-encoded and never returned through readiness.
- Production configuration fails closed when MongoDB authentication is absent, disabled, incomplete, or uses obvious placeholder passwords.
- Development may explicitly use unauthenticated local MongoDB or the in-memory database.

The first-run initializer at `deploy/hostinger/mongodb/init-application-user.sh` runs only during official MongoDB empty-volume initialization. It is idempotent and does not print credentials.

## Existing Volume Safety

MongoDB image initialization variables do not create users in an existing populated volume. Adding root variables and restarting can therefore enable authentication before a valid user exists. Phase 56.5.5 intentionally does not automate that migration.

The required migration sequence is:

1. Take and verify a pre-migration MongoDB and document-export backup.
2. Copy verified backup sets off the VPS.
3. Schedule a maintenance window and stop backend/frontend writes.
4. Confirm MongoDB remains unexposed and use only local `docker compose exec` access.
5. Create an administrative user in `admin` and an application user in `MONGO_AUTH_SOURCE`, granting the latter `readWrite` only on `MONGO_DATABASE`.
6. Verify both identities before changing the MongoDB startup mode.
7. Populate protected production environment values and run preflight checks.
8. Switch Compose to authenticated operation and reconnect the backend.
9. Verify backend health, public-safe readiness, application reads, and a fresh authenticated backup.
10. If verification fails, stop application traffic, revert the Compose/configuration switch during the same maintenance window, and investigate without deleting the volume.

Exact commands and rollback checkpoints are in `deploy/hostinger/MONGODB_DISASTER_RECOVERY_RUNBOOK.md`.

## Credential Handling

Examples contain placeholders only. `.env` remains ignored. Scripts consume a protected environment file and execute MongoDB tools inside the internal container without echoing passwords or authenticated URIs. The backend container masks root credentials and receives only application credentials. Manifests reject credential-like fields. Readiness reports only boolean capabilities. Future Docker secrets or managed secret-store adoption can replace environment resolution without changing the application-user or backup design.

## Backup Architecture

`deploy/hostinger/scripts/backup_mongo.sh` uses authenticated `mongodump` and creates:

```text
/var/backups/aeroassist/YYYYMMDDTHHMMSSZ/
  mongodb-YYYYMMDDTHHMMSSZ.archive.gz
  mongodb-YYYYMMDDTHHMMSSZ.archive.gz.sha256
  mongodb-YYYYMMDDTHHMMSSZ.manifest.json
```

The manifest records only non-sensitive metadata: UTC timestamp, database name, archive name and size, SHA-256, Git revision, canonical build phase, MongoDB/tool versions, environment label, collection/document counts, document-export backup reference, and verification timestamps. `verify_mongodb_backup.sh` checks the manifest and checksum, then asks `mongorestore --dryRun` to parse the archive before marking it inspected.

`backup_all.sh` coordinates this logical database backup with the existing `document_exports.tar.gz` backup. It does not include `.env`, credentials, nginx files, uploaded external state, or document content in the MongoDB manifest.

## Non-Database Recovery Inventory

- `mongo_data`: application collections and indexes, covered by logical MongoDB backup.
- `document_exports`: generated document artifacts, covered by `backup_exports.sh`.
- VPS `.env.production`: secrets and deployment settings; protect separately, never place in ordinary backup archives.
- Host nginx and TLS configuration: preserve through controlled infrastructure configuration backup.
- Repository and Compose configuration: recover from the verified Git revision.
- External providers or future object storage: governed by their own recovery systems and not included here.

## Retention

`prune_backups.sh` is dry-run by default. `BACKUP_RETENTION_DAYS` and `BACKUP_MINIMUM_COUNT` are configurable. Only complete manifests marked `archive_inspected` or `restore_rehearsed` are eligible. The newest verified set is never removed, the minimum verified count is always retained, unrelated files are ignored, and an archive/checksum/manifest set is handled together. Operators may begin with daily backups, 30 days, and at least 7 verified sets, but legal and business requirements must determine production policy.

## Restore Safety

`restore_mongodb_backup.sh` requires an explicit archive and target database and performs validation only unless `--execute` is supplied. Test execution requires a non-production environment file, `RESTORE_TARGET_ENV=test`, and `ALLOW_DESTRUCTIVE_TEST_RESTORE=true`. Any write to a production-configured MongoDB cluster, including a differently named candidate database, requires `RESTORE_TARGET_ENV=production`, `ALLOW_PRODUCTION_RESTORE=true`, the exact confirmation phrase, and a matching `--confirm-target`. Restore is never called by deployment, application startup, systemd, or CI.

`test_restore_mongodb_backup.sh` creates a disposable authenticated MongoDB container and volume, maps the source database to an explicitly different test database, compares collection/document counts with the manifest, records the rehearsal, and removes all disposable resources by default.

## Scheduling

Existing Ubuntu systemd timer examples run `backup_all.sh` daily and verification separately. Installation and enablement remain manual. Application containers do not schedule backups. Operators should monitor systemd exit status and journal logs, copy verified backups off-host, and rehearse restoration on a regular cadence appropriate to operational risk.

## Recovery Objectives

RPO depends on backup frequency, successful verification, and off-host replication. RTO depends on image availability, archive size, document-export volume, VPS provisioning, DNS/TLS recovery, and operator rehearsal. This foundation provides measurement inputs and repeatable procedures but does not guarantee RPO or RTO values.

## Readiness

`mongodb_security_backup_disaster_recovery_foundation` reports support for authentication, network isolation, backup tooling, checksum/manifest verification, retention, dry-run restore, disposable rehearsal, credential redaction, migration documentation, storage inventory, and scheduler examples. It never scans backup directories on a readiness request or exposes usernames, paths, URIs, archive contents, or secrets.

## Limitations

- Production authentication is supported but is not enabled by this repository change.
- Existing-volume migration is manual and must occur in a maintenance window.
- Backups remain local until an operator configures protected off-host copies.
- Logical backups are not point-in-time oplog recovery.
- Credential rotation and restore cutover require human authorization.
- The foundation does not install timers, deploy, restore production, or claim disaster-recovery certification.
