import os
import logging
from dotenv import load_dotenv
from dateutil.parser import parse

from .fetch_papers import fetch_papers
from .summarize import summarize_paper
from .generate_pdf import generate_pdf

load_dotenv()

logger = logging.getLogger(__name__)


def normalize_date(published):
    try:
        if isinstance(published, str):
            published = parse(published)

        if hasattr(published, "strftime"):
            return published.strftime("%Y-%m-%d")

    except Exception:
        pass

    return str(published)


def run_agent(query, max_results=3, generate_pdf_report=False):
    """
    Production-safe agent.

    Returns:
        payload dict
        pdf filename
    """

    if not query or not isinstance(query, str):
        return {"papers": [], "query": query}, None

    max_results = min(max_results, 10)

    try:
        papers = fetch_papers(query, max_results)

        if not papers:
            return {"papers": [], "query": query}, None

        enriched_papers = []

        for paper in papers:

            paper["published"] = normalize_date(
                paper.get("published")
            )

            # ---------- SAFE SUMMARY ----------
            summary_structured = None

            if os.getenv("GROQ_API_KEY"):
                try:
                    summary_structured = summarize_paper(paper)

                except Exception as e:
                    logger.error(f"Summarization failed: {e}")

            # fallback if LLM fails
            if not summary_structured:
                summary_structured = {
                    "tldr": paper.get("summary", "")[:300],
                    "key_contributions": [],
                    "methods": [],
                    "results": [],
                    "why_it_matters": "See paper.",
                    "citation": f"{paper.get('authors',['Unknown'])[0]} et al."
                }

            enriched_papers.append({
                "title": paper.get("title"),
                "authors": paper.get("authors", []),
                "published": paper.get("published"),
                "url": paper.get("url"),
                "summary": summary_structured
            })

        pdf_filename = None

        if generate_pdf_report:
            try:
                pdf_filename = generate_pdf(enriched_papers, query)
            except Exception as e:
                logger.error(f"PDF generation failed: {e}")

        return {
            "papers": enriched_papers,
            "query": query
        }, pdf_filename

    except Exception as e:
        logger.error(f"Agent fatal error: {e}")
        return {"papers": [], "query": query}, None
