from collections import Counter
from django.db import transaction
from django.test import Client
from django.urls import reverse
from researcher_UI.models import Administration, SummaryData, Study
allowed = {"<1", "not computed"} | {str(p) for p in range(1, 100)}
vals = Counter(SummaryData.objects.filter(title__contains="Percentile").values_list("value", flat=True))
bad = {v: n for v, n in vals.items() if v not in allowed}
print("CHECK percentile values:", sum(vals.values()), "| invalid:", bad)
print("CHECK completed:", Administration.objects.filter(completed=True).count(), "| completed but unscored:", Administration.objects.filter(completed=True, scored=False).count())
theta = Counter(SummaryData.objects.filter(title="Benchmark Theta").values_list("value", flat=True))
print("CHECK CAT theta rows:", sum(theta.values()), "| zeros:", theta.get("0", 0) + theta.get("0.0", 0), "| blank:", theta.get("", 0))
actions = ["download-study-csv", "download-study-csv-adjusted", "download-summary-csv"]
res = Counter()
for inst in Study.objects.filter(active=True).values_list("instrument__name", flat=True).distinct():
    st = Study.objects.filter(active=True, instrument__name=inst, administration__completed=True).order_by("-id").first()
    if not st: continue
    with transaction.atomic():  # everything, including the login, is rolled back
        c = Client(HTTP_HOST="webcdi.org", HTTP_X_FORWARDED_PROTO="https", raise_request_exception=False); c.force_login(st.researcher)
        for a in actions:
            try:
                with transaction.atomic():
                    r = c.post(reverse("researcher_ui:console_study", args=[st.pk]), {a: a}, secure=True)
                code, size = r.status_code, len(r.content)
            except Exception as e:
                code, size = type(e).__name__, 0
            k = "ok" if code == 200 and size > 100 else str(code)
            res[k] += 1
            if k != "ok": print("CHECK not-200:", inst, a, code)
        transaction.set_rollback(True)
print("CHECK downloads:", dict(res), "(expect 83 ok + Argentine_Spanish_WG summary 302)")
