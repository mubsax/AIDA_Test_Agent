# Skill: PDF Generation

## When to use this skill
Read this file when generating any PDF output. There are two separate
scripts for two separate purposes — never mix them up.

| Purpose | Script | Called from |
|---|---|---|
| Test case document (manual tracking) | `scripts/generate_test_cases_pdf.py` | After writing `test_cases/<feature>.md` |
| Test cycle report (automated run results) | `scripts/generate_pdf_report.py` | End of every test cycle |

---

## A — Test Cases PDF
### `scripts/generate_test_cases_pdf.py`

Called after writing `test_cases/<feature>.md` (step 6 of `test_case_writing.md`).

```python
from scripts.generate_test_cases_pdf import generate_test_cases_pdf
generate_test_cases_pdf("test_cases/<feature>.md")
```

Output: `test_cases/<feature>_test_cases.pdf`
Renders every step row with a Result column (□ Pass  □ Fail  □ Skip)
for manual testers to fill in during execution.

---

## B — Test Cycle Report PDF
### `scripts/generate_pdf_report.py`

Called at the end of every automated test cycle (step 8 of `test_cycle.md`).

### report_data schema
Build this dict exactly — the schema is defined at the top of `scripts/generate_pdf_report.py`.
Re-read that file's docstring before calling if you are unsure — the schema may have evolved.

```python
report_data = {
    "feature":     str,           # e.g. "huddles"
    "story_ids":   list[str],     # e.g. ["SIB-204", "SIB-211"]
    "date":        str,           # e.g. "2026-06-24"
    "tester":      str,           # e.g. "AIDA Agent"
    "environment": str,           # e.g. "staging"
    "summary":     str,           # plain-English summary of findings
    "steps": [
        {
            "id":          int,
            "area":        str,   # sub-feature or section name
            "description": str,   # what was tested
            "expected":    str,   # grounded in doc rule or story AC
            "actual":      str,   # what the UI actually did
            "status":      str,   # "PASS" | "FAIL" | "WARN"
            "notes":       str,   # optional — appended to actual in italics
            "screenshot":  str,   # relative path — FAIL steps only, else None
            # metadata (not rendered in PDF, kept for audit trail):
            "story_id":    str,   # e.g. "SIB-204"
            "doc_source":  str,   # e.g. "huddles.md"
        }
    ]
}
```

### Calling generate_pdf

**Preferred — CLI via JSON file (no temp scripts needed):**
```bash
# 1. Write report_data to a JSON file
# 2. Call the script directly
python scripts/generate_pdf_report.py --input reports/<feature>_report.json
# writes to reports/<feature>_report.pdf
```

**Alternative — import in Python:**
```python
from scripts.generate_pdf_report import generate_pdf
generate_pdf(report_data)
# writes to reports/<feature>_report.pdf
```

### Screenshot rules
- Set `"screenshot"` only on FAIL steps, to the relative path:
  `"reports/screenshots/<feature>_<storyID>_step_<n>.png"`
- For PASS and WARN steps, omit the `"screenshot"` key entirely (or set to `None`).
- Only steps with a valid screenshot path are embedded as images in the PDF.

---

## Rules
- Both scripts must exist before calling. Verify with `ls scripts/` if unsure.
- If either script raises a schema error, re-read its docstring — do not guess at fields.
- Both `.md` and `.pdf` report files are required at the end of every test cycle.
  Neither is optional.