# Production cutover (#688)

Drafted with Claude Opus 5.5; not yet reviewed. **Status: draft.** The
production environment was built on 2026-11-07 and holds the 2026-11-10
dress-rehearsal copy; webcdi.org still points at AWS. **Cutover: Thursday
2026-11-19, 9–11 pm Pacific.** Each step below that creates
or changes something waits for Mike's go-ahead.

Moves webcdi.org from AWS Elastic Beanstalk to the GCP build, with the
production database copied across while writes are stopped. Rollback is
pointing DNS back at AWS, which stays running, untouched and read-only through
a holding period before decommissioning (#689).

## Decisions (agreed 2026-11-06)

1. **Production has its own GCP project**, `hs-langcog-webcdi-prod` (same
   Moderate Risk classification). Staging's deploy identity and runtime
   account have no access to it.
2. **webcdi.org reaches Cloud Run through a global HTTPS load balancer**
   (`deploy/terraform/lb.tf`), with a Google-managed certificate authorized
   through DNS, so it is issued before DNS moves. Cloud Run accepts traffic
   only from the load balancer.
3. **Email jobs (Brookes monthly report, renewal reminders) stay off** until
   Virginia confirms the Brookes contact. They haven't run on AWS since Nov
   2024 (#695).
4. **Rollback by DNS only until the window closes**; fix forward after that.
5. **30 days** on GCP before #689.

## Production environment

The staging configuration with `production.tfvars`: custom domains and the
load balancer, `PRIMARY_HOST=webcdi.org` (www redirects to it), a dedicated-core
database (`db-custom-1-3840`) with maintenance on Tuesdays at 10:00 UTC, one
instance always warm, and email jobs off. Deploy credentials go only to GitHub
jobs in the `production` environment, which needs Mike's approval. After each
staging deploy, the workflow's `production` job waits for that approval, copies
**the same image** into the production registry, migrates, deploys,
smoke-tests as `webcdi.org`, and routes traffic back if the smoke test fails.
It only runs once the repository variable `DEPLOY_PRODUCTION` is `true`.

### First build (once)

1. Mike grants himself, on the production project, the roles he has on
   staging beyond Editor and Project IAM Admin: Service Account Admin,
   Workload Identity Pool Admin, Cloud Run Admin, Logs Configuration Writer.
2. Postmark production token into Secret Manager as `postmark-server-token`
   (the service won't start without it).
3. `deploy/terraform/bootstrap.sh hs-langcog-webcdi-prod` (state bucket), then
   `tofu init -reconfigure -backend-config=bucket=hs-langcog-webcdi-prod-tfstate`.
4. Registry first: a saved plan with
   `-target=google_artifact_registry_repository.images`, reviewed, applied.
5. Copy the image staging runs into it, unchanged:
   `docker pull --platform linux/amd64 <staging image>`, `docker tag`,
   `docker push` to
   `us-west1-docker.pkg.dev/hs-langcog-webcdi-prod/webcdi/webcdi:<sha>`.
6. Database and jobs before the web service, whose startup check needs the
   tables: a saved plan with `-target=google_cloud_run_v2_job.manage` (it
   pulls in the database, secrets and accounts), applied; run the `migrate`
   and `load-instruments` jobs; then the full saved plan with
   `-var-file=production.tfvars -var image=<that image>`, reviewed by Mike,
   applied. (Done 2026-11-07 in the other order: the service failed its
   startup check on the empty database and had to be redeployed.)
7. GitHub: the `production` environment's variables `GCP_PROJECT`,
   `GCP_REGION`, `GCP_WIF_PROVIDER` (from `tofu output github_wif_provider`);
   then the repository variable `DEPLOY_PRODUCTION=true`.
8. Vic adds the two `_acme-challenge` CNAMEs from `tofu output
   dns_authorizations`; wait for the certificate to show ACTIVE. (Done
   2026-11-10, along with step 7; `DEPLOY_PRODUCTION=true` set 2026-11-12.)
9. Budget alert on the project (needs billing-account access; Stanford may
   have to set it).

## Before the day

- [x] Postmark account approved, Basic plan (10,000 emails a month); Vic's
      test send delivered (2026-11-06).
- [x] A test email from production (`manage.py sendtestemail` through the
      migrate job) reached webcdi-contact (2026-11-10).
- [x] A password-reset email from production reaches a stanford.edu address
      (2026-11-12).
- [x] First build done (above); the certificate is ACTIVE (2026-11-10).
      `curl --resolve` to the load balancer: `/health/` 200, www redirects.
- [x] AWS database password copied into the production project's Secret
      Manager as `webcdi-production-aws-prod-db-password` (never printed), and
      a `webcdi-production-load-from-aws` job created there
      (`deploy/rehearsal/README.md` step 2, production names) (2026-11-10).
      The job was created through the Cloud Run API: `gcloud run jobs create
      --set-cloudsql-instances` asks to enable `sql-component.googleapis.com`,
      which the project doesn't otherwise need. The password rotates, so
      re-copy it on the day (`gcloud secrets versions add`).
- [x] **Dress rehearsal into the production database** (2026-11-10): steps
      2–7 of "On the day" (browser test aside) without stopping writes or
      touching DNS. Copy 128 s (1.6 GB; counts matched except 17 item rows
      written on AWS during the copy), migrate 32 s (4 migrations), reload instruments 48 s, rescore
      15 min (32,555 completed, 0 failed, 0 left unscored). Percentile values
      all valid (511,729); downloads as each owner 83 OK and the known
      Argentine Spanish WG redirect (#764); `/health/` and the login page 200
      through the load balancer. Found: Dutch CAT theta stored as 0 (#798).
      The database now holds this copy; the real copy overwrites it.
- [x] Browser test of production before DNS: map `webcdi.org` to the load
      balancer IP in your `/etc/hosts`, log in with your own account, open a
      group, a download, and a CAT form. Remove the line afterwards. (Mike,
      2026-11-12: login, download and Japanese CAT worked. Check the padlock
      first: the certificate is from Google Trust Services on GCP, Amazon on
      AWS. Safari reached AWS on the first try despite the mapping. Findings:
      CAT progress bar (#801); groups without a background form (#802).)
- [x] Restore drill: point-in-time restore of the production database to a
      scratch instance; delete it after. (2026-11-12: `gcloud sql instances
      clone --point-in-time`, 8.5 min; row counts matched production up to the
      restore point; scratch instance deleted.)
- [ ] Open items from the rehearsal: CAT forms through a browser in each
      language; the 2 completed CAT administrations with no theta.
- [x] QA sign-off (Cherrie, 2026-11-12).
- [ ] Percentile sign-off (Virginia): given on 2026-11-12 if both Web-CDI and
      "the scoring app" use the 36-month tables. Web-CDI does (#767); which
      scoring app she means is still open.
- [ ] Researchers told the date at least a week ahead (Virginia's email),
      including the Dutch group, who run their own server.
- [x] Current alias targets of `webcdi.org` and `www.webcdi.org` written
      down for rollback (Vic, 2026-11-10; kept outside the repo).
- [ ] Vic available in the window to change DNS.
- [ ] No merges to master on the day.

## Window

Forms completed per hour, Monday to Thursday, Aug–Oct 2026 (staging copy,
by last change, Pacific time): averaged over the 13 weeks, at most about 4 an
hour at the busiest (9–11 am), under 1 an hour from midnight to 6 am, and about
1 an hour from 9 to 11 pm. Friday, Saturday and early Sunday show thousands of
changes that look like bulk updates rather than participants, so they aren't a
guide. **Proposal: a Tuesday–Thursday evening, 9–11 pm Pacific.** The
production Cloud SQL maintenance window goes in the quietest weekday hour
(around 2 am Pacific).

Rehearsal timings on 2026-11-03: copy 132 s for 1.6 GB, migrate 25 s, reload
instruments 21 s, rescore 804 s. Production dress rehearsal on 2026-11-10:
copy 128 s, migrate 32 s, reload 48 s, rescore 15 min. Announce two hours;
expect about one.

## On the day

`P` is the production project, `R=us-west1`.

1. **Stop writes on AWS** (Mike's go-ahead; the only change made to AWS).
   Runs from the production project with the `load-from-aws` job's image and
   password, overriding its arguments:
   ```sql
   ALTER DATABASE "webcdi-admin" SET default_transaction_read_only = on;
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity
    WHERE datname = current_database() AND pid <> pg_backend_pid();
   ```
   Check from a new session: `SHOW default_transaction_read_only` is `on`.
   The AWS site still shows pages; saving anything fails with an error page,
   and AWS sends error emails to webcdi-contact. That is expected.
2. **Copy:** pause the scoring schedule
   (`gcloud scheduler jobs pause webcdi-production-scoring --location $R`)
   so it doesn't run against half-copied tables, then
   `gcloud run jobs execute webcdi-production-load-from-aws --wait`.
   Every row count in its log must match exactly (writes are stopped).
3. **Before migrating:** no duplicate `InstrumentScore (instrument, title)`
   rows.
4. **Migrate**, then **reload instruments** (`webcdi-production-migrate`,
   `webcdi-production-load-instruments`). Afterwards every instrument in
   `instruments.json` has a family; 15 retired instruments that aren't in it
   have none, as on AWS.
5. **Site row:** stays `www.webcdi.org`, as copied (links to www redirect to
   `webcdi.org` with path and query kept). Check it.
6. **Rescore:** `update_summary_data` through the migrate job with
   `--task-timeout=4h`. No completed administration left unscored. Then
   resume the scoring schedule.
7. **Checks before DNS:** percentile values valid; download sweep;
   `curl --resolve webcdi.org:443:<LB IP> https://webcdi.org/health/`; the
   `/etc/hosts` browser test again (login, group page, download, a CAT form).
8. **Switch DNS** (Vic): `webcdi.org` and `www.webcdi.org` from the Elastic
   Beanstalk aliases to A records for the load balancer IP, TTL 300. Leave the
   Postmark records (`_dmarc`, the DKIM key, `pm-bounces`) alone.
9. **Watch** for an hour: `dig webcdi.org` from outside Stanford; alert
   emails; Cloud Run 5xx and Error Reporting; the scoring job's runs; a
   password-reset email arrives; the first participant form completed on GCP
   (count only).
10. **Close the window:** tell researchers it's done.

## Rollback

- **Before step 8:** users only saw the write stop. Undo it:
  ```sql
  SET default_transaction_read_only = off;
  ALTER DATABASE "webcdi-admin" RESET default_transaction_read_only;
  SELECT pg_terminate_backend(pid) FROM pg_stat_activity
   WHERE datname = current_database() AND pid <> pg_backend_pid();
  ```
  (the last statement makes the app reconnect without the setting).
- **After step 8, until the window closes:** Vic restores the two aliases;
  undo the write stop as above. Forms saved on GCP in between are listed
  (administrations modified after the switch) and handled by hand.
- **After the window:** fix forward on GCP (decision 4).

## Afterwards

- Delete the AWS password secret and the `load-from-aws` job in the
  production project.
- Raise `HSTS_SECONDS` after a week without problems.
- Turn on the email jobs when the Brookes contact is confirmed.
- Staging: reload synthetic data or refresh its scrubbed copy from the
  production project.
- After the holding period: #689.
