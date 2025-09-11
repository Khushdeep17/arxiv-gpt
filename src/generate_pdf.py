# src/generate_pdf.py
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os
from datetime import datetime

def generate_pdf(papers, query):
    """
    Generate a PDF report from the list of papers.
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "data"
        os.makedirs(output_dir, exist_ok=True)
        pdf_filename = os.path.join(output_dir, f"arxiv_gpt_{query.replace(' ', '_')}_{timestamp}.pdf")

        doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph(f"Research Papers on {query}", styles['Title']))
        story.append(Spacer(1, 12))

        for i, paper in enumerate(papers, 1):
            # Paper details
            story.append(Paragraph(f"Paper {i}: {paper['title']}", styles['Heading2']))
            story.append(Paragraph(f"Authors: {', '.join(paper['authors'])}", styles['Normal']))
            story.append(Paragraph(f"Published: {paper['published'].strftime('%Y-%m-%d')}", styles['Normal']))
            story.append(Paragraph(f"URL: {paper['url']}", styles['Normal']))
            story.append(Paragraph(f"Source: {'Semantic Scholar' if 'semanticscholar' in paper['url'] else 'arXiv'}", styles['Normal']))
            
            # Summary (use raw abstract if summary is an error)
            summary = paper['summary']
            if summary.startswith("Error summarizing paper"):
                summary = paper.get('raw_summary', 'No summary available.')
            story.append(Paragraph(f"Summary:", styles['Heading3']))
            story.append(Paragraph(summary, styles['Normal']))
            story.append(Spacer(1, 12))

        doc.build(story)
        return pdf_filename
    except Exception as e:
        print(f"PDF generation error: {e}")
        return None