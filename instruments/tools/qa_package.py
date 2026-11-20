"""Run LLM item QA on a package with every configured model; write the union of flags.

Calibration (instruments/calibration/) showed the models catch similar shares of
injected faults but different real errors, so reviewers get the union, with a
column saying which model(s) raised each flag.

Writes instruments/packages/<Package>/qa/item_flags.csv.

Usage: python qa_package.py PACKAGE [PACKAGE ...]
"""

import csv
import sys
from collections import defaultdict

import yaml

import qa_items
import sources

MODELS = ["gemini-3.8-flash", "gemini-3.1-pro-preview"]
SCRIPT_NAMES = {"latin": "Latin", "cjk": "Chinese characters", "hangul": "Hangul",
                "hebrew": "Hebrew", "devanagari": "Devanagari", "cyrillic": "Cyrillic"}


def run(package):
    pdir = sources.PACKAGES / package
    manifest = yaml.safe_load((pdir / "manifest.yaml").read_text())
    ins = manifest["instrument"]
    with open(pdir / "items.csv", encoding="utf8") as f:
        rows = list(csv.DictReader(f))
    items = [r for r in rows if r["item_type"] == "word"]
    script = ins.get("script_description") or SCRIPT_NAMES[ins["script"]]

    merged = defaultdict(lambda: {"models": []})
    for model in MODELS:
        qa_items.CONFIG["models"]["item_qa"] = model
        flags, _ = qa_items.run(items, ins["verbose_name"], ins["form"], script)
        for fl in flags:
            m = merged[(fl["itemID"], fl["issue"])]
            m.update({k: v for k, v in fl.items() if k not in m or not m[k]})
            m["models"].append(model)

    by_id = {r["itemID"]: r for r in rows}
    out = pdir / "qa" / "item_flags.csv"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", encoding="utf8", newline="") as f:
        w = csv.DictWriter(f, lineterminator="\n", fieldnames=[
            "itemID", "source_ref", "definition", "issue", "confidence", "models",
            "explanation", "suggested_fix"])
        w.writeheader()
        for (iid, _), fl in sorted(merged.items(), key=lambda kv: kv[0]):
            r = by_id.get(iid, {})
            w.writerow({"itemID": iid, "source_ref": r.get("source_ref", ""),
                        "definition": r.get("definition", ""), "issue": fl["issue"],
                        "confidence": fl["confidence"], "models": "+".join(fl["models"]),
                        "explanation": fl["explanation"], "suggested_fix": fl["suggested_fix"]})
    print(f"{package}: {len(merged)} flags -> {out.relative_to(sources.REPO)}")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        run(p)
