#!/bin/bash
# Run a Django management command from cron on Elastic Beanstalk.
#
# Cron starts with an empty environment, but settings.py needs the EB
# environment properties (RDS_*, AWS_STORAGE_BUCKET_NAME, ADMINS, ...); without
# them every job crashed at import (#673). Load them, then run the command
# under flock so a slow run is never overlapped by the next one.
#
# Usage (crontab): /bin/bash /var/app/current/scripts/cron-manage.sh <command> [args]
set -euo pipefail

set -a
eval "$(/opt/elasticbeanstalk/bin/get-config environment \
    | jq -r 'to_entries[] | "\(.key)=\(.value | @sh)"')"
set +a

source /var/app/venv/*/bin/activate
cd /var/app/current

echo "$(date -u +%FT%TZ) start $*"
status=0
flock -n "/tmp/webcdi-cron-$1.lock" python manage.py "$@" || status=$?
echo "$(date -u +%FT%TZ) end $* (exit $status)"
exit $status
