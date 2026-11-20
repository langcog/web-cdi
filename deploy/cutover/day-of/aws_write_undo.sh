set -euo pipefail
SRC="host=$SRC_HOST dbname=$SRC_DB user=$SRC_USER password=$SRC_PASSWORD sslmode=require"
psql "$SRC" -v ON_ERROR_STOP=1 <<'SQL'
SET default_transaction_read_only = off;
ALTER ROLE "webcdi-admin" RESET default_transaction_read_only;
SQL
echo "UNDO role setting: $(psql "$SRC" -Atc "select coalesce((select array_to_string(setconfig, ',') from pg_db_role_setting where setrole = (select oid from pg_roles where rolname = current_user) and setdatabase = 0), 'none')")"
echo "UNDO sessions ended: $(psql "$SRC" -Atc "select count(pg_terminate_backend(pid)) from pg_stat_activity where datname = current_database() and usename = current_user and pid <> pg_backend_pid()")"
echo "UNDO new session read-only: $(psql "$SRC" -Atc 'show default_transaction_read_only')"
