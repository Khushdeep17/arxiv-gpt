# src/test_agent.py
from agent import run_agent
import traceback

def main():
    query = "self-driving cars"
    max_results = 2
    print(f"Running agent with query: '{query}', max_results: {max_results}")
    try:
        result, pdf_filename = run_agent(query, max_results, generate_pdf_report=True)
        print("\nAgent Output:")
        print(result)
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