import os
import uuid
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


class CertificateService:
    @staticmethod
    def generate_certificate_pdf(user, roadmap_title, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        certificate_id = f"SKG-{uuid.uuid4().hex[:12].upper()}"
        completion_date = datetime.utcnow().strftime('%B %d, %Y')
        file_name = f"{user.username or 'skillgap'}-{certificate_id}.pdf"
        output_path = os.path.join(output_dir, file_name)

        pdf = canvas.Canvas(output_path, pagesize=letter)
        pdf.setTitle('SkillGap AI Certificate of Completion')
        pdf.setAuthor(user.username or user.email)

        width, height = letter
        pdf.setFillColor(colors.HexColor('#0f172a'))
        pdf.rect(0, 0, width, height, fill=1)

        pdf.setFillColor(colors.HexColor('#00f7a8'))
        pdf.setFont('Helvetica-Bold', 28)
        pdf.drawCentredString(width / 2, height - 1.0 * inch, 'SKILLGAP.AI')

        pdf.setFillColor(colors.HexColor('#e2e8f0'))
        pdf.setFont('Helvetica-Bold', 22)
        pdf.drawCentredString(width / 2, height - 1.6 * inch, 'Certificate of Completion')

        pdf.setFont('Helvetica', 13)
        pdf.drawCentredString(width / 2, height - 2.3 * inch, 'This is to certify that')

        pdf.setFillColor(colors.HexColor('#f8fafc'))
        pdf.setFont('Helvetica-Bold', 20)
        pdf.drawCentredString(width / 2, height - 2.8 * inch, user.full_name or user.username)

        pdf.setFillColor(colors.HexColor('#e2e8f0'))
        pdf.setFont('Helvetica', 12)
        statement = (
            f"This is to certify that {user.full_name or user.username} has successfully completed the "
            'SkillGap AI Learning Program with 100% completion.'
        )
        wrapped = pdf.beginText()
        wrapped.setTextOrigin(0.7 * inch, height - 3.45 * inch)
        wrapped.setFont('Helvetica', 12)
        for line in [statement[:70], statement[70:140]]:
            if line.strip():
                wrapped.textLine(line.strip())
        pdf.drawText(wrapped)

        pdf.setFillColor(colors.HexColor('#94a3b8'))
        pdf.setFont('Helvetica', 11)
        pdf.drawString(0.8 * inch, height - 4.7 * inch, f'Email: {user.email}')
        pdf.drawString(0.8 * inch, height - 5.0 * inch, f'Completion Date: {completion_date}')
        pdf.drawString(0.8 * inch, height - 5.3 * inch, f'Certificate ID: {certificate_id}')

        pdf.setFillColor(colors.HexColor('#0f172a'))
        pdf.rect(0.6 * inch, 0.65 * inch, width - 1.2 * inch, 0.8 * inch, fill=1, stroke=0)
        pdf.setFillColor(colors.HexColor('#f8fafc'))
        pdf.setFont('Helvetica-Bold', 10)
        pdf.drawCentredString(width / 2, 0.95 * inch, 'SkillGap AI Analyzer')

        pdf.save()
        return {
            'certificate_id': certificate_id,
            'file_name': file_name,
            'download_path': output_path,
            'completion_date': completion_date,
        }
