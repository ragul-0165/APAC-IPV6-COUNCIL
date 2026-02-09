from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
import io
import os
import logging

class PDFService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.output_dir = "static/reports"
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_report(self, stats_data):
        """Generates an Executive PDF Briefing."""
        filename = f"APAC_IPv6_Briefing_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Custom Styles
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1e3a8a'),
                spaceAfter=20
            )
            
            heading_style = ParagraphStyle(
                'Heading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#334155'),
                spaceBefore=15,
                spaceAfter=10
            )

            # Header
            story.append(Paragraph("APAC IPv6 Intelligence Summit", title_style))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Executive Summary
            story.append(Paragraph("Executive Summary", heading_style))
            summary_text = (
                "This intelligence briefing provides a tactical overview of IPv6 adoption across the Asia-Pacific "
                "region. The data below is derived from real-time DNS and Web connectivity scans of government and "
                "academic infrastructure."
            )
            story.append(Paragraph(summary_text, styles['Normal']))
            story.append(Spacer(1, 20))

            # Leaderboard Table
            story.append(Paragraph("Regional Readiness Leaderboard", heading_style))
            
            if stats_data and 'ranking' in stats_data:
                table_data = [["Rank", "Economy", "Score", "Readiness Level"]]
                for item in stats_data['ranking'][:10]: # Top 10
                    table_data.append([
                        f"#{item['rank']}",
                        item['country'],
                        str(item['score']),
                        item['level']
                    ])
                
                t = Table(table_data, colWidths=[50, 200, 80, 100])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f1f5f9')),
                    ('GRID', (0, 0), (-1, -1), 1, colors.white)
                ]))
                story.append(t)
            else:
                story.append(Paragraph("No ranking data available.", styles['Normal']))

            story.append(Spacer(1, 30))
            
            # Recommendation
            story.append(Paragraph("Strategic Recommendation", heading_style))
            rec_text = (
                "Economies with scores below 50 are advised to implement the 'IPv6-Mostly' transition architecture "
                "immediately. This involves enabling DHCPv4 Option 108 to signal IPv6 preference to modern clients, "
                "allowing for the gradual retirement of legacy IPv4 assignments."
            )
            story.append(Paragraph(rec_text, styles['Normal']))

            doc.build(story)
            return {"status": "success", "url": f"/static/reports/{filename}"}

        except Exception as e:
            self.logger.error(f"PDF Generation failed: {e}")
            return {"status": "error", "message": str(e)}

pdf_service = PDFService()
