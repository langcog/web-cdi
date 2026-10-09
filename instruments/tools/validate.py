"""Deterministic checks on a web-cdi instrument item CSV (no LLM).

Errors would break import or rendering; warnings need a human look.

Usage: python validate.py PATH/TO/items.csv [--script hangul|hebrew|latin|cjk|devanagari]
       python validate.py --all-existing      # run over every instrument in the repo
"""

import argparse
import csv
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WEBCDI = REPO / "webcdi"
REQUIRED = ["itemID", "item", "item_type", "category", "choices", "definition"]

SCRIPTS = {  # Unicode script prefixes from unicodedata.name()
    "latin": ("LATIN",),
    "hangul": ("HANGUL",),
    "hebrew": ("HEBREW",),
    "cjk": ("CJK", "HIRAGANA", "KATAKANA", "FULLWIDTH", "IDEOGRAPHIC"),
    "devanagari": ("DEVANAGARI",),
    "cyrillic": ("CYRILLIC",),
}


def choice_sets():
    with open(WEBCDI / "cdi_form_csv" / "choice_options.csv", encoding="utf8") as f:
        return {r["choice_set"] for r in csv.DictReader(f)}


def letters_outside(text, script):
    allowed = SCRIPTS[script] + ("LATIN",)  # Latin always tolerated (loanwords, brands)
    return sorted({c for c in text if c.isalpha()
                   and not unicodedata.name(c, "").startswith(allowed)})


def check(path, script=None, meta=None):
    errors, warnings = [], []
    raw = Path(path).read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        warnings.append("file starts with a UTF-8 BOM")
    rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    if not rows:
        return ["no rows"], warnings
    missing = [c for c in REQUIRED if c not in rows[0]]
    if missing:
        return [f"missing columns: {missing}"], warnings

    ids = Counter(r["itemID"] for r in rows)
    errors += [f"duplicate itemID {i} (x{n})" for i, n in ids.items() if n > 1]
    known = choice_sets()
    for r in rows:
        if "example" not in r["item_type"] and r["choices"] not in known:
            errors.append(f'{r["itemID"]}: choice set "{r["choices"]}" not in choice_options.csv')

    if meta:
        types = {t["id"] for part in meta["parts"] for t in part["types"]}
        cats = {s["id"] for part in meta["parts"] for t in part["types"]
                for s in t.get("sections", [])}
        for r in rows:
            if r["item_type"] not in types:
                errors.append(f'{r["itemID"]}: item_type "{r["item_type"]}" not in meta.json')
            elif cats and r["category"] and r["category"] not in cats and r["item_type"] == "word":
                errors.append(f'{r["itemID"]}: category "{r["category"]}" not in meta.json sections')

    words = [r for r in rows if r["item_type"] == "word"]
    defs = Counter((r["category"], r["definition"].strip()) for r in words)
    warnings += [f'duplicate word "{d}" in category {c}' for (c, d), n in defs.items() if n > 1]
    for r in rows:
        d = r["definition"]
        iid = r["itemID"]
        if d != d.strip() or "  " in d:
            warnings.append(f"{iid}: stray whitespace in {d!r}")
        if unicodedata.normalize("NFC", d) != d:
            warnings.append(f"{iid}: definition not NFC-normalized")
        if "\n" in d:
            warnings.append(f"{iid}: newline inside definition")
        if script:
            odd = letters_outside(d, script)
            if odd:
                warnings.append(f"{iid}: letters outside {script} script in {d!r}: {''.join(odd)}")
        if script == "hangul":
            # a decomposed jamo or unusual syllable is a common transcription slip
            if any(0x1100 <= ord(c) <= 0x11FF or 0x3130 <= ord(c) <= 0x318F for c in d):
                warnings.append(f"{iid}: bare Hangul jamo in {d!r}")
    return errors, warnings


def existing():
    instruments = json.loads((WEBCDI / "static" / "json" / "instruments.json").read_text())
    scripts = {"Korean": "hangul", "Hebrew": "hebrew", "Japanese": "cjk"}
    for ins in instruments:
        if ins["form"] == "CAT":
            continue
        meta = json.loads((WEBCDI / ins["json_data"]).read_text()) if ins.get("json_data") else None
        yield ins["csv_file"], scripts.get(ins["language"], "latin"), meta


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?")
    ap.add_argument("--script", choices=SCRIPTS)
    ap.add_argument("--all-existing", action="store_true")
    args = ap.parse_args()
    targets = list(existing()) if args.all_existing else [(args.path, args.script, None)]
    n_err = 0
    for csv_file, script, meta in targets:
        errors, warnings = check(WEBCDI / csv_file if args.all_existing else csv_file, script, meta)
        n_err += len(errors)
        print(f"== {csv_file}: {len(errors)} errors, {len(warnings)} warnings")
        for e in errors:
            print("  ERROR", e)
        for w in warnings:
            print("  warn ", w)
    sys.exit(1 if n_err else 0)
