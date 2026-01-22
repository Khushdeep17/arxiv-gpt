from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
import os
import logging


def _normalize_summary(summary_obj):
    """
    Ensure summary is a list of bullet strings.
    Handles:
      - dict with keys {summary: [...], raw: "..."}
      - list[str]
      - single string
      - None
    """
    if summary_obj is None:
        return []

    # Case 1: dict from summarize_paper()
    if isinstance(summary_obj, dict):
        bullets = summary_obj.get("summary")
        if isinstance(bullets, list):
            return [str(b).strip() for b in bullets if str(b).strip()]
        raw = summary_obj.get("raw")
        if isinstance(raw, str) and raw.strip():
            return [raw.strip()]
        return []

    # Case 2: already a list
    if isinstance(summary_obj, list):
        return [str(b).strip() for b in summary_obj if str(b).strip()]

    # Case 3: single string
    if isinstance(summary_obj, str):
        return [summary_obj.strip()] if summary_obj.strip() else []

    return []


def generate_pdf(papers, query, output_dir="data"):
    """
    Generate a cleanly formatted PDF report of fetched papers and summaries.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = query.replace(" ", "_").replace("/", "_")
        filename = os.path.join(
            output_dir,
            f"arxiv_gpt_{safe_query}_{timestamp}.pdf"
        )

        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50,
        )

        styles = getSampleStyleSheet()
        title_style = styles["Title"]
        h_style = styles["Heading2"]
        normal_style = styles["Normal"]

        bullet_style = ParagraphStyle(
            name="BulletStyle",
            parent=styles["Normal"],
            leftIndent=18,
            spaceBefore=4,
            spaceAfter=4,
        )

        story = []

        # Title
        story.append(Paragraph(f"arXiv-GPT Research Report: {query}", title_style))
        story.append(Spacer(1, 16))

        for i, paper in enumerate(papers, 1):
            story.append(Paragraph(f"Paper {i}", h_style))
            story.append(Spacer(1, 6))

            story.append(Paragraph(f"<b>Title:</b> {paper.get('title', '')}", normal_style))
            story.append(Paragraph(f"<b>Authors:</b> {', '.join(paper.get('authors', []))}", normal_style))
            story.append(Paragraph(f"<b>Published:</b> {paper.get('published', '')}", normal_style))

            url = paper.get("url", "")
            if url:
                story.append(
                    Paragraph(
                        f"<b>URL:</b> <link href='{url}' color='blue'>{url}</link>",
                        normal_style,
                    )
                )

            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>Summary:</b>", normal_style))
            story.append(Spacer(1, 6))

            bullets = _normalize_summary(paper.get("summary"))

            if not bullets:
                story.append(Paragraph("No summary available.", normal_style))
            else:
                bullet_items = []
                for point in bullets:
                    bullet_items.append(
                        ListItem(
                            Paragraph(point, bullet_style),
                            leftIndent=12,
                        )
                    )

                story.append(
                    ListFlowable(
                        bullet_items,
                        bulletType="bullet",
                        start="circle",
                        leftIndent=18,
                    )
                )

            story.append(Spacer(1, 14))
            story.append(Paragraph("—" * 60, normal_style))
            story.append(Spacer(1, 14))

        doc.build(story)
        logging.info(f"Generated PDF: {filename}")
        return filename

    except Exception as e:
        logging.error(f"Error generating PDF: {e}")
        return None
