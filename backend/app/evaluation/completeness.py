import numpy as np
from app.agent.research_agent import ResearchAgent

FIELDS = [
    "tldr",
    "key_contributions",
    "methods",
    "results",
    "why_it_matters"
]

TEST_QUERY = "transformer architecture"

def run_completeness_test():
    response, _ = ResearchAgent.run(TEST_QUERY, max_results=5, generate_pdf=False)

    papers = response["papers"]

    completeness_scores = []
    schema_valid = True

    for paper in papers:
        summary = paper.get("summary", {})
        filled = 0

        for field in FIELDS:
            if field not in summary:
                schema_valid = False
            elif summary[field] and len(str(summary[field])) > 20:
                filled += 1

        completeness_scores.append(filled / len(FIELDS))

    avg_completeness = np.mean(completeness_scores) * 100

    print("\n=== Completeness Results ===")
    print(f"Summary Completeness: {avg_completeness:.1f}%")
    print(f"Schema Validity: {schema_valid}")

    return avg_completeness, schema_valid