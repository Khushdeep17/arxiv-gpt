# src/fetch_papers.py
import arxiv
import tenacity
from datetime import datetime
import requests
import logging
import os
import time

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

logging.basicConfig(filename='logs/arxiv_gpt.log', level=logging.INFO)

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
            papers.append({
                'title': result.title,
                'summary': result.summary,
                'raw_summary': result.summary,  # Store raw abstract
                'url': result.pdf_url,
                'authors': [author.name for author in result.authors],
                'published': result.published
            })
        logging.info(f"Fetched {len(papers)} papers from arXiv for query: {query}")
        return papers
    except Exception as e:
        logging.error(f"arXiv fetch error: {e}")
        raise

@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_fixed(60),  # Wait 60s for 429 errors
    retry=tenacity.retry_if_exception_type(Exception),
    before_sleep=tenacity.before_sleep_log(logging.getLogger(), logging.DEBUG)
)
def fetch_semantic_scholar(query, max_results=5):
    """
    Fetch papers from Semantic Scholar using direct HTTP request to avoid pagination.
    """
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit={max_results}&fields=title,abstract,url,authors,publicationDate"
        headers = {
            "User-Agent": "arXiv-GPT/1.0",
            "x-api-key": os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json().get('data', [])
        
        papers = []
        for paper in data[:max_results]:
            abstract = paper.get('abstract', 'No abstract available.')
            papers.append({
                'title': paper.get('title', 'Unknown'),
                'summary': abstract,
                'raw_summary': abstract,  # Store raw abstract
                'url': paper.get('url', f"https://www.semanticscholar.org/paper/{paper.get('paperId', 'unknown')}"),
                'authors': [author.get('name', 'Unknown') for author in paper.get('authors', [])] or ['Unknown'],
                'published': datetime.strptime(paper.get('publicationDate', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d') if paper.get('publicationDate') else datetime.now()
            })
        logging.info(f"Fetched {len(papers)} papers from Semantic Scholar for query: {query}")
        time.sleep(3.5)  # Respect rate limit
        return papers
    except Exception as e:
        logging.error(f"Semantic Scholar fetch error: {e}")
        raise

def fetch_papers(query, max_results=5, sources=["arxiv"]):
    """
    Fetch papers from specified sources (arXiv, Semantic Scholar, or both).
    """
    try:
        papers = []
        if len(sources) == 1:
            max_per_source = max_results
        else:
            max_per_source = max_results // len(sources) + (1 if max_results % len(sources) else 0)
        if "arxiv" in sources:
            papers.extend(fetch_arxiv(query, max_per_source))
        if "semantic_scholar" in sources:
            papers.extend(fetch_semantic_scholar(query, max_per_source))
        papers = papers[:max_results]
        return papers
    except Exception as e:
        logging.error(f"Fetch papers error: {e}")
        return []