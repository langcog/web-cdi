# Roadmap to cutover (as of 2026-10-20)

Agreed with Mike. Check `gh issue list` / `gh pr list` for current state.

1. **Pre-QA backlog** — done (below).
2. **Refresh the rehearsal** — done 2026-10-21 (#687; ~15 min end to end;
   checklist in `deploy/rehearsal/README.md`). Restore drill still to do.
3. **Full QA** by a naive lab member following the QA guide (a claude.ai
   artifact, results saved per tester; test accounts `qa-tester-1..3` on
   staging, credentials with Mike); Virginia signs off on percentiles.
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

## Pre-QA backlog — done (2026-10-21)

Merged: #723 (#744), #739 (#745), #741 (#746), #640 (#747), #722 part 1 (#748),
#635 (#749), #685 (#750), #648 (#754), #726 (#736), #675 (#737), plus the
download correctness fixes from the backlog run (#755 #759, #756 #761, #757
#762, #758 #760, summary-text #763) and scoring robustness (#742). Rehearsal
refreshed with all of it (#687). Open decisions and small items: #764.

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
