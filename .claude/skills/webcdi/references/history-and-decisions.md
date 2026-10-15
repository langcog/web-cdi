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
- CI-now, CD-later; Selenium nightly and non-blocking.
- Interpolated vs floor percentiles: floor since #652 (Aug 2026) — confirm with
  Virginia before changing either way.

## Known bugs and debts (as of 2026-10-15)

- **Downloads:** pandas-3 silent no-ops (blank count scores not zeroed;
  `[]` left in `child_ethnicity`/`other_languages`); empty-selection 500;
  #649 CDI-format crash; #640 API export crash. A prod download 500 reported
  2026-10-14 was diagnosed by Henry — confirm the fix landed in master.
- **Scoring:** no value-level tests; slow full rescoring (days); see
  `scoring-and-cat.md`.
- **Ops:** cron `MAILTO`/`ADMINS` point at Henry (#638); cron calls
  nonexistent `monthly_report`/`weekly_reminder`; 7-day log retention.
- **Code health:** Bootstrap 3+4 mix (#633), D3 v3 graphs (#634), collectstatic
  output committed (#632), dead `registration/` + `supplementtut/` apps
  (#635), action-dispatch refactor (#636), migration squash (#637), stale
  Selenium locators (#648), lint config, two diverged instruments.json copies,
  the R CAT API still in production (#528).
- Long-standing feature requests: #449 group studies, #321 Canadian norms,
  #491 Spanish short-form scoring, #290 currency in Spanish forms, #148 more
  download options, #122/#107 bilingual and cross-study linkage, #102 Danish.

## Waiting on others

- Virginia: golden-case scoring examples; French (France) CAT citation
  (public "forthcoming" placeholder), Japanese (in review), Korean (Pae 2003?).
- Native speakers: Korean, Hebrew, Quebec French item checks (PR #666).
- Hindi developers: Word version of the Hindi WS.
