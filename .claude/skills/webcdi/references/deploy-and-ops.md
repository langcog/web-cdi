# Deploy and operations

## AWS layout

Lab AWS account, region **us-west-2** (other regions empty). CLI profile on
Mike's machine: `webcdi` (IAM user `webcdi-deploy`; EB deploy + S3 multipart).
Other people need their own credentials from Mike — never share keys in chat
or commits.

- **EB environments:** `Webcdi-env-2` = production (webcdi.org);
  `Webcdi-dev-django4` = staging (testing.webcdi.org); `webcdi-dev` = Henry's
  old demo (don't touch); `CdiCatApi-env` / `CdiCatApi-dev` = R CAT API;
  `Wordbank-prod` / `Wordbank-dev` belong to Wordbank, not Web-CDI.
- **RDS (Postgres):** prod and dev DBs; public access is intentional (other
  lab resources read them). Don't flag it.
- **S3:** media buckets (`webcdi-media-prod`, `webcdi-media-dev`).
- **Secrets Manager:** DB password at
  `{DJANGO_SERVER_TYPE lower}/webcdi/RDS_PASSWORD` (rotated automatically —
  that's why `RDS_ENGINE=webcdi_postgresql_engine` exists) and IAM creds at
  `webcdi/webcdi-IAM`. Only read when `AWS_INSTANCE` is true.
- **Email:** AWS SES (`django_ses.SESBackend`, us-west-2).
- **Logs:** EB streams `/var/log/app/*.log`, httpd, etc. to **CloudWatch**
  with **7-day retention**; `eb logs <env>` pulls a bundle. Reading prod logs
  is a production read — ask Mike first.
- A 2026-09 cost audit found runaway AWS Backup snapshots (a wildcard monthly
  plan) and many stopped legacy instances; cleanup is in progress and owned by
  Mike. Don't delete AWS resources without explicit instruction.

## Deploying

1. Merge to `master` (CI green). Deploy from a clean checkout of what you
   merged.
2. From `webcdi/`: `eb deploy Webcdi-dev-django4` (staging) → check
   testing.webcdi.org → `eb deploy Webcdi-env-2` (production, **only with
   Mike's go-ahead**). `git archive` from `webcdi/` roots the bundle
   correctly.
3. `.platform/hooks/postdeploy/02_django.sh` then runs on each instance:
   `migrate`, `collectstatic`, and populate commands `01_populate_instrument_family`,
   `02_populate_instrument`, `03_populate_scoring`, `04a_delete_benchmark`,
   `04_populate_benchmark`, `05_populate_choices`, `06_populate_items`. So
   changes to instruments.json, item CSVs, scoring JSON or benchmark CSVs go
   live on deploy with no manual step. One-off rescoring commands
   (`update_summary_data`, `update_english_ws_scoring`) are commented out —
   Henry toggles them in for a release that changes scoring, then back out.
4. `01_copy_env.sh` copies EB env vars to a file readable by cron jobs.
5. Env vars are set per environment in EB (`eb setenv KEY=value`; empty
   `PRIMARY_HOST=` disables the host-redirect middleware).

Henry's wiki also says deploying needs the EC2 key `web-cdi_011017.pem` in
`~/.ssh` (for `eb ssh`; plain `eb deploy` doesn't need it).

## Cron (`.ebextensions/crontab.txt` → `/etc/cron.d/webcdi_cron_jobs`)

- `crontab_scoring` every 10 min — scores newly completed administrations.
- `monthly_report` (1st of month) and `weekly_reminder` (Sundays) — **these
  management commands don't exist in the repo**, so they fail every run.
- `MAILTO` is Henry's personal address (#638) — must change.
- The file must end with a blank line or cron rejects it.
- `crontab2.txt` is an unused leftover; slated for deletion.

## Environment variables (read in `webcdi/settings.py`; template `.env.example`)

| Variable | Meaning |
|---|---|
| `AWS_INSTANCE` | true on EB (Secrets Manager, S3); **false locally** |
| `DJANGO_SERVER_TYPE` | `DEV` / `PROD` (picks the Secrets Manager path) |
| `RDS_ENGINE`, `RDS_DB_NAME`, `RDS_USERNAME`, `RDS_PASSWORD`, `RDS_HOSTNAME`, `RDS_PORT` | DB; sqlite not supported |
| `EMAIL_BACKEND`, `AWS_SES_REGION_NAME`, `AWS_SES_REGION_ENDPOINT`, `EMAIL_PORT` | email |
| `DEFAULT_FROM_EMAIL_NAME`, `DEFAULT_FROM_EMAIL_ADDRESS`, `DEFAULT_RECIPIENT_EMAIL`, `SERVER_EMAIL` | senders |
| `ADMINS` | JSON list of (name, email) — **receives 500-error emails** |
| `BROOKES_EMAIL` | Brookes contact notified about code use; leave as is unless Brookes asks |
| `CONTACT_EMAIL`, `MORE_INFO_ADDRESS` | home-page links |
| `ALLOWED_HOSTS`, `TRUSTED_ORIGINS` | JSON lists (prod: `[".webcdi.org"]`) |
| `DEBUG` | false in prod; **true locally** |
| `SITE_ID` | Django Sites row: 1 WebCDI, 2 test, 3 local, 4 MPI |
| `PRIMARY_HOST` | redirect bare host to this host (optional) |
| `TIME_ZONE`, `LOG_FILE_PATH` | defaults UTC, `/tmp/` |
| `CAT_API_URL` | R CAT API base URL |
| `CAT_ENGINE` | `remote` (R API, prod default) or `browser` (jsCat) |
| `SECRET_KEY`, `GOOGLE_ANALYTICS_ID` | from env |
| `AWS_STORAGE_BUCKET_NAME`, AWS keys | S3 media; only when `AWS_INSTANCE` |

## Common DB fixes (Django admin `/wcadmin/` or psql)

- **Researcher "lost" a group:** `researcher_UI_study.active` is False (soft
  delete) → set True.
- **Reuse a gift-card code** (used in testing): in `researcher_UI_payment_code`
  clear `hash_id` and `assignment_date`; change `study_id` to move it.
- **Grant instrument access:** Users → user → Researcher → "Instruments this
  researcher has access to"; Brookes-gated families also need a code.

## Things only Henry had (handoff checklist)

Confirm each with Mike/Henry and record where it now lives:
- [ ] Error emails: prod `ADMINS` and cron `MAILTO` point at Henry.
- [ ] EC2 key pair `web-cdi_011017.pem` (only needed for `eb ssh`).
- [ ] Prod Django superuser(s); GitHub repo admin; Dependabot triage.
- [ ] Brookes Publishing contact and the code-issuing workflow.
- [ ] Dutch group's EU server: who deploys it, which version it runs.
- [ ] REDCap/Wordful study links (`references/researcher-features.md`).
- [ ] DNS for webcdi.org and SES sender verification — who controls them.
- [ ] The R CAT API (`langcog/cdi-cat-api`, George Kachergis) — redeploys.
