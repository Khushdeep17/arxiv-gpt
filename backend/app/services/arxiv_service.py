import arxiv
import logging
from functools import lru_cache
import tenacity

logger = logging.getLogger(__name__)

# Lightweight query expansion mapping for common AI/CS topics
SEARCH_ALIASES = {
    "self-driving": '"autonomous driving" OR "autonomous vehicles" OR "self-driving"',
    "self-driving cars": '"autonomous driving" OR "autonomous vehicles" OR "self-driving"',
    "autonomous driving": '"autonomous driving" OR "autonomous vehicles" OR "self-driving"',
    "rag": '"retrieval augmented generation" OR RAG',
    "retrieval augmented generation": '"retrieval augmented generation" OR RAG',
    "llm": '"large language model" OR "large language models" OR LLM',
    "llms": '"large language model" OR "large language models" OR LLMs',
    "large language model": '"large language model" OR "large language models" OR LLM',
    "speech": '"text to speech" OR "speech synthesis" OR TTS',
    "speech generation": '"text to speech" OR "speech synthesis" OR TTS',
    "speech synthesis": '"text to speech" OR "speech synthesis" OR TTS',
    "tts": '"text to speech" OR "speech synthesis" OR TTS',
    "vision": '"computer vision" OR "object detection" OR "image segmentation"',
    "computer vision": '"computer vision" OR "object detection" OR "image segmentation"',
    "nlp": '"natural language processing" OR NLP',
    "natural language processing": '"natural language processing" OR NLP',
    "reinforcement learning": '"reinforcement learning" OR RL',
    "rl": '"reinforcement learning" OR RL',
    "diffusion": '"diffusion model" OR "generative model"',
    "robot": 'robotics OR robot OR manipulation',
    "robotics": 'robotics OR robot OR manipulation',
    "chatbot": '"dialogue systems" OR "conversational AI" OR chatbot',
    "chatbots": '"dialogue systems" OR "conversational AI" OR chatbots',
}

# Category-aware search heuristics mapping keywords to primary arXiv categories
CATEGORY_MAP = {
    "self-driving": ["cs.CV", "cs.RO", "cs.AI"],
    "autonomous": ["cs.CV", "cs.RO", "cs.AI"],
    "vision": ["cs.CV"],
    "image": ["cs.CV"],
    "nlp": ["cs.CL"],
    "language": ["cs.CL"],
    "rag": ["cs.CL", "cs.AI"],
    "llm": ["cs.CL", "cs.AI"],
    "speech": ["cs.SD", "eess.AS"],
    "audio": ["cs.SD", "eess.AS"],
    "tts": ["cs.SD", "eess.AS"],
    "robot": ["cs.RO"],
    "robotics": ["cs.RO"],
    "reinforcement": ["cs.LG", "cs.AI"],
    "diffusion": ["cs.CV", "cs.LG"],
    "chatbot": ["cs.CL", "cs.AI"],
}


class ArxivService:

    @staticmethod
    def _optimize_query(query: str) -> str:
        """
        Optimizes user search query using keyword expansion and category heuristics.
        Returns arXiv-formatted search query string.
        """
        raw_query = query.strip()
        if not raw_query:
            return raw_query

        lowered = raw_query.lower()

        # Step 1: Query expansion using aliases
        expanded_term = None
        for key, alias in SEARCH_ALIASES.items():
            if key in lowered:
                expanded_term = alias
                break

        base_query = expanded_term if expanded_term else raw_query

        # Step 2: Category matching heuristics
        matched_cats = set()
        for key, cats in CATEGORY_MAP.items():
            if key in lowered:
                matched_cats.update(cats)

        # Step 3: Combine query with categories if matched
        if matched_cats:
            cat_query = " OR ".join(f"cat:{cat}" for cat in sorted(matched_cats))
            optimized = f"({base_query}) AND ({cat_query})"
        else:
            optimized = base_query

        logger.info(f"Optimized query: '{raw_query}' -> '{optimized}'")
        return optimized

    @staticmethod
    @lru_cache(maxsize=32)
    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=6),
        retry=tenacity.retry_if_exception_type(Exception),
    )
    def fetch_papers(query: str, max_results: int = 5):
        try:
            optimized_query = ArxivService._optimize_query(query)
            client = arxiv.Client(page_size=max_results)

            search = arxiv.Search(
                query=optimized_query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )

            papers = []

            for result in client.results(search):
                papers.append({
                    "title": result.title,
                    "summary": result.summary.strip() if result.summary else "",
                    "url": result.pdf_url,
                    "authors": [a.name for a in result.authors],
                    "published": result.published.strftime("%Y-%m-%d"),
                    "category": result.primary_category
                })

            logger.info(f"Fetched {len(papers)} papers for query='{query}' (optimized='{optimized_query}')")
            return papers

        except Exception as e:
            logger.error(f"Arxiv fetch failed: {e}")
            return []

