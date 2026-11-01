import os
import unittest
import uuid
from unittest.mock import patch, MagicMock
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.models.db_models import User, Paper, Summary, Search, SearchPaper, Collection, CollectionPaper, SavedPaper
from app.services.persistence_service import PersistenceService
from app.agent.research_agent import ResearchAgent
from app.tests.db_test_utils import create_test_engine, safe_clean_test_tables, safe_teardown_test_db


class TestPersistence(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Creates an isolated test engine (defaults to SQLite in-memory, or validated arxiv_gpt_test)
        cls.engine = None
        cls.SessionLocal = None
        engine = create_test_engine()
        cls.engine = engine
        try:
            Base.metadata.create_all(engine)
            cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        except Exception:
            try:
                engine.dispose()
            except Exception:
                pass
            cls.engine = None
            raise

    @classmethod
    def tearDownClass(cls):
        if cls.engine is not None:
            safe_teardown_test_db(cls.engine)

    def setUp(self):
        self.db: Session = self.SessionLocal()

    def tearDown(self):
        try:
            if hasattr(self, "db") and self.db is not None:
                safe_clean_test_tables(self.db, self.engine)
        finally:
            if hasattr(self, "db") and self.db is not None:
                self.db.close()

    def test_paper_deduplication_by_arxiv_id_and_url(self):
        paper_data1 = {
            "title": "Attention Is All You Need",
            "authors": ["Ashish Vaswani", "Noam Shazeer"],
            "published": "2017-06-12",
            "category": "cs.CL",
            "url": "https://arxiv.org/abs/1706.03762v1",
            "summary": "The dominant sequence transduction models...",
        }
        paper1 = PersistenceService.get_or_create_paper(self.db, paper_data1)
        self.db.commit()

        self.assertIsNotNone(paper1.id)
        self.assertEqual(paper1.arxiv_id, "1706.03762")

        # Second paper with same canonical arxiv_id but different url version
        paper_data2 = {
            "title": "Attention Is All You Need (Updated)",
            "authors": ["Ashish Vaswani", "Noam Shazeer"],
            "published": "2017-06-12",
            "category": "cs.CL",
            "url": "https://arxiv.org/pdf/1706.03762",
            "summary": "Abstract content",
        }
        paper2 = PersistenceService.get_or_create_paper(self.db, paper_data2)
        self.db.commit()

        self.assertEqual(paper1.id, paper2.id)

        # Confirm only one paper in DB
        papers_count = len(self.db.scalars(select(Paper)).all())
        self.assertEqual(papers_count, 1)

    def test_summary_persistence_and_version_scoped_reuse(self):
        paper = Paper(
            title="Transformer Paper",
            url="https://arxiv.org/abs/1706.03762",
            arxiv_id="1706.03762",
            authors=["Vaswani et al."],
        )
        self.db.add(paper)
        self.db.commit()

        summary_data = {
            "tldr": "Introduces Transformer architecture.",
            "key_contributions": ["Self-attention mechanism", "Replaces recurrent layers"],
            "methods": ["Multi-head attention", "Positional encoding"],
            "results": ["State-of-the-art BLEU score"],
            "why_it_matters": "Foundation for modern LLMs.",
            "citation": "Vaswani et al., 2017",
        }

        # Save under model openai/gpt-oss-120b and version v1.0
        saved_summary = PersistenceService.save_summary(
            self.db,
            paper_id=paper.id,
            summary_data=summary_data,
            model_name="openai/gpt-oss-120b",
            prompt_version="v1.0",
        )
        self.db.commit()

        self.assertIsNotNone(saved_summary.id)

        # Compatible lookup matches
        cached = PersistenceService.get_cached_summary(
            self.db,
            paper_id=paper.id,
            model_name="openai/gpt-oss-120b",
            prompt_version="v1.0",
        )
        self.assertIsNotNone(cached)
        self.assertEqual(cached.tldr, "Introduces Transformer architecture.")

        # Incompatible prompt version returns None (prevents stale summary reuse across prompt upgrades)
        incompatible_version = PersistenceService.get_cached_summary(
            self.db,
            paper_id=paper.id,
            model_name="openai/gpt-oss-120b",
            prompt_version="v2.0",
        )
        self.assertIsNone(incompatible_version)

        # Incompatible model returns None
        incompatible_model = PersistenceService.get_cached_summary(
            self.db,
            paper_id=paper.id,
            model_name="llama-3-8b",
            prompt_version="v1.0",
        )
        self.assertIsNone(incompatible_model)

    def test_search_and_ranked_paper_associations(self):
        papers_data = [
            {
                "title": f"Paper {i}",
                "url": f"https://arxiv.org/abs/2601.0000{i}",
                "authors": [f"Author {i}"],
                "published": "2026-01-01",
                "category": "cs.AI",
                "summary": {
                    "tldr": f"TLDR {i}",
                    "key_contributions": [f"Contribution {i}"],
                    "methods": [f"Method {i}"],
                    "results": [f"Result {i}"],
                    "why_it_matters": f"Why {i}",
                    "citation": f"Author {i}, 2026",
                },
            }
            for i in range(1, 4)
        ]

        search = PersistenceService.record_search(
            db=self.db,
            query="artificial intelligence",
            max_results=3,
            enriched_papers=papers_data,
            pdf_filename="arxiv_gpt_ai.pdf",
        )

        self.assertIsNotNone(search.id)
        self.assertEqual(search.query, "artificial intelligence")
        self.assertEqual(len(search.search_papers), 3)

        # Verify ranks are ordered 1, 2, 3
        ranks = [sp.rank for sp in search.search_papers]
        self.assertEqual(ranks, [1, 2, 3])

        # Security check: unauthenticated search retrieval returns empty list by default
        unscoped_blocked = PersistenceService.get_recent_searches(self.db, limit=10)
        self.assertEqual(unscoped_blocked, [])

        # Internal/admin retrieval with allow_unscoped=True returns the recent search
        recent = PersistenceService.get_recent_searches(self.db, limit=10, allow_unscoped=True)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["query"], "artificial intelligence")
        self.assertEqual(recent[0]["pdf_filename"], "arxiv_gpt_ai.pdf")
        self.assertEqual(len(recent[0]["papers"]), 3)
        self.assertEqual(recent[0]["papers"][0]["title"], "Paper 1")
        self.assertEqual(recent[0]["papers"][0]["summary"]["tldr"], "TLDR 1")


    def test_database_rollback_on_failure(self):
        # Force a failure during search recording to verify complete rollback
        with patch.object(self.db, "flush", side_effect=RuntimeError("Simulated database failure")):
            with self.assertRaises(RuntimeError):
                PersistenceService.record_search(
                    db=self.db,
                    query="failed query",
                    max_results=3,
                    enriched_papers=[{"title": "P", "url": "https://arxiv.org/abs/1"}],
                )

        # Verify no orphan search was committed
        searches = self.db.scalars(select(Search)).all()
        self.assertEqual(len(searches), 0)

    def test_unique_constraints_enforced(self):
        # SearchPaper unique constraint (search_id, paper_id)
        search = Search(query="test query")
        paper = Paper(title="Unique Paper", url="https://arxiv.org/abs/2601.99999")
        self.db.add_all([search, paper])
        self.db.commit()

        sp1 = SearchPaper(search_id=search.id, paper_id=paper.id, rank=1)
        self.db.add(sp1)
        self.db.commit()

        sp2 = SearchPaper(search_id=search.id, paper_id=paper.id, rank=2)
        self.db.add(sp2)
        with self.assertRaises(IntegrityError):
            self.db.commit()
        self.db.rollback()

    @patch("app.services.arxiv_service.ArxivService.fetch_papers")
    @patch("app.services.summarizer_service.SummarizerService.summarize")
    def test_research_agent_summary_cache_reuse(self, mock_summarize, mock_fetch):
        # Pre-populate paper and summary in DB
        paper_url = "https://arxiv.org/abs/1706.03762"
        paper = Paper(title="Attention Is All You Need", url=paper_url, arxiv_id="1706.03762", authors=["Vaswani"])
        self.db.add(paper)
        self.db.flush()

        PersistenceService.save_summary(
            self.db,
            paper_id=paper.id,
            summary_data={
                "tldr": "Cached TLDR from DB",
                "key_contributions": ["Contribution"],
                "methods": ["Method"],
                "results": ["Result"],
                "why_it_matters": "Matters",
                "citation": "Vaswani 2017",
            },
        )
        self.db.commit()

        # Mock ArxivService returning this paper
        mock_fetch.return_value = [
            {
                "title": "Attention Is All You Need",
                "url": paper_url,
                "authors": ["Vaswani"],
                "published": "2017-06-12",
                "category": "cs.CL",
                "summary": "Raw abstract",
            }
        ]

        # Run ResearchAgent with DB session
        result, _ = ResearchAgent.run("transformers", max_results=1, db=self.db)

        # SummarizerService.summarize should NOT have been called because cached summary was reused!
        self.assertEqual(mock_summarize.call_count, 0)
        self.assertEqual(len(result["papers"]), 1)
        self.assertEqual(result["papers"][0]["summary"]["tldr"], "Cached TLDR from DB")


if __name__ == "__main__":
    unittest.main()
