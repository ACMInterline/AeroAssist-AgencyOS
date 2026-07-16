#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${MONGO_INITDB_ROOT_USERNAME:-}" || -z "${MONGO_INITDB_ROOT_PASSWORD:-}" ]]; then
  echo "MongoDB authentication initialization is explicitly disabled; application user initialization skipped."
  exit 0
fi

if [[ -z "${MONGO_APP_USERNAME:-}" || -z "${MONGO_APP_PASSWORD:-}" || -z "${MONGO_DATABASE:-}" ]]; then
  echo "FAIL: authenticated MongoDB initialization requires application credentials and a database name." >&2
  exit 1
fi

export MONGO_AUTH_SOURCE="${MONGO_AUTH_SOURCE:-admin}"

mongosh --quiet \
  --host 127.0.0.1 \
  --username "$MONGO_INITDB_ROOT_USERNAME" \
  --password "$MONGO_INITDB_ROOT_PASSWORD" \
  --authenticationDatabase admin <<'MONGOSH'
const authDatabaseName = process.env.MONGO_AUTH_SOURCE || "admin";
const applicationDatabaseName = process.env.MONGO_DATABASE;
const applicationUsername = process.env.MONGO_APP_USERNAME;
const applicationPassword = process.env.MONGO_APP_PASSWORD;
const authDatabase = db.getSiblingDB(authDatabaseName);

if (authDatabase.getUser(applicationUsername) === null) {
  authDatabase.createUser({
    user: applicationUsername,
    pwd: applicationPassword,
    roles: [{role: "readWrite", db: applicationDatabaseName}],
  });
}
MONGOSH

echo "MongoDB application user initialization completed without printing credentials."
