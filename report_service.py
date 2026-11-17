# ==========================================================
# FITPRO - PHASE 8
# PDF REPORT GENERATOR
# ==========================================================

from io import BytesIO
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


RED = colors.HexColor("#DC2626")
DARK = colors.HexColor("#171717")
LIGHT_GREY = colors.HexColor("#F3F4F6")
MID_GREY = colors.HexColor("#6B7280")


def _safe(value):
    if value is None or value == "":
        return "-"
    return escape(str(value))


def _cell(value, style):
    return Paragraph(_safe(value), style)


def _make_table(data, widths=None):
    table = Table(
        data,
        colWidths=widths,
        repeatRows=1,
        hAlign="LEFT"
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEADING", (0, 0), (-1, -1), 11),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D1D5DB")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.white,
            LIGHT_GREY
        ])
    ]))

    return table


def generate_client_pdf_report(report_data, generated_by="FITPRO"):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=17 * mm,
        bottomMargin=17 * mm,
        title="FITPRO Client Fitness Report",
        author="FITPRO"
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="FitproTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=23,
        leading=28,
        textColor=RED,
        alignment=TA_CENTER,
        spaceAfter=5
    ))

    styles.add(ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=RED,
        spaceBefore=12,
        spaceAfter=7
    ))

    styles.add(ParagraphStyle(
        name="SmallNote",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=MID_GREY
    ))

    cell_style = ParagraphStyle(
        name="TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10
    )

    story = []

    profile = report_data["profile"]

    client_name = profile[0] or "Client"
    username = profile[1] or "-"

    if len(profile) >= 7:
        age = profile[3]
        height = profile[4]
        goal = profile[5]
    else:
        age = profile[2]
        height = profile[3]
        goal = profile[4]

    height_display = f"{_safe(height)} cm" if height not in (None, "") else "-"

    story.append(Paragraph("FITPRO", styles["FitproTitle"]))

    story.append(Paragraph(
        "CLIENT FITNESS PROGRESS REPORT",
        styles["Heading2"]
    ))

    story.append(Spacer(1, 8))

    story.append(Paragraph(
        f"<b>Client:</b> {_safe(client_name)}",
        styles["Normal"]
    ))

    story.append(Paragraph(
        f"<b>Username:</b> {_safe(username)}",
        styles["Normal"]
    ))

    story.append(Paragraph(
        f"<b>Age:</b> {_safe(age)}",
        styles["Normal"]
    ))

    story.append(Paragraph(
        f"<b>Height:</b> {height_display}",
        styles["Normal"]
    ))

    story.append(Paragraph(
        f"<b>Fitness Goal:</b> {_safe(goal)}",
        styles["Normal"]
    ))

    story.append(Paragraph(
        f"<b>Report Period:</b> "
        f"{_safe(report_data['start_date'])} to "
        f"{_safe(report_data['end_date'])}",
        styles["Normal"]
    ))

    story.append(Paragraph(
        f"<b>Generated:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}",
        styles["Normal"]
    ))

    story.append(Spacer(1, 12))

    # --------------------------
    # 1. WEIGHT PROGRESS
    # --------------------------

    story.append(Paragraph(
        "1. Weight Progress",
        styles["SectionHeading"]
    ))

    weights = report_data.get("weights", [])

    if weights:
        start_weight = float(weights[0][0])
        current_weight = float(weights[-1][0])
        change = round(current_weight - start_weight, 2)

        summary_data = [
            ["Starting Weight", "Latest Weight", "Weight Change"],
            [
                f"{start_weight:.2f} kg",
                f"{current_weight:.2f} kg",
                f"{change:+.2f} kg"
            ]
        ]

        story.append(_make_table(
            summary_data,
            [60 * mm, 60 * mm, 60 * mm]
        ))

        story.append(Spacer(1, 8))

        weight_rows = [[
            "Date", "Weight (kg)", "BMI", "Notes"
        ]]

        for item in weights:
            weight_rows.append([
                _safe(item[3]),
                _safe(item[0]),
                _safe(item[1]),
                _cell(item[2], cell_style)
            ])

        story.append(_make_table(
            weight_rows,
            [30 * mm, 30 * mm, 22 * mm, 98 * mm]
        ))

    else:
        story.append(Paragraph(
            "No weight records available for this period.",
            styles["Normal"]
        ))

    # --------------------------
    # 2. BODY MEASUREMENTS
    # --------------------------

    story.append(Paragraph(
        "2. Body Measurements",
        styles["SectionHeading"]
    ))

    measurements = report_data.get("measurements", [])

    if measurements:
        rows = [[
            "Date", "Waist", "Chest", "Hips",
            "L. Arm", "R. Arm", "L. Thigh", "R. Thigh"
        ]]

        for item in measurements:
            rows.append([
                _safe(item[8]),
                _safe(item[0]),
                _safe(item[1]),
                _safe(item[2]),
                _safe(item[3]),
                _safe(item[4]),
                _safe(item[5]),
                _safe(item[6]),
            ])

        story.append(_make_table(
            rows,
            [26 * mm, 22 * mm, 22 * mm, 22 * mm, 22 * mm, 22 * mm, 22 * mm, 22 * mm]
        ))

        story.append(Spacer(1, 4))

        story.append(Paragraph(
            "Measurements are shown in centimetres (cm).",
            styles["SmallNote"]
        ))

    else:
        story.append(Paragraph(
            "No body measurements recorded for this period.",
            styles["Normal"]
        ))

    # --------------------------
    # 3. WORKOUT ACTIVITY
    # --------------------------

    story.append(Paragraph(
        "3. Workout Activity",
        styles["SectionHeading"]
    ))

    workouts = report_data.get("workouts", [])

    if workouts:
        completed = sum(
            1 for item in workouts if item[4] == 1
        )

        rows = [[
            "Date", "Workout Day", "Exercise", "Status"
        ]]

        for item in workouts:
            rows.append([
                _safe(item[3]),
                _safe(item[1]),
                _cell(item[2], cell_style),
                "Completed" if item[4] == 1 else "Not completed"
            ])

        story.append(Paragraph(
            f"Recorded completed entries: {completed} / {len(workouts)}",
            styles["Normal"]
        ))

        story.append(Spacer(1, 6))

        story.append(_make_table(
            rows,
            [28 * mm, 32 * mm, 82 * mm, 38 * mm]
        ))

    else:
        story.append(Paragraph(
            "No workout activity recorded for this period.",
            styles["Normal"]
        ))

    # --------------------------
    # 4. DIET ACTIVITY
    # --------------------------

    story.append(Paragraph(
        "4. Nutrition Activity",
        styles["SectionHeading"]
    ))

    diet_activity = report_data.get("diet_activity", [])

    if diet_activity:
        consumed = sum(
            1 for item in diet_activity if item[4] == 1
        )

        rows = [[
            "Date", "Meal Type", "Meal", "Status"
        ]]

        for item in diet_activity:
            rows.append([
                _safe(item[3]),
                _cell(item[1], cell_style),
                _cell(item[2], cell_style),
                "Consumed" if item[4] == 1 else "Not consumed"
            ])

        story.append(Paragraph(
            f"Recorded consumed meals: {consumed} / {len(diet_activity)}",
            styles["Normal"]
        ))

        story.append(Spacer(1, 6))

        story.append(_make_table(
            rows,
            [28 * mm, 40 * mm, 74 * mm, 38 * mm]
        ))

    else:
        story.append(Paragraph(
            "No nutrition activity recorded for this period.",
            styles["Normal"]
        ))

    # --------------------------
    # DISCLAIMER
    # --------------------------

    story.append(Spacer(1, 15))

    story.append(Paragraph(
        "Important Notice",
        styles["SectionHeading"]
    ))

    story.append(Paragraph(
        "This report summarizes records entered into FITPRO. "
        "It is not a medical diagnosis, medical advice, or a "
        "guarantee of fitness outcomes. BMI is a screening measure "
        "and should not be interpreted in isolation. Nutrition "
        "and workout records may be self-reported or incomplete. "
        "Review the information with an appropriately qualified "
        "professional.",
        styles["SmallNote"]
    ))

    story.append(Spacer(1, 8))

    story.append(Paragraph(
        f"Generated by {escape(str(generated_by))} | FITPRO",
        styles["SmallNote"]
    ))

    doc.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes