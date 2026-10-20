# Deploy and operations

Web-CDI is moving from AWS Elastic Beanstalk to Google Cloud (tracking #690).
**GCP is where all deploys and QA happen; AWS production is frozen** on the
2026-10-11 release until cutover (#688) and decommissioning (#689).

## GCP (project `hs-langcog-webcdi`, region `us-west1`)

Stanford Moderate Risk data; this project is approved for real data.
Infrastructure is code: `deploy/terraform/` (OpenTofu), image
`deploy/Dockerfile`, runbooks in `deploy/README.md` and `deploy/rehearsal/`.

| Piece | Name |
|---|---|
| Web service (Cloud Run) | `webcdi-staging` — https://webcdi-staging-qiqpffb23q-uw.a.run.app |
| Database (Cloud SQL, Postgres 16; backups + point-in-time recovery) | `webcdi-staging-db` |
| Jobs (Cloud Run, same image) | `webcdi-staging-{migrate,load-instruments,scoring,monthly-report,weekly-reminder}` |
| Schedule (Cloud Scheduler) | scoring every 10 min; email jobs off on staging (`enable_email_jobs`) |
| Secrets (Secret Manager) | `webcdi-staging-*` (generated) and `postmark-server-token` (by hand) |
| Images (Artifact Registry) | `us-west1-docker.pkg.dev/hs-langcog-webcdi/webcdi/webcdi:<git sha>` |
| State | `gs://hs-langcog-webcdi-tfstate` (prefix `webcdi`) |

There is **no GCP production environment yet** — building it (with a GitHub
deploy-approval gate, webcdi.org domain mapping, Postmark live) is the next
infrastructure step; see `references/roadmap.md`.

### Deploys: merge to master

`.github/workflows/deploy.yml` runs after CI passes on master: build and push
`:<sha>`, point the jobs at it, run `migrate`, rerun `load-instruments` only if
instrument data files changed, deploy the service, smoke-test, and roll traffic
back on failure. GitHub authenticates with Workload Identity Federation — **no
stored keys**. When the service is private (see below) the smoke test runs the
same pages through Django's test client inside a one-off job (#731).

CI uses `concurrency: cancel-in-progress` on master, so rapid merges cancel
older runs and only the newest commit deploys. Check the true master head's
run, not a cancelled one.

### Staging access (current state, Oct 2026)

Staging holds a **scrubbed copy of production** for the migration rehearsal
(#687), so it is private:
- **Browser:** Google sign-in (Identity-Aware Proxy, #725). Allowed accounts
  are `iap_members` in a gitignored `deploy/terraform/*.local.tfvars` (never
  commit personal addresses). Only accounts in Stanford's Google organisation
  get through; gmail accounts are refused. Then log into Web-CDI normally.
- **Email:** console backend (logged, not sent).
- **Scrubbed** so test clicks can't reach the outside world: completion-flag
  URLs and server-side redirect URLs blanked, gift-card codes replaced with
  `STAGING-TEST-<id>`. Redo this after every fresh copy (`deploy/rehearsal/`).
- QA testers get **fresh test researcher accounts**, never real ones.

### Operating it (needs Mike's gcloud login — not available to cloud sessions)

- Infrastructure changes: `tofu plan -var-file=staging.tfvars [-var-file=qa.local.tfvars] -var image=unused … -out=X.tfplan`,
  review, then `tofu apply X.tfplan`. **Never apply without a reviewed saved
  plan.** Plans from a branch that lacks merged infra code will try to undo it.
- One-off Django code against staging data: execute the migrate job with
  `--args="^~^shell~-c~<python>"`; read output with `gcloud logging read`
  filtered by `labels."run.googleapis.com/execution_name"`.
- IAM quirks: Editor can't set resource-level IAM policies; Mike self-granted
  `run.admin`, `iam.serviceAccountAdmin`, `iam.workloadIdentityPoolAdmin`,
  `iap.admin`. Conditioned project grants work for Secret Manager (must match
  `/versions/` too) but not for job invoke or Artifact Registry upload.
  `gcloud run jobs replace` and `gcloud iap` need the Cloud Resource Manager
  API, which is off — use `jobs create` with flags / the REST API.
- If `gcloud` says "Reauthentication failed", Mike must run `gcloud auth login`
  (OpenTofu's application-default credentials may still work meanwhile).

### Email (Postmark)

django-anymail → Postmark; From `noreply@webcdi.org` (DKIM and Return-Path
verified), Reply-To `webcdi-contact@stanford.edu`. As of 2026-10-20 the
Postmark account is **pending approval**: it only delivers to `@webcdi.org`
addresses (error 412 otherwise). Errors and alerts go to
webcdi-contact@stanford.edu (forwards to Mike). Django error emails
can contain participant data — summarize them in issues, don't paste them.

## AWS (legacy production, frozen)

Lab AWS account, us-west-2. **No deploys or changes without Mike's explicit
OK** — including "small" ones; Mike prefers to leave AWS alone until it's
decommissioned. CLI profile `webcdi` (IAM user `webcdi-deploy`).

- **EB:** `Webcdi-env-2` = production (webcdi.org); `Webcdi-dev-django4` = old
  staging (testing.webcdi.org); `webcdi-dev` = Henry's old demo;
  `CdiCatApi-env` / `-dev` = R CAT API (prod still uses it).
- **RDS:** prod = `webcdiadmin` (**never delete** until decommissioning, #689),
  `webcdi-dev-3` = old staging.
- **Secrets Manager:** prod DB password at `prod/webcdi/RDS_PASSWORD`
  (`password` field). `webcdi-deploy` can read it (inline policy
  `read-webcdi-rds-password`, added by Vic for the rehearsal and cutover);
  copy it straight into GCP Secret Manager — never print it.
- **Cron** (`.ebextensions/crontab.txt`) was silently broken from Nov 2024 to
  Oct 2026 (env not loaded); fixed in master (#695) but AWS still runs the
  Oct 11 code.
- Security fixes merged since Oct 11 reach production only at cutover (Mike's
  decision; don't hotfix AWS without him).
- Reading prod logs is a production read — ask Mike first.

## Common DB fixes (Django admin `/wcadmin/` or a one-off job)

- **Researcher "lost" a group:** `Study.active` is False (soft delete) → True.
- **Reuse a gift-card code:** clear `hash_id` and `assignment_date`.
- **Grant instrument access:** Users → user → Researcher → instruments;
  Brookes-gated families also need a code.

## Handoff status (things only Henry had)

- [x] Error emails → webcdi-contact@stanford.edu (GCP build).
- [x] GitHub access trimmed (Oct 2026) to Mike, mikabr, vic-moreno, Henry
  (write), Alvin (write), plus langcog organisation owners.
- [ ] Brookes Publishing contact and the code-issuing workflow.
- [ ] Dutch group's EU server: who deploys it, which version it runs.
- [ ] DNS for webcdi.org (Vic set the Postmark records) — needed for cutover.
