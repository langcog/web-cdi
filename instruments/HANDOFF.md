# Handoff: adding new CDI instruments to Web-CDI (November 2026)

> Drafted with Claude Opus 5.5 for Mike Frank, from the October 2026 working sessions. Not yet reviewed by the team.

**Bottom line:** the tooling is built and calibrated, and one instrument (the
New Zealand English short form) is extracted and checked but not yet on the
site. The work paused in October while Web-CDI moved from AWS to Google
Cloud. Your job is to take instruments from the Drive folder to the live site,
one at a time, with a paper trail a reviewer can check.

## Background

The ManyBabies 8 (MB8) study and the CDI Advisory Board want more languages on
Web-CDI. Virginia Marchman collects the source forms (PDFs and item lists) in
the Drive folder "Web-CDI Updates 2026"; the "Ready to go" subfolder holds the
languages with complete materials. Each form has to become a web form that
matches the printed one, with errors fixed and every change traceable.

## Where things stand

See [STATUS.md](STATUS.md) for the table. In short:
- **NZ English short form:** extracted and validated; next it needs publishing
  into the app and an end-to-end test. Two small decisions first (background
  questionnaire, export column names; see STATUS.md "Open questions").
- **Turkish, Swedish, Serbian:** sources are clean PDFs; not yet extracted.
  Turkish and Swedish can be checked item by item against Wordbank.
- **Australian English:** newly in "Ready to go"; not yet assessed.
- **Hindi:** waiting on a Word version from its developers.

Along the way, the QA checks found real typos in forms already live, and
those fixes are merged (#666). A few more are waiting on native speakers.

## People

- **Mike Frank** — PI; reviews and merges pull requests.
- **Virginia Marchman** — CDI Advisory Board; decides on content, wording,
  permissions and citations. Ask her about anything in a form.
- **Henry Mehta** — Web-CDI's developer.
- **Alvin Tan** — Wordbank data imports.
- Discussion happens in Slack **#cdi-team**.

## Access you need (ask Mike unless noted)

1. Write access to the GitHub repo `langcog/web-cdi`.
2. The Drive folder "Web-CDI Updates 2026" (Virginia). Download it as a zip and
   unpack it into `forms/` in your checkout. This folder is never committed:
   the forms are licensed.
3. The **Vertex AI User** role on Google Cloud project `hs-hs-langcog-gemini`
   (for the Gemini QA checks), then run `gcloud auth application-default login`.
4. Staging access with your Stanford Google account (Mike adds you), so you
   can check forms on the staging site after they merge.
5. A local copy of Web-CDI running in Docker: follow `DEVELOPMENT.md`.

## How the work goes

[README.md](README.md) describes the pipeline. For each instrument:
extract → validate → LLM QA → native-speaker and Advisory Board review →
publish into the app → test → pull request → staging. One instrument per pull
request. Record decisions in STATUS.md in the same pull request, with the
date and who decided.

Ground rules:
- Never commit anything from `forms/`, or contact details from the MB8 tracker
  spreadsheet. The repo is public.
- LLM flags are suggestions. A person (a native speaker, then Virginia)
  decides; corrections go in the manifest with a reason.
- Fix display typos in the `definition` column, never the `item` column: the
  `item` names are column headers in researchers' downloads.

## Working with Claude

Claude Code loads the project's orientation (`.claude/skills/webcdi/`)
automatically. Use a **local** session for anything that runs the Gemini QA
or touches Google Cloud; cloud sessions have no credentials. A good first
prompt:

> I'm Cherrie, taking over the Web-CDI new-instruments campaign. Read
> `instruments/STATUS.md`, `instruments/README.md` and
> `.claude/skills/webcdi/references/instruments-and-forms.md`, check that
> `forms/Web-CDI Updates 2026/` is present, and run the validator on the NZ
> English package to confirm the tools work. Then summarize what's next and
> the open questions I should take to #cdi-team before publishing NZ English.
> Don't push or open pull requests without asking me.
