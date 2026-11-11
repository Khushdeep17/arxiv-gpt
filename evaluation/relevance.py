from app.services.arxiv_service import ArxivService

TEST_QUERIES = [
    "transformer attention",
    "diffusion image generation",
    "robot learning",
]

def run_relevance_test():
    print("\n=== Manual Relevance Test ===")

    total_score = 0
    total_possible = 0

    for query in TEST_QUERIES:
        print(f"\nQuery: {query}")
        papers = ArxivService.fetch_papers(query, max_results=3)

        for i, paper in enumerate(papers, 1):
            print(f"{i}. {paper['title']}")

            score = int(input("Relevance score (0-2): "))
            total_score += score
            total_possible += 2

    relevance_percent = (total_score / total_possible) * 100
    print(f"\nTop-3 Relevance: {relevance_percent:.1f}%")

    return relevance_percent