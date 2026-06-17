# AI Test Agent

An autonomous browser-based UI testing agent powered by **Claude Code** and **Playwright MCP**. Feed it user stories or bug reports — from local files or a live Confluence page — and it plans, executes, and reports end-to-end UI tests without human intervention.

---

## What it does

Most test automation tools require you to write the tests. This agent writes them, runs them, and tells you what broke — by reading your requirements the same way a QA engineer would.

The agent:

1. **Reads context** — user stories, bug reports, and optionally a live Confluence page, via a custom MCP context server
2. **Plans test steps** — derives acceptance criteria and maps them to browser actions
3. **Drives a real browser** — navigates, clicks, fills forms, and asserts outcomes using the Playwright MCP server
4. **Handles auth** — reuses a saved session so it doesn't log in on every run
5. **Reports findings** — writes a plain-English markdown report with pass/fail per step and screenshots on failure
6. **Generates test files** — produces reusable Playwright Python test files from each run

---

## Architecture

```
┌─────────────────────────────────────┐
│         Claude Code (agent)         │  ← reasons, plans, iterates
└────────────┬────────────────────────┘
             │
     ┌───────┴────────┐
     │                │
┌────▼─────┐    ┌─────▼──────────┐
│ Context  │    │  Playwright    │
│  MCP     │    │  MCP server    │
│ server   │    │                │
└────┬─────┘    └─────┬──────────┘
     │                │
     │         ┌──────▼──────────┐
     │         │  auth.json      │  ← saved session/tokens
     │         └──────┬──────────┘
     │                │
     └────────►───────▼──────────┐
                  App under test  │
              └───────────────────┘
                       │
               ┌───────▼────────┐
               │  Test report   │  ← markdown + screenshots
               └────────────────┘
```

**Context MCP server** — a lightweight Python MCP server you run locally. It exposes tools that return user stories, bug reports, and optionally Confluence page content to the agent. Confluence is fully optional — the server works fine with just local files.

**Playwright MCP server** — the official `@playwright/mcp` server. Gives the agent real browser control: navigate, snapshot the accessibility tree, click, type, assert.

**CLAUDE.md** — the agent's standing instructions. Defines the app's URL structure, auth behaviour, async/non-deterministic areas, and report format. The agent reads this at the start of every session.

---

## How context works

Context can come from three sources, mixed and matched:

| Source | How |
|---|---|
| Local user stories | `.md` files in `context_server/stories/` |
| Local bug reports | `.md` files in `context_server/bugs/` |
| Confluence page | Fetched live via REST API (optional — skipped gracefully if no token) |

The context server merges all available sources and returns a single unified object to the agent. If Confluence is unavailable, the agent proceeds with whatever local context exists.

---

## Project structure

```
your-project/
├── .mcp.json                    ← MCP server definitions (commit to git)
├── CLAUDE.md                    ← Agent standing instructions
├── auth.json                    ← Saved browser session (gitignore this)
├── context_server/
│   ├── server.py                ← Custom context MCP server
│   ├── stories/                 ← User stories as .md files
│   └── bugs/                    ← Bug reports as .md files
├── scripts/
│   └── save_auth.py             ← One-time script to save login session
├── tests/
│   └── generated/               ← Agent-generated Playwright test files
└── reports/                     ← Test run reports and screenshots
```

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- Claude Code CLI (`npm install -g @anthropic-ai/claude-code`)
- A Claude Code subscription

### Install dependencies

```bash
pip install playwright pytest-playwright mcp requests
npx playwright install --with-deps
```

### Configure MCP servers

Create `.mcp.json` at the project root:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "-y",
        "@playwright/mcp@latest",
        "--browser=chromium",
        "--viewport-size=1440,900",
        "--storage-state=auth.json",
        "--allowed-origins=https://your-app.com"
      ]
    },
    "context": {
      "command": "python",
      "args": ["context_server/server.py"]
    }
  }
}
```

### Save a login session

If your app requires authentication, run this once to capture the session:

```bash
python scripts/save_auth.py
```

This logs in with a test account and saves the full browser state (cookies, localStorage, tokens) to `auth.json`. The Playwright MCP server reloads this on every run so the agent never has to log in manually.

Regenerate `auth.json` whenever the session expires. Add it to `.gitignore`.

### Write your first user story

Create a file in `context_server/stories/`:

```markdown
# Story: User login

As a user, I want to log in with my email and password
so that I can access my account dashboard.

## Acceptance criteria
- Valid credentials redirect to /dashboard
- Dashboard shows the user's name
- Invalid credentials show an error message
- The login button is disabled while the request is in flight
```

### Run the agent

```bash
claude
```

Then give it a task:

```
Fetch context for the "login" feature, test it against 
https://your-app.com, and write a report to reports/login_report.md
```

---

## Running without the context server

For quick one-off tests, paste the story directly into the Claude Code prompt — no server needed:

```
Here is a user story to test:

As a user, I want to reset my password via email link.

Acceptance criteria:
- Submitting the reset form shows a confirmation message
- An invalid email shows a validation error

Test this against https://your-app.com and write a report to reports/password_reset_report.md
```

---

## Confluence integration (optional)

Set environment variables:

```bash
export CONFLUENCE_EMAIL=you@yourorg.com
export CONFLUENCE_API_TOKEN=your_token_here
```

Then include a page ID when calling the context tool:

```
Fetch context for "onboarding" using Confluence page 123456789 and run the tests.
```

If the token is missing or the call fails, the server falls back to local files silently. The agent's report will note which context sources were used.

---

## CI / CD

The agent runs headlessly in pipelines:

```yaml
# .github/workflows/ai-test-agent.yml
name: AI test agent
on: [pull_request]

jobs:
  agent-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install playwright mcp pytest-playwright requests
      - run: npx playwright install --with-deps
      - name: Refresh auth session
        run: python scripts/save_auth.py
        env:
          TEST_EMAIL: ${{ secrets.TEST_EMAIL }}
          TEST_PASSWORD: ${{ secrets.TEST_PASSWORD }}
      - name: Run agent
        run: |
          claude --headless --print \
            "Fetch context for all features and run UI tests. Write reports to reports/"
        env:
          CONFLUENCE_EMAIL: ${{ secrets.CONFLUENCE_EMAIL }}
          CONFLUENCE_API_TOKEN: ${{ secrets.CONFLUENCE_TOKEN }}
      - uses: actions/upload-artifact@v4
        with:
          name: test-reports
          path: reports/
```

---

## Report format

Each run produces a markdown report in `reports/`:

```
# Test report — login feature

**Date:** 2026-06-17  
**Context sources:** 2 user stories, 1 bug report, Confluence: not available  

## Results

| Step | Status | Notes |
|---|---|---|
| Navigate to /login | ✅ Pass | |
| Fill valid credentials and submit | ✅ Pass | |
| Assert redirect to /dashboard | ✅ Pass | |
| Assert username visible on dashboard | ✅ Pass | |
| Submit invalid credentials | ✅ Pass | |
| Assert error message displayed | ❌ Fail | Error message not found — screenshot: reports/screenshots/login_error.png |

## Summary

1 of 6 steps failed. The error message for invalid credentials was not rendered 
in the expected element. Likely a regression in the auth error handler.
```

---

## Key design decisions

**Accessibility tree over screenshots** — the agent reads the browser's accessibility tree (roles, names, states) rather than pixel-based screenshots. This makes tests resilient to visual redesigns and much cheaper in tokens.

**Auth state via storage file** — saving session state to `auth.json` and pointing the MCP server at it means the agent never has to handle login flows mid-run. Tokens and cookies are restored automatically.

**Graceful context degradation** — the context server never blocks the agent. Missing Confluence credentials, empty story folders, or failed API calls all result in a reduced but functional context, not a crash.

**CLAUDE.md as the agent's brain** — all app-specific knowledge (URL structure, auth quirks, async areas, non-deterministic modules) lives in `CLAUDE.md`. This is the most important file in the project — the richer it is, the better the tests.

---

## Tech stack

| Component | Technology |
|---|---|
| Agent | Claude Code (Anthropic) |
| Browser automation | Playwright MCP (`@playwright/mcp`) |
| Context server | Python + MCP SDK |
| Test runner | pytest-playwright |
| Language | Python 3.11+ |
| Requirements source | Local markdown files / Confluence REST API |

---

## Contributing

1. Add user stories to `context_server/stories/` as `.md` files
2. Add bug reports to `context_server/bugs/` as `.md` files
3. Update `CLAUDE.md` when new sections of the app are in scope
4. Review agent-generated tests in `tests/generated/` before committing them — treat them like any other PR

---

## Licence

MIT