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
        - payload dict with structured paper data
        - PDF filename (if generate_pdf_report=True)
    """
    try:
        if not query or not isinstance(query, str):
            return {"papers": [], "query": query}, None

        if max_results > 10:
            max_results = 10

        papers = fetch_papers(query, max_results)
        if not papers:
            return {"papers": [], "query": query}, None

        enriched_papers = []

        for paper in papers:
            # Normalize published date
            published = paper.get("published")
            if isinstance(published, str):
                try:
                    published = parse(published)
                except Exception:
                    pass

            paper["published"] = (
                published.strftime("%Y-%m-%d")
                if hasattr(published, "strftime")
                else paper.get("published")
            )

            # Summarize (Groq if available)
            if os.getenv("GROQ_API_KEY"):
                summary_dict = summarize_paper(paper)
                summary_text = " ".join(summary_dict.get("summary", []))
            else:
                summary_text = paper.get("summary", "")

            enriched_papers.append({
                "title": paper.get("title"),
                "authors": paper.get("authors", []),
                "published": paper.get("published"),
                "url": paper.get("url"),
                "summary": summary_text
            })

        pdf_filename = generate_pdf(enriched_papers, query) if generate_pdf_report else None

        return {
            "papers": enriched_papers,
            "query": query
        }, pdf_filename

    except Exception as e:
        logging.error(f"Agent error: {e}")
        return {"papers": [], "query": query}, None
