# src/agent.py
from langchain_groq import ChatGroq
from fetch_papers import fetch_papers
from summarize import summarize_paper
from generate_pdf import generate_pdf
from dotenv import load_dotenv
import os
import logging

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

load_dotenv()

logging.basicConfig(filename='logs/arxiv_gpt.log', level=logging.DEBUG)

def run_agent(query, max_results=3, generate_pdf_report=False, sources=["arxiv"], summary_format="bullet"):
    """
    Custom agent workflow to fetch, summarize papers, and optionally generate a PDF report.
    Returns the formatted output and the PDF filename (if generated).
    """
    try:
        # Validate Groq API key
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logging.error("GROQ_API_KEY not found in .env")
            return "Error: GROQ_API_KEY not found in .env", None

        # Warn about Semantic Scholar API key
        if "semantic_scholar" in sources and not os.getenv("SEMANTIC_SCHOLAR_API_KEY"):
            logging.warning("No SEMANTIC_SCHOLAR_API_KEY found in .env, rate limits may apply")

        # Initialize Groq LLM
        model_name = "llama-3.1-70b-versatile"
        try:
            llm = ChatGroq(
                model=model_name,
                api_key=api_key,
                temperature=0.0,
                max_tokens=200
            )
            logging.info(f"Using model: {model_name}")
        except Exception as e:
            logging.warning(f"Failed to load LLaMA-3.1-70B model: {e}. Falling back to LLaMA-3.1-8B.")
            llm = ChatGroq(
                model="llama-3.1-8b-instant",
                api_key=api_key,
                temperature=0.0,
                max_tokens=200
            )
            model_name = "llama-3.1-8b-instant"

        logging.info(f"Fetching {max_results} papers for query: {query}, sources: {sources}")
        papers = fetch_papers(query, max_results, sources)
        if not papers:
            logging.warning(f"No papers found for query: {query}")
            return "No papers found.", None

        result = []
        for i, paper in enumerate(papers, 1):
            logging.debug(f"Calling summarize_paper for paper {i}: {paper['title']} with format: {summary_format}")
            summary = summarize_paper(paper, summary_format=summary_format)
            paper['summary'] = summary
            result.append(
                f"**Paper {i}**\n"
                f"Title: {paper['title']}\n"
                f"Authors: {', '.join(paper['authors'])}\n"
                f"Published: {paper['published'].strftime('%Y-%m-%d')}\n"
                f"URL: {paper['url']}\n"
                f"Source: {'Semantic Scholar' if 'semanticscholar' in paper['url'] else 'arXiv'}\n"
                f"Summary:\n{summary}\n"
                f"{'-' * 50}"
            )

        # Generate PDF if requested
        pdf_filename = None
        if generate_pdf_report:
            pdf_filename = generate_pdf(papers, query)
        
        return "\n".join(result), pdf_filename
    except Exception as e:
        logging.error(f"Agent error: {e}")
        return f"Unable to process request: {str(e)}", None