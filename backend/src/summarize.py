import os
import json
import logging
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

load_dotenv()

logger = logging.getLogger(__name__)

PROMPT = ChatPromptTemplate.from_template("""
You MUST return ONLY valid JSON.

DO NOT write explanations.
DO NOT wrap in markdown.
DO NOT write ```.

Return EXACT schema:

{{
 "tldr": "1 sentence",
 "key_contributions": ["bullet"],
 "methods": ["bullet"],
 "results": ["bullet"],
 "why_it_matters": "1-2 sentences",
 "citation": "Author et al., Year"
}}

Title: {title}
Authors: {authors}
Published: {published}

Abstract:
{abstract}
""")


def extract_json(text):
    """
    LLMs often wrap JSON.
    This safely extracts it.
    """

    match = re.search(r'\{.*\}', text, re.DOTALL)

    if match:
        return json.loads(match.group())

    raise ValueError("No JSON found in response")


def summarize_paper(paper):

    groq_key = os.getenv("GROQ_API_KEY")

    if not groq_key:
        raise ValueError("Missing GROQ_API_KEY")

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=groq_key,
        temperature=0.1,
        max_tokens=700
    )

    try:

        response = llm.invoke(
            PROMPT.format_messages(
                title=paper["title"],
                authors=", ".join(paper["authors"]),
                published=paper["published"],
                abstract=paper["summary"]
            )
        ).content.strip()

        structured = extract_json(response)

        return structured

    except Exception as e:

        logger.error(f"Structured summary failed: {e}")

        # HARD fallback
        return {
            "tldr": paper["summary"][:300],
            "key_contributions": [],
            "methods": [],
            "results": [],
            "why_it_matters": "See paper.",
            "citation": f"{paper['authors'][0]} et al., {paper['published'][:4]}"
        }
