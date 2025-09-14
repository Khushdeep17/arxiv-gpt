import argparse
import logging
from agent import run_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """
    Test the arXiv-GPT agent in the terminal.
    """
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Test arXiv-GPT agent in terminal")
    parser.add_argument('--query', type=str, default="quantum physics", help="Search query for arXiv papers")
    parser.add_argument('--max-results', type=int, default=3, help="Maximum number of papers to fetch (1-10)")
    parser.add_argument('--pdf', action='store_true', help="Generate PDF report")
    
    args = parser.parse_args()
    
    # Validate inputs
    query = args.query
    max_results = args.max_results
    generate_pdf = args.pdf
    
    if max_results < 1 or max_results > 10:
        logging.error("Max results must be between 1 and 10")
        print("Error: Max results must be between 1 and 10")
        return
    
    # Interactive mode if no query is provided via arguments
    if not query:
        query = input("Enter search query (e.g., 'quantum physics'): ").strip()
        if not query:
            logging.error("No query provided")
            print("Error: Please provide a valid search query")
            return
    
    # Run the agent
    logging.info(f"Running agent with query='{query}', max_results={max_results}, generate_pdf={generate_pdf}")
    result, pdf_filename = run_agent(query, max_results, generate_pdf_report=generate_pdf)
    
    # Print results
    print("\n📑 Latest Papers")
    print("-" * 50)
    if "No papers found" in result or "Unable to process" in result:
        print(f"Error: {result}")
    else:
        print(result)
    
    # Print PDF filename if generated
    if pdf_filename:
        print(f"\n📄 PDF generated: {pdf_filename}")
    else:
        print("\nNo PDF generated")

if __name__ == "__main__":
    main()