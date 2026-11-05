"""
utils/pdf_report.py
Match result ko ek clean PDF report me export karne ke liye (reportlab use karke).
"""

import io
import json
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem


def generate_pdf_report(entry):
    """MatchHistory entry se ek PDF (BytesIO) banata hai: score, strengths, missing skills, suggestions."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=50, bottomMargin=50)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("T", parent=styles["Title"], textColor=colors.HexColor("#16213E"))
    heading_style = ParagraphStyle("H", parent=styles["Heading2"], textColor=colors.HexColor("#16213E"), spaceBefore=14)
    score_style = ParagraphStyle("S", parent=styles["Normal"], fontSize=20, textColor=colors.HexColor("#0EA87A"), spaceAfter=10)
    normal = styles["Normal"]

    story = [
        Paragraph("ResumeMatch AI - Match Report", title_style),
        Spacer(1, 10),
        Paragraph("Resume: " + escape(entry.resume_filename), normal),
        Paragraph("Date: " + entry.created_at.strftime("%d %b %Y"), normal),
        Spacer(1, 10),
        Paragraph("Match Score: " + str(entry.match_score) + "%", score_style),
    ]

    def add_section(title, items_json):
        items = json.loads(items_json) if items_json else []
        if items:
            story.append(Paragraph(title, heading_style))
            story.append(ListFlowable(
                [ListItem(Paragraph(escape(str(i)), normal)) for i in items],
                bulletType="bullet",
            ))

    add_section("Strengths", entry.strengths)
    add_section("Missing Skills", entry.missing_skills)
    add_section("Suggestions", entry.suggestions)

    doc.build(story)
    buffer.seek(0)
    return buffer