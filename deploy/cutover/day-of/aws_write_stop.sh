set -euo pipefail
SRC="host=$SRC_HOST dbname=$SRC_DB user=$SRC_USER password=$SRC_PASSWORD sslmode=require"
psql "$SRC" -v ON_ERROR_STOP=1 -c 'ALTER ROLE "webcdi-admin" SET default_transaction_read_only = on'
echo "STOP role setting: $(psql "$SRC" -Atc "select coalesce(array_to_string(setconfig, ','), 'none') from pg_db_role_setting where setrole = (select oid from pg_roles where rolname = current_user) and setdatabase = 0")"
echo "STOP sessions ended: $(psql "$SRC" -Atc "select count(pg_terminate_backend(pid)) from pg_stat_activity where datname = current_database() and usename = current_user and pid <> pg_backend_pid()")"
echo "STOP new session read-only: $(psql "$SRC" -Atc 'show default_transaction_read_only')"
# a write must now be refused (WHERE false: it would touch no rows anyway)
if psql "$SRC" -v ON_ERROR_STOP=1 -qc 'update django_site set domain = domain where false' 2>/tmp/err; then
  echo "STOP WRITE TEST FAILED: a write was allowed"; exit 1
else
  echo "STOP write test refused: $(head -1 /tmp/err)"
fi
