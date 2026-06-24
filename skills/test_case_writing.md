# Skill: Writing Test Cases

## When to use this skill
Read this file whenever the task is to produce a test case document
(not to execute tests in the browser — see `test_cycle.md` for that).

## Steps
1. Read `skills/context_loading.md` and follow it to load context for the feature.
2. Read the `docs` array first — these define WHAT is correct.
3. Plan test steps based on acceptance criteria from stories, cross-checked against docs.
4. Tag every test case with the story ID(s) and doc filename(s) it validates.
5. Write the generated test cases to `test_cases/<feature>.md`.

### Test case table format
Every step row must follow this format:

```
| Step | Action | Expected Result | Story ID | Doc Source | Result |
|------|--------|-----------------|----------|------------|--------|
| 1    | ...    | ...             | SIB-XXX  | huddles.md | □ Pass  □ Fail  □ Skip |
```

- **Step** — sequential number
- **Action** — what the tester does
- **Expected Result** — what the system should do, grounded in docs/stories
- **Story ID** — the SIB-XXX story this step validates
- **Doc Source** — the `context_server/docs/` filename whose rule this step checks
- **Result** — left blank for manual testers to fill in

6. Generate a printable PDF:
   ```python
   from scripts.generate_test_cases_pdf import generate_test_cases_pdf
   generate_test_cases_pdf("test_cases/<feature>.md")
   ```
   Output: `test_cases/<feature>_test_cases.pdf`
   The PDF renders the Result column as checkboxes (□ Pass  □ Fail  □ Skip)
   on every step row for manual execution tracking.

## Rules
- Never write an assertion that is not grounded in a doc rule or story acceptance criterion.
- If no doc exists for a feature yet, note it as a gap in the test case file header.
- One test case file per feature. Use the feature name as the filename.