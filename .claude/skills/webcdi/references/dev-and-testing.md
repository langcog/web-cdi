# Local development and testing

## Running locally

Follow `DEVELOPMENT.md` (docker compose: `web`, `db`, `selenium`; site at
http://localhost:8001). Things it doesn't say:

- `db` is pinned to `postgres:16`; unpinned `postgres` (18) breaks the volume
  mount. After a pin change you may see a collation warning — fix with
  `ALTER DATABASE postgres REFRESH COLLATION VERSION` or recreate the volume.
- Docker Desktop is often not running: `open -a Docker`, wait for
  `docker info`, then `docker compose up -d --wait db web`. If web races db on
  first start ("could not translate host name db"), restart web.
- `.env`: `AWS_INSTANCE=False` (else settings call AWS Secrets Manager),
  `DEBUG=True` (no WhiteNoise → no static files when False), console email
  backend. `ALLOWED_HOSTS`/`ADMINS` are JSON strings — keep the quotes.
  Full variable list: `references/deploy-and-ops.md`.
- After migrate + collectstatic, load instruments with
  `make docker-db-populate` (commands `01`–`06`, a few minutes).
- pip installs made inside the container (e.g. `tblib`) vanish when it's
  recreated.
- Make a researcher via `createsuperuser` or `/accounts/register/`; grant
  Brookes codes and instrument access in `/wcadmin/` to unlock paid forms.
- Routes: `/accounts/login/`, `/wcadmin/` (Django admin), `/interface/`
  (researcher console; group page `/interface/study/<pk>/detail/`),
  `/form/administration/<hash>/<page>/` (participant form),
  `/brookes/codes/<family>/`, `/about/`, `/documentation/`, `/health/`.
- Debugging against real data: `pg_dump` the dev DB and load locally (wiki
  "Local Deployment"); credentials come from AWS Secrets Manager, never the
  repo.

## Tests

- **Fast suite** (what CI runs; ~260 tests, ~18 min locally, ~40 min on
  GitHub's 2-core runners):
  ```
  docker compose exec -T web python manage.py test --exclude=selenium --exclude=known_failure --parallel auto --noinput
  ```
  (`make docker-test` is the same.)
- **Discovery is via package `__init__.py` re-exports.** Every new test module
  must be imported in its package `__init__.py`. (This once hid the
  browser-CAT tests for months.)
- Fixtures are huge — even one test class can take many minutes (setUp
  generates fake administrations). Run single tests by dotted path while
  iterating.
- Django test `Client` sometimes needs `HTTP_HOST='localhost'` (else 400 from
  ALLOWED_HOSTS).
- **Randomized fixtures hide bugs:** some tests pick `Instrument...order_by("?")`,
  so a bug in one language/form shows up as intermittent CI failure. When CI
  flakes, suspect this first and add a test pinned to the failing instrument.
- `known_failure` tag = quarantined bugs (#640 StudyAPI `to_json` duplicate
  index).
- WeasyPrint PDF tests may error under `--parallel` but pass alone.
- CAT: Django tests cover rendering/persistence for all 5 languages
  (`cat_forms/tests/browser_engine.py`); the engine itself is validated by
  `npm test` in `cat_forms/jscat/` (also a CI job).
- **Selenium** (`--tag=selenium`, 28 tests, 60–90 min) runs nightly in
  `selenium.yml`, non-blocking. ~21 researcher-flow tests fail on stale
  locators from the 2026 redesign (#648) — test rot, not app bugs. Between
  killed local runs: `docker compose restart selenium`.
- Scoring has value-level tests (`cdi_forms/tests/tests_scoring/`) — see
  `references/scoring-and-cat.md`.
- `make docker-lint` is broken (black/flake8 have no config and scan
  `node_modules`).

## CI (GitHub Actions; repo is public so minutes are free)

- `ci.yml`: fast suite + `jscat` job on every PR and push to master. Builds
  via `docker compose up -d --build --wait` with `.env` from `.env.example`
  (CI generates a random DB password — never put password literals in the
  repo; GitGuardian blocks them). Required checks: "Django suite (unit +
  integration)", "GitGuardian Security Checks", "jsCat engine vs mirtCAT".
  Branches need not be up to date with master to merge.
- `deploy.yml`: after CI passes on master, deploys to GCP staging
  (`references/deploy-and-ops.md`).
- `selenium.yml`: nightly 08:00 UTC + manual dispatch.
- Reading failures: `gh run view <id> --log-failed`, then grep for
  `^ERROR:|^FAIL:|Traceback`.

## Working from a cloud session

Cloud sessions clone the repo and can run tests and open PRs, but have no
gcloud/AWS credentials and no access to staging. Install Postgres 16 in the
environment (tests need it: `ArrayField`), or use the docker compose stack if
Docker is available. Leave anything needing GCP (job runs, data counts,
`tofu apply`, logs) to Mike's primary session and say so in the PR.

## Browser checks

- Use the in-app browser against localhost:8001; screenshot UI changes.
- Theme CSS is cached aggressively (no hashed filenames): bust with
  `link.href += '?v=' + Date.now()` or hard reload.
- If the browser pane is hidden, screenshots come back blank and
  rAF/IntersectionObserver pause — verify with synchronous JS instead.
- Benign console noise on testing.webcdi.org: COOP header warning (site is
  http) and `ERR_BLOCKED_BY_CLIENT` (ad blocker eating Google Analytics).
