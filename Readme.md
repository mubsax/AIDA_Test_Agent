# AIDA (AI Driven Autonomous) Test Agent

An autonomous QA agent for web platforms. AIDA uses Claude as its reasoning
engine, a custom Context MCP server as its knowledge base, and the Playwright MCP
server as its browser — writing test cases, executing them, and producing PDF
reports with full story-level traceability.

---

## How it works

```
Task arrives
     │
     ▼
Context MCP Server ──► get_all_context(feature)
                        stories + bugs + docs + Confluence
                        agent knows WHAT correct behaviour looks like
     │
     ▼
Agent writes test cases → generates test cases PDF
     │
     ▼
Playwright MCP Server ──► drives browser, executes each step
                           observes actual UI behaviour
     │
     ▼
Agent writes MD + PDF report
(actual behaviour vs expected behaviour from context)
```

The Context server answers *"what should the app do?"*
The Playwright server answers *"what is the app actually doing?"*
The report is the diff between the two.

---

## Project structure

```
AIDA Test Agent/
├── skills/                          # How-to skill files (agent reads before each task)
│   ├── auth.md                      # Login and session management
│   ├── context_loading.md           # How to load stories, bugs, docs
│   ├── test_case_writing.md         # How to write and document test cases
│   ├── test_cycle.md                # How to execute a test cycle in the browser
│   ├── pdf_generation.md            # How to generate both types of PDF
│   └── copilot.md                   # Special rules for testing non-deterministic modules
│
├── context_server/                  # Custom MCP server — project knowledge base
│   ├── server.py                    # MCP server entry point
│   ├── stories/                     # User story .md files (acceptance criteria)
│   ├── bugs/                        # Bug report .md files
│   └── docs/                        # Business-logic docs (rules, constraints, domain knowledge)
│
├── scripts/
│   ├── generate_pdf_report.py       # Generates automated test cycle report PDF
│   ├── generate_test_cases_pdf.py   # Generates manual test case tracking PDF
│   └── save_auth.py                 # Performs login and saves session to auth.json
│
├── tests/
│   └── generated/                   # Test scripts written by the agent
│
├── test_cases/                      # Test case .md files + generated PDFs
│
├── reports/
│   ├── screenshots/                 # FAIL-only screenshots (<feature>_<storyID>_step_<n>.png)
│   ├── context_log.json             # Audit trail: run → stories → docs → files
│   ├── <feature>_report.md          # Markdown report per test cycle
│   └── <feature>_report.pdf         # PDF report per test cycle
│
├── .playwright-mcp/                 # Playwright MCP server config
├── auth.json                        # Pre-loaded session state (do not commit)
├── .env                             # Environment variables (do not commit)
├── .env.example                     # Environment variable template
├── CLAUDE.md                        # Agent instructions and project map
└── .mcp.json                        # MCP server registry
```

---

## MCP servers

### Playwright MCP Server
Controls a real browser on behalf of the agent. Used to:
- Navigate to pages and wait for redirects
- Locate elements via accessibility tree snapshots (`getByRole`)
- Click, type, and interact with the UI
- Take screenshots on test failures

### Context MCP Server (`context_server/server.py`)
The project's knowledge base. Exposes five tools:

| Tool | Returns |
|---|---|
| `get_all_context(feature)` | Stories + bugs + docs + optional Confluence page |
| `get_user_stories()` | All story files (feature-agnostic) |
| `get_bug_reports()` | All bug report files (feature-agnostic) |
| `get_docs(feature)` | Business-logic docs filtered by feature name |
| `get_confluence_page(page_id)` | Live Confluence page fetched via Atlassian REST API |

---

## Setup

### Prerequisites
- Python 3.13+
- Node.js (for Playwright MCP)
- A valid account on the target platform
- Confluence API token (optional — only needed for live spec fetching)

### Installation

```bash
# Clone the repo
git clone <repo-url>
cd aida-test-agent

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright MCP
npm install
```

### Environment variables

Copy `.env.example` to `.env` and fill in your values:

```env
BASE_URL=https://your-app-url.com
TARGET_ACCOUNT=<your account name>
CONFLUENCE_EMAIL=<your atlassian email>
CONFLUENCE_API_TOKEN=<your confluence API token>
```

### Authentication

On first run (or when `auth.json` is missing or expired):

```bash
python scripts/save_auth.py
```

This performs the full login flow and writes a fresh `auth.json`.
Subsequent runs load the saved session automatically — no manual login needed.

---

## Usage

Open the project in your AI editor with the MCP servers active, then give the
agent a task in natural language:

```
Run a test cycle for the <feature> feature.
```

```
Write test cases for the <feature> module.
```

The agent follows this workflow automatically:
1. Reads the relevant skill file(s) for the task
2. Loads context via the Context MCP server
3. Writes test cases and generates the test cases PDF
4. Executes in the browser via Playwright MCP
5. Writes a Markdown + PDF report
6. Appends to `reports/context_log.json`

---

## Knowledge base

The knowledge base lives in `context_server/` and has three layers.
All files are plain Markdown, scoped by feature name.

### Stories (`context_server/stories/`)
Capture acceptance criteria and user flows, tagged with story IDs.

```markdown
# <STORY-ID> — <Story title>

## Acceptance criteria
- ...
- ...
```

### Bugs (`context_server/bugs/`)
Capture known defects with reproduction steps and expected vs actual behaviour.

```markdown
# <BUG-ID> — <Bug title>

## Steps to reproduce
1. ...

## Expected
...

## Actual
...
```

### Docs (`context_server/docs/`)
Capture business rules, constraints, and domain knowledge that are neither
a story nor a bug. One file per feature.

```markdown
# <Feature> — Business Logic

- feature: <feature>
- last_updated: YYYY-MM-DD

## Rules
- ...
- ...
```

---

## Confluence integration

Spec pages are fetched live from Atlassian during `get_all_context()`.
Page IDs are maintained in `CLAUDE.md` under the Confluence page map —
update them there if pages change.

```python
get_all_context("<feature>", confluence_page_id="<page_id>")
```

---

## Reports and traceability

Every test cycle produces the following outputs:

| Output | Location |
|---|---|
| Test case document | `test_cases/<feature>.md` |
| Test case PDF (manual tracking) | `test_cases/<feature>_test_cases.pdf` |
| Execution report (Markdown) | `reports/<feature>_report.md` |
| Execution report (PDF) | `reports/<feature>_report.pdf` |
| FAIL screenshots | `reports/screenshots/<feature>_<storyID>_step_<n>.png` |
| Audit log entry | `reports/context_log.json` |

`context_log.json` links every run to the stories, docs, and files involved:

```json
{
  "run_id": "YYYY-MM-DD-NNN",
  "feature": "<feature>",
  "stories_covered": ["<STORY-ID>"],
  "docs_referenced": ["<feature>.md"],
  "bugs_covered": ["<BUG-ID>"],
  "test_file": "tests/generated/<feature>.py",
  "report_md": "reports/<feature>_report.md",
  "report_pdf": "reports/<feature>_report.pdf"
}
```

---

## Agent rules (non-negotiable)

1. `get_all_context(feature)` is always called before planning any steps
2. `docs` are read before stories — docs define correctness
3. AI module responses: assert existence only, never exact content
4. Screenshots on FAIL steps only — never on PASS or WARN
5. `context_log.json` is appended after every test cycle
6. Both `.md` and `.pdf` reports are produced after every test cycle
7. Source conflicts are logged as WARN "Specification Conflict" — never silently resolved
8. Test cases PDF is always generated before browser execution begins