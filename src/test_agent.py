from agent import run_agent
import traceback
import time
import logging
import os
from datetime import datetime

os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    filename='logs/arxiv_gpt.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    query = "self-driving cars"
    max_results = 3
    print(f"\nRunning agent with query: '{query}', max_results: {max_results}")
    start_time = time.time()
    try:
        result, pdf_filename = run_agent(query, max_results, generate_pdf_report=True)
        print("\nAgent Output:")
        print(result)
        elapsed = time.time() - start_time
        print(f"Time taken: {elapsed:.2f} seconds")
        if isinstance(result, str) and "Unable to process" not in result:
            print("Agent executed successfully!")
            if pdf_filename:
                print(f"PDF generated: {pdf_filename}")
            else:
                print("PDF generation failed.")
        else:
            print("Agent failed to produce valid output.")
        logging.info(f"Test run completed for {query}, time: {elapsed:.2f}s")
    except Exception as e:
        print(f"Test error: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        logging.error(f"Test error for {query}: {e}")

if __name__ == "__main__":
    main()