# Scoring, benchmarks, and CAT

## Scoring definitions (`cdi_forms/form_data/scoring/<Instrument>_scoring.json`)

Pointed to by `scoring_json` in instruments.json; loaded by
`03_populate_scoring` into `InstrumentScore` (+ `Measure`). Each entry:

```json
{"title": "Total Gestures",
 "category": "gestures_parents;gestures_adults;gestures_objects;gestures_first;gestures_games",
 "measure": "sometimes;often;yes",
 "order": 8,
 "kind": "count",
 "scores": [{"key": "understands", "value": 1}, {"key": "produces", "value": 2}]}
```

- `title`: unique per instrument; becomes the download column name.
- `category`: `;`-separated item `scoring_category` values (falls back to
  `item_type`).
- `measure`: `;`-separated responses that count.
- `order`: column order in downloads.
- `kind`: `count` (default; sum) or `list` (copies the response text, e.g.
  typed sentences).
- `scores` (optional): per-response weights; default 1 each.

## Benchmarks (`cdi_forms/form_data/benchmarking/<Instrument>_benchmark.csv`)

Pointed to by `benchmark`; loaded by `04a_delete_benchmark` +
`04_populate_benchmark`. Header `title,percentile,age,raw_score,raw_score_boy,raw_score_girl`;
one row per (score title × age × percentile). `title` must match the scoring
title exactly. Sentinel: `percentile = 999` → the row holds a mean "% yes at
this age and sex" rather than percentiles (e.g. English WS Combining; English
WG Phrases). `percentile = 0` rows are ignored. Some tables have every
percentile 1–99; others are coarse (5, 10, …, 95, 99: English CDI-III,
L1/L2A/L2B short forms, French CAT, Japanese CAT).

## How scoring runs (`cdi_forms/scores.py`)

- `update_summary_scores(administration)` deletes and rebuilds the
  administration's `SummaryData` rows: raw counts per title, then benchmark
  ages and percentiles.
- **Triggered** by a post_save signal when an administration completes
  (disabled under TESTING) and by cron `crontab_scoring` every 10 min
  (`completed=True, scored=False`). Bulk rescoring:
  `update_summary_data -l <language> -f <form>` (or `-u <username>`).
- **Ages:** child age is clamped to the benchmark table's min/max age
  ("benchmark cohort age"). "Adjusted" age subtracts (early) or adds (late)
  `due_date_diff / 4` months for prematurity (missing weeks = no adjustment);
  both plain and adjusted percentiles are stored.
- **Percentile rules (Virginia, #686; implemented in #727).** One
  implementation — `percentile_thresholds` / `percentile_of` / `value_at` in
  `scores.py` — used by the scorer, the CAT report tag (`get_cat_benchmark`)
  and the CAT download (`cat_utils`, via `cat_norms`):
  - full tables (1–99) are used as published;
  - coarse tables are filled in linearly at 1-point steps (95→99 in quarters);
  - below the lowest published percentile (the 5th), extend at the slope
    between the two lowest rows (5th→10th) to establish the 1st;
  - a score below the 1st is `"<1"`; the top is 99; ties (several percentiles
    with the same raw score) take the **highest** percentile;
  - sex-specific results for a child not recorded as M/F are `"not computed"`;
  - a table with no 1–99 rows means no norms → no percentile.
  Reports print `%` only after a number (`as_percent` filter).
- **CAT summaries** are scored from `CatResponse.est_theta` (before #727 the
  stored "Benchmark Theta" was always 0); "Total Produced" is the estimated
  words produced = the Total Produced norm at the child's theta percentile.
- Old vs new on 300 real administrations per instrument (2026-10-19): full
  tables unchanged; coarse tables up a median of 2 (max 4); CAT ±1 for full
  tables. Stored summaries need a full rescore after deploy.

## Performance

The scorer loads an instrument's configuration once (`InstrumentScoring`) and
writes `SummaryData` in bulk: ~7 queries per administration instead of ~5,600
(#694). A full rescore takes minutes. Before the percentile change it matched
the original row-by-row scorer exactly on 500 production administrations; the
legacy scorer and `compare_scoring` were then retired (#727). Note: scoring
saves the administration, which fires the completion-notice signal (#723).

## Test coverage

Value-level tests now exist: `cdi_forms/tests/tests_scoring/` —
`PercentileRulesTest` (golden cases from Virginia's rules and the published
L1 16-month table), `CatScoringTest`, `SexPercentileTest`, and
`ScoringEquivalenceTest` (every fixture instrument scores with valid
percentile values).

## Downloads that expose scores

`researcher_UI/utils/download/`: `download_data.py` (items + scores),
`download_summary.py` (scores only), `download_cat_data.py`,
`download_dictionary.py`, `download_links.py`. (The CDI scoring-program zip
export, `download_cdi_format.py`, was removed in #764.) All
pandas-heavy and full of pandas-3 hazards (see SKILL.md "Rules that bite").

## CAT (computerized adaptive testing)

Forms in `settings.CAT_FORMS` (`CAT`, `CAT2`); languages EN, SP, FR, JP, NL.
2PL IRT, max-information item selection, theta by ML (MAP until the response
pattern is mixed), stop at 25–50 items or SEM ≤ 0.15. Starting item comes
from per-language age→item tables.

- **jsCat only (since #684).** The CAT runs in the browser: `@bdelab/jscat`
  wrapped in `cdi_forms/cat_forms/jscat/` (`npm run build` →
  `static/cdi_forms/cat/webcdi-cat.js`), item banks from `08_generate_cat_json`
  in `static/cdi_forms/cat/{EN,SP,FR,JP,NL}.json`. The server only renders the
  page, persists answers (`CatAnswerView`) and finishes the form; hardest/easiest
  words come from the bank. CI's `jscat` job checks the committed bundle
  rebuilds from source and reproduces mirtCAT ground truth (all 5 languages).
  The R plumber API (github.com/langcog/cdi-cat-api; EB `CdiCatApi-env`) is
  retired with the AWS stack.
- Item parameters: webcdi CSVs use classic difficulty b; R repo CSVs are
  slope-intercept (b = −d/a1). In the R repo, the NL coefficient table is from
  a different fit than the NL model — take NL parameters from the model.
- The deployed R API can lag its repo (e.g. pre-rename Spanish item names).
