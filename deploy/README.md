# Production container

`deploy/Dockerfile` builds the image that runs Web-CDI on Cloud Run (#677,
tracking #690). The dev image (`./Dockerfile`, used by docker-compose and CI)
is separate.

```bash
docker build -f deploy/Dockerfile -t webcdi .
```

The image runs gunicorn on `$PORT` (default 8080) as a non-root user, serves
static files itself (WhiteNoise: hashed names, Brotli/gzip, immutable caching),
and logs one JSON object per line to stdout. Any management command can run in
the same image, e.g. `python manage.py migrate` (Cloud Run jobs).

## Configuration (environment variables)

Set in the image: `AWS_INSTANCE=false`, `LOG_FORMAT=json`, `STATIC_ROOT`,
`PORT`.

Required at runtime (secrets come from Secret Manager, never the image):

| Variable | Notes |
|---|---|
| `SECRET_KEY` | required — the app refuses to start without it outside DEBUG |
| `ALLOWED_HOSTS` | JSON list, e.g. `["staging.webcdi.org", ".run.app"]` |
| `RDS_DB_NAME`, `RDS_USERNAME`, `RDS_PASSWORD`, `RDS_PORT` | Postgres |
| `RDS_HOSTNAME` | host, or `/cloudsql/<project>:<region>:<instance>` for Cloud SQL |
| `ADMINS` | `[("WebCDI","webcdi-contact@stanford.edu")]` — request errors are emailed here |
| `DEFAULT_FROM_EMAIL_NAME`, `DEFAULT_FROM_EMAIL_ADDRESS`, `DEFAULT_RECIPIENT_EMAIL`, `BROOKES_EMAIL`, `EMAIL_BACKEND` | email |
| `SITE_ID` | Django Sites row |

Optional:

| Variable | Default | Notes |
|---|---|---|
| `HTTPS_ONLY` | false | behind Cloud Run/LB: trusts `X-Forwarded-Proto`, redirects to HTTPS (except `/health/`), secure cookies, HSTS |
| `HSTS_SECONDS` | 3600 | raise once HTTPS is settled |
| `DB_CONN_MAX_AGE` | 0 | seconds to reuse DB connections (e.g. 60) |
| `WEB_CONCURRENCY`, `GUNICORN_THREADS`, `GUNICORN_TIMEOUT` | 2, 4, 300 | gunicorn |
| `PRIMARY_HOST`, `TRUSTED_ORIGINS`, `GOOGLE_ANALYTICS_ID`, `TIME_ZONE` | | see `.env.example` |

`/health/` checks the database, cache and storage; use it for startup and
liveness probes.

## Infrastructure (`deploy/terraform`, OpenTofu)

One configuration per environment, parameterised by project (`staging.tfvars`
→ `hs-langcog-general` for now, #690). It creates: APIs, an Artifact Registry
repo, Cloud SQL Postgres 16 (backups + PITR, deletion protection, reachable
only via the IAM-authenticated connector), generated secrets in Secret
Manager, runtime and scheduler service accounts (IAM grants are project-level
but conditioned to this environment's resource names), the public Cloud Run
service, and Cloud Run jobs (`migrate`, `load-instruments`, `scoring`,
`monthly-report`, `weekly-reminder`) with Cloud Scheduler triggers (email jobs
only when `enable_email_jobs = true`).

```bash
deploy/terraform/bootstrap.sh <project>            # once: private state bucket
cd deploy/terraform
tofu init -backend-config=bucket=<project>-tfstate
tofu plan -var-file=staging.tfvars -var image=<image> -out=plan.tfplan
tofu apply plan.tfplan                              # review the plan first
```

Images: until CI/CD (#681) exists, build amd64 and push
(`docker buildx build --platform linux/amd64 -f deploy/Dockerfile -t <image> --push .`);
Cloud Build (`deploy/cloudbuild.yaml`) needs a build service account first.
New images roll out with `gcloud run deploy`/`gcloud run jobs update`; tofu
ignores image changes so `apply` never rolls them back.

First-time data: run the `migrate` job, then `load-instruments`
(`gcloud run jobs execute <name> --wait`). One-off commands run as job
executions with overridden args, e.g.
`gcloud run jobs execute webcdi-staging-migrate --args="^~^shell~-c~<python>"`.

Staging: https://webcdi-staging-z2fr43hbjq-uw.a.run.app (email goes to the
service logs; no real mail is sent).
