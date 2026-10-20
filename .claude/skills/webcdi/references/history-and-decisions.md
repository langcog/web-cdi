# History, standing decisions, open threads

## History in brief

- 2016–2018: built at Stanford (langcog); hosted at webcdi.stanford.edu, later
  webcdi.org. 2019–2026: Henry Mehta maintained it (Django upgrades, bespoke
  background forms, scoring/benchmarks, Brookes payments, CAT via R API,
  Dutch/Japanese/French CAT). His 2024–26 PRs mostly lack descriptions.
- 2026 modernization (Mike + Claude, PRs #617–#661, consolidated by Henry into
  `phases1to11`, merged to master as #664 and deployed **2026-10-11**):
  dev docs + `.env.example`; mobile viewport; facelift (design-token theme,
  About/Documentation pages, dashboard cards); jsCat in-browser CAT behind
  `CAT_ENGINE`; security fixes (clinical-PDF exposure, SECRET_KEY from env);
  CKEditor → Markdown, jQuery 1.11 → 3.7; hermetic CAT tests; regression
  tests; GitHub Actions CI; group-page redesign; form headers aligned to
  3rd-edition print; citations by instrument; logout POST fix.
- The stacked PRs #617–#661 still show "open" but their content is in master —
  close them rather than merge.
- 2026-10: Henry steps back; Mike's team owns development. New-instruments
  campaign underway (`references/instruments-and-forms.md`).
- 2026-10-15 onward: GCP rebuild (#690) — container, OpenTofu, CI/CD with
  keyless deploys, monitoring, jsCat-only CAT, bulk scorer, security fixes,
  Postmark email; AWS frozen. Migration rehearsal on a scrubbed copy of
  production (#687). Roadmap: `references/roadmap.md`.

## Standing decisions (don't relitigate without Mike)

- Form section headers follow the 3rd-edition printed forms; **instruction
  text stays as-is** (web version deliberately richer — Virginia).
- Word "boxes" on WG/WS forms are deliberate.
- Citations: Web-CDI → deMayo et al. 2021; CDIs in general → Marchman, Dale &
  Fenson 2023 manual; per-instrument references by language in
  `webcdi/templates/webcdi/_instrument_citations.html` (About + Documentation,
  `#instrument-citations`). Citation content comes from Virginia.
- Rich text (waiver, end message) = Markdown + bleach, not CKEditor.
- Group page vocabulary: "Add administrations", "Group settings" (holds the
  rare delete-group danger zone), one scoped "Download ▾", status badge.
- Dashboard "Get started" card: everyone sees it; expanded when the user has
  no groups, collapsed otherwise.
- Bug fixes in item text: fix `definition`/`gloss`; never rename `item`
  (export column names).
- Merges to master deploy to GCP staging automatically; Selenium is nightly
  and non-blocking. AWS production is frozen (no deploys without Mike).
- Percentiles follow Virginia's rules (#686, implemented #727; see
  `scoring-and-cat.md`) — change them only with her.
- Subject IDs are integers; zero-padded IDs are rejected at entry (#718).
- Staging with real data is private (Google sign-in) and scrubbed; QA testers
  get fresh test accounts.

## Known bugs and debts (as of 2026-10-20)

- Pre-QA backlog with scopes: `references/roadmap.md`.
- **Code health (after cutover):** Bootstrap 3+4 mix (#633), D3 v3 graphs
  (#634), console dispatch refactor (#636), migration squash (#637), lint
  config, two diverged instruments.json copies.
- `test_populate_items` errors under `--parallel` but passes alone.
- Long-standing feature requests carry the `feature` label (e.g. #449 group
  studies semantics, #321 Canadian norms, #491 Spanish short-form scoring,
  #290 currency in Spanish forms, #148 download filters, #122/#107 bilingual
  and cross-study linkage, #102 Danish, #408 completion emails, #401
  citation policy).
- French CAT rarely records sex (1,083 of 1,138 completed administrations have
  it blank), so its sex percentiles are mostly "not computed".

## Waiting on others

- Postmark account approval (pending since 2026-10-16).
- DNS access for webcdi.org (cutover).
- Virginia: French (France) CAT citation
  (public "forthcoming" placeholder), Japanese (in review), Korean (Pae 2003?).
- Native speakers: Korean, Hebrew, Quebec French item checks (PR #666).
- Hindi developers: Word version of the Hindi WS.
