# src/fetch_papers.py
import arxiv
import tenacity
from datetime import datetime
import requests
import logging
import os
import time
import urllib.parse
from functools import lru_cache

@lru_cache(maxsize=32)
@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    retry=tenacity.retry_if_exception_type(Exception),
    before_sleep=tenacity.before_sleep_log(logging.getLogger(), logging.DEBUG)
)
def fetch_arxiv(query, max_results=5):
    """
    Fetch papers from arXiv.
    """
    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        papers = []
        for result in client.results(search):
            abstract = result.summary if result.summary else 'No abstract available.'
            papers.append({
                'title': result.title,
                'summary': abstract,
                'url': result.pdf_url,
                'authors': [author.name for author in result.authors],
                'published': result.published
            })
        logging.info(f"Fetched {len(papers)} papers from arXiv for query: {query}")
        return papers
    except Exception as e:
        logging.error(f"arXiv fetch error: {e}")
        return []

@lru_cache(maxsize=32)
@tenacity.retry(
    stop=tenacity.stop_after_attempt(5),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=60),
    retry=tenacity.retry_if_exception_type(Exception),
    before_sleep=tenacity.before_sleep_log(logging.getLogger(), logging.DEBUG)
)
def fetch_semantic_scholar(query, max_results=5):
    """
    Fetch papers from Semantic Scholar using direct HTTP request.
    """
    try:
        query = urllib.parse.quote(query.strip().lower().replace(" ", "+"))
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit={max_results}&fields=title,abstract,url,authors,publicationDate"
        headers = {
            "User-Agent": "arXiv-GPT/1.0",
            "x-api-key": os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
        }
        response = requests.get(url, headers=headers, timeout=10)
        logging.debug(f"Semantic Scholar response status: {response.status_code}, headers: {response.headers}")
        response.raise_for_status()
        data = response.json().get('data', [])

        papers = []
        for paper in data[:max_results]:
            abstract = paper.get('abstract', 'No abstract available.') if paper.get('abstract') else 'No abstract available.'
            papers.append({
                'title': paper.get('title', 'Unknown'),
                'summary': abstract,
                'url': paper.get('url', f"https://www.semanticscholar.org/paper/{paper.get('paperId', 'unknown')}"),
                'authors': [author.get('name', 'Unknown') for author in paper.get('authors', [])] or ['Unknown'],
                'published': datetime.strptime(paper.get('publicationDate', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d') if paper.get('publicationDate') else datetime.now()
            })
        logging.info(f"Fetched {len(papers)} papers from Semantic Scholar for query: {query}")
        if not os.getenv("SEMANTIC_SCHOLAR_API_KEY"):
            time.sleep(1)  # Reduced delay
        return papers
    except requests.exceptions.HTTPError as e:
        logging.error(f"Semantic Scholar HTTP error: {e}, status: {e.response.status_code if e.response else 'N/A'}")
        return []
    except Exception as e:
        logging.error(f"Semantic Scholar fetch error: {e}")
        return []

def fetch_papers(query, max_results=5, sources=["arxiv"]):
    """
    Fetch papers from specified sources (arXiv, Semantic Scholar, or both).
    """
    try:
        if not query or not isinstance(query, str):
            logging.error("Invalid query provided")
            return []
        papers = []
        if len(sources) == 1:
            max_per_source = max_results
        else:
            max_per_source = max_results // len(sources) + (1 if max_results % len(sources) else 0)

        if "arxiv" in sources:
            papers.extend(fetch_arxiv(query, max_per_source))
        if "semantic_scholar" in sources:
            papers.extend(fetch_semantic_scholar(query, max_per_source))

        # Sort by publication date and trim
        papers = sorted(papers, key=lambda x: x['published'], reverse=True)[:max_results]
        logging.info(f"Total papers fetched: {len(papers)}")
        return papers
    except Exception as e:
        logging.error(f"Fetch papers error: {e}")
        return []