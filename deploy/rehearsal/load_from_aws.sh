#!/bin/bash
# Stream the AWS production database into the staging Cloud SQL database.
# Runs as a one-off Cloud Run job (image postgres:16) — see README.md.
# Env: SRC_HOST, SRC_DB, SRC_USER, SRC_PASSWORD (secret), TGT_CONN (Cloud SQL
# connection name, mounted at /cloudsql), TGT_DB, TGT_USER, TGT_PASSWORD (secret).
set -euo pipefail

SRC="host=$SRC_HOST dbname=$SRC_DB user=$SRC_USER password=$SRC_PASSWORD sslmode=${SRC_SSLMODE:-require}"
TGT="host=${TGT_HOST:-/cloudsql/$TGT_CONN} dbname=$TGT_DB user=$TGT_USER password=$TGT_PASSWORD"

echo "$(date -u +%FT%TZ) source size: $(psql "$SRC" -Atc "select pg_size_pretty(pg_database_size(current_database()))")"
echo "$(date -u +%FT%TZ) emptying target"
# drop every table/view/sequence in public (works whoever owns the database)
psql "$TGT" -v ON_ERROR_STOP=1 -At -c "
  select format('drop view if exists public.%I cascade;', viewname) from pg_views where schemaname = 'public'
  union all
  select format('drop table if exists public.%I cascade;', tablename) from pg_tables where schemaname = 'public'
  union all
  select format('drop sequence if exists public.%I cascade;', sequencename) from pg_sequences where schemaname = 'public'
" | psql "$TGT" -v ON_ERROR_STOP=1 -q

echo "$(date -u +%FT%TZ) copying"
pg_dump --no-owner --no-acl --format=plain "$SRC" | psql "$TGT" -v ON_ERROR_STOP=1 -q

echo "$(date -u +%FT%TZ) row counts (source vs target)"
for t in researcher_UI_administration researcher_UI_study researcher_UI_administration_data cdi_forms_backgroundinfo researcher_UI_summarydata auth_user; do
  s=$(psql "$SRC" -Atc "select count(*) from \"$t\"" 2>/dev/null || echo "?")
  d=$(psql "$TGT" -Atc "select count(*) from \"$t\"" 2>/dev/null || echo "?")
  echo "  $t: $s -> $d"
done
echo "$(date -u +%FT%TZ) done"
