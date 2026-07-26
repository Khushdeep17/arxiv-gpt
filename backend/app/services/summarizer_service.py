import json
import re
import logging
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from app.core.config import settings

logger = logging.getLogger(__name__)


PROMPT = ChatPromptTemplate.from_template("""
You summarize research papers for a dashboard that users scan in under 30 seconds.
Return ONLY valid JSON. Keep every field concise and easy to scan.
Focus on the main contribution, core methodology, and headline findings.
Do not rewrite the abstract or include unnecessary implementation details.
Use short bullet points and do not invent information.

Schema:
{{
 "tldr": "1 concise sentence",
 "key_contributions": ["1-3 concise bullets"],
 "methods": ["1-3 concise bullets"],
 "results": ["1-3 concise bullets"],
 "why_it_matters": "1 concise sentence",
 "citation": "Surname et al., YEAR"
}}

Title: {title}
Authors: {authors}
Published: {published}

Abstract:
{abstract}
""")


# 🔥 Create ONCE (Huge performance win)
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    groq_api_key=settings.GROQ_API_KEY,
    temperature=0.1,
    max_tokens=1400
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