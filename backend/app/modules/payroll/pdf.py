from html import escape
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_payslip_pdf_bytes(
    company_name: str,
    employee: dict[str, Any],
    payslip: dict[str, Any],
    month: str,
) -> bytes:
    output = BytesIO()
    document = SimpleDocTemplate(
        output, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph(escape(company_name or "HCM Lite"), styles["Title"]),
        Paragraph(f"Payslip — {escape(month)}", styles["Heading2"]),
        Spacer(1, 16),
    ]
    employee_rows = [
        ["Employee", escape(str(employee.get("full_name") or "N/A")), "Code", escape(str(employee.get("employee_code") or "N/A"))],
        ["Department", escape(str(employee.get("department") or "N/A")), "Designation", escape(str(employee.get("designation") or "N/A"))],
    ]
    story.append(Table(employee_rows, colWidths=[75, 165, 75, 165], style=TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef2ff")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#eef2ff")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ])))
    story.append(Spacer(1, 20))

    def amount(value: Any) -> str:
        return f"{float(value or 0):,.2f}"

    payroll_rows = [["Description", "Amount (PKR)"]] + [
        [label, amount(payslip.get(key))]
        for label, key in (
            ("Basic salary", "basic_salary"),
            ("Gross salary", "gross"),
            ("Deductions", "deduction"),
            ("Income tax", "tax"),
            ("Net pay", "net"),
        )
    ]
    story.append(Table(payroll_rows, colWidths=[330, 150], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e2e8f0")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ])))
    document.build(story)
    return output.getvalue()
