import json
import re
import logging
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from app.core.config import settings

logger = logging.getLogger(__name__)


PROMPT = ChatPromptTemplate.from_template("""
Return ONLY valid JSON.

Schema:
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


# 🔥 Create ONCE (Huge performance win)
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=settings.GROQ_API_KEY,
    temperature=0.1,
    max_tokens=700
)


def extract_json(text: str):
    match = re.search(r'\{.*\}', text, re.DOTALL)

    if match:
        return json.loads(match.group())

    raise ValueError("No JSON found")


class SummarizerService:

    @staticmethod
    def summarize(paper: dict):

        try:
            response = llm.invoke(
                PROMPT.format_messages(
                    title=paper["title"],
                    authors=", ".join(paper["authors"]),
                    published=paper["published"],
                    abstract=paper["summary"]
                )
            ).content.strip()

            return extract_json(response)

        except Exception as e:

            logger.error(f"LLM summary failed: {e}")

            # HARD fallback
            return {
                "tldr": paper.get("summary", "")[:300],
                "key_contributions": [],
                "methods": [],
                "results": [],
                "why_it_matters": "See paper.",
                "citation": f"{paper['authors'][0]} et al., {paper['published'][:4]}"
            }
