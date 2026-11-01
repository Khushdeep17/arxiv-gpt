import logging
import uuid
from typing import Optional
from sqlalchemy.orm import Session

from app.services.arxiv_service import ArxivService
from app.services.summarizer_service import SummarizerService
from app.services.pdf_service import PDFService
from app.services.persistence_service import PersistenceService
from app.core.config import settings

logger = logging.getLogger(__name__)


class ResearchAgent:

    @staticmethod
    def run(query: str, max_results: int = 3, generate_pdf: bool = False, db: Optional[Session] = None, user_id: Optional[uuid.UUID] = None):

        papers = ArxivService.fetch_papers(query, max_results)

        if not papers:
            return {"papers": [], "query": query}, None

        enriched = []

        for paper in papers:
            summary = None

            # Check if a compatible summary already exists in the database
            if db is not None:
                try:
                    db_paper = PersistenceService.find_paper(db, url=paper.get("url", ""))
                    if db_paper is not None:
                        cached_sum = PersistenceService.get_cached_summary(
                            db=db,
                            paper_id=db_paper.id,
                            model_name=settings.SUMMARY_MODEL_NAME,
                            prompt_version=settings.SUMMARY_PROMPT_VERSION,
                        )
                        if cached_sum is not None:
                            logger.info(f"Reusing cached summary for '{paper['title'][:40]}'")
                            summary = {
                                "tldr": cached_sum.tldr,
                                "key_contributions": cached_sum.key_contributions,
                                "methods": cached_sum.methods,
                                "results": cached_sum.results,
                                "why_it_matters": cached_sum.why_it_matters,
                                "citation": cached_sum.citation,
                            }
                except Exception as e:
                    logger.warning(f"Failed to check cached summary from database: {e}")

            # If no cached summary was found or db was not provided, invoke LLM
            if summary is None:
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

        # Record search and paper associations in database if session provided
        if db is not None:
            try:
                PersistenceService.record_search(
                    db=db,
                    query=query,
                    max_results=max_results,
                    enriched_papers=enriched,
                    pdf_filename=pdf,
                    user_id=user_id,
                )
            except Exception as e:
                logger.error(f"Failed to record search in database: {e}")
                # We do not crash the search response for the user if database write fails

        return {
            "papers": enriched,
            "query": query
        }, pdf
