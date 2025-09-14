from src.agent import run_agent
from src.fetch_papers import fetch_papers
from src.summarize import summarize_paper
from src.generate_pdf import generate_pdf

def test_backend():
    print("🔍 Starting backend tests...\n")

    # Test fetch_papers
    print("=== Testing fetch_papers ===")
    papers = fetch_papers("self-driving cars", max_results=2)
    print(f"Fetched {len(papers)} papers")
    for p in papers:
        print(f"- {p['title']} ({p['published']})")
    print("")

    # Test summarize_paper
    print("=== Testing summarize_paper ===")
    for paper in papers:
        summary = summarize_paper(paper)
        print(f"{paper['title']} summary:\n{summary['summary']}\n")

    # Test run_agent
    print("=== Testing run_agent ===")
    output, pdf_file = run_agent("self-driving cars", max_results=2, generate_pdf_report=True)
    print("Agent output preview:\n", output[:500], "...\n")  # preview only
    if pdf_file:
        print(f"PDF generated at: {pdf_file}")
    print("\n✅ Backend tests completed successfully.")

if __name__ == "__main__":
    test_backend()
