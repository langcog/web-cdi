# Web-CDI

_Updated with Claude Opus 5.5 (Nov 2026)._

[Web-CDI](https://webcdi.org) is a web platform for administering the
[MacArthur-Bates Communicative Development Inventories](https://mb-cdi.stanford.edu)
(CDI), parent-report checklists of children's early language, in many
languages, including computer-adaptive (CAT) versions. Researchers create
administration groups, send parents links, and download scored data.

## Using the system

Researchers can register at [webcdi.org](https://webcdi.org). Questions:
[webcdi-contact (at) stanford (dot) edu](mailto:webcdi-contact@stanford.edu).
The researcher manual is in the
[wiki](https://github.com/langcog/web-cdi/wiki/Researcher-Manual), and the
site's [changelog page](https://webcdi.org/changelog/) lists user-visible
changes.

## Documentation

| Topic | Where |
|---|---|
| Local development (Docker), tests, environment variables | [DEVELOPMENT.md](DEVELOPMENT.md) |
| Production and staging on Google Cloud: deploys, jobs, monitoring, infrastructure | [deploy/README.md](deploy/README.md) |
| The 2026 move from AWS to Google Cloud (runbook and record) | [deploy/cutover/README.md](deploy/cutover/README.md) |
| Adding instruments: pipeline, status, handoff | [instruments/README.md](instruments/README.md), [instruments/HANDOFF.md](instruments/HANDOFF.md) |
| Forms, background questionnaires, scoring and benchmark files | [wiki](https://github.com/langcog/web-cdi/wiki) |
| Orientation for Claude Code sessions (people, rules, history) | [.claude/skills/webcdi/](.claude/skills/webcdi/SKILL.md) |

Bugs and requests: [GitHub issues](https://github.com/langcog/web-cdi/issues).
