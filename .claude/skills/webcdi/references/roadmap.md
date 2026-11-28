# Roadmap after the cutover (as of 2026-11-28)

The move to Google Cloud is done (2026-11-19). What's left is collected in
**#810**; check `gh issue list` / `gh pr list` for current state.

## Open, by what they wait on

| Item | Waiting on |
|---|---|
| Delete the AWS password secret and `load-from-aws` job in the production project | Mike's OK |
| Staging: reload synthetic data, or a fresh scrubbed copy of production | Mike's choice |
| Account cleanup: about 5,300 accounts never created a group (#722) — mark inactive, never delete | Mike's OK on the criteria |
| #802: groups with no background form get the built-in US form; mixed currency codes in income answers | decision (Mike / Virginia) |
| Raise `HSTS_SECONDS` | a week without HTTPS problems (from about 2026-11-26) |
| Budget alert on the production project | billing-account access |
| Email jobs (Brookes monthly report, renewal reminders) | Virginia confirming the Brookes contact |
| Japanese CAT item labels and background form translations | a native speaker |
| AWS decommissioning (#689), then retire the Postmark stanford.edu sender signature | from about 2026-12-19; final export archived first (#671) |
| Security baseline leftovers (#683): collaborator review, jscat lockfile, #449 | — |

**Deferred code health** (start only when asked): #633 Bootstrap, #634 D3,
#636 console refactor, #637 migration squash, #632 committed static files,
#722 part 2, and feature requests (label `feature`). The new-instruments
campaign has its own plan in `instruments/STATUS.md`.

## Rules for any session working issues

- Branch from `origin/master`; one issue per PR; PR body says what changed,
  why, and how it was verified; end with the Claude Code attribution line.
- Bug fix ⇒ a test that fails before and passes after. Run the relevant
  tests and say which.
- Never commit secrets, `forms/` PDFs, `.env`, or `*.local.tfvars`; the repo
  is public. Describe security problems neutrally.
- Every merge to master goes to production after approval. Merge one PR at a
  time, after CI passes; the approver (Mike or mikabr) decides when it ships.
- Data migrations: scoped as narrowly as possible, with a count of affected
  production rows in the PR (from a one-off job; aggregates only).
- Don't touch AWS.
