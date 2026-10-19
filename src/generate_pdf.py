# src/generate_pdf.py
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import os

def generate_pdf(papers, query, output_dir="data"):
    """
    Generate a PDF report of fetched papers and their summaries.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"arxiv_gpt_{query.replace(' ', '_')}_{timestamp}.pdf")
        
        # Create PDF document
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Add title
        story.append(Paragraph(f"arXiv-GPT Research Report: {query}", styles['Title']))
        story.append(Spacer(1, 12))

        # Add papers
        for i, paper in enumerate(papers, 1):
            story.append(Paragraph(f"Paper {i}", styles['Heading2']))
            story.append(Paragraph(f"<b>Title:</b> {paper['title']}", styles['Normal']))
            story.append(Paragraph(f"<b>Authors:</b> {', '.join(paper['authors'])}", styles['Normal']))
            story.append(Paragraph(f"<b>Published:</b> {paper['published'].strftime('%Y-%m-%d')}", styles['Normal']))
            story.append(Paragraph(f"<b>URL:</b> <link href='{paper['url']}' color='blue'>{paper['url']}</link>", styles['Normal']))
            story.append(Paragraph(f"<b>Summary:</b>", styles['Normal']))
            # Split summary into bullet points
            summary_lines = paper.get('summary', 'Summary unavailable').split('\n')
            for line in summary_lines:
                if line.strip():
                    story.append(Paragraph(f"• {line.strip()}", styles['Normal']))
            story.append(Spacer(1, 12))
            story.append(Paragraph("-" * 50, styles['Normal']))
            story.append(Spacer(1, 12))

        # Build PDF
        doc.build(story)
        return filename
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None