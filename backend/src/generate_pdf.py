from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import os
import logging

def generate_pdf(papers, query, output_dir="data"):
    """
    Generate a PDF report of fetched papers and their summaries.
    Works with structured paper dicts.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(
            output_dir,
            f"arxiv_gpt_{query.replace(' ', '_')}_{timestamp}.pdf"
        )
        
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(f"arXiv-GPT Research Report: {query}", styles['Title']))
        story.append(Spacer(1, 12))

        for i, paper in enumerate(papers, 1):
            story.append(Paragraph(f"Paper {i}", styles['Heading2']))
            story.append(Paragraph(f"<b>Title:</b> {paper['title']}", styles['Normal']))
            story.append(Paragraph(f"<b>Authors:</b> {', '.join(paper['authors'])}", styles['Normal']))
            story.append(Paragraph(f"<b>Published:</b> {paper['published']}", styles['Normal']))
            story.append(
                Paragraph(
                    f"<b>URL:</b> <link href='{paper['url']}' color='blue'>{paper['url']}</link>",
                    styles['Normal']
                )
            )

            story.append(Paragraph("<b>Summary:</b>", styles['Normal']))
            summary = paper.get("summary", [])
            if not summary:
                story.append(Paragraph("No summary available.", styles['Normal']))
            else:
                # summary is now a list of bullet points
                for point in summary:
                    story.append(Paragraph(f"• {point}", styles['Normal']))

            story.append(Spacer(1, 12))
            story.append(Paragraph("-" * 50, styles['Normal']))
            story.append(Spacer(1, 12))

        doc.build(story)
        logging.info(f"Generated PDF: {filename}")
        return filename
    except Exception as e:
        logging.error(f"Error generating PDF: {e}")
        return None
