"""Run a prod Cloud Run job and print its log.
usage: runjob.py JOB [--timeout NNNs] [-- arg1 arg2 ...]   |   runjob.py attach:EXECUTION"""
import json, subprocess, sys, time, urllib.request
P, R = "hs-langcog-webcdi-prod", "us-west1"
argv = sys.argv[1:]
job = argv.pop(0)
timeout = None
if argv[:1] == ["--timeout"]:
    argv.pop(0); timeout = argv.pop(0)
args = argv[1:] if argv[:1] == ["--"] else None
def tok():
    return subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()
def _call(url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {tok()}", "Content-Type": "application/json"},
        method="POST" if body is not None else "GET")
    return json.load(urllib.request.urlopen(req))
def call(url, body=None, retry=True):
    for i in range(8):
        try:
            return _call(url, body)
        except Exception as e:
            if not retry: raise
            print("retrying after", e, flush=True); time.sleep(15)
    return _call(url, body)
if job.startswith("attach:"):
    name = job[7:]
    ex = f"projects/{P}/locations/{R}/jobs/{name.rsplit('-', 1)[0]}/executions/{name}"
else:
    over = {}
    if args is not None: over["containerOverrides"] = [{"args": args}]
    if timeout: over["timeout"] = timeout
    # never retry the run request itself: it could start the job twice
    op = call(f"https://run.googleapis.com/v2/projects/{P}/locations/{R}/jobs/{job}:run", {"overrides": over}, retry=False)
    ex = op["metadata"]["name"]
print("execution", ex.rsplit("/", 1)[-1], flush=True)
t0 = time.time()
while True:
    time.sleep(10)
    e = call(f"https://run.googleapis.com/v2/{ex}")
    if e.get("completionTime"): break
print(f"done in {time.time()-t0:.0f}s succeeded={e.get('succeededCount',0)} failed={e.get('failedCount',0)}", flush=True)
time.sleep(20)
name = ex.rsplit("/", 1)[-1]
flt = f'resource.type="cloud_run_job" labels."run.googleapis.com/execution_name"="{name}"'
ents, page = [], None
while True:
    body = {"resourceNames": [f"projects/{P}"], "filter": flt, "orderBy": "timestamp asc", "pageSize": 1000}
    if page: body["pageToken"] = page
    r = call("https://logging.googleapis.com/v2/entries:list", body)
    ents += r.get("entries", []); page = r.get("nextPageToken")
    if not page: break
for x in ents:
    m = x.get("textPayload") or x.get("jsonPayload", {}).get("message") or ""
    print(x.get("severity", ""), m[:3000])
