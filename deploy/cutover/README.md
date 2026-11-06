# Production cutover (#688)

Drafted with Claude Opus 5.5; not yet reviewed. **Status: draft.** Nothing in
the production environment exists yet. Each step below that creates or changes
something waits for Mike's go-ahead.

Moves webcdi.org from AWS Elastic Beanstalk to the GCP build, with the
production database copied across while writes are stopped. Rollback is
pointing DNS back at AWS, which stays running, untouched and read-only through
a holding period before decommissioning (#689).

## Decisions to make

| # | Question | Proposal |
|---|---|---|
| 1 | Where production lives | **Its own GCP project** (e.g. `hs-langcog-webcdi-prod`), requested from Stanford with the same Moderate Risk classification. The same OpenTofu config applies with a `production.tfvars`. Staging's deploy identity and runtime account then have no access to production at all, which a shared project can't give (several grants are project-wide: deploy, image push, Cloud SQL client). The first project took a day to provision. |
| 2 | How webcdi.org reaches Cloud Run | **Global HTTPS load balancer** with a Google-managed certificate issued through Certificate Manager DNS authorization. The certificate is ready *before* DNS moves, so the switch has no certificate gap, and Cloud Run can then refuse traffic that doesn't come through the load balancer. About $18 a month. (Cloud Run domain mapping is cheaper but a preview feature, and its certificate is only issued after DNS points at it.) |
| 3 | Email jobs (Brookes monthly report, renewal reminders) | **Off at cutover.** They haven't run on AWS since Nov 2024 (#695). Turn on once Virginia confirms the Brookes contact address. |
| 4 | Rollback cutoff | Roll back by DNS only until the window closes. After that, fix forward: rolling back later would strand forms completed on GCP. |
| 5 | Holding period before #689 | 30 days. |

## Production environment (to build)

Same shape as staging (`deploy/README.md`), differences only:

- `production.tfvars`: production project, `environment = "production"`,
  `allowed_hosts = ["webcdi.org","www.webcdi.org"]`, `PRIMARY_HOST=webcdi.org`
  (redirects www), `TRUSTED_ORIGINS`, `min_instances = 1` (no cold starts),
  a larger `db_tier` than staging's `db-g1-small`, Postmark backend,
  `enable_email_jobs = false` (decision 3).
- Load balancer, static IP, Certificate Manager certificate with DNS
  authorizations for `webcdi.org` and `www.webcdi.org`; Cloud Run ingress
  limited to the load balancer.
- Workload Identity provider that only accepts GitHub jobs running in the
  `production` environment (`assertion.environment == "production"`), which
  needs Mike's approval in GitHub.
- Deploy workflow: after the staging deploy succeeds, a `production` job waits
  for approval, promotes **the same image** (by digest) into the production
  registry, migrates, deploys, smoke-tests as `webcdi.org`, and routes traffic
  back if the smoke test fails.
- Alerts as on staging, to webcdi-contact@stanford.edu, plus an uptime check
  on `https://webcdi.org/health/`.
- Cloud SQL maintenance window in the lowest-traffic hour (see "Window").
- Budget alert on the project.

## Before the day

- [ ] Postmark account approved; a test message from staging reaches a
      stanford.edu address (it only delivers to @webcdi.org until approved).
- [ ] Production project provisioned; `tofu apply` from a reviewed saved plan
      built from current master.
- [ ] GitHub `production` environment with required reviewer; production
      variables set from `tofu output`.
- [ ] Certificate: Vic adds the two `_acme-challenge` CNAME records from
      `tofu output`; the certificate shows ACTIVE.
- [ ] Postmark production token in the production project's Secret Manager.
- [ ] AWS database password copied into the production project's Secret
      Manager (as for the rehearsal, never printed), and a `load-from-aws` job
      created there (`deploy/rehearsal/README.md` step 2, production names).
- [ ] **Dress rehearsal into the production database:** steps 2–6 of "On the
      day" without stopping writes or touching DNS. Proves the job,
      permissions and timings in the real environment. The real copy
      overwrites it.
- [ ] Browser test of production before DNS: map `webcdi.org` to the load
      balancer IP in your `/etc/hosts`, log in with your own account, open a
      group, a download, and a CAT form. Remove the line afterwards.
- [ ] Restore drill: point-in-time restore of the production database to a
      scratch instance; delete it after.
- [ ] Open items from the rehearsal: CAT forms through a browser in each
      language; the 2 completed CAT administrations with no theta.
- [ ] QA sign-off (Cherrie) and percentile sign-off (Virginia).
- [ ] Researchers told the date at least a week ahead (Virginia's email),
      including the Dutch group, who run their own server.
- [ ] Vic available in the window to change DNS; current alias targets of
      `webcdi.org` and `www.webcdi.org` written down for rollback.
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
instruments 21 s, rescore 804 s. Announce two hours; expect about one.

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
2. **Copy:** `gcloud run jobs execute webcdi-production-load-from-aws --wait`.
   Every row count in its log must match exactly (writes are stopped).
3. **Before migrating:** no duplicate `InstrumentScore (instrument, title)`
   rows; every instrument has a family.
4. **Migrate**, then **reload instruments** (`webcdi-production-migrate`,
   `webcdi-production-load-instruments`).
5. **Site row:** stays `webcdi.org`, as copied. Check it.
6. **Rescore:** `update_summary_data` through the migrate job with
   `--task-timeout=4h`. No completed administration left unscored.
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
