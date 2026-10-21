# Migration rehearsal (#687)

Copy the AWS production database into GCP staging, run the GCP build against
it, and check that it behaves like production before cutover (#688). Web-CDI
data is Stanford Moderate Risk; `hs-langcog-webcdi` is approved for it. While
staging holds this copy it is **private** and sends **no email**.

The copy runs entirely in GCP (a one-off Cloud Run job streams `pg_dump` from
RDS into Cloud SQL); a laptop is only needed to start the steps and browse.

## 0. Prerequisite (Mike): the AWS prod database password

It lives in AWS Secrets Manager (`prod/webcdi/RDS_PASSWORD`, the `password`
field of its JSON), which the deploy user can't read. Copy it into GCP without
it appearing anywhere — the silent prompt keeps it out of history and adds no
trailing newline:

```bash
read -rs PW && printf %s "$PW" | gcloud secrets create webcdi-staging-aws-prod-db-password --data-file=- --project=hs-langcog-webcdi; unset PW
# paste the password at the (invisible) prompt, then Enter
```

The `webcdi-staging-` prefix lets the staging runtime account read it. Delete
the secret after the rehearsal (step 8).

## Refresh, as run on 2026-10-21 (≈15 minutes)

Staging is already private behind Google sign-in (#725) with email on the
console backend, so a refresh is:

1. **Re-copy the production DB password.** It rotates, so a stored copy goes
   stale (the copy then fails fast without touching staging). The deploy user
   can read it (inline policy `read-webcdi-rds-password`); pipe it straight
   across, never print it:
   ```bash
   AWS_PROFILE=webcdi aws secretsmanager get-secret-value --region us-west-2 --secret-id prod/webcdi/RDS_PASSWORD --query SecretString --output text \
     | python3 -c 'import sys,json; sys.stdout.write(json.loads(sys.stdin.read())["password"])' \
     | gcloud secrets versions add webcdi-staging-aws-prod-db-password --data-file=- --project=hs-langcog-webcdi
   ```
   then disable the previous version.
2. **Copy** (step 2 below): `gcloud run jobs execute webcdi-staging-load-from-aws --wait` — 85 s.
3. **Check before migrating**: no duplicate `InstrumentScore (instrument, title)`
   rows (the unique constraint's migration would fail).
4. **Scrub** with [`scrub_staging.py`](scrub_staging.py) (refuses to run outside
   Cloud SQL): blanks completion-flag and server-side redirect URLs, replaces
   gift codes. Run it via the migrate job's `shell -c`.
5. **Migrate** (`webcdi-staging-migrate`) — 25 s.
6. **Reload instruments** (`webcdi-staging-load-instruments`) — 21 s. Production's
   instrument data predates master's item fixes.
7. **Site row** → staging host (step 4 below).
8. **Full rescore**: `update_summary_data` via the migrate job with
   `--task-timeout=4h` — 11 min 40 s for 31,801 administrations.
9. **Checks**: valid percentile values, nothing completed-but-unscored, CAT
   theta non-zero, and a download sweep (each study's owner via the test
   client, inside a rolled-back transaction). Results: #687.
10. **QA accounts**: fresh test researchers (never real accounts), created
    from locally hashed passwords so plaintext never reaches job arguments.

For the production cutover (#688), steps 1, 2, 5, 6, 7 and 8 apply (no
scrub, no QA accounts), against the production database.

## 1. Make staging private and stop its email

```bash
cd deploy/terraform
tofu plan -var-file=staging.tfvars -var image=unused -var public=false \
  -var email_backend=django.core.mail.backends.console.EmailBackend -out=private.tfplan
tofu apply private.tfplan
```

Browse it through an authenticated local proxy:
`gcloud run services proxy webcdi-staging --region us-west1 --project hs-langcog-webcdi`
→ http://localhost:8080. **Don't merge to master during the rehearsal**: the
deploy's smoke test calls the public URL and would roll back.

## 2. Copy production into staging

```bash
P=hs-langcog-webcdi; R=us-west1
CONN=$(gcloud sql instances describe webcdi-staging-db --project $P --format='value(connectionName)')
gcloud run jobs create webcdi-staging-load-from-aws --project $P --region $R \
  --image docker.io/library/postgres:16 \
  --service-account webcdi-staging-run@$P.iam.gserviceaccount.com \
  --set-cloudsql-instances "$CONN" --task-timeout 2h --max-retries 0 \
  --set-env-vars "SRC_HOST=webcdiadmin.canyiscnpddk.us-west-2.rds.amazonaws.com,SRC_DB=webcdi-admin,SRC_USER=webcdi-admin,TGT_CONN=$CONN,TGT_DB=webcdi,TGT_USER=webcdi" \
  --set-secrets "SRC_PASSWORD=webcdi-staging-aws-prod-db-password:latest,TGT_PASSWORD=webcdi-staging-db-password:latest" \
  --command bash --args="^~^-c~$(cat deploy/rehearsal/load_from_aws.sh)"
gcloud run jobs execute webcdi-staging-load-from-aws --project $P --region $R --wait
```

The job logs source size and source→target row counts for the main tables;
they must match. (Tested against local databases: idempotent, counts match.)

## 3. Bring the schema up to the new code

```bash
gcloud run jobs execute webcdi-staging-migrate --project $P --region $R --wait
```

Expect few or no migrations (no model changes since the 2026-10-11 release).

## 4. Point the Sites row at staging

Production's Site 1 is `webcdi.org`; links in downloads use it. Set it to the
staging host with a one-off `shell -c` execution of the migrate job (see
`deploy/README.md`).

## 5. Checks

| Check | How | Pass if |
|---|---|---|
| Scoring equivalence | done 2026-10-19: legacy vs bulk scorer, 500 production administrations | 0 differences (the comparison tool was then retired with the #686 percentile rules) |
| Duplicate score titles | `InstrumentScore` rows grouped by (instrument, title) | none (then add the unique constraint, #675) |
| Full rescore | `update_summary_data` | completes in minutes; "<1" sex percentiles gone (#674) |
| Downloads | sweep: each instrument's newest group with completed forms × whole-group downloads, as its owner | 200, or a redirect with a message where a download doesn't apply (CAT scoring zip) |
| CAT | open a CAT administration per language via the proxy | renders, answers save, completes |
| Researcher flows | log in (your own account), group page, add administrations, downloads | work as on AWS |
| Restore drill | Cloud SQL point-in-time restore to a scratch instance | restores; delete it after |
| Timings | how long the copy took | sizes the cutover window |

## 6. Record

Write results on #687: counts, timings, differences found and how each was
resolved.

## 7. Afterwards

Either keep the real-data copy on private staging until cutover, or reload
synthetic data (`migrate` + `load-instruments` after re-running step 2 against
an empty source). Re-public staging only without real data:
`-var public=true` and the Postmark backend.

## 8. Clean up

```bash
gcloud run jobs delete webcdi-staging-load-from-aws --project $P --region $R --quiet
gcloud secrets delete webcdi-staging-aws-prod-db-password --project $P --quiet
```
