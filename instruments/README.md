# Adding instruments to Web-CDI

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
  tools/                   fetch, extract, validate, LLM QA, calibration
  calibration/             LLM QA calibration results (committed)
  qa_config.yaml           pinned QA model IDs
  requirements.txt         tool dependencies (separate from the Django app)
```

Source files (form PDFs, item lists) are fetched into `forms/new-instruments/`,
which is gitignored: they are licensed and are never committed. The manifest
records each file's Drive id and sha256 instead.

## Setup

```bash
python3 -m venv instruments/.venv
instruments/.venv/bin/pip install -r instruments/requirements.txt
gcloud auth application-default login --scopes=https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/drive.readonly
```

LLM QA runs Gemini on Vertex AI (project in `qa_config.yaml`). Responses are
cached in `instruments/.cache/` so reruns are free and identical.

## Pipeline

1. **Fetch** — `tools/fetch.py <Package>` downloads sources by Drive id and
   pins their sha256 in the manifest.
2. **Extract** — source-specific: deterministic parsers for spreadsheets;
   for PDFs, two independent extractions (text layer and page images) whose
   disagreements go to a person.
3. **Validate** — `tools/validate.py` (deterministic: schema, IDs, choice sets,
   meta.json consistency, duplicates, whitespace, Unicode normalization,
   script). Cross-check counts and items against Wordbank where the
   instrument exists there.
4. **LLM QA** — `tools/qa_items.py` flags typed problems (misspelling, wrong
   script, merged items, wrong language, category/gloss mismatch, duplicate).
   Flags are advisory and go to the reviewer; nothing is changed automatically.
   The QA model is trusted only to the extent `tools/calibrate.py` shows
   (fault injection into instruments already in production).
5. **Human review** — a native-speaker proofreader reviews flagged items plus a
   random sample; the CDI Advisory Board signs off on structure. Sign-offs are
   recorded in the manifest.
6. **Import and stage** — load into a test database, render every page, fill a
   full form programmatically, check the export; then stage on testing.
