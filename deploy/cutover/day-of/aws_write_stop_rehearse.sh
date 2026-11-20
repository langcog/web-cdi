set -euo pipefail
SRC="host=$SRC_HOST dbname=$SRC_DB user=$SRC_USER password=$SRC_PASSWORD sslmode=require"
# the real statement inside a transaction that is always rolled back
psql "$SRC" -v ON_ERROR_STOP=1 -At <<'SQL'
BEGIN;
ALTER ROLE "webcdi-admin" SET default_transaction_read_only = on;
SELECT 'TEST inside transaction: ' || coalesce(array_to_string(setconfig, ','), 'none') FROM pg_db_role_setting WHERE setrole = (select oid from pg_roles where rolname = current_user) AND setdatabase = 0;
ROLLBACK;
SQL
echo "TEST after rollback: $(psql "$SRC" -Atc "select coalesce((select array_to_string(setconfig, ',') from pg_db_role_setting where setrole = (select oid from pg_roles where rolname = current_user) and setdatabase = 0), 'none')")"
echo "TEST new session read-only: $(psql "$SRC" -Atc 'show default_transaction_read_only')"
