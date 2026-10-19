import os
import logging
import unicodedata
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    HRFlowable
)

logger = logging.getLogger(__name__)


class PDFService:
    @staticmethod
    def _normalize_text(text):
        """
        Convert problematic Unicode characters into safe ASCII equivalents
        and escape XML/HTML-sensitive characters for ReportLab Paragraphs.
        """
        if text is None:
            return ""

        text = str(text)

        replacements = {
            "\u2011": "-",   # non-breaking hyphen
            "\u2010": "-",   # hyphen
            "\u2012": "-",   # figure dash
            "\u2013": "-",   # en dash
            "\u2014": "--",  # em dash
            "\u2212": "-",   # minus sign
            "\u2018": "'",
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
            "\u2026": "...",  # ellipsis
            "\u00a0": " ",    # non-breaking space
        }

        for bad, good in replacements.items():
            text = text.replace(bad, good)

        # Remove any remaining weird combining / compatibility forms
        text = unicodedata.normalize("NFKC", text)

        # Escape XML/HTML special chars for ReportLab Paragraph
        return escape(text)

    @staticmethod
    def _header_footer(canvas, doc):
        """
        Adds page numbers + footer
        """
        canvas.saveState()
        canvas.setFont("Helvetica", 9)

        footer_text = PDFService._normalize_text(
            f"arXiv-GPT • Generated {datetime.now().strftime('%Y-%m-%d')}"
        )

        # drawString does not parse XML, so don't use escaped markup here
        canvas.drawString(
            40,
            20,
            f"arXiv-GPT • Generated {datetime.now().strftime('%Y-%m-%d')}"
        )

        canvas.drawRightString(
            570,
            20,
            f"Page {doc.page}"
        )

        canvas.restoreState()

    @staticmethod
    def generate(papers, query, output_dir="data"):
        try:
            os.makedirs(output_dir, exist_ok=True)

            safe_query = str(query).replace(" ", "_")
            safe_query = "".join(ch for ch in safe_query if ch.isalnum() or ch in ("_", "-", "."))
            filename = os.path.join(
                output_dir,
                f"arxiv_gpt_{safe_query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )

            doc = SimpleDocTemplate(
                filename,
                pagesize=letter,
                leftMargin=45,
                rightMargin=45,
                topMargin=50,
                bottomMargin=40
            )

            styles = getSampleStyleSheet()

            # ---------- CUSTOM STYLES ----------
            title_style = styles["Title"]

            meta_style = ParagraphStyle(
                "meta",
                parent=styles["Normal"],
                fontSize=9.5,
                textColor="grey",
                spaceAfter=6
            )

            tldr_style = ParagraphStyle(
                "tldr",
                parent=styles["Normal"],
                fontSize=11,
                leading=15,
                spaceAfter=10
            )

            section_style = ParagraphStyle(
                "section",
                parent=styles["Heading3"],
                spaceBefore=10,
                spaceAfter=4
            )

            bullet_style = ParagraphStyle(
                "bullet",
                parent=styles["Normal"],
                leftIndent=4,
                leading=14
            )

            story = []

            # ---------- TITLE ----------
            story.append(
                Paragraph(
                    f"arXiv-GPT Research Report<br/><font size=11>Query: {PDFService._normalize_text(query)}</font>",
                    title_style
                )
            )

            story.append(Spacer(1, 18))

            # ---------- PAPERS ----------
            for i, paper in enumerate(papers, start=1):
                summary = paper.get("summary", {})

                paper_title = PDFService._normalize_text(paper.get("title", "Untitled"))
                authors = paper.get("authors", [])
                authors_text = PDFService._normalize_text(", ".join(authors))
                published_text = PDFService._normalize_text(paper.get("published", ""))
                category_text = PDFService._normalize_text(paper.get("category", ""))
                paper_url = paper.get("url", "#")

                # Paper title
                story.append(
                    Paragraph(
                        f"<b>{i}. {paper_title}</b>",
                        styles["Heading2"]
                    )
                )

                # metadata
                story.append(
                    Paragraph(
                        f"{authors_text} • {published_text} • {category_text}",
                        meta_style
                    )
                )

                # clickable link
                story.append(
                    Paragraph(
                        f"<link href='{paper_url}' color='blue'>Open Paper</link>",
                        styles["Normal"]
                    )
                )

                story.append(Spacer(1, 6))

                # TL;DR
                if summary.get("tldr"):
                    story.append(
                        Paragraph(
                            f"<b>TL;DR:</b> {PDFService._normalize_text(summary['tldr'])}",
                            tldr_style
                        )
                    )

                # bullet helper
                def add_bullets(title, items):
                    if items:
                        story.append(Paragraph(title, section_style))
                        story.append(
                            ListFlowable(
                                [
                                    Paragraph(PDFService._normalize_text(x), bullet_style)
                                    for x in items
                                ],
                                bulletType="bullet",
                                leftIndent=12
                            )
                        )

                add_bullets("<b>Key Contributions</b>", summary.get("key_contributions"))
                add_bullets("<b>Methods</b>", summary.get("methods"))
                add_bullets("<b>Results</b>", summary.get("results"))

                if summary.get("why_it_matters"):
                    story.append(
                        Paragraph(
                            f"<b>Why it matters:</b> {PDFService._normalize_text(summary['why_it_matters'])}",
                            styles["Normal"]
                        )
                    )

                if summary.get("citation"):
                    story.append(
                        Paragraph(
                            f"<i>{PDFService._normalize_text(summary['citation'])}</i>",
                            styles["Italic"]
                        )
                    )

                story.append(Spacer(1, 12))

                # divider line
                story.append(
                    HRFlowable(
                        width="100%",
                        thickness=0.6,
                        color="grey"
                    )
                )

                story.append(Spacer(1, 14))

            # ---------- BUILD ----------
            doc.build(
                story,
                onFirstPage=PDFService._header_footer,
                onLaterPages=PDFService._header_footer
            )

            logger.info("PDF generated successfully")
            return os.path.basename(filename)

        except Exception as e:
            logger.error(f"PDF failed: {e}")
            return None