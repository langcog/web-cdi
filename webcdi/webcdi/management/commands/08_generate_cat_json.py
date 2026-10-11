import csv
import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

# Generates the static per-language parameter files consumed by the
# in-browser CAT engine (static/cdi_forms/cat/<CODE>.json) from the item
# CSVs referenced in static/json/instruments.json. Item indices are
# 1-based row numbers, matching the R API's item indexing so that
# CatResponse.administered_items stays comparable across engines.

# instrument.language -> engine code (mirrors CAT_LANG_DICT + language_map)
LANGUAGE_CODES = {
    "English": "EN",
    "Spanish": "SP",
    "French French": "FR",
    "Japanese": "JP",
    "Dutch": "NL",
}

DESIGN = {"minItems": 25, "maxItems": 50, "minSEM": 0.15}
DEFAULT_START_AGE = 30


class Command(BaseCommand):
    help = "Generate static JSON item banks for the in-browser CAT engine"

    def handle(self, *args, **options):
        instruments = json.load(
            open(
                os.path.realpath(settings.BASE_DIR + "/static/json/instruments.json"),
                encoding="utf8",
            )
        )
        out_dir = os.path.join(
            settings.BASE_DIR, "cdi_forms", "static", "cdi_forms", "cat"
        )
        os.makedirs(out_dir, exist_ok=True)

        for inst in instruments:
            if inst.get("form") not in settings.CAT_FORMS:
                continue
            code = LANGUAGE_CODES.get(inst["language"])
            if code is None:
                self.stdout.write(f"    skipping {inst['language']} (no engine code)")
                continue

            items = []
            with open(
                os.path.realpath(settings.BASE_DIR + "/" + inst["csv_file"]),
                encoding="utf8",
            ) as f:
                for i, row in enumerate(csv.DictReader(f), start=1):
                    items.append(
                        {
                            "index": i,
                            "definition": row["definition"],
                            "a": float(row["discrimination"]),
                            "b": float(row["difficulty"]),
                            "c": float(row["guessing"]),
                            "d": float(row["upper_asymptote"]),
                        }
                    )

            start_items = {}
            if "starting_words" in inst:
                with open(
                    os.path.realpath(settings.BASE_DIR + "/" + inst["starting_words"]),
                    encoding="utf8",
                ) as f:
                    for row in csv.DictReader(f):
                        start_items[str(int(row["age"]))] = {
                            "index": int(row["index"]),
                            "definition": row["definition"],
                        }

            payload = {
                "language": code,
                "design": DESIGN,
                "defaultStartAge": DEFAULT_START_AGE,
                "startItems": start_items,
                "items": items,
            }
            out_path = os.path.join(out_dir, f"{code}.json")
            with open(out_path, "w", encoding="utf8") as f:
                json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
            self.stdout.write(
                f"    wrote {code}.json ({len(items)} items, "
                f"{len(start_items)} start ages)"
            )
