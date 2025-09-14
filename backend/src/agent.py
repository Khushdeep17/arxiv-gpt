import os
import logging
from dotenv import load_dotenv
from dateutil.parser import parse

from .fetch_papers import fetch_papers
from .summarize import summarize_paper
from .generate_pdf import generate_pdf

load_dotenv()

def run_agent(query, max_results=3, generate_pdf_report=False):
    """
    Fetch and summarize papers from arXiv.
    Returns:
        - formatted string ready for frontend display
        - PDF filename (if generate_pdf_report=True)
    """
    try:
        if not query or not isinstance(query, str):
            return "Invalid query provided.", None

        if max_results > 10:
            max_results = 10  # enforce max cap

        papers = fetch_papers(query, max_results)
        if not papers:
            return "No papers found.", None

        result_lines = []

        for i, paper in enumerate(papers, start=1):
            # Convert published string to datetime for formatting
            published = paper['published']
            if isinstance(published, str):
                try:
                    published = parse(published)
                except Exception:
                    published = paper['published']
            paper['published'] = published

            # Summarize using Groq if API key exists
            summary_dict = summarize_paper(paper) if os.getenv("GROQ_API_KEY") else {
                "summary": [paper['summary']],
                "raw": paper['summary']
            }
            paper['summary'] = summary_dict

            # Format summary as bullets
            summary_text = "\n".join([f"- {line}" for line in summary_dict.get("summary", [])])
            result_lines.append(
                f"**Paper {i}**\n"
                f"Title: {paper['title']}\n"
                f"Authors: {', '.join(paper['authors'])}\n"
                f"Published: {paper['published'].strftime('%Y-%m-%d') if hasattr(paper['published'], 'strftime') else paper['published']}\n"
                f"URL: {paper['url']}\n"
                f"Summary:\n{summary_text}\n"
                + "-"*50
            )

        pdf_filename = generate_pdf(papers, query) if generate_pdf_report else None
        return "\n".join(result_lines), pdf_filename

    except Exception as e:
        logging.error(f"Agent error: {e}")
        return f"Unable to process request: {str(e)}", None
