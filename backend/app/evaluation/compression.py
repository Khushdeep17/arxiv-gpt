import numpy as np
from app.agent.research_agent import ResearchAgent
from app.services.arxiv_service import ArxivService

TEST_QUERY = "diffusion models"

def run_compression_test():
    raw_papers = ArxivService.fetch_papers(TEST_QUERY, max_results=3)
    response, _ = ResearchAgent.run(TEST_QUERY, max_results=3, generate_pdf=False)

    structured = response["papers"]

    ratios = []

    for raw, structured_paper in zip(raw_papers, structured):
        original_len = len(raw.get("summary", ""))
        generated_len = len(str(structured_paper.get("summary", "")))

        if generated_len > 0:
            ratios.append(original_len / generated_len)

    avg_ratio = np.mean(ratios)

    print("\n=== Compression Results ===")
    print(f"Compression Ratio: {avg_ratio:.2f}x")

    return avg_ratio