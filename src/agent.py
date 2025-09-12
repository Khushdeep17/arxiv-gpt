from langchain_groq import ChatGroq
from fetch_papers import fetch_papers
from summarize import summarize_paper
from generate_pdf import generate_pdf
from dotenv import load_dotenv
import os
import logging

load_dotenv()

def run_agent(query, max_results=3, generate_pdf_report=False):
    """
    Custom agent workflow to fetch and summarize papers from arXiv.
    Returns the formatted output and the PDF filename (if generated).
    """
    try:
        if not query or not isinstance(query, str):
            return "Invalid query provided.", None
        if max_results > 10:
            max_results = 10  # Cap at 10
        if not os.getenv("GROQ_API_KEY"):
            return "Error: GROQ_API_KEY not found in .env", None

        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.0,
            max_tokens=100  # Reduced for speed
        )
        logging.info(f"Fetching {max_results} papers for query: {query}")
        papers = fetch_papers(query, max_results)
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
                f"Summary:\n{summary}\n"
                f"{'-' * 50}"
            )

        pdf_filename = None
        if generate_pdf_report:
            pdf_filename = generate_pdf(papers, query)
        
        return "\n".join(result), pdf_filename
    except Exception as e:
        logging.error(f"Agent error: {e}")
        return f"Unable to process request: {str(e)}", None