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

logging.basicConfig(filename='logs/arxiv_gpt.log', level=logging.INFO)

def run_agent(query, max_results=3, generate_pdf_report=False, sources=["arxiv"]):
    """
    Custom agent workflow to fetch, summarize papers, and optionally generate a PDF report.
    Returns the formatted output and the PDF filename (if generated).
    """
    try:
        # Initialize Groq LLM
        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=os.getenv("GROQ_API_KEY")
        )
        logging.info(f"Fetching {max_results} papers for query: {query}, sources: {sources}")
        papers = fetch_papers(query, max_results, sources)
        if not papers:
            return "No papers found.", None

        result = []
        for i, paper in enumerate(papers, 1):
            logging.info(f"Summarizing paper {i}: {paper['title']}")
            summary = summarize_paper(paper)
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