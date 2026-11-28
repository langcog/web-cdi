# Developing Web-CDI locally

_Updated with Claude Opus 5.5 (Nov 2026)._

Web-CDI is a Django 5 / PostgreSQL application. Local development runs
entirely in Docker via `docker compose`; you do not need Python or Postgres
installed on your machine.

## Prerequisites

- Docker Desktop (or another Docker engine with the compose plugin)
- ~2 GB free disk for images and the database volume

## First-time setup

```bash
git clone https://github.com/langcog/web-cdi.git
cd web-cdi

# 1. Create your local environment file, then set RDS_PASSWORD in it to any
#    value (it becomes the local database container's password)
cp .env.example .env

# 2. Build the web image and start the stack
docker compose build web
docker compose up -d db web

# 3. Create the schema and static files
docker compose exec web ./manage.py migrate
docker compose exec web ./manage.py collectstatic --noinput

# 4. Load instruments, scoring rules, and items (a few minutes)
make docker-db-populate

# 5. Create yourself an admin account
docker compose exec web ./manage.py createsuperuser
```

The site is then available at <http://localhost:8001>:

| URL | What it is |
|---|---|
| `/` | Public home page |
| `/accounts/login/`, `/accounts/register/` | Researcher login / signup |
| `/interface/` | Researcher dashboard (study management) |
| `/wcadmin/` | Django admin |
| `/form/...` | Participant-facing CDI forms |

Other services in the compose stack:

- **mail** — MailHog UI at <http://localhost:8025> (only used if you point
  `EMAIL_BACKEND` at SMTP; the default `.env.example` prints email to the
  web container log instead)
- **pgadmin** — database UI (port is dynamically mapped; `docker compose port pgadmin 80`)
- **selenium** — Firefox WebDriver used by the browser test suite

## Day-to-day commands

```bash
docker compose up -d db web     # start
docker compose logs -f web      # tail the dev server
docker compose exec web bash    # shell inside the container
make docker-test                # run the test suite (excludes selenium tests)
make docker-lint                # flake8 + black --check
make docker-cleanup             # black + isort (auto-format)
docker compose down             # stop (add -v to also delete the database)
```

The `./webcdi` directory is bind-mounted into the container, so code edits
reload the dev server automatically.

## Environment variables

All configuration is read from environment variables in
`webcdi/webcdi/settings.py`; `docker-compose.yml` loads them from `.env`.
See [.env.example](.env.example) for the full annotated list. Two to know
about:

- `AWS_INSTANCE` — **must be False locally.** When True (the settings
  default, kept from the AWS era) the app pulls credentials from AWS Secrets
  Manager and stores uploads in S3. The production image sets it to false.
- Computer-adaptive (CAT) forms run entirely in the browser (jsCat engine in
  `webcdi/cdi_forms/cat_forms/jscat/`, item banks in
  `cdi_forms/static/cdi_forms/cat/`); no external CAT service is needed.

## Architecture at a glance

- `webcdi/webcdi/` — settings, root urls, middleware
- `webcdi/researcher_UI/` — researcher dashboard: studies, administrations,
  scoring, data download
- `webcdi/cdi_forms/` — participant-facing forms (background info + CDI
  items); `cdi_forms/cat_forms/` is the adaptive variant, which runs in
  the browser (jsCat)
- `webcdi/brookes/` — Brookes Publishing licensing/payment codes
- `webcdi/api/` — read-only JSON export endpoints
- `webcdi/cdi_form_csv/` + `webcdi/cdi_forms/form_data/` — instrument
  definitions (items as CSV, per-form metadata as JSON) loaded by the
  numbered management commands in `webcdi/webcdi/management/commands/`
- Scoring runs every 10 minutes in production (the `crontab_scoring`
  management command as a Cloud Run job, triggered by Cloud Scheduler)

## Browser tests (Selenium)

The `selenium`-tagged tests (28, about 25 minutes) run nightly on GitHub and
on demand (Actions → "Selenium (browser suite)" → Run workflow). To run them
locally, start the `selenium` service and run the tests in a container that
answers to the hostname `web`:

```bash
docker compose up -d db selenium
docker compose run --rm --use-aliases web python manage.py test --tag=selenium --noinput -v 2
```

## Production deployment

Production (webcdi.org) and staging run on Google Cloud. Merging to `master`
deploys to staging automatically and then waits for approval to deploy the
same image to production; see [deploy/README.md](deploy/README.md). The AWS
Elastic Beanstalk files (`webcdi/.ebextensions/`, the `Makefile` targets
`dev-deploy` / `live-deploy`, `setup.txt`) are from the old AWS site, which
was retired from service on 2026-11-19 and is kept read-only until it is
decommissioned (#689); don't use them.
