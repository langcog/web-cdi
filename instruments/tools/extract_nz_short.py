"""Extract the New Zealand short-form item lists (xlsx) into package items.csv files.

Every NZ source has the same layout in column A: A1 instructions, then one
vocabulary item per cell, then an "other words" free-text prompt, then the
word-combining question and its three options. One cell = one item, even when
the cell holds several words (e.g. Tongan "'ai tīvī").

Item IDs: New Zealand English is the US English Level II-A short form with
local substitutions, so it reuses the US L2A item IDs (keeping the two
comparable); every other list is language-specific and is numbered in source
order. Items are laid out as four 25-item pages (col_1..col_4) as on the
US short forms.

Usage: python extract_nz_short.py PACKAGE [PACKAGE ...]
"""

import csv
import json
import sys
import unicodedata
from pathlib import Path

import openpyxl
import yaml

import sources

REPO = Path(__file__).resolve().parents[2]
US_L2A = REPO / "webcdi" / "cdi_form_csv" / "cdi_forms" / "[English_L2A].csv"

# NZ English substitutions for US L2A items (US definition -> NZ definition).
NZ_FROM_US = {
    "airplane": "aeroplane", "applesauce": "tomato sauce", "candy": "lollies",
    "coke": "fizzy drink", "trash": "rubbish", "mommy": "mum",
}

COLUMNS = ["itemID", "item", "item_type", "category", "choices", "definition", "gloss",
           "uni_lemma", "source_ref", "corrected_from"]


def apply_corrections(items, corrections):
    """Apply the manifest's documented corrections, keyed by source cell.

    Each correction must match the source text exactly, so a changed source
    or a stale correction fails loudly instead of being silently skipped.
    """
    fixes = {c["source_ref"]: c for c in corrections or []}
    out = []
    for ref, text in items:
        c = fixes.pop(ref, None)
        if c:
            assert c["from"] == text, f"{ref}: correction expects {c['from']!r}, source has {text!r}"
        out.append((ref, c["to"] if c else text, text if c else ""))
    assert not fixes, f"corrections for cells not in the item list: {list(fixes)}"
    return out


def read_column_a(path):
    ws = openpyxl.load_workbook(path).active
    cells = [(r, ws.cell(r, 1).value) for r in range(1, ws.max_row + 1)]
    cells = [(r, unicodedata.normalize("NFC", str(v).strip())) for r, v in cells
             if v not in (None, "")]
    instructions = cells[0][1]
    other = next(i for i, (_, v) in enumerate(cells) if v.startswith("Please list here"))
    items = cells[1:other]
    other_prompt = cells[other][1]
    combine_q, options = cells[other + 1][1], [v for _, v in cells[other + 2:]]
    return instructions, items, other_prompt, combine_q, options


def us_l2a_ids():
    with open(US_L2A, encoding="utf8") as f:
        rows = [r for r in csv.DictReader(f) if r["item_type"] == "word"]
    return {NZ_FROM_US.get(r["definition"], r["definition"]): r for r in rows}


def extract(package):
    pdir = sources.PACKAGES / package
    manifest = yaml.safe_load((pdir / "manifest.yaml").read_text())
    src = manifest["sources"][0]
    instructions, items, other_prompt, combine_q, options = read_column_a(sources.path(src))
    assert options == ["Not yet", "Sometimes", "Often"], options

    items = apply_corrections([(f"A{r}", t) for r, t in items], manifest.get("corrections"))
    us = us_l2a_ids() if manifest.get("item_ids") == "us_l2a" else None
    rows = []
    for n, (ref, text, original) in enumerate(items, start=1):
        if us is not None:
            # KeyError here means an NZ item with no US L2A counterpart: stop and look
            iid, gloss = us[text]["itemID"], text
        else:
            iid, gloss = f"item_{n}", ""
        rows.append({"itemID": iid, "item": f"word_{n}", "item_type": "word",
                     "category": f"col_{(n - 1) * 4 // len(items) + 1}", "choices": "produces",
                     "definition": text, "gloss": gloss,
                     "uni_lemma": "", "source_ref": ref, "corrected_from": original})
    rows.append({"itemID": "item_other", "item": "other_words", "item_type": "other_examples",
                 "category": "other_examples", "choices": "", "definition": other_prompt,
                 "gloss": "", "uni_lemma": "", "source_ref": "", "corrected_from": ""})
    rows.append({"itemID": "item_combine", "item": "combine", "item_type": "combine",
                 "category": "combine", "choices": "not yet; sometimes; often",
                 "definition": combine_q, "gloss": "", "uni_lemma": "", "source_ref": "", "corrected_from": ""})

    with open(pdir / "items.csv", "w", encoding="utf8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    meta = {"parts": [
        {"id": 1, "title": manifest["instrument"]["checklist_title"], "types": [
            {"id": "word", "type": "checkbox", "text": instructions,
             "sections": [{"id": f"col_{i}", "page": i} for i in range(1, 5)]},
            {"id": "other_examples", "type": "textbox", "page": 5},
        ]},
        {"id": 2, "title": "", "types": [{"id": "combine", "type": "radiobutton", "page": 5}]},
    ]}
    (pdir / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n")
    print(f"{package}: {len(items)} items")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        sources.verify(p)
        extract(p)
