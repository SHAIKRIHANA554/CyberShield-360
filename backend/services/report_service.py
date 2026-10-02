"""Report generation service for PDF and Excel exports."""
import os
import uuid
from datetime import datetime

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class ReportService:
    """Generate PDF and Excel threat reports."""

    def __init__(self, reports_folder: str):
        self.reports_folder = reports_folder
        os.makedirs(reports_folder, exist_ok=True)

    def generate_pdf(self, report_data: dict, user_name: str = "User") -> str:
        """Generate PDF threat report."""
        filename = f"report_{uuid.uuid4().hex[:8]}.pdf"
        filepath = os.path.join(self.reports_folder, filename)

        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                rightMargin=inch, leftMargin=inch,
                                topMargin=inch, bottomMargin=inch)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("Title", parent=styles["Heading1"],
                                     fontSize=18, textColor=colors.HexColor("#C1121F"))
        elements = []

        elements.append(Paragraph("CYBERSHIELD 360 - Threat Report", title_style))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
        elements.append(Paragraph(f"User: {user_name}", styles["Normal"]))
        elements.append(Spacer(1, 20))

        # Report details table
        data = [
            ["Field", "Value"],
            ["Scan Type", report_data.get("scan_type", "N/A")],
            ["Threat Level", report_data.get("threat_level", "N/A").upper()],
            ["Confidence", f"{report_data.get('confidence', 0)}%"],
            ["Threat Type", report_data.get("threat_type", "N/A")],
        ]

        reasons = report_data.get("reasons", [])
        if reasons:
            data.append(["Reasons", "; ".join(reasons[:3])])

        data.append(["Recommendation", report_data.get("recommendation", "N/A")])

        table = Table(data, colWidths=[2 * inch, 4 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#C1121F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F5F5F5")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Protect • Detect • Educate", styles["Italic"]))

        doc.build(elements)
        return filename

    def generate_excel(self, reports: list, user_name: str = "User") -> str:
        """Generate Excel report from multiple scan results."""
        filename = f"reports_{uuid.uuid4().hex[:8]}.xlsx"
        filepath = os.path.join(self.reports_folder, filename)

        wb = Workbook()
        ws = wb.active
        ws.title = "Threat Reports"

        headers = ["Date", "Scan Type", "Threat Level", "Confidence", "Threat Type", "Recommendation"]
        ws.append(headers)

        for report in reports:
            ws.append([
                report.get("created_at", ""),
                report.get("scan_type", ""),
                report.get("threat_level", ""),
                report.get("confidence", 0),
                report.get("threat_type", ""),
                report.get("recommendation", "")[:100]
            ])

        wb.save(filepath)
        return filename
