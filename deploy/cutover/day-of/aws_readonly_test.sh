set -euo pipefail
# read-only session: the server refuses any write from this connection
export PGOPTIONS='-c default_transaction_read_only=on'
SRC="host=$SRC_HOST dbname=$SRC_DB user=$SRC_USER password=$SRC_PASSWORD sslmode=require"
echo "AWS connect: $(psql "$SRC" -Atc 'select 1')"
echo "AWS database default read-only: $(psql "$SRC" -Atc "select coalesce((select array_to_string(setconfig, ',') from pg_db_role_setting s join pg_database d on d.oid=s.setdatabase where d.datname=current_database() and s.setrole=0), 'none set')")"
echo "AWS size: $(psql "$SRC" -Atc 'select pg_size_pretty(pg_database_size(current_database()))')"
echo "AWS active connections: $(psql "$SRC" -Atc 'select count(*) from pg_stat_activity where datname = current_database()')"
echo "AWS server version: $(psql "$SRC" -Atc 'show server_version')"
unset PGOPTIONS
TGT="host=/cloudsql/$TGT_CONN dbname=$TGT_DB user=$TGT_USER password=$TGT_PASSWORD"
echo "GCP connect: $(psql "$TGT" -Atc 'select 1')"
