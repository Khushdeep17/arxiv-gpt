import os
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable
from reportlab.lib.styles import getSampleStyleSheet

logger = logging.getLogger(__name__)


class PDFService:

    @staticmethod
    def generate(papers, query, output_dir="data"):

        try:
            os.makedirs(output_dir, exist_ok=True)

            filename = os.path.join(
                output_dir,
                f"arxiv_gpt_{query.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )

            doc = SimpleDocTemplate(filename, pagesize=letter)
            styles = getSampleStyleSheet()

            story = []

            story.append(Paragraph(f"arXiv-GPT Report: {query}", styles["Title"]))
            story.append(Spacer(1, 16))

            for i, paper in enumerate(papers, 1):

                story.append(Paragraph(f"<b>{i}. {paper['title']}</b>", styles["Heading2"]))
                story.append(Paragraph(", ".join(paper["authors"]), styles["Normal"]))
                story.append(Paragraph(paper["published"], styles["Normal"]))
                story.append(Spacer(1, 8))

                bullets = paper["summary"].get("key_contributions", [])

                if bullets:
                    story.append(ListFlowable(
                        [Paragraph(b, styles["Normal"]) for b in bullets],
                        bulletType="bullet"
                    ))

                story.append(Spacer(1, 12))

            doc.build(story)

            logger.info("PDF generated")

            return filename

        except Exception as e:
            logger.error(f"PDF failed: {e}")
            return None
