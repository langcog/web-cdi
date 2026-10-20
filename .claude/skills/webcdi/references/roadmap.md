# Roadmap to cutover (as of 2026-10-20)

Agreed with Mike. Check `gh issue list` / `gh pr list` for current state.

1. **Pre-QA backlog** (below) — fix, test, merge; each merge deploys to
   private staging automatically.
2. **Refresh the rehearsal** (#687, `deploy/rehearsal/`): fresh copy of AWS
   production, scrub, migrate, full rescore (`update_summary_data`), timed;
   downloads per instrument, CAT per language, restore drill.
3. **Full QA** by a naive lab member following a written QA guide (researcher
   and parent flows), with a results checklist; Virginia signs off on
   percentiles.
4. **GCP production environment** (can proceed in parallel): prod tfvars /
   service / DB / secrets, deletion protection, GitHub environment approval for
   prod deploys, webcdi.org domain mapping + certificate (needs DNS access),
   Postmark live, cutover + rollback runbook.
5. **Cutover** (#688): announce a window, freeze AWS, final copy (~2 min),
   migrate, rescore (minutes), switch DNS, verify; rollback = DNS back to AWS.
6. **Decommission AWS** (#689) after a holding period.

Before cutover, decide with Mike/Virginia how to tell researchers that
percentiles changed (#727: coarse tables up ~2 points on average, "not
computed" for non-M/F sex percentiles, CAT summaries corrected).

## Pre-QA backlog (do these; one issue per PR)

| Issue | Scope |
|---|---|
| #723 | Completion notices: send only on the transition to completed; persist pending retries (e.g. a field swept by the scheduled scoring job) instead of `threading.Timer`. Keep behaviour for the 8 studies that use it; test with mocked `requests.post`. |
| #726 | CAT download (`cat_utils.get_pd_norms`) adjusts age only when `born_on_due_date` is true — check how the field is stored for early/late children, then adjust on `early_or_late` like the scorer and CAT report. |
| #675 | Unique constraint on `InstrumentScore (instrument, title)`. The rehearsal copy has no duplicates (verified 2026-10-19). Migration + test. |
| #630 | Anonymous AJAX endpoints 500 on missing params → 400/redirect. |
| #640 | `/api` StudyAPI export crashes on pandas 3 (`to_json` duplicate index); currently `known_failure`. |
| #722 (part 1 only) | Login with username **or** email (case-insensitive); if an email matches several accounts, ask for the username. Unique email (case-insensitive) on new registrations. **Do not** delete or deactivate existing accounts (part 2 needs Mike's sign-off on a list). |
| #685 | `load_instruments` takes ~19 min; make it faster without changing results. |
| #682 | Log retention for the GCP project (infra code; `tofu apply` is Mike's). |
| #648 | Refresh Selenium locators for the redesigned console. |
| #632, #635 | Stop committing collectstatic output; delete dead `registration/` and `supplementtut/` apps. |

**Deferred until after cutover** (don't start): #633 Bootstrap, #634 D3,
#636 console refactor, #637 migration squash, #722 part 2, feature requests
(label `feature`).

## Rules for any session working the backlog

- Branch from `origin/master`; one issue per PR; PR body says what changed,
  why, and how it was verified; end with the Claude Code attribution line.
- Bug fix ⇒ a test that fails before and passes after (show it). Run the
  relevant tests and say which.
- Never commit secrets, `forms/` PDFs, `.env`, or `*.local.tfvars`; the repo
  is public. Describe security problems neutrally.
- Don't merge; Mike's primary session reviews and merges. Don't touch AWS.
- Data migrations: reversible, scoped as narrowly as possible, and with a
  count of affected rows from the rehearsal copy noted in the PR (ask the
  primary session to run it — cloud sessions can't reach GCP).
