# MongoDB Restore Entry Point

Direct unattended restore commands have been replaced by guarded Phase 56.5.5 tooling.

Use:

```text
deploy/hostinger/scripts/restore_mongodb_backup.sh
deploy/hostinger/scripts/test_restore_mongodb_backup.sh
deploy/hostinger/MONGODB_DISASTER_RECOVERY_RUNBOOK.md
```

`restore_mongodb_backup.sh` is validation-only by default. Any execution against a production-configured MongoDB cluster requires multiple independent confirmations and is never called by deployment, CI, application startup, or systemd. Rehearse every selected archive in a disposable container before considering a controlled recovery cutover.
