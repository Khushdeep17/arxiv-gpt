import arxiv
import tenacity
import logging
from functools import lru_cache

@lru_cache(maxsize=32)
@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    retry=tenacity.retry_if_exception_type(Exception),
    before_sleep=tenacity.before_sleep_log(logging.getLogger(), logging.DEBUG)
)
def fetch_papers(query, max_results=5):
    """
    Fetch latest papers from arXiv.
    Returns a list of dicts with clean fields.
    """
    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=query.strip().lower(),
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        papers = []
        for result in client.results(search):
            abstract = result.summary.strip() if result.summary else ""
            if not abstract:
                abstract = f"No abstract available. Paper title: {result.title}"
            papers.append({
                "title": result.title,
                "summary": abstract,   # raw abstract, summarizer will replace with bullet list
                "url": result.pdf_url,
                "authors": [author.name for author in result.authors],
                "published": result.published.strftime("%Y-%m-%d")  # string format
            })
        logging.info(f"Fetched {len(papers)} papers from arXiv for query: {query}")
        return papers[:max_results]
    except Exception as e:
        logging.error(f"arXiv fetch error: {e}")
        return []
