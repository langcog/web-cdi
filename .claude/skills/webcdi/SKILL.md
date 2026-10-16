---
name: webcdi
description: Orientation for developing and operating Web-CDI (webcdi.org — the Django app that administers MacArthur-Bates CDI vocabulary inventories online). Covers people and ownership, environments and deploys, repo map, local dev and tests, instrument/form data files, scoring and benchmarks, CAT, researcher features, standing decisions, known bugs and open threads. Use whenever developing, testing, deploying, debugging, reviewing, or answering questions about web-cdi.
---

# Web-CDI

Snapshot **2026-10-15**. Consolidates Henry Mehta's wiki
(github.com/langcog/web-cdi/wiki), the 2026 modernization and QA sessions,
and the new-instruments campaign. Branch/PR/issue facts go stale — check
`gh pr list` / `gh issue list` before relying on them. Setup basics live in
`DEVELOPMENT.md`; this skill covers what that file doesn't.

## What it is

Researchers register, create **administration groups** ("studies" in the
code/DB) for a licensed **instrument** (language × form, e.g. English WS,
Spanish CAT), and send parents links. Parents fill a background questionnaire
plus the CDI item checklist (or a computer-adaptive CAT). The app scores
responses against norms (percentiles) and researchers download CSVs. English
and Spanish Long + CAT forms require a paid Brookes Publishing code.

## People and ownership

- **Mike Frank** — PI; sets priorities, approves UX/design. **Development is
  now owned by Mike's team** (Henry stepped back, Oct 2026).
- **Henry Mehta** — built and ran the app 2019–2026; author of the wiki.
  Still the person to ask about undocumented history.
- **Virginia Marchman** (call her Virginia) — CDI Advisory Board; authority on
  instrument content, wording, citations, norms and scoring expectations.
- **Alvin** — working on web-cdi development with Mike.
- A QA tester sends feedback rounds via Mike; the Dutch group runs their own
  EU server (behind our code).
- Ownership handoff is incomplete — see `references/deploy-and-ops.md`
  ("Things only Henry had").

## Environments (AWS Elastic Beanstalk, us-west-2)

| Env | URL | Notes |
|---|---|---|
| `Webcdi-env-2` | webcdi.org | **production** |
| `Webcdi-dev-django4` | testing.webcdi.org | staging; plain http |
| `webcdi-dev` | — | Henry's old demo env; leave alone |
| `CdiCatApi-env` / `-dev` | — | retired R CAT API (AWS prod still uses it until cutover) |

Deploy = `eb deploy <env>` from `webcdi/`; the postdeploy hook migrates and
re-runs all populate commands. Details, env vars, cron, DB tasks:
`references/deploy-and-ops.md`. **Never deploy to production without Mike's
go-ahead.**

## Repo map (`webcdi/`)

- `webcdi/` — settings (all config from env vars), urls, management commands
  `01`–`08` that load instruments/scoring/benchmarks/choices/items/CAT banks.
- `researcher_UI/` — researcher console: groups, administrations, downloads
  (`utils/download/`), scoring (`cdi_forms/scores.py` is called from here),
  Brookes gating, models (`Study`, `Administration`, `Instrument`,
  `InstrumentScore`, `Benchmark`, `Demographic`, `PaymentCode`).
- `cdi_forms/` — participant forms: background info + item pages;
  `form_data/*_meta.json` (page structure), `form_data/background_info/*.json`
  (questionnaires), `form_data/scoring/*.json`, `form_data/benchmarking/*.csv`;
  `cat_forms/` (CAT; `jscat/` is the in-browser engine).
- `cdi_form_csv/cdi_forms/` — item lists (`[Language_Form].csv`);
  `cdi_form_csv/choice_options.csv` — response choice sets + translations.
- `static/json/instruments.json` — master instrument registry (a second copy
  in `researcher_UI/static/json/` has **diverged**; migrations and populate
  read `static/json/`).
- `brookes/` — purchase codes; `api/` — JSON export; `locale/` — translations.

## Rules that bite (read before editing)

- **Test discovery is via package `__init__.py` re-exports** (files aren't
  `test_*.py`). A new test module that isn't imported in its package
  `__init__` silently never runs.
- **Theme CSS exists twice** and must stay identical:
  `cdi_forms/static/cdi_forms/webcdi-theme.css` and
  `static/cdi_forms/webcdi-theme.css`.
- **Django 5: logout is POST-only.** Never reintroduce
  `<a href="{% url 'logout' %}">`; `webcdi/tests/test_auth.py` guards it.
- **pandas 3 + Copy-on-Write:** `df[col].replace(..., inplace=True)` is a
  silent no-op (CI prints `ChainedAssignmentError`); `DataFrame.append` is
  gone. The download code is full of both — assign results instead
  (`df[col] = df[col].replace(...)`).
- **`_meta.json` sections carry explicit `"page"` numbers** — reordering
  sections means renumbering pages.
- **DEBUG must be True locally** (no WhiteNoise → no static files otherwise).
- Deletes are **soft**: groups set `Study.active=False`, administrations
  `Administration.is_active=False`.
- Printed form PDFs in `forms/` are **gitignored — never commit them** (also
  never commit the MB8 tracker sheet: personal emails).
- **Never put secrets in commits, chat, or this skill.** The repo is public.

## Where to look next

| Task | Read |
|---|---|
| Run locally, write/run tests, CI, browser checks | `references/dev-and-testing.md` |
| Deploy, env vars, cron, AWS, DB fixes, ownership gaps | `references/deploy-and-ops.md` |
| Add/modify an instrument, language, background form, graphs | `references/instruments-and-forms.md` |
| Scoring, benchmarks/percentiles, CAT engines | `references/scoring-and-cat.md` |
| Researcher console features, downloads, payments, Wordful/REDCap | `references/researcher-features.md` |
| History, standing decisions, known bugs, open threads | `references/history-and-decisions.md` |

## Working style Mike expects

- Rigor and honesty over reassurance: if tests don't cover something, say so;
  report failures with output.
- Surgical diffs. State interpretations explicitly and offer the flip if a
  request could be read two ways.
- Bug fix ⇒ first a test that reproduces it, then the fix.
- Verify UI changes in a browser (screenshot); run the fast suite before
  pushing.
