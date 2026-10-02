---
name: webcdi
description: Orientation for working on web-cdi (Django app for MacArthur-Bates CDI vocabulary inventories) — people, branch/PR state, dev/test recipes, codebase gotchas, scoring/CAT/form-structure knowledge, standing decisions, and open threads. Use whenever developing, testing, reviewing, or answering questions about web-cdi.
---

# Web-CDI working notes

Snapshot as of **2026-10-01** (Mike Frank's modernization + QA work). Facts about
branches and PRs go stale — check `gh pr list` before relying on them. For
setup basics read `DEVELOPMENT.md` first; this file covers what it doesn't.

## People and roles

- **Mike Frank** — PI; drives priorities and approves UX/design decisions.
- **Henry** — the app's developer; merges and deploys. Changes to export
  shapes, prod infrastructure, or deploy pipeline are his call.
- **Virginia Marchman** (call her Virginia) — CDI Advisory Board; authority on
  instrument content, wording, citations, and scoring expectations.
- A QA tester sends rounds of feedback (screenshots + comments) via Mike.
- A Dutch group runs their own EU server (behind our code); they send feedback too.

## Environments

- **Prod:** webcdi.org (EB env `Webcdi-env-2`). **Testing:** testing.webcdi.org
  (EB `Webcdi-dev-django4`), runs branch `phases1to11`. `webcdi-dev` EB env is
  Henry's demo — don't touch. Deploys are Henry's; don't `eb deploy` without
  being asked.
- testing.webcdi.org is plain http → browser console shows a COOP-header
  warning (fix is https on EB, not code). `ERR_BLOCKED_BY_CLIENT` in console =
  the viewer's ad blocker eating Google Analytics. Both are benign.

## Branches and PRs (as of 2026-10-01)

- Henry consolidated the whole modernization stack (#617–#622, #641–#645, #647)
  into **`origin/phases1to11`**. Those PRs still show "open" but their content
  is merged there. **Base new work on `phases1to11`.**
- Merged into phases1to11: #657 (Brookes purchase links, docs page), #659
  (form headers aligned to 3rd-edition printed forms).
- Open, awaiting Henry: **#658** group-page redesign (base: round2-brookes-docs),
  **#661** `qa-round3` (base: form-headers-3e) — home copy, citations by
  instrument, CSV-upload copy, radio alignment, form scroll hint, **logout fix**,
  auth tests, collapsible Get-started card. #656 CAT progress counter, #654
  Dutch feedback (off master; minor conflict with stack in `cat_completed.html`
  — keep `btn-primary` + "Submit your responses").

## Running things locally

Docker compose: services `web`, `db` (postgres:16 — pinned; 18 breaks the
volume path), `selenium`. Site at http://localhost:8001.

- Docker Desktop often isn't running: `open -a Docker`, wait for `docker info`,
  then `docker compose up -d --wait db web`.
- `.env` must set `AWS_INSTANCE=False` and **`DEBUG=True`** — there's no
  WhiteNoise, so with DEBUG off runserver serves no static files and pages look
  broken.
- pip installs inside the container (e.g. `tblib`) vanish on container
  recreation — reinstall after `up`/`restart`.
- Make a local test researcher via `createsuperuser` or the register page;
  give it Brookes codes in `/wcadmin/` to unlock English/Spanish Long & CAT.

### Tests

- Fast suite (what CI runs, ~250 tests):
  `docker compose exec -T -e CAT_ENGINE=remote web python manage.py test --exclude=selenium --exclude=known_failure --parallel auto --noinput`
  (≈18 min locally, ≈40 min on GitHub's 2-core runners).
- **Test discovery is via package `__init__.py` re-exports** — files are not
  named `test_*.py`. Every new test module must be imported in its package
  `__init__.py` or it silently never runs (this hid the browser-CAT tests once).
- Django test `Client` needs `HTTP_HOST='localhost'` in some contexts, else 400
  from ALLOWED_HOSTS.
- `known_failure` tag = two quarantined pandas-3 bugs (#640 StudyAPI
  `to_json` duplicate index; #649 scoring download `'item_1' is not in list`).
  They pass on arm64 in isolation but fail in full amd64 runs.
- Selenium (`--tag=selenium`, 28 tests) runs nightly, non-blocking. ~21
  researcher-flow tests fail on **stale locators from the redesign (#648)** —
  test rot, not app bugs. Between killed runs: `docker compose restart selenium`.
- WeasyPrint PDF tests can error under `--parallel` but pass in isolation.
- CAT tests are hermetic (mock replays recorded R-API sequences); no network.

### Browser checks

- Theme CSS is cached aggressively (no hashed static filenames). Bust it in
  devtools with `link.href += '?v=' + Date.now()` or hard reload.

## Codebase gotchas

- **Two identical copies of the theme CSS** must stay in sync:
  `webcdi/cdi_forms/static/cdi_forms/webcdi-theme.css` and
  `webcdi/static/cdi_forms/webcdi-theme.css`. Tokens: `--wcdi-primary`
  (#2b5d8c), `--wcdi-ink`, `--wcdi-ink-soft`, `--wcdi-line`, `--wcdi-card`,
  `--wcdi-check`, `--wcdi-primary-wash`.
- **Django 5 removed GET logout.** Logout must be a POST form with
  `{% csrf_token %}`; never reintroduce `<a href="{% url 'logout' %}">`.
  `webcdi/webcdi/tests/test_auth.py` guards this (GET → 405).
- **Form structure** comes from `webcdi/cdi_forms/form_data/*_meta.json`
  (part/type/section titles per page). Sections carry explicit `"page"`
  numbers; reordering sections means swapping page numbers too.
  `cdi_items.html` hides empty part/type titles.
- **Background questionnaires**: `Demographic` model (name + path to
  `form_data/background_info/*.json`); `cdi_forms/utils.py
  get_demographic_filename`; opt-out forces `{language}_no_demographics.json`.
- Group-page "add administrations" dialog: the tabs are template-only; the
  backend (`admin_new_fun`) dispatches on which fields are filled. Keep POST
  field names. CSV upload uses the first column (others ignored) unless a
  header row names another.
- Group delete and administration delete are both **soft** (rows are
  deactivated, not removed).
- django-axes is installed but `AXES_ENABLED=False`. A 403 right after login is
  most likely a stale/duplicate POST after Django rotates the CSRF token — the
  user is actually logged in.
- "Import completed responses" (researcher importer of Brookes-PDF CSVs) is a
  2018-era feature with two end-to-end tests that check counts, not values.

## Scoring and CAT

- **Classic scoring:** `cdi_forms/scores.py` — `update_summary_scores`,
  `create_benchmark_score` / `calc_benchmark` (linear interpolation into
  `Benchmark` norm tables). Triggered by a post_save signal when an
  Administration completes (**disabled under TESTING**); prod also runs the
  `crontab_scoring` command every 10 min.
- **Test coverage is thin:** only one test runs classic scoring
  (`update_summary_data` over fake WS admins) and it asserts only that admins
  get marked scored — **no value-level checks of raw scores or percentiles.**
  Plan: golden-case tests where Virginia supplies (age, sex, responses) →
  expected score/percentile from the published norms. Waiting on her values.
- **CAT:** `CAT_ENGINE=remote` (default) calls the R plumber API
  (github.com/langcog/cdi-cat-api, mirtCAT 2PL, MI selection, 25–50 items,
  SEM 0.15); `CAT_ENGINE=browser` uses the in-browser jsCat port
  (`cdi_forms/cat_forms/jscat/`, banks in `static/cdi_forms/cat/*.json`),
  validated against mirtCAT ground truth. Languages: EN, SP, FR, JP, NL. The
  R repo's NL coefficient table is from a different fit than the NL model —
  take NL params from the model, not the table.

## Standing decisions (don't relitigate without Mike)

- Form **section headers** follow the 3rd-edition printed forms; **instruction
  text stays as-is** (web version is deliberately richer — Virginia).
- Printed form PDFs live in `forms/` and are **gitignored — never commit them.**
- Word "boxes" on WG/WS forms are deliberate; Mike likes them.
- Citations: Web-CDI → deMayo et al. 2021; CDIs generally → Marchman, Dale &
  Fenson 2023 manual; per-instrument refs by language live in
  `webcdi/webcdi/templates/webcdi/_instrument_citations.html` (shared by About
  and Documentation, anchor `#instrument-citations`). Citation content comes
  from Virginia.
- Dashboard "Get started" card: shown to everyone; expanded when the user has
  no groups, collapsed once they do.
- Rich text (waiver / end message) is Markdown + bleach sanitizer, not CKEditor.
- Group page vocabulary: "Add administrations", "Group settings" (contains the
  rare delete-group danger zone), one scoped "Download ▾", status badge column.

## Open threads

- Virginia: golden-case scoring values; confirm French (France) CAT citation
  (currently a public "forthcoming" placeholder), Japanese (in review), Korean
  (Pae 2003 — she was unsure). Upcoming: European French long/short and Dutch
  short forms → add citation rows when they land.
- Henry: merge/deploy #658 and #661 (logout is broken on testing until #661
  deploys — users can only log out by clearing cookies); https on testing.
- Long-standing: #648 selenium locators, #640/#649 pandas-3 bugs, CD via OIDC
  (#639 second half), lint config (`make docker-lint` scans node_modules and
  fails), Bootstrap #633, D3 #634, static-untrack #632.

## Working style Mike expects

- Rigor and honesty over reassurance: if tests don't cover something, say so.
- Surgical diffs; flag interpretations explicitly (and offer the one-line flip
  if you might have read a request backwards).
- Verify UI changes in a browser and show a screenshot; run the fast suite
  before pushing.
- Never put secrets (AWS keys, passwords) in chat, commits, or this file.
