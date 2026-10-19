# src/fetch_papers.py
import arxiv

def fetch_papers(query="self-driving cars", max_results=5):
    """
    Fetch papers from arXiv based on a query.
    Returns a list of dictionaries with title, summary, and URL.
    """
    try:
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        papers = []
        for result in search.results():
            papers.append({
                "title": result.title,
                "summary": result.summary,
                "url": result.entry_id,
                "authors": [author.name for author in result.authors],
                "published": result.published
            })
        return papers
    except Exception as e:
        print(f"Error fetching papers: {e}")
        return []