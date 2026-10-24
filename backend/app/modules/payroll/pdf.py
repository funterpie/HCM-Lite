import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import async_sessionmaker

async def build_payslip_pdf_bytes(company_name: str, employee: dict, payslip: dict, month: str) -> bytes:
    """Generate payslip PDF using ReportLab returning bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'PayslipTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1f2937'),
        alignment=1 # Center
    )

    subtitle_style = ParagraphStyle(
        'PayslipSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#4b5563'),
        alignment=1
    )

    story.append(Paragraph(company_name or "HCM Lite Company", title_style))
    story.append(Paragraph(f"Payslip for Month: {month}", subtitle_style))
    story.append(Spacer(1, 20))

    # Employee info table
    emp_data = [
        [Paragraph(f"<b>Employee Name:</b> {employee.get('full_name', 'N/A')}", styles['Normal']),
         Paragraph(f"<b>Employee Code:</b> {employee.get('employee_code', 'N/A')}", styles['Normal'])],
        [Paragraph(f"<b>Department:</b> {employee.get('department', 'N/A')}", styles['Normal']),
         Paragraph(f"<b>Designation:</b> {employee.get('designation', 'N/A')}", styles['Normal'])],
    ]
    t_emp = Table(emp_data, colWidths=[250, 250])
    t_emp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f3f4f6')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_emp)
    story.append(Spacer(1, 20))

    # Earnings & Deductions table
    basic = payslip.get('basic_salary', 0.0)
    gross = payslip.get('gross', 0.0)
    deduction = payslip.get('deduction', 0.0)
    tax = payslip.get('tax', 0.0)
    net = payslip.get('net', 0.0)

    table_data = [
        ["Description", "Amount (PKR)"],
        ["Basic Salary", f"{basic:,.2f}"],
        ["Gross Salary (with HRA & Medical)", f"{gross:,.2f}"],
        ["Attendance & Leave Deductions", f"-{deduction:,.2f}"],
        ["Monthly Income Tax", f"-{tax:,.2f}"],
        ["Net Pay", f"{net:,.2f}"]
    ]

    t_pay = Table(table_data, colWidths=[320, 180])
    t_pay.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-2), colors.HexColor('#ffffff')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#e5e7eb')),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d1d5db')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_pay)
    story.append(Spacer(1, 40))

    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#9ca3af'),
        alignment=1
    )
    story.append(Paragraph("This is a computer-generated payslip from HCM Lite.", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
