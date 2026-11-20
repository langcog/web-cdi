# New-instruments campaign: status

> Drafted with Claude Opus 5.5 from the campaign's working sessions (Oct–Nov 2026). Not yet reviewed by the team.

This page is the single record of where each instrument stands and what has
been decided. Update it in the same PR as the work it describes. Discussion
happens in Slack #cdi-team; when something is decided there, copy the
decision here with its date.

## Status by instrument

Stages: **sourced** (files in the Drive folder) → **extracted** (package in
`packages/`) → **validated** (checks + LLM QA pass) → **reviewed** (native
speaker + Advisory Board sign-off, recorded in the manifest) → **published**
(copied into `webcdi/`, PR merged, on staging) → **live**.

| Instrument | Stage | Next step | Notes |
|---|---|---|---|
| English (New Zealand) short form | extracted, validated | publish into `webcdi/` and test end to end | US L2A + 6 NZ substitutions; reuses L2A itemIDs; 16–30 mo |
| Turkish WG/WS (TİGE-I/II) | sourced | extract (PDF) | clean text layer; Wordbank has both (418/711 words) |
| Swedish WG/WS/CDI-III | sourced | extract (PDF) | clean text layer; Wordbank has WG/WS (385/710 vs forms' 382/711); CC BY-NC-ND |
| Serbian WG/WS, Ekavian + Ijekavian | sourced | extract (PDF) | clean Latin text; not in Wordbank; dialects differ in some items |
| English (Australian) | sourced | assess | long form as an xlsx item table + short form in a paper supplement; Wordbank has the WS long form |
| Hindi WS | blocked | wait for a Word version | PDF uses a pre-Unicode font; Virginia has asked the developers |
| Arabic, Cantonese (WS), Mandarin | not ready | — | still collecting forms (see the Drive folder names) |

## Decisions

- **2026-10-09 (Virginia, Mike):** Serbian forms are final; ignore "pilot".
  Turkish: adapt as standalone parent-report WG/WS and drop the stopping
  rules. Swedish: the existing permission covers web adaptation. Hindi waits
  for a Word version.
- **2026-10-12 (#cdi-team):** host the **NZ English short form only**, age
  range 16–30 months. The other NZ lists (Te Reo Māori, Cantonese, Mandarin
  simplified/traditional, Samoan, Tongan) are dropped. Their extraction, QA
  flags and documented corrections are kept out of this public repo (no
  recorded permission to publish them); Mike has them on a local branch if
  Mandarin/Cantonese short forms are revisited. MB8 may instead use the
  Texas team's forthcoming forms (needed Feb/Mar 2027).
  Note: only the Te Reo list was a translation of NZ English; the others
  were language-specific lists.
- **2026-10-12:** typo fixes to live instruments confirmed by Virginia and
  merged (#666): US short forms (show→shoe, raisin→rain), Argentine Spanish
  (adiós), Dutch (fruitsap, pistolet, sleutel). Item code names (export
  column headers) were deliberately left unchanged.
- **LLM QA (2026-10):** run both Gemini models and give reviewers the union of
  flags. On 141 injected faults in five live instruments, gemini-3.8-flash
  caught 135 and gemini-3.1-pro-preview 136, but Pro found about twice as
  many real errors already in the live forms (`calibration/`). Flags are
  advisory; nothing changes without a person.

## Open questions

- **NZ English background questionnaire:** the US one asks for zip codes and
  US race categories. Use the existing "no demographics" variant, or build an
  NZ version? (Raised in #cdi-team 2026-10-12, unanswered.)
- **NZ English export column names:** items are currently named `word_1`…
  `word_100`; reusing the US L2A code names (`baa_baa`…) would make the two
  forms' downloads line up. Decide before publishing.
- **Live typos awaiting a native speaker:** Korean WS 떄려→때려, 뺴앗아→빼앗아;
  Hebrew WS קלמטינה→קלמנטינה, עיין→עין; Quebec French WS "pinnote"→"pinotte".
  The calibration also found English-gloss errors in Dutch WS and a misspelled
  itemID (`itme_445`); see `calibration/*_untouched_flags.csv`.
- **Interface language for new languages:** each new UI language means about
  400 interface strings plus a background questionnaire (see
  `.claude/skills/webcdi/references/instruments-and-forms.md`). Decide per
  language whether to translate fully; MB8's tracker lists proofreaders.
