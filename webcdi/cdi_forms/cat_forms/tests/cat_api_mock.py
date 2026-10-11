"""Hermetic replay of the R CAT API for the language CAT view tests.

The per-language CAT tests replay a recorded item/response/theta sequence and
assert the word shown at each step. They used to reach the *live* production R
API to obtain each next item, which made the suite require a network connection
and coupled it to whatever parameters happen to be deployed (that drift is what
broke the Spanish sequence test). The recorded sequences are the ground truth
the API is supposed to return, so replaying them locally exercises the full view
flow — render, store answer, advance, stop, persist theta — with no network.

Install with `install_sequence_api` / `install_start_api` inside a test; both
register cleanup so the patch is torn down automatically.
"""
import csv
import re
from unittest import mock

_PATCH_TARGET = "cdi_forms.cat_forms.views.cdi_cat_api"


def _load(path):
    with open(path, encoding="utf8") as f:
        return list(csv.DictReader(f))


def _administered_count(query_string):
    """Number of items in a nextItem query's `items=[...]` list."""
    m = re.search(r"items=\[([^\]]*)\]", query_string)
    if not m:
        return 0
    inner = m.group(1).strip()
    return 0 if not inner else len([x for x in inner.split(",") if x.strip()])


def _theta4(value):
    # the live API returned theta rounded to 4 decimals; the view stores it
    # verbatim and the tests compare against the same 4-decimal rounding
    return float("{:.4f}".format(float(value)))


def _sequence_api(rows):
    def fake(query_string):
        if query_string.startswith("startItem"):
            r = rows[0]
            return {"index": int(r["index"]), "definition": r["item"],
                    "stop": False, "curTheta": None}
        if query_string.startswith("nextItem"):
            n = _administered_count(query_string)
            if n >= len(rows):
                return {"stop": True, "definition": None, "index": None,
                        "curTheta": _theta4(rows[-1]["theta"])}
            r = rows[n]
            return {"index": int(r["index"]), "definition": r["item"],
                    "stop": False, "curTheta": _theta4(rows[n - 1]["theta"])}
        # hardestWord / easiestWord: not asserted by the tests, return any item
        r = rows[0]
        return {"index": int(r["index"]), "definition": r["item"]}
    return fake


def _start_api(path):
    by_age = {str(int(float(r["age"]))): r for r in _load(path)}
    fallback = by_age.get("30") or next(iter(by_age.values()))

    def fake(query_string):
        m = re.search(r"age_mos=(\d+)", query_string)
        r = by_age.get(m.group(1)) if m else None
        r = r or fallback
        return {"index": int(float(r["index"])), "definition": r["definition"],
                "stop": False, "curTheta": float(r["theta"])}
    return fake


def install_sequence_api(testcase, sequence_path):
    """Patch the view's cdi_cat_api to replay a recorded sequence CSV."""
    patcher = mock.patch(_PATCH_TARGET, side_effect=_sequence_api(_load(sequence_path)))
    patcher.start()
    testcase.addCleanup(patcher.stop)


def install_start_api(testcase, start_path):
    """Patch the view's cdi_cat_api to answer startItem from a start-items CSV."""
    patcher = mock.patch(_PATCH_TARGET, side_effect=_start_api(start_path))
    patcher.start()
    testcase.addCleanup(patcher.stop)
