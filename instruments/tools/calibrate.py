"""Calibrate LLM item QA by fault injection on instruments already in production.

For each instrument: take its word items, inject known faults into ~N items per
fault type (seeded, so reruns are identical), run qa_items, and score
  - recall per fault type (an injected item counts as caught if it got ANY flag;
    we also report whether the issue type matched),
  - flags on untouched items. These are NOT automatically false positives —
    production items can be genuinely wrong — so they are written out for
    human review.

Usage: python calibrate.py [--per-type 6] [--seed 1] [INSTRUMENT ...]
"""

import argparse
import csv
import json
import random
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import qa_items

REPO = Path(__file__).resolve().parents[2]
CSV_DIR = REPO / "webcdi" / "cdi_form_csv" / "cdi_forms"
OUT = REPO / "instruments" / "calibration"

# instrument -> (language label, form label, expected script)
INSTRUMENTS = {
    "Korean_WS": ("Korean", "Words & Sentences", "Hangul"),
    "Dutch_WS": ("Dutch", "Words & Sentences", "Latin (Dutch orthography)"),
    "Hebrew_WS": ("Hebrew", "Words & Sentences", "Hebrew"),
    "French_Quebec_WS": ("French (Quebec)", "Words & Sentences", "Latin (French orthography, with accents)"),
    "Argentine_Spanish_WS": ("Spanish (Argentina)", "Words & Sentences", "Latin (Spanish orthography, with accents)"),
}

# category pairs that are clearly incompatible, for the wrong-category fault
FAR = ["animals", "vehicles", "food_drink", "clothing", "body_parts", "furniture_rooms",
       "outside", "people", "action_words", "descriptive_words"]


def load(name):
    with open(CSV_DIR / f"[{name}].csv", encoding="utf8") as f:
        rows = list(csv.DictReader(f))
    return [
        {"itemID": r["itemID"], "category": r["category"],
         "definition": r["definition"].strip(), "gloss": (r.get("gloss") or "").strip()}
        for r in rows
        if r["item_type"] == "word" and r["definition"].strip()
        and not r["item"].endswith("_textbox")  # Dutch per-category comment boxes
    ]


def typo(it, items, rng):
    s = it["definition"]
    idx = [i for i in range(len(s) - 1) if s[i].isalpha() and s[i + 1].isalpha() and s[i] != s[i + 1]]
    if not idx:
        return None
    i = rng.choice(idx)
    return {**it, "definition": s[:i] + s[i + 1] + s[i] + s[i + 2:]}


def strip_diacritics(it, items, rng):
    s = it["definition"]
    t = unicodedata.normalize("NFC", "".join(
        c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c)))
    return None if t == s else {**it, "definition": t}


def merged(it, items, rng):
    i = items.index(it)
    if i + 1 >= len(items) or items[i + 1]["category"] != it["category"]:
        return None
    return {**it, "definition": it["definition"] + " " + items[i + 1]["definition"]}


def untranslated(it, items, rng):
    g = it["gloss"]
    if not g or g.lower() == it["definition"].lower():
        return None
    return {**it, "definition": g}


def wrong_category(it, items, rng):
    if it["category"] not in FAR:
        return None
    present = {x["category"] for x in items}
    choices = [c for c in FAR if c in present and c != it["category"]]
    return {**it, "category": rng.choice(choices)} if choices else None


def gloss_swap(it, items, rng):
    if not it["gloss"]:
        return None
    others = [x for x in items if x["gloss"] and x["category"] != it["category"]]
    return {**it, "gloss": rng.choice(others)["gloss"]} if others else None


FAULTS = {
    "typo": (typo, {"misspelling", "wrong_script"}),
    "strip_diacritics": (strip_diacritics, {"misspelling", "wrong_script"}),
    "merged": (merged, {"merged_items"}),
    "untranslated": (untranslated, {"wrong_language"}),
    "wrong_category": (wrong_category, {"category_mismatch"}),
    "gloss_swap": (gloss_swap, {"gloss_mismatch"}),
}


def inject(items, per_type, rng):
    items = [dict(x) for x in items]
    injected = {}  # itemID -> fault type
    for ftype, (fn, _) in FAULTS.items():
        pool = [x for x in items if x["itemID"] not in injected]
        rng.shuffle(pool)
        n = 0
        for it in pool:
            new = fn(it, items, rng)
            if new is None:
                continue
            items[items.index(it)] = new
            injected[it["itemID"]] = ftype
            n += 1
            if n == per_type:
                break
    # wrong-category items move position too, as they would in a mis-sorted extraction
    return items, injected


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("instruments", nargs="*", default=list(INSTRUMENTS))
    ap.add_argument("--per-type", type=int, default=6)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--model", help="override the pinned item_qa model, for comparisons")
    args = ap.parse_args()
    if args.model:
        qa_items.CONFIG["models"]["item_qa"] = args.model

    OUT.mkdir(parents=True, exist_ok=True)
    summary = {}
    review_rows = []
    for name in args.instruments:
        lang, form, script = INSTRUMENTS[name]
        rng = random.Random(f"{args.seed}-{name}")
        clean = load(name)
        faulty, injected = inject(clean, args.per_type, rng)
        flags, metas = qa_items.run(faulty, lang, form, script)

        by_item = defaultdict(list)
        for f in flags:
            by_item[f["itemID"]].append(f)
        caught, typed = Counter(), Counter()
        for iid, ftype in injected.items():
            if by_item.get(iid):
                caught[ftype] += 1
                if any(f["issue"] in FAULTS[ftype][1] for f in by_item[iid]):
                    typed[ftype] += 1
        totals = Counter(injected.values())
        orig = {x["itemID"]: x for x in clean}
        extra = [f for f in flags if f["itemID"] not in injected]
        for f in extra:
            o = orig.get(f["itemID"], {})
            review_rows.append({"instrument": name, **f, "category": o.get("category", ""),
                                "definition": o.get("definition", ""), "gloss": o.get("gloss", "")})
        summary[name] = {
            "n_items": len(clean),
            "injected": dict(totals),
            "caught_any_flag": dict(caught),
            "caught_right_type": dict(typed),
            "flags_on_untouched_items": len(extra),
            "flags_on_untouched_by_confidence": dict(Counter(f["confidence"] for f in extra)),
            "model_version": metas[0]["model_version"],
            "tokens": [sum(m["input_tokens"] for m in metas), sum(m["output_tokens"] or 0 for m in metas)],
        }
        print(name, json.dumps(summary[name], ensure_ascii=False))

    model = summary[args.instruments[0]]["model_version"]
    stem = f"{model}_seed{args.seed}"
    (OUT / f"{stem}_summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))
    with open(OUT / f"{stem}_untouched_flags.csv", "w", encoding="utf8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["instrument", "itemID", "category", "definition", "gloss",
                                          "issue", "confidence", "explanation", "suggested_fix"],
                           lineterminator="\n")
        w.writeheader()
        w.writerows(review_rows)


if __name__ == "__main__":
    main()
