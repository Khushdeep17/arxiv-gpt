# src/test_tools.py
from fetch_papers import fetch_papers
from summarize import summarize_paper

papers = fetch_papers("self-driving cars", max_results=1)
if papers:
    print(f"Fetched paper: {papers[0]['title']}")
    summary = summarize_paper(papers[0])
    print(f"Summary:\n{summary}")
else:
    print("No papers fetched.")