# reports/report.py

import os
import sqlite3
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

DB_PATH = "database/attendance.db"
REPORTS_DIR = "reports/generated"


def get_connection():
    """Return a database connection."""
    return sqlite3.connect(DB_PATH)


def fetch_attendance_data():
    """Fetch all attendance logs from DB."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, name, status, timestamp FROM attendance ORDER BY timestamp ASC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def generate_attendance_report(filename=None):
    """Generate a PDF attendance report."""
    os.makedirs(REPORTS_DIR, exist_ok=True)

    if not filename:
        filename = f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    filepath = os.path.join(REPORTS_DIR, filename)

    # Create PDF document
    doc = SimpleDocTemplate(filepath, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title = Paragraph("University Attendance Report", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Table data
    data = [["Student ID", "Name", "Status", "Timestamp"]]
    records = fetch_attendance_data()

    if not records:
        data.append(["-", "-", "-", "No records available"])
    else:
        for row in records:
            data.append(row)

    # Build table
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4CAF50")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)

    # Footer
    footer = Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
    elements.append(Spacer(1, 12))
    elements.append(footer)

    # Save PDF
    doc.build(elements)
    print(f"[INFO] Report generated: {filepath}")
    return filepath
