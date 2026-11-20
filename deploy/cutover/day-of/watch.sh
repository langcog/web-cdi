#!/bin/bash
# Post-switch summary since $1 (UTC, e.g. 2026-11-20T05:18:00Z). Counts only; no URLs or identifiers.
SINCE=$1; P=hs-langcog-webcdi-prod
echo "== $(date '+%H:%M') since $SINCE"
gcloud logging read "resource.labels.service_name=\"webcdi-production\" AND timestamp>=\"$SINCE\" AND NOT textPayload:\"/health/\" AND textPayload:\"HTTP/1.1\"" --project $P --limit 5000 --format='value(textPayload)' 2>/dev/null | python3 -c "
import sys,re,collections
st=collections.Counter(); area=collections.Counter(); ips=set()
for l in sys.stdin:
    r=re.search(r'\"(GET|POST|HEAD) (/[^/ ?]*)[^\"]*\" (\d+)', l)
    if not r: continue
    if r.group(2)=='/static': continue
    st[r.group(3)[0]+'xx']+=1; area[r.group(2)]+=1
print('requests (no static/health) by status:', dict(st)); print('by area:', dict(area.most_common(8)))"
echo "error-level log entries: $(gcloud logging read "resource.labels.service_name=\"webcdi-production\" AND timestamp>=\"$SINCE\" AND severity>=ERROR" --project $P --limit 500 --format='value(timestamp)' 2>/dev/null | wc -l | tr -d ' ')"
echo "scoring runs: $(gcloud run jobs executions list --job webcdi-production-scoring --project $P --region us-west1 --limit 3 --format='value(status.completionTime,status.succeededCount,status.failedCount)' 2>/dev/null | tr '\t\n' ' |')"
