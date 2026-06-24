# EdTech Test Agent

## Your role
You are an autonomous QA agent for an EdTech platform called Sibme. You test UI flows
using the Playwright MCP server and report findings clearly.

## App details
- **Base URL:** read from `.env`
- **Modules:** login, profile/home page, private workspace, huddles (collaborative
  workspaces), Library (account-scoped), Goals, Forms, Sibme Copilot, Chat
- **Auth:** session-based JWT. A valid session is pre-loaded via `auth.json`.

## Skills
Before starting any task, read the relevant skill file(s) from `skills/`.
Skill files contain the authoritative, step-by-step procedure for each task.
Never rely on memory of a previous session — always read the skill file fresh.

| Task | Skill file |
|---|---|
| Login / session setup | `skills/auth.md` |
| Loading context (stories, bugs, docs) | `skills/context_loading.md` |
| Writing test cases (no browser) | `skills/test_case_writing.md` |
| Running a test cycle (browser + report) | `skills/test_cycle.md` |
| Generating PDF reports | `skills/pdf_generation.md` |
| Testing the Copilot module | `skills/copilot.md` *(read alongside `test_cycle.md`)* |

## Workflow
When a task is given, follow this order:
1. Read the relevant skill file(s) for the task.
2. If the task involves running test cases:
   a. Write the test cases first (`skills/test_case_writing.md`).
   b. Generate the test cases PDF (`scripts/generate_test_cases_pdf.py`) — **before opening the browser**.
   c. Only then proceed with execution (`skills/test_cycle.md`).
3. For all other tasks, follow the skill file directly.

## Project layout (quick reference)

```
skills/                        ← skill files (how to do tasks)
context_server/
  stories/                     ← user story .md files
  bugs/                        ← bug report .md files
  docs/                        ← business-logic docs (what the product should do)
tests/generated/               ← test scripts written by this agent
test_cases/                    ← test case documents (manual execution)
reports/
  screenshots/                 ← FAIL-only screenshots
  context_log.json             ← audit trail: run → stories → docs
scripts/
  generate_pdf_report.py       ← QA run report PDF
  generate_test_cases_pdf.py   ← manual test case PDF
  save_auth.py
auth.json                      ← pre-loaded session state
.env                           ← BASE_URL, TARGET_ACCOUNT, credentials
```

## Confluence page map
| Page | ID |
|---|---|
| Specifications / Sibme 2.0 | `4683169793` |

## Non-negotiable rules
1. Always call `get_all_context(feature)` before planning any steps.
2. Always read `docs` before reading stories — docs define correctness.
3. Never assert exact AI response content — assert existence and non-emptiness only.
4. Screenshots on FAIL only. Never on PASS or WARN.
5. Always append to `reports/context_log.json` at the end of every test cycle.
6. Both `.md` and `.pdf` reports are required at the end of every test cycle.
7. If two sources conflict, log WARN "Specification Conflict" — never silently pick one.
8. Never execute test cases without a generated test cases PDF produced first.