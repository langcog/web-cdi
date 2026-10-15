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
title exactly. Sentinels: `raw_score = 9999` → no unisex norms for that
measure; `percentile = 999` → row holds a mean "% yes at this age and sex"
rather than percentiles (e.g. English WS Combining; English WG Phrases).

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
  `due_date_diff / 4` months for prematurity; both plain and adjusted
  percentiles are stored.
- **Percentile lookup is a floor, not interpolation:** the reported value is
  the percentile of the highest benchmark row whose raw score ≤ the child's
  raw score (`calc_benchmark` linear interpolation is commented out — changed
  in Henry's "English99" PR #652, Aug 2026). Values below 1 are reported as
  `"<1"`. Sex-specific percentiles need sex M/F; unisex unless 9999.
- Floor lookup is exact when the table has every percentile (English WS/WG,
  Spanish WS/WG, English CAT: 99–100 rows per age), but **coarse for
  instruments that still have 5-point tables** (English CDI-III, L1/L2A/L2B
  short forms, French CAT, Japanese CAT) — those reported interpolated values
  before #652. Rows are read in percentile order via `Benchmark.Meta.ordering`,
  so CSV row order doesn't matter.
- Known bug: a child whose sex is O/P/blank gets a sex-specific percentile of
  `"<1"` (should be blank) — `sex_score` defaults to 0. Verified locally
  2026-10-15.
- Other fragile spots: the "late" branch adds to the clamped age while "early"
  subtracts from the raw age; several bare `except:` blocks swallow errors.

## Performance: why a full rescore takes days

`update_summary_scores` is row-by-row ORM: for every response it re-fetches
the item (`Instrument_Forms.get`), queries matching `InstrumentScore`s, then
per score does `get_or_create` + `Measure.get` + `save`. Measured locally
(2026-10-15): one English WS administration (398 responses) = **5,576
queries**, 1.8 s with the DB on localhost; on EB→RDS each query is a network
round trip, so several seconds per administration, single-threaded. Rescoring
all English WS on prod (`update_summary_data -l English -f WS`) therefore
takes 2–3 days. The fix is to load the instrument's items/scores/measures
once, count in Python, and `bulk_create` the SummaryData rows (a handful of
queries per administration). Before optimizing, snapshot current outputs on a
sample and require identical results from the new code.

`crontab_scoring` has no lock: if a run takes longer than 10 minutes, the next
run starts on the same unscored administrations.

## Test coverage — honest status

Only one test runs classic scoring (`update_summary_data` over fake WS
administrations) and it asserts only that administrations get marked scored.
**No test checks a raw score or percentile value.** Plan agreed with Mike:
golden-case tests where Virginia supplies (age, sex, responses) → expected
scores/percentiles from the published norms; we build the harness. Still
waiting on her cases. CAT theta, by contrast, is value-tested.

## Downloads that expose scores

`researcher_UI/utils/download/`: `download_data.py` (items + scores),
`download_summary.py` (scores only), `download_cdi_format.py` (CDI scoring
format; #649 crash), `download_cat_data.py`, `download_dictionary.py`. All
pandas-heavy and full of pandas-3 hazards (see SKILL.md "Rules that bite").

## CAT (computerized adaptive testing)

Forms in `settings.CAT_FORMS` (`CAT`, `CAT2`); languages EN, SP, FR, JP, NL.
2PL IRT, max-information item selection, theta by ML (MAP until the response
pattern is mixed), stop at 25–50 items or SEM ≤ 0.15. Starting item comes
from per-language age→item tables.

- **`CAT_ENGINE=remote`** (production default): calls the R plumber API
  (github.com/langcog/cdi-cat-api, George Kachergis; EB env `CdiCatApi-env`)
  via `cdi_forms/cat_forms/cdi_cat_api.py` — `startItem`, `nextItem`,
  `hardestWord`, `easiestWord`. Stateless; state lives in `CatResponse`.
- **`CAT_ENGINE=browser`**: in-browser jsCat (`@bdelab/jscat` wrapped in
  `cdi_forms/cat_forms/jscat/`, `npm run build`; banks generated by
  `08_generate_cat_json` into `static/cdi_forms/cat/*.json`). Validated
  against mirtCAT ground truth for all 5 languages (theta ≤ 0.0024, identical
  item selection). Not yet enabled in production — switching would retire the
  R API (#528).
- Item parameters: webcdi CSVs use classic difficulty b; R repo CSVs are
  slope-intercept (b = −d/a1). In the R repo, the NL coefficient table is from
  a different fit than the NL model — take NL parameters from the model.
- The deployed R API can lag its repo (e.g. pre-rename Spanish item names).
