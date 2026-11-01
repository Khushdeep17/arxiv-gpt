import re
import uuid
import logging
from typing import List, Dict, Optional, Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.db_models import Paper, Summary, Search, SearchPaper

logger = logging.getLogger(__name__)

ARXIV_ID_PATTERN = re.compile(r"(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)", re.IGNORECASE)
OLD_ARXIV_ID_PATTERN = re.compile(r"(?:abs|pdf)/([a-z\-]+(?:\.[A-Z]{2})?/[0-9]{7}(?:v[0-9]+)?)", re.IGNORECASE)


class PersistenceService:
    @staticmethod
    def extract_arxiv_id(url: str) -> Optional[str]:
        """
        Extracts the canonical arXiv identifier from an abs or pdf URL.
        e.g., 'https://arxiv.org/pdf/1706.03762' -> '1706.03762'
        """
        if not url:
            return None

        match = ARXIV_ID_PATTERN.search(url)
        if match:
            # Strip version suffix (e.g. '1706.03762v1' -> '1706.03762') for canonical paper identity
            arxiv_id = match.group(1)
            return re.sub(r"v\d+$", "", arxiv_id)

        old_match = OLD_ARXIV_ID_PATTERN.search(url)
        if old_match:
            arxiv_id = old_match.group(1)
            return re.sub(r"v\d+$", "", arxiv_id)

        return None

    @staticmethod
    def find_paper(db: Session, url: str, arxiv_id: Optional[str] = None) -> Optional[Paper]:
        """
        Pure read-only query to find an existing paper by arXiv ID or URL without session mutation.
        """
        clean_url = url.strip()
        effective_arxiv_id = arxiv_id or PersistenceService.extract_arxiv_id(clean_url)

        if effective_arxiv_id:
            paper = db.scalar(select(Paper).where(Paper.arxiv_id == effective_arxiv_id))
            if paper:
                return paper

        if clean_url:
            return db.scalar(select(Paper).where(Paper.url == clean_url))

        return None

    @staticmethod
    def get_or_create_paper(db: Session, paper_data: Dict[str, Any]) -> Paper:
        """
        Finds an existing paper by arXiv ID or URL, or creates a new canonical record.
        Uses nested transaction savepoint to handle concurrent insertion collisions gracefully.
        """
        url = paper_data.get("url", "").strip()
        arxiv_id = paper_data.get("arxiv_id") or PersistenceService.extract_arxiv_id(url)

        paper = PersistenceService.find_paper(db, url=url, arxiv_id=arxiv_id)

        if paper:
            # Update fields if new metadata is more complete
            if not paper.arxiv_id and arxiv_id:
                paper.arxiv_id = arxiv_id
            if not paper.abstract and paper_data.get("summary"):
                abstract_text = paper_data.get("summary")
                if isinstance(abstract_text, str):
                    paper.abstract = abstract_text
            return paper

        # Create fresh canonical paper record
        abstract_val = paper_data.get("abstract")
        if not abstract_val and isinstance(paper_data.get("summary"), str):
            abstract_val = paper_data.get("summary")

        new_paper = Paper(
            arxiv_id=arxiv_id,
            title=paper_data.get("title", "Untitled").strip(),
            authors=paper_data.get("authors") or [],
            published=paper_data.get("published"),
            category=paper_data.get("category"),
            url=url,
            abstract=abstract_val,
        )

        from sqlalchemy.exc import IntegrityError
        try:
            with db.begin_nested():
                db.add(new_paper)
                db.flush()
                logger.info(f"Created canonical paper: arxiv_id={arxiv_id}, title='{new_paper.title[:40]}...'")
                return new_paper
        except IntegrityError:
            # Concurrent process inserted the same paper; re-fetch existing
            existing_paper = PersistenceService.find_paper(db, url=url, arxiv_id=arxiv_id)
            if existing_paper:
                return existing_paper
            raise

    @staticmethod
    def get_cached_summary(
        db: Session,
        paper_id: uuid.UUID,
        model_name: Optional[str] = None,
        prompt_version: Optional[str] = None,
    ) -> Optional[Summary]:
        """
        Retrieves a cached summary only if it matches the current model and prompt version.
        """
        target_model = model_name or settings.SUMMARY_MODEL_NAME
        target_version = prompt_version or settings.SUMMARY_PROMPT_VERSION

        return db.scalar(
            select(Summary).where(
                Summary.paper_id == paper_id,
                Summary.model_name == target_model,
                Summary.prompt_version == target_version,
            )
        )

    @staticmethod
    def save_summary(
        db: Session,
        paper_id: uuid.UUID,
        summary_data: Dict[str, Any],
        model_name: Optional[str] = None,
        prompt_version: Optional[str] = None,
    ) -> Summary:
        """
        Persists a structured 6-field summary for a paper, scoped by model and prompt version.
        Uses nested savepoint to handle concurrent inserts safely.
        """
        target_model = model_name or settings.SUMMARY_MODEL_NAME
        target_version = prompt_version or settings.SUMMARY_PROMPT_VERSION

        existing = db.scalar(
            select(Summary).where(
                Summary.paper_id == paper_id,
                Summary.model_name == target_model,
                Summary.prompt_version == target_version,
            )
        )

        if existing:
            existing.tldr = summary_data.get("tldr", existing.tldr)
            existing.key_contributions = summary_data.get("key_contributions", existing.key_contributions)
            existing.methods = summary_data.get("methods", existing.methods)
            existing.results = summary_data.get("results", existing.results)
            existing.why_it_matters = summary_data.get("why_it_matters", existing.why_it_matters)
            existing.citation = summary_data.get("citation", existing.citation)
            return existing

        summary = Summary(
            paper_id=paper_id,
            model_name=target_model,
            prompt_version=target_version,
            tldr=summary_data.get("tldr", ""),
            key_contributions=summary_data.get("key_contributions") or [],
            methods=summary_data.get("methods") or [],
            results=summary_data.get("results") or [],
            why_it_matters=summary_data.get("why_it_matters", ""),
            citation=summary_data.get("citation", ""),
        )

        from sqlalchemy.exc import IntegrityError
        try:
            with db.begin_nested():
                db.add(summary)
                db.flush()
                return summary
        except IntegrityError:
            existing = db.scalar(
                select(Summary).where(
                    Summary.paper_id == paper_id,
                    Summary.model_name == target_model,
                    Summary.prompt_version == target_version,
                )
            )
            if existing:
                return existing
            raise

    @staticmethod
    def record_search(
        db: Session,
        query: str,
        max_results: int,
        enriched_papers: List[Dict[str, Any]],
        pdf_filename: Optional[str] = None,
        optimized_query: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> Search:
        """
        Atomically records a search event and its ranked paper associations in PostgreSQL.
        Rolls back explicitly on any failure to prevent database corruption.
        """
        try:
            search = Search(
                user_id=user_id,
                query=query.strip(),
                optimized_query=optimized_query,
                max_results=max_results,
                pdf_filename=pdf_filename,
            )
            db.add(search)
            db.flush()

            for rank, paper_dict in enumerate(enriched_papers, start=1):
                paper = PersistenceService.get_or_create_paper(db, paper_dict)

                summary_obj = paper_dict.get("summary")
                if isinstance(summary_obj, dict):
                    PersistenceService.save_summary(
                        db=db,
                        paper_id=paper.id,
                        summary_data=summary_obj,
                        model_name=settings.SUMMARY_MODEL_NAME,
                        prompt_version=settings.SUMMARY_PROMPT_VERSION,
                    )

                search_paper = SearchPaper(
                    search_id=search.id,
                    paper_id=paper.id,
                    rank=rank,
                )
                db.add(search_paper)

            db.commit()
            db.refresh(search)
            logger.info(f"Recorded search '{query}' with {len(enriched_papers)} papers (search_id={search.id})")
            return search
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to record search in database: {e}")
            raise

    @staticmethod
    def get_recent_searches(
        db: Session,
        user_id: Optional[uuid.UUID] = None,
        limit: int = 20,
        allow_unscoped: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Returns recent searches scoped to a specific user.
        To prevent search query/history leakage across unauthenticated visitors,
        returns an empty list when user_id is None unless allow_unscoped=True is specified.
        """
        if user_id is None and not allow_unscoped:
            return []

        stmt = select(Search)
        if user_id is not None:
            stmt = stmt.where(Search.user_id == user_id)

        stmt = stmt.order_by(Search.created_at.desc()).limit(limit)
        searches = db.scalars(stmt).all()

        results = []
        for s in searches:
            papers_list = []
            for sp in s.search_papers:
                p = sp.paper
                # Find matching summary for current model version or most recent
                summary_data = None
                if p.summaries:
                    exact_match = next(
                        (sum_item for sum_item in p.summaries
                         if sum_item.model_name == settings.SUMMARY_MODEL_NAME
                         and sum_item.prompt_version == settings.SUMMARY_PROMPT_VERSION),
                        p.summaries[0]
                    )
                    summary_data = {
                        "tldr": exact_match.tldr,
                        "key_contributions": exact_match.key_contributions,
                        "methods": exact_match.methods,
                        "results": exact_match.results,
                        "why_it_matters": exact_match.why_it_matters,
                        "citation": exact_match.citation,
                    }

                papers_list.append({
                    "id": sp.rank,
                    "title": p.title,
                    "authors": p.authors,
                    "published": p.published or "",
                    "category": p.category or "",
                    "url": p.url,
                    "summary": summary_data or {
                        "tldr": "",
                        "key_contributions": [],
                        "methods": [],
                        "results": [],
                        "why_it_matters": "",
                        "citation": "",
                    },
                })

            results.append({
                "id": str(s.id),
                "query": s.query,
                "timestamp": s.created_at.strftime("%Y-%m-%d %H:%M:%S") if s.created_at else "",
                "pdf_filename": s.pdf_filename,
                "papers": papers_list,
            })

        return results

