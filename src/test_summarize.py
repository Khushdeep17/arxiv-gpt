from fetch_papers import fetch_papers
from summarize import summarize_paper

papers = fetch_papers(query="self-driving cars", max_results=1)
if papers:
    summary = summarize_paper(papers[0])
    print(f"Title: {papers[0]['title']}")
    print(f"Summary:\n{summary}")