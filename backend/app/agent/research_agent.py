import logging
from app.services.arxiv_service import ArxivService
from app.services.summarizer_service import SummarizerService
from app.services.pdf_service import PDFService

logger = logging.getLogger(__name__)


class ResearchAgent:

    @staticmethod
    def run(query, max_results=3, generate_pdf=False):

        papers = ArxivService.fetch_papers(query, max_results)

        if not papers:
            return {"papers": [], "query": query}, None

        enriched = []

        for paper in papers:

            summary = SummarizerService.summarize(paper)

            enriched.append({
                "title": paper["title"],
                "authors": paper["authors"],
                "published": paper["published"],
                "category": paper["category"],
                "url": paper["url"],
                "summary": summary
            })

        pdf = None

        if generate_pdf:
            pdf = PDFService.generate(enriched, query)

        return {
            "papers": enriched,
            "query": query
        }, pdf
