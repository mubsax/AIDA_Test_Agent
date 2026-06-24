"""
generate_pdf_report.py

Converts a structured QA report dict into a formatted PDF file using reportlab.

Usage (standalone — generates Row 13 UI comparison report):
    python scripts/generate_pdf_report.py

Usage (imported):
    from scripts.generate_pdf_report import generate_pdf
    generate_pdf(report_data, output_path="reports/my_report.pdf")

Report dict schema:
    {
        "feature": str,
        "story_ids": list[str],
        "date": str,
        "tester": str,
        "environment": str,
        "summary": str,
        "steps": [
            {
                "id": int,
                "area": str,
                "description": str,
                "expected": str,
                "actual": str,
                "status": "PASS" | "FAIL" | "WARN",
                "screenshot": str | None,   # path relative to project root
                "notes": str | None,
            },
            ...
        ],
    }
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ── resolve project root so this script works from any cwd ────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ── Colour palette ─────────────────────────────────────────────────────────────
BRAND_GREEN  = colors.HexColor("#2E7D32")
BRAND_DARK   = colors.HexColor("#1A237E")
PASS_GREEN   = colors.HexColor("#43A047")
FAIL_RED     = colors.HexColor("#E53935")
WARN_AMBER   = colors.HexColor("#FB8C00")
LIGHT_GREY   = colors.HexColor("#F5F5F5")
MID_GREY     = colors.HexColor("#BDBDBD")
DARK_GREY    = colors.HexColor("#424242")
WHITE        = colors.white
BLACK        = colors.black

STATUS_COLORS = {
    "PASS": PASS_GREEN,
    "FAIL": FAIL_RED,
    "WARN": WARN_AMBER,
}

PAGE_W, PAGE_H = A4
MARGIN = 1.8 * cm


# ── Styles ─────────────────────────────────────────────────────────────────────
def _build_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["title"] = ParagraphStyle(
        "title",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=WHITE,
        alignment=TA_LEFT,
        spaceAfter=4,
    )
    styles["subtitle"] = ParagraphStyle(
        "subtitle",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#CFD8DC"),
        alignment=TA_LEFT,
    )
    styles["section"] = ParagraphStyle(
        "section",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=BRAND_DARK,
        spaceBefore=14,
        spaceAfter=6,
    )
    styles["body"] = ParagraphStyle(
        "body",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=DARK_GREY,
        leading=13,
        spaceAfter=4,
    )
    styles["cell"] = ParagraphStyle(
        "cell",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=DARK_GREY,
        leading=11,
    )
    styles["cell_bold"] = ParagraphStyle(
        "cell_bold",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=DARK_GREY,
        leading=11,
    )
    styles["status"] = ParagraphStyle(
        "status",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        alignment=TA_CENTER,
        leading=11,
    )
    styles["footer"] = ParagraphStyle(
        "footer",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=7,
        textColor=MID_GREY,
        alignment=TA_CENTER,
    )
    styles["summary_box"] = ParagraphStyle(
        "summary_box",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=DARK_GREY,
        leading=14,
        leftIndent=6,
    )
    return styles


# ── Header / Footer callbacks ──────────────────────────────────────────────────
def _header(canvas, doc, meta):
    canvas.saveState()
    # Dark banner across the top
    canvas.setFillColor(BRAND_DARK)
    canvas.rect(0, PAGE_H - 3.2 * cm, PAGE_W, 3.2 * cm, fill=1, stroke=0)

    # Green accent stripe
    canvas.setFillColor(BRAND_GREEN)
    canvas.rect(0, PAGE_H - 3.5 * cm, PAGE_W, 0.3 * cm, fill=1, stroke=0)

    styles = _build_styles()

    # Title
    p = Paragraph(meta["feature"], styles["title"])
    p.wrapOn(canvas, PAGE_W - 2 * MARGIN, 2 * cm)
    p.drawOn(canvas, MARGIN, PAGE_H - 2.4 * cm)

    # Subtitle line
    sub_text = (
        f"Environment: {meta['environment']}   |   "
        f"Date: {meta['date']}   |   "
        f"Tester: {meta['tester']}"
    )
    p2 = Paragraph(sub_text, styles["subtitle"])
    p2.wrapOn(canvas, PAGE_W - 2 * MARGIN, 1 * cm)
    p2.drawOn(canvas, MARGIN, PAGE_H - 3.15 * cm)

    # Page number (right side of banner)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#CFD8DC"))
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 2.0 * cm, f"Page {doc.page}")

    # Footer
    canvas.setFillColor(LIGHT_GREY)
    canvas.rect(0, 0, PAGE_W, 1.0 * cm, fill=1, stroke=0)
    canvas.setFillColor(MID_GREY)
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(
        PAGE_W / 2, 0.35 * cm,
        f"Generated by AIDA QA Agent  •  {meta['feature']}  •  Confidential"
    )

    canvas.restoreState()


# ── Stats bar ──────────────────────────────────────────────────────────────────
def _stats_table(steps, styles):
    total = len(steps)
    counts = {"PASS": 0, "FAIL": 0, "WARN": 0}
    for s in steps:
        counts[s["status"]] += 1

    data = [
        [
            Paragraph(f"<b>{total}</b><br/>Total", styles["status"]),
            Paragraph(f"<b>{counts['PASS']}</b><br/>Pass", styles["status"]),
            Paragraph(f"<b>{counts['FAIL']}</b><br/>Fail", styles["status"]),
            Paragraph(f"<b>{counts['WARN']}</b><br/>Warn", styles["status"]),
        ]
    ]

    col_w = (PAGE_W - 2 * MARGIN) / 4
    tbl = Table(data, colWidths=[col_w] * 4, rowHeights=[1.4 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), BRAND_DARK),
        ("BACKGROUND", (1, 0), (1, 0), PASS_GREEN),
        ("BACKGROUND", (2, 0), (2, 0), FAIL_RED),
        ("BACKGROUND", (3, 0), (3, 0), WARN_AMBER),
        ("TEXTCOLOR",  (0, 0), (-1, -1), WHITE),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",       (0, 0), (-1, -1), 0.5, WHITE),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [None]),
    ]))
    return tbl


# ── Step detail table ──────────────────────────────────────────────────────────
def _steps_table(steps, styles, screenshots_base: Path):
    col_widths = [
        0.8 * cm,   # #
        2.5 * cm,   # Area
        4.0 * cm,   # Description
        3.5 * cm,   # Expected
        3.5 * cm,   # Actual
        1.5 * cm,   # Status
    ]

    header_style = ParagraphStyle(
        "th",
        parent=styles["cell_bold"],
        textColor=WHITE,
        fontSize=8,
    )
    header = [
        Paragraph("#", header_style),
        Paragraph("Area", header_style),
        Paragraph("Description", header_style),
        Paragraph("Expected", header_style),
        Paragraph("Actual", header_style),
        Paragraph("Status", header_style),
    ]
    rows = [header]

    for step in steps:
        status = step["status"]
        status_color = STATUS_COLORS.get(status, DARK_GREY)

        status_para = Paragraph(
            f'<font color="{status_color.hexval()}"><b>{status}</b></font>',
            styles["status"],
        )

        actual_text = step["actual"]
        if step.get("notes"):
            actual_text += f" <i>({step['notes']})</i>"

        rows.append([
            Paragraph(str(step["id"]), styles["cell"]),
            Paragraph(step["area"], styles["cell_bold"]),
            Paragraph(step["description"], styles["cell"]),
            Paragraph(step["expected"], styles["cell"]),
            Paragraph(actual_text, styles["cell"]),
            status_para,
        ])

    tbl = Table(rows, colWidths=col_widths, repeatRows=1)

    ts = TableStyle([
        # Header row
        ("BACKGROUND",  (0, 0), (-1, 0), BRAND_DARK),
        ("TEXTCOLOR",   (0, 0), (-1, 0), WHITE),
        ("ALIGN",       (0, 0), (-1, 0), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        ("GRID",        (0, 0), (-1, -1), 0.4, MID_GREY),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ])

    # Colour FAIL / WARN rows
    for i, step in enumerate(steps, start=1):
        if step["status"] == "FAIL":
            ts.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FFEBEE"))
        elif step["status"] == "WARN":
            ts.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FFF8E1"))

    tbl.setStyle(ts)
    return tbl


# ── Screenshot block ───────────────────────────────────────────────────────────
def _screenshot_flowables(steps, styles, screenshots_base: Path):
    """Embed screenshots for FAIL steps only."""
    items = []
    steps_with_shots = [
        s for s in steps
        if s.get("status") == "FAIL"
        and s.get("screenshot")
        and Path(screenshots_base / s["screenshot"]).exists()
    ]
    if not steps_with_shots:
        return items

    items.append(Paragraph("Screenshots", styles["section"]))
    items.append(HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=6))

    for step in steps_with_shots:
        status = step["status"]
        status_color = STATUS_COLORS.get(status, DARK_GREY)

        # Caption row: step number + area on left, coloured status badge on right
        caption_data = [[
            Paragraph(
                f'<b>Step {step["id"]}</b>  —  {step["area"]}: {step["description"]}',
                styles["cell_bold"],
            ),
            Paragraph(
                f'<font color="{status_color.hexval()}"><b>{status}</b></font>',
                ParagraphStyle(
                    "badge",
                    parent=styles["status"],
                    alignment=TA_RIGHT,
                    fontSize=8,
                ),
            ),
        ]]
        caption_tbl = Table(
            caption_data,
            colWidths=[PAGE_W - 2 * MARGIN - 1.5 * cm, 1.5 * cm],
        )
        caption_tbl.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        items.append(caption_tbl)

        # Embed image — cap height so tall screenshots don't overflow the page
        img_path = screenshots_base / step["screenshot"]
        try:
            max_w = PAGE_W - 2 * MARGIN
            max_h = 11 * cm
            img = Image(str(img_path), width=max_w, height=max_h, kind="proportional")
            items.append(img)
        except Exception as e:
            items.append(Paragraph(f"[Image could not be embedded: {e}]", styles["cell"]))

        # Thin divider between screenshots
        items.append(Spacer(1, 0.3 * cm))
        items.append(HRFlowable(width="100%", thickness=0.5, color=MID_GREY, spaceAfter=6))

    return items


# ── Main public function ───────────────────────────────────────────────────────
def generate_pdf(report_data: dict, output_path: str | None = None) -> str:
    """
    Generate a PDF QA report.

    Args:
        report_data: Report dict matching the schema described at the top.
        output_path: Where to write the PDF. Defaults to reports/<slug>_report.pdf.

    Returns:
        Absolute path to the generated PDF file.
    """
    if output_path is None:
        slug = report_data["feature"].lower()
        slug = re.sub(r"[^\w\s-]", "", slug)          # strip non-word chars
        slug = re.sub(r"[\s\-]+", "_", slug).strip("_")
        output_path = str(PROJECT_ROOT / "reports" / f"{slug}_report.pdf")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    styles = _build_styles()
    meta = {
        "feature":     report_data["feature"],
        "date":        report_data.get("date", datetime.today().strftime("%Y-%m-%d")),
        "tester":      report_data.get("tester", "AIDA QA Agent"),
        "environment": report_data.get("environment", "q41.sibme.com"),
    }

    doc = BaseDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=3.8 * cm,
        bottomMargin=1.6 * cm,
    )

    frame = Frame(
        MARGIN, 1.6 * cm,
        PAGE_W - 2 * MARGIN, PAGE_H - 3.8 * cm - 1.6 * cm,
        id="body",
    )
    template = PageTemplate(
        id="main",
        frames=[frame],
        onPage=lambda canvas, doc: _header(canvas, doc, meta),
    )
    doc.addPageTemplates([template])

    story = []

    # ── Story / Bug ID row ─────────────────────────────────────────────────────
    if report_data.get("story_ids"):
        ids_text = "  |  ".join(report_data["story_ids"])
        story.append(Paragraph(f"<b>Spec refs:</b>  {ids_text}", styles["body"]))

    story.append(Spacer(1, 0.3 * cm))

    # ── Stats bar ──────────────────────────────────────────────────────────────
    story.append(_stats_table(report_data["steps"], styles))
    story.append(Spacer(1, 0.5 * cm))

    # ── Summary ────────────────────────────────────────────────────────────────
    story.append(Paragraph("Summary", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=6))

    summary_tbl = Table(
        [[Paragraph(report_data["summary"], styles["summary_box"])]],
        colWidths=[PAGE_W - 2 * MARGIN],
    )
    summary_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
        ("BOX",        (0, 0), (-1, -1), 1, MID_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
    ]))
    story.append(summary_tbl)
    story.append(Spacer(1, 0.5 * cm))

    # ── Steps table ────────────────────────────────────────────────────────────
    story.append(Paragraph("Test Steps", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=6))
    story.append(_steps_table(report_data["steps"], styles, PROJECT_ROOT))
    story.append(Spacer(1, 0.6 * cm))

    # ── Screenshots ────────────────────────────────────────────────────────────
    for flowable in _screenshot_flowables(report_data["steps"], styles, PROJECT_ROOT):
        story.append(flowable)

    doc.build(story)
    return os.path.abspath(output_path)


# ── Row 13 report data ─────────────────────────────────────────────────────────
ROW13_REPORT = {
    "feature":     "Row 13 UI Comparison — Workspace & Huddles (Sibme 2.0)",
    "story_ids":   ["Confluence Row 13 — Prioritized List for July 1", "Sibme 2.0 Spec Page ID: 4683169793"],
    "date":        "2026-06-18",
    "tester":      "AIDA QA Agent (Claude Sonnet 4.6)",
    "environment": "https://q41.sibme.com  |  Account: Sibme Learning",
    "summary": (
        "Visual comparison of the Workspace page on q41.sibme.com against the Row 13 design "
        "screenshots from Confluence (image-20260615-204848.png — Workspace). "
        "8 discrepancies were identified across the top navigation area, filter/tab row, and left sidebar. "
        "The two highest-severity issues are the complete absence of the Library icon and Mobile App icon "
        "from the left sidebar. The '+' add button is rendered in dark/navy instead of the specified green. "
        "Minor label and separator differences exist in the filter bar. "
        "Huddle page comparison (Screenshots #5, #6) is pending a follow-up cycle."
    ),
    "steps": [
        {
            "id": 1,
            "area": "Top Nav — Breadcrumb",
            "description": "Breadcrumb should show 'Home › Workspace' prefix per design",
            "expected": "Breadcrumb displays 'Home ›' before section name",
            "actual": "Breadcrumb missing 'Home ›' prefix — only section name shown",
            "status": "FAIL",
            "screenshot": None,
            "notes": "Medium severity — navigational context missing",
        },
        {
            "id": 2,
            "area": "Left Sidebar — Library icon",
            "description": "Library icon (stacked-pages) should appear between Huddles and Observations",
            "expected": "Library icon present in sidebar between Huddles and Observations links",
            "actual": "Library icon completely absent — sidebar jumps from Huddles to Observations",
            "status": "FAIL",
            "screenshot": None,
            "notes": "High severity — entire module navigation link missing",
        },
        {
            "id": 3,
            "area": "Left Sidebar — Mobile App icon",
            "description": "Mobile App icon (tablet) required at bottom of sidebar (Row 12 spec)",
            "expected": "Tablet/phone icon pinned at bottom of left sidebar",
            "actual": "No Mobile App icon anywhere in the sidebar",
            "status": "FAIL",
            "screenshot": None,
            "notes": "High severity — Row 12 explicitly requires this icon",
        },
        {
            "id": 4,
            "area": "Left Sidebar — '+' Add button",
            "description": "Add button should be a prominent green rounded rectangle",
            "expected": "Bright green '+' button at top of sidebar",
            "actual": "Dark/navy small icon rendered instead of green button",
            "status": "FAIL",
            "screenshot": None,
            "notes": "Medium severity — incorrect colour/style",
        },
        {
            "id": 5,
            "area": "Tabs row — Upload icon badge",
            "description": "Design shows no extra icon with badge counter in tabs row",
            "expected": "Tabs row: Workspace | Videos | Docs | Links | URLs tabs only",
            "actual": "Extra upload/folder icon with badge '6' present — not in design",
            "status": "WARN",
            "screenshot": None,
            "notes": "Possibly a functional icon not yet in design; verify with PO",
        },
        {
            "id": 6,
            "area": "Filter row — 'Videos' label",
            "description": "Filter pill for media type is labelled 'Videos' in design",
            "expected": "Filter pill: 'Videos'",
            "actual": "Filter pill shows: 'Media'",
            "status": "FAIL",
            "screenshot": None,
            "notes": "Medium severity — label mismatch with spec",
        },
        {
            "id": 7,
            "area": "Filter row — Separator pipes",
            "description": "Design shows '|' pipe characters separating filter groups",
            "expected": "Visible '|' separator between filter pill groups",
            "actual": "No pipe separators between groups",
            "status": "FAIL",
            "screenshot": None,
            "notes": "Low severity — visual grouping cue absent",
        },
        {
            "id": 8,
            "area": "Filter row — 'URL' label",
            "description": "URL filter tab label should be 'URLs' (plural) per design",
            "expected": "'URLs' tab label",
            "actual": "'URL' tab label (singular)",
            "status": "WARN",
            "screenshot": None,
            "notes": "Low severity — minor copy inconsistency",
        },
        {
            "id": 9,
            "area": "Left Sidebar — Copilot Home",
            "description": "Home/house icon present and correctly positioned",
            "expected": "House icon at position 2 in sidebar",
            "actual": "House icon present at correct position",
            "status": "PASS",
            "screenshot": None,
            "notes": None,
        },
        {
            "id": 10,
            "area": "Left Sidebar — Workspace",
            "description": "Briefcase/bag icon for Workspace present and active-highlighted",
            "expected": "Briefcase icon highlighted (active state) at position 3",
            "actual": "Briefcase icon highlighted in blue — matches design",
            "status": "PASS",
            "screenshot": None,
            "notes": None,
        },
        {
            "id": 11,
            "area": "Left Sidebar — Huddles",
            "description": "Diamond/sparkle icon for Huddles present at position 4",
            "expected": "Huddles icon (diamond/sparkle) at position 4",
            "actual": "Diamond/sparkle icon present at position 4",
            "status": "PASS",
            "screenshot": None,
            "notes": None,
        },
        {
            "id": 12,
            "area": "Left Sidebar — Goals, Forms, Analytics, People, Academy, edTPA, Launchpad",
            "description": "Remaining sidebar icons Observations → Launchpad present and in order",
            "expected": "7 icons in correct order after Huddles",
            "actual": "6 icons present (Library missing shifts count); remaining order correct",
            "status": "PASS",
            "screenshot": None,
            "notes": "Icons match design shape/style; only Library is absent",
        },
    ],
}


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    import json
    from scripts.generate_test_cases_pdf import generate_test_cases_pdf

    parser = argparse.ArgumentParser(description="AIDA QA PDF generator")
    parser.add_argument(
        "--input", metavar="JSON_PATH",
        help="Generate a QA run report PDF from a JSON file containing report_data",
    )
    parser.add_argument(
        "--test-cases", metavar="MD_PATH",
        help="Generate a manual test case PDF from a test_cases/*.md file",
    )
    args = parser.parse_args()

    if args.input:
        json_path = Path(args.input)
        if not json_path.exists():
            print(f"Error: {json_path} not found")
            sys.exit(1)
        report_data = json.loads(json_path.read_text(encoding="utf-8"))
        out = generate_pdf(report_data)
        print(f"PDF report generated: {out}")
    elif args.test_cases:
        out = generate_test_cases_pdf(args.test_cases)
        print(f"Test cases PDF generated: {out}")
    else:
        out = generate_pdf(ROW13_REPORT)
        print(f"PDF report generated: {out}")
        tc_path = PROJECT_ROOT / "test_cases" / "new_sibme_2_0.md"
        if tc_path.exists():
            tc_out = generate_test_cases_pdf(tc_path)
            print(f"Test cases PDF generated: {tc_out}")