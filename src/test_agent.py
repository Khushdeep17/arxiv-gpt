# src/test_agent.py
from agent import run_agent
import traceback
import time
import logging
import os

# Centralize logging configuration
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    filename='logs/arxiv_gpt.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    query = "self-driving cars"
    max_results = 3
    sources_list = [
        ["arxiv"],
        ["semantic_scholar"],
        ["arxiv", "semantic_scholar"]
    ]
    for sources in sources_list:
        print(f"\nRunning agent with query: '{query}', max_results: {max_results}, sources: {sources}")
        start_time = time.time()
        try:
            result, pdf_filename = run_agent(query, max_results, generate_pdf_report=True, sources=sources)
            print("\nAgent Output:")
            print(result)
            print(f"Time taken: {time.time() - start_time:.2f} seconds")
            if isinstance(result, str) and "Unable to process" not in result:
                print("Agent executed successfully!")
                if pdf_filename:
                    print(f"PDF generated: {pdf_filename}")
                else:
                    print("PDF generation failed.")
            else:
                print("Agent failed to produce valid output.")
        except Exception as e:
            print(f"Test error: {e}")
            print("\nFull traceback:")
            traceback.print_exc()

if __name__ == "__main__":
    main()