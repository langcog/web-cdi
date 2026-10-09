"""LLM item-level QA for a CDI vocabulary checklist.

Sends the checklist in category-aligned batches and asks for narrowly typed
flags. Output is a list of flag dicts; it is advisory — flags go to a human
reviewer, they never change items automatically.
"""

from llm import CONFIG, ask_json

ISSUES = [
    "misspelling",        # typo or extraction/OCR error in the item text
    "wrong_script",       # wrong writing system/variant, lost diacritics or macrons
    "merged_items",       # two separate checklist items run together in one entry
    "wrong_language",     # item is not in the target language (e.g. untranslated English)
    "category_mismatch",  # item clearly does not belong in its category
    "gloss_mismatch",     # English gloss does not match the item
    "duplicate",          # same item listed twice where that looks unintended
    "other",
]

SCHEMA = {
    "type": "object",
    "properties": {
        "flags": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "itemID": {"type": "string"},
                    "issue": {"type": "string", "enum": ISSUES},
                    "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
                    "explanation": {"type": "string"},
                    "suggested_fix": {"type": "string"},
                },
                "required": ["itemID", "issue", "confidence", "explanation", "suggested_fix"],
            },
        }
    },
    "required": ["flags"],
}

PROMPT = """You are checking a digitized MacArthur-Bates Communicative Development Inventory (CDI) vocabulary checklist for errors introduced when it was transcribed from the printed form.

Instrument: {language} — {form}
Expected writing system: {script}
All categories in this instrument: {categories}

Flag ONLY genuine problems of these types: {issues}.

These are NORMAL on CDI forms and are NOT errors: alternatives separated by "/" or ","; parenthetical clarifications or senses, e.g. "drink (beverage)"; animal sounds and onomatopoeia; baby-talk and diminutive forms; colloquial or dialect forms; loanwords that are commonly used in the target language; brand names; the same word appearing in two categories in different senses.

Be conservative: a parent-report checklist written by native-speaker researchers is usually right. Flag an item only when you can say concretely what is wrong, and give the corrected text in suggested_fix (empty string if unsure). Use confidence "high" only when the error is unambiguous.

Items (itemID | category | item text | English gloss if available):
{rows}

Return every flag you find; return an empty list if there are none."""


def batches(items, max_items=180):
    """Group items into batches that do not split categories when avoidable."""
    out, cur, cat = [], [], None
    for it in items:
        if cur and len(cur) >= max_items and it["category"] != cat:
            out.append(cur)
            cur = []
        cur.append(it)
        cat = it["category"]
    if cur:
        out.append(cur)
    return out


def run(items, language, form, script):
    """items: dicts with itemID, category, definition, gloss (may be empty)."""
    categories = ", ".join(dict.fromkeys(it["category"] for it in items))
    flags, metas = [], []
    for batch in batches(items):
        rows = "\n".join(
            f'{it["itemID"]} | {it["category"]} | {it["definition"]} | {it.get("gloss") or ""}'
            for it in batch
        )
        prompt = PROMPT.format(
            language=language, form=form, script=script, categories=categories,
            issues=", ".join(ISSUES), rows=rows,
        )
        parsed, meta = ask_json("item_qa", prompt, SCHEMA)
        flags.extend(parsed["flags"])
        metas.append(meta)
    return flags, metas
