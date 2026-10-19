import arxiv
import logging
from functools import lru_cache
import tenacity

logger = logging.getLogger(__name__)


class ArxivService:

    @staticmethod
    @lru_cache(maxsize=32)
    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=6),
        retry=tenacity.retry_if_exception_type(Exception),
    )
    def fetch_papers(query: str, max_results: int = 5):

        try:
            client = arxiv.Client(page_size=max_results)

            search = arxiv.Search(
                query=query.strip().lower(),
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )

            papers = []

            for result in client.results(search):

                papers.append({
                    "title": result.title,
                    "summary": result.summary.strip() if result.summary else "",
                    "url": result.pdf_url,
                    "authors": [a.name for a in result.authors],
                    "published": result.published.strftime("%Y-%m-%d"),
                    "category": result.primary_category
                })

            logger.info(f"Fetched {len(papers)} papers for query='{query}'")

            return papers

        except Exception as e:
            logger.error(f"Arxiv fetch failed: {e}")
            return []
