from fetch_papers import fetch_papers

papers = fetch_papers(query="self-driving cars", max_results=3)
for paper in papers:
    print(f"Title: {paper['title']}")
    print(f"URL: {paper['url']}")
    print("-" * 50)