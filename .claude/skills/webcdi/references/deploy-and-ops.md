# Deploy and operations

**webcdi.org runs on Google Cloud since 2026-11-19** (cutover record:
`deploy/cutover/README.md`; follow-ups #810). AWS is retired and read-only
until decommissioning (#689, from about 2026-12-19). Infrastructure is code:
`deploy/terraform/` (OpenTofu), image `deploy/Dockerfile`, operations guide
`deploy/README.md`.

## Environments (region `us-west1`; Stanford Moderate Risk data in both)

| Piece | Production (`hs-langcog-webcdi-prod`) | Staging (`hs-langcog-webcdi`) |
|---|---|---|
| Address | https://webcdi.org via a global HTTPS load balancer (IP 136.110.158.67, Google-managed certificate); `www` and `http` redirect to `https://webcdi.org` | https://webcdi-staging-qiqpffb23q-uw.a.run.app (Google sign-in) |
| Web service | `webcdi-production` (1 CPU, 2 GiB, one instance always warm, up to 5) | `webcdi-staging` |
| Database | Cloud SQL `webcdi-production-db`, Postgres 16, dedicated core, backups + PITR, deletion protection | `webcdi-staging-db` |
| Jobs (same image) | `webcdi-production-{migrate,load-instruments,scoring,monthly-report,weekly-reminder}` | `webcdi-staging-…` |
| Schedule | scoring every 10 min; email jobs **off** until Virginia confirms the Brookes contact | scoring; email jobs off |
| Email | Postmark (live) | console backend (logged) |
| Terraform state | `gs://hs-langcog-webcdi-prod-tfstate` | `gs://hs-langcog-webcdi-tfstate` |

The production project also still holds `webcdi-production-aws-prod-db-password`
and the `webcdi-production-load-from-aws` job used for the cutover copy;
delete both when Mike agrees (#810).

## Deploys: merge to master

`.github/workflows/deploy.yml` runs after CI passes on master. **Staging**:
build and push `:<sha>`, point the jobs at it, run `migrate`, rerun
`load-instruments` only if instrument data files changed, deploy, smoke-test,
roll back on failure. **Production** then waits for approval in the GitHub
`production` environment (mcfrank or mikabr), copies the same image into the
production registry and does the same steps against webcdi.org. GitHub
authenticates with Workload Identity Federation — no stored keys.

- CI uses `cancel-in-progress` on master, so rapid merges cancel older CI runs
  (their deploys show as "skipped").
- Production runs queue one at a time. After several merges, **cancel the
  older waiting production runs** and approve the newest, so one approval puts
  production on master's head.
- Never approve a production deploy yourself; Mike or mikabr do.
- Data migrations run in production the moment the deploy is approved: count
  the affected rows first (one-off job, below) and put the count in the PR.

## Operating production (needs a Google account with project roles)

- **Health and traffic:** `deploy/cutover/day-of/watch.sh <since-UTC>` — request
  counts by status and area, error-level log count, recent scoring runs.
  Counts only.
- **One-off Django code:** `deploy/cutover/day-of/runjob.py
  webcdi-production-migrate [--timeout 900s] -- shell -c "<python>"` runs it as
  a job execution and prints the log (it retries polling, never the run
  request). Print aggregates only — never participant identifiers. Prefix
  output lines (e.g. `CHECK`) and grep for them.
- **Logs:** `gcloud logging read 'resource.labels.service_name="webcdi-production" …'
  --project hs-langcog-webcdi-prod`. Request logs carry `httpRequest.status`
  and paths; mask hashes and IDs when summarizing.
- **Infrastructure:** `tofu plan -var-file=production.tfvars -var image=<the
  running image> -out=X.tfplan` from current master, with
  `TF_DATA_DIR` separate from staging's and
  `tofu init -reconfigure -backend-config=bucket=hs-langcog-webcdi-prod-tfstate`.
  Mike reviews; then `tofu apply X.tfplan`. **Never apply without a reviewed
  saved plan.** Images are in `ignore_changes`, so apply doesn't roll back a
  deploy, but get the running image from `gcloud run services describe`
  anyway.
- **Limits learned the hard way:** Cloud Run refuses non-streamed responses
  over 32 MiB (HBCD's study API pull failed until #812 added gzip); building
  big pandas exports needs memory (raised to 2 GiB, #813).
- **Site row:** production `django_site` id 1 = `webcdi.org` (changed from
  `www.webcdi.org` on 2026-11-20; the unused legacy row 3 became
  `localhost:8000`, since domains are unique). Instances cache it until
  restart.
- **API clients:** HBCD pulls studies 947, 948 and 949 through
  `POST /api/study/<id>/` every 30 minutes (python-requests). If those calls
  fail, they notice.
- **Restore:** `gcloud sql instances clone --point-in-time` to a scratch
  instance took about 9 minutes in the 2026-11-12 drill; delete it after.

### Access and IAM quirks

- Mike holds the project roles (Editor, Project IAM Admin, plus self-granted
  `run.admin`, `iam.serviceAccountAdmin`, `iam.workloadIdentityPoolAdmin`,
  `logging.configWriter`, and on staging `iap.admin`). Production secret
  **values** are unreadable to him by design.
- Editor can't set resource-level IAM policies. Conditioned project grants
  work for Secret Manager (must match `/versions/` too) but not for job invoke
  or Artifact Registry upload. `gcloud run jobs replace`, `gcloud iap` and
  `gcloud run jobs create --set-cloudsql-instances` want APIs that are off —
  use `jobs create` with flags or the Cloud Run REST API.
- Stanford sessions expire often: if `gcloud` says "Reauthentication failed",
  the account owner runs `gcloud auth login` (OpenTofu's application-default
  credentials may still work meanwhile).
- zsh: `$R:w`-style expansions are mangled by modifiers; write `${R}`.

### Staging access

Staging holds a **scrubbed copy of production**, so it is private:
- **Browser:** Google sign-in (Identity-Aware Proxy, #725). Allowed accounts
  are `iap_members` in the gitignored `deploy/terraform/staging.local.tfvars`
  (never commit personal addresses). Only Stanford Google accounts get
  through. Then log into Web-CDI normally.
- **Scrubbed** so test clicks can't reach the outside world: completion-flag
  URLs and redirect URLs blanked, gift-card codes replaced with
  `STAGING-TEST-<id>`. Redo after every fresh copy (`deploy/rehearsal/`). A
  refresh from production (or a reload of synthetic data) is pending (#810).
- QA testers get **fresh test researcher accounts**, never real ones.

## Email (Postmark)

django-anymail → Postmark (Basic plan, 10,000 emails a month, transactional
stream only); From `noreply@webcdi.org` (DKIM and Return-Path verified),
Reply-To `webcdi-contact@stanford.edu`. Bulk mail to researchers is sent by
Virginia or Mike from Stanford, not Postmark. Alerts and Django error emails
go to webcdi-contact@stanford.edu (forwards to Mike). Error emails can contain participant data — summarize them in
issues, don't paste them. "[MESSAGE AUTH FAILURE]" mail is AWS sending as
stanford.edu through SES; it stops when AWS is gone.

## AWS (retired, read-only)

Lab AWS account, us-west-2, managed by Vic. **No changes without Mike's
explicit OK.** At the cutover the app's database role was made read-only
(`ALTER ROLE "webcdi-admin" SET default_transaction_read_only = on`; the
role doesn't own the database, so `ALTER DATABASE` fails). Rollback by DNS was
possible only on the cutover night; now we fix forward. The password rotation
can't complete while the role is read-only: expect failed-rotation notices.
Decommissioning (#689) starts about 2026-12-19; don't delete the RDS
database (`webcdiadmin`) until a final export is archived (#671).

## Common DB fixes (Django admin `/wcadmin/` or a one-off job)

- **Researcher "lost" a group:** `Study.active` is False (soft delete) → True.
  Deletes never remove data.
- **Reuse a gift-card code:** clear `hash_id` and `assignment_date`.
- **Grant instrument access:** Users → user → Researcher → instruments;
  Brookes-gated families also need a code.
- **Parent says they finished but the form isn't complete:** the parent must
  submit; before the group's minimum time the Submit button is disabled with
  a wait message (#808). A researcher can open the link and submit for them.

## Handoff status

- [x] Error emails and alerts → webcdi-contact@stanford.edu.
- [x] DNS for webcdi.org: Route 53 in the lab AWS account (Vic); records are
  A → 136.110.158.67 for `webcdi.org` and `www`, plus Postmark's DKIM,
  `pm-bounces` and `_dmarc`.
- [x] Production approvals: mcfrank, mikabr.
- [ ] Cherrie: GitHub write access, Google Cloud roles on both projects, and
  (if wanted) production-deploy approval.
- [ ] Brookes Publishing contact and the code-issuing workflow (blocks the
  email jobs).
- [ ] Dutch group's EU server: who deploys it, which version it runs.
- [ ] Budget alert on the production project (needs billing-account access).
