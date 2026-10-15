# Instruments, forms, and languages

An **instrument** = language × form (`English_WS`, `Spanish_WG`, `English_CAT`,
`English_L2A` short form, `English_CDI3`, …). Instruments belong to an
**instrument family** (used for Brookes licensing and researcher access).
Sources: Henry's wiki pages "Adding a New Form", "Adding a new language",
"Bespoke Background Information", "Graphs"; verified against the code where
noted.

## Files that define an instrument

1. **`webcdi/static/json/instruments.json`** — registry; one record per
   instrument:
   ```json
   {"language": "English", "form": "WS", "verbose_name": "Words and Sentences",
    "min_age": 16, "max_age": 30,
    "csv_file": "cdi_form_csv/cdi_forms/[English_WS].csv",
    "json_data": "cdi_forms/form_data/English_WS_meta.json",
    "scoring_json": "cdi_forms/form_data/scoring/English_WS_scoring.json",
    "benchmark": "cdi_forms/form_data/benchmarking/English_WS_benchmark.csv",
    "fillable_headers": "cdi_form_csv/cdi_forms/EnglishWS_pdf_headers.csv",
    "family": "English (American/Canadian) Long", "demographics": ["English_Split.json"]}
   ```
   `fillable_headers` optional. A second copy in
   `researcher_UI/static/json/instruments.json` has diverged — the populate
   commands and migrations read `static/json/`.
2. **Item CSV** `cdi_form_csv/cdi_forms/[Language_Form].csv` — header
   `itemID,item,item_type,category,choices,uni_lemma,definition,gloss,complexity_category,presentation_order`
   (+ optional `scoring_category`).
   - `itemID`: unique within the instrument (`item_1`…); download column order
     and short forms rely on it — short forms reuse the parent form's itemIDs.
   - `item`: code name, no spaces; becomes the **export column header** —
     don't rename to fix display typos (fix `definition`/`gloss` instead).
   - `item_type`: page type (word, gestures_*, complexity, word_form,
     word_ending, usage, combine, phrases, …) — a new page when it changes.
   - `category`: section within the type (e.g. animals); maps to meta.json
     section ids.
   - `choices`: must match an existing choice set (`understands; produces`,
     `produces`, `not yet;sometimes;often`, `simple;complex`, `no;yes`, …) —
     see `cdi_form_csv/choice_options.csv`.
   - `definition`/`gloss`: text shown to parents.
   - `scoring_category`: overrides `item_type` for scoring (blank → item_type).
3. **Meta JSON** `cdi_forms/form_data/<Instrument>_meta.json` — parts →
   types → sections with titles, instruction `text`, `type`
   (checkbox/radiobutton/textbox), optional section `footnote`, and explicit
   `"page"` numbers. Reordering sections requires renumbering pages.
   `cdi_items.html` hides empty part/type titles.
4. **Scoring JSON** and **benchmark CSV** — see `scoring-and-cat.md`.
5. **Background questionnaire** — see below.
6. **Graphs** shown to parents after completion: add the instrument to
   `static/data_csv/word_categories.csv` (instrument across top row, category
   translations down the column) and, if needed, the instrument list in
   `cdi_forms/templates/cdi_forms/printable_cdi.html` (~line 128).

Loading: management commands `01`–`06` (also run by every deploy). Then grant
researchers access to the instrument family in `/wcadmin/`.

Ignore `webcdi/adding_new_instrument.txt` (pre-2019 procedure with per-
instrument models; obsolete).

## Adding a new UI language (beyond a new instrument)

Per the wiki "Adding a new language", plus code reality:
- `settings.LANGUAGES` and `LANGUAGE_DICT` entries.
- Choices translation: add a column to `cdi_form_csv/choice_options.csv`, then
  `makemigrations` and hand-edit the migration to call `updateChoiceModel`
  (template: `cdi_forms/migrations/0056_choices_choice_set_nl.py`; adds a
  modeltranslation column `choice_set_xx`).
- `locale/<code>/LC_MESSAGES/django.po`: `makemessages -l xx`, translate,
  `compilemessages`.
- Datepicker locale script + date format in `cdi_forms/templates/cdi_forms/cdi_base.html`.
- `word_categories.csv` translations (graphs).
- Background questionnaire JSON in the language.

## Background questionnaires

- Default form is built in; per-study choice via the `Demographic` model
  (name + path to `cdi_forms/form_data/background_info/*.json`).
  `cdi_forms/utils.py:get_demographic_filename` resolves it; a study with
  `demographic_opt_out` uses `{language}_no_demographics.json`.
- **Bespoke forms** (`background_info/<Instrument>.json`): list of pages
  `front` (before items) and `back` (after); each has optional `help_text`
  (HTML) and `contents` = fieldsets with `fields`. Each `field` must be a
  `BackgroundInfo` model field (new fields need a migration). `div` lists
  dependent fields revealed by a parent answer. Per-field `choices` override
  options (e.g. local income bands) with `widget_type` and `required`.
- Confirmation questions (`mother_yob_confirmation`,
  `birth_weight_confirmation_lb/kg`) go on the front page and show only when
  the study enables them. Sibling fields: `sibling_boolean`, `sibling_count`,
  `sibling_data`.
- GDPR variants exist (e.g. `Dutch_CAT_no_location.json` drops country/zip).

## The 2026 new-instruments pipeline (branch `new-instruments`)

`instruments/` holds one package per instrument (`manifest.yaml` with sources
+ sha256 + permissions + sign-offs; `items.csv` with provenance; `meta.json`)
and tools: `sources.py` (verify source files), extractors, `validate.py`
(deterministic checks), `qa_items.py` (LLM QA via Gemini on Vertex, project
`hs-hs-langcog-gemini`, pinned models in `qa_config.yaml`), `calibrate.py`
(fault-injection calibration). Read `instruments/README.md` on that branch.

- Source files live in `forms/` (gitignored; licensed — never commit), from
  Virginia's Drive folder "Web-CDI Updates 2026".
- Calibration: flash and pro each catch ~96% of injected faults; pro finds
  ~2× more real errors — run both, union the flags. Flags are advisory; a
  native speaker and the Advisory Board sign off.
- Current scope (decided 2026-10): **NZ English short form** first (16–30 mo;
  = US L2A + 8 substitutions, reuses L2A itemIDs); then Turkish (TİGE, as
  standalone parent-report WG/WS without stopping rules), Serbian (Ekavian +
  Ijekavian, treat as final), Swedish WG/WS/CDI-III. Hindi blocked on a Word
  version. Other NZ lists (Te Reo, Cantonese, Mandarin, Samoan, Tongan)
  dropped for now; MB8 Mandarin/Cantonese may come from the Texas team
  (needed Feb/Mar 2027).
- Typo fixes to live instruments: PR #666 (US short forms, Argentine Spanish,
  Dutch). Pending native-speaker checks: Korean, Hebrew, Quebec French items.
