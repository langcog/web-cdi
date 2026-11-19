# Adding instruments to Web-CDI

> Drafted with Claude Opus 5.5. Where each instrument stands, and what has
> been decided, is in [STATUS.md](STATUS.md).

Tooling and per-instrument packages for adding new CDI instruments in bulk
while keeping a verifiable trail from each web form back to its source.

## Layout

```
instruments/
  packages/<Package>/      one directory per instrument (one PR per instrument)
    manifest.yaml          identity, age range, sources (Drive id + sha256),
                           permissions, citation, review sign-offs, status
    items.csv              web-cdi item schema + provenance columns
    meta.json              section structure (same format as cdi_forms/form_data/*_meta.json)
  tools/                   source checks, extract, validate, LLM QA, calibration
  calibration/             LLM QA calibration results (committed)
  qa_config.yaml           pinned QA model IDs
  requirements.txt         tool dependencies (separate from the Django app)
```

Source files (form PDFs, item lists) live under `forms/` (gitignored: they are
licensed and are never committed), unpacked from the team's Drive folder
"Web-CDI Updates 2026" downloaded as a zip. The manifest records each file's
path, Drive id and sha256 instead.

## Setup

```bash
python3 -m venv instruments/.venv
instruments/.venv/bin/pip install -r instruments/requirements.txt
gcloud auth application-default login   # for Vertex AI (LLM QA)
```

LLM QA runs Gemini on Vertex AI (project in `qa_config.yaml`); your Google
account needs the Vertex AI User role on that project. Responses are cached
in `instruments/.cache/` so reruns are free and identical. Cloud Claude
sessions have no Google credentials, so run QA from a local session.

Most steps run with `instruments/tools` as the working directory, e.g.
`../.venv/bin/python validate.py ../packages/NZ_English_Short/items.csv --script latin`.

## Pipeline

1. **Sources** — `tools/sources.py <Package>` checks the manifest's source
   files are present under `forms/` and pins (or verifies) their sha256.
2. **Extract** — source-specific: deterministic parsers for spreadsheets;
   for PDFs, two independent extractions (text layer and page images) whose
   disagreements go to a person.
3. **Validate** — `tools/validate.py` (deterministic: schema, IDs, choice sets,
   meta.json consistency, duplicates, whitespace, Unicode normalization,
   script). Cross-check counts and items against Wordbank where the
   instrument exists there.
4. **LLM QA** — `tools/qa_package.py <Package>` runs `qa_items.py` with both
   configured models and writes the union of flags to the package's
   `qa/item_flags.csv` (misspelling, wrong script, merged items, wrong
   language, category/gloss mismatch, duplicate). Flags are advisory and go
   to the reviewer; nothing is changed automatically. Fixes to the source go
   in the manifest's `corrections:` list (cell, from, to, reason), which the
   extractor applies and records in `items.csv`'s `corrected_from` column.
   The QA model is trusted only to the extent `tools/calibrate.py` shows
   (fault injection into instruments already in production).
5. **Human review** — a native-speaker proofreader reviews flagged items plus a
   random sample; the CDI Advisory Board signs off on structure. Sign-offs are
   recorded in the manifest.
6. **Publish** — copy the package's `items.csv` and `meta.json` to where the
   app reads them (`webcdi/cdi_form_csv/cdi_forms/[Language_Form].csv` and
   `webcdi/cdi_forms/form_data/Language_Form_meta.json`), add the
   instrument (and any new family) to `webcdi/static/json/instruments.json`
   and `instrument_families.json`, plus a scoring JSON. The package stays
   the authoring source; the copies are what the app loads. Then
   `python manage.py load_instruments` locally, render every page, fill a
   full form, and check the download. The PR should contain both the package
   and the published files.
7. **Stage** — merging to master deploys to staging, and the deploy reruns
   `load_instruments` because instrument data files changed. Check the form
   on staging, then mark it published in STATUS.md. Production follows the
   same image.
