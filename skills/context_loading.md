# Skill: Context Loading

## When to use this skill
Read this file at the start of every test cycle and every test-writing session,
before planning any steps or touching the browser.

## Available tools

| Tool | Returns | When to call directly |
|---|---|---|
| `get_all_context(feature)` | stories + bugs + docs + confluence | Start of every session — default choice |
| `get_user_stories()` | All story files | When you need stories only, feature-agnostic |
| `get_bug_reports()` | All bug files | When you need bugs only, feature-agnostic |
| `get_docs(feature)` | Business-logic docs for a feature | When you need rules/constraints without stories or bugs |
| `get_confluence_page(page_id)` | Raw Confluence page text | When you need a specific spec page by ID |

## What each source contains
- **Stories** (`context_server/stories/`) — acceptance criteria, user flows, story IDs (e.g. SIB-204)
- **Bugs** (`context_server/bugs/`) — reported defects, reproduction steps, bug IDs (e.g. SIB-891)
- **Docs** (`context_server/docs/`) — business rules, constraints, domain knowledge that is
  neither a story nor a bug (e.g. Copilot timeout, Library scoping rules, max collaborator counts)
- **Confluence** — original product spec pages fetched live from Atlassian

## Steps
1. Call `get_all_context(feature)` — this is always the first action.
2. Read the `docs` array before reading stories or bugs.
   Docs define WHAT is correct. Stories define WHAT should happen. Bugs define WHAT is broken.
3. Extract all story IDs (e.g. SIB-204) and doc filenames from the response.
   You will stamp these onto every test step, screenshot, and report entry.
4. If a Confluence page is relevant, pass its ID as `confluence_page_id`.
   All page IDs are listed in the **Confluence page map** in `CLAUDE.md` — look them up there.

## Priority order when sources conflict
1. Confluence (most authoritative — written by product)
2. Stories (acceptance criteria)
3. Docs (engineering/QA captured rules)
4. Bugs (known deviations from expected behaviour)

If any two sources contradict each other, do NOT silently pick one.
Log a **WARN** in the report labelled "Specification Conflict" and flag it for the team.