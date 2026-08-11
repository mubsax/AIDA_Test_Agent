# Skill: Running a Test Cycle

## When to use this skill
Read this file whenever the task is to execute tests in the browser and
produce a report. For writing test cases without execution, see `test_case_writing.md`.

## Pre-flight checklist
Before touching the browser:
- [ ] Read `skills/auth.md` and confirm a valid session is loaded
- [ ] Read `skills/context_loading.md` and call `get_all_context(feature)`
- [ ] Read the `docs` array — know the business rules before you click anything

## Steps

### 1 — Load context
Follow `skills/context_loading.md`. Extract all story IDs and doc filenames.

### 1a — Look up the page-level business logic doc
Before planning any steps, identify which page of the app the feature under test lives on.
Check whether a business logic doc exists for that page in `context_server/docs/`.

- List the files in `context_server/docs/` and look for a doc whose name corresponds to the page (e.g. `Sibme_login_page_spec.md` for the login page).
- If a matching doc exists, read it in full — even if `get_all_context()` already returned it. Confirm you have read the page doc before continuing.
- If no matching doc exists for the page, log a note in the report header: "No page-level doc found for `<page name>` — test steps grounded in feature stories and confluence only."
- If the feature spans more than one page, repeat this check for each page.

The page doc defines correctness for the whole page. Feature stories define what is new. Both must be read before planning.

### 2 — Plan steps
Plan test steps based on acceptance criteria from stories, grounded in docs.
Do not improvise steps that have no story or doc backing.

### 3 — Execute in browser
- Use the Playwright MCP server for all browser interactions.
- Use accessibility tree snapshots to locate elements.
- Prefer `getByRole` over CSS selectors.
- After each key action, assert the expected outcome before moving to the next step.
- Base assertions on doc rules, not on what the UI happens to show.
- Cite the doc filename and specific rule in every assertion comment.

### 4 — Screenshots
Take a screenshot **only on FAIL**. Save to:
```
reports/screenshots/<feature>_<storyID>_step_<n>.png
```
Note the element state at time of failure. Do not take screenshots for PASS or WARN steps.
Only FAIL screenshots are embedded in the PDF report.

### 5 — Write the generated test file
Save to `tests/generated/<feature>.py`.
Every test function must include this header comment block:
```python
# Story:   SIB-XXX — <story title>
# Doc:     <doc filename> — <rule being validated>
# Bugs:    SIB-YYY (known, expected to fail)
```

### 6 — Write the markdown report
Save to `reports/<feature>_report.md`. See `skills/pdf_generation.md`
for the required fields.

### 7 — Append to context log
Append one entry to `reports/context_log.json`:
```json
{
  "run_id": "<YYYY-MM-DD-NNN>",
  "feature": "<feature>",
  "stories_covered": ["SIB-XXX"],
  "docs_referenced": ["<doc filename>"],
  "bugs_covered": ["SIB-YYY"],
  "test_file": "tests/generated/<feature>.py",
  "report_md": "reports/<feature>_report.md",
  "report_pdf": "reports/<feature>_report.pdf"
}
```
This is the persistent audit trail linking test runs to stories and docs.
Do not skip this step.

### 8 — Generate PDF report
Follow `skills/pdf_generation.md`.

## Step result classification
| Status | Meaning |
|--------|---------|
| PASS | Actual matches expected, grounded in doc rule |
| FAIL | Actual differs from expected — take screenshot, note element state |
| WARN | Ambiguous outcome (e.g. non-deterministic AI response, spec conflict) — no screenshot |