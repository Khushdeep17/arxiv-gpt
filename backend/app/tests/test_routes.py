import os
import unittest
import uuid
from unittest.mock import patch
from starlette.testclient import TestClient
from sqlalchemy.orm import sessionmaker

# Provide placeholders for environment variables in test environment
os.environ.setdefault("GROQ_API_KEY", "mock_groq_key_for_testing")
os.environ.setdefault("JWT_SECRET_KEY", "mock_test_jwt_secret_key_for_routes_suite_32b!")

from app.db.base import Base
from app.db.session import get_db
from app.models import db_models
from app.main import app as fastapi_app
from app.core.security import create_access_token, hash_password
from app.tests.db_test_utils import create_test_engine, safe_clean_test_tables, safe_teardown_test_db


class TestRoutes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_engine = None
        cls.TestSession = None
        cls.client = None
        engine = create_test_engine()
        cls.test_engine = engine

        try:
            Base.metadata.create_all(engine)
            cls.TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

            def override_get_db():
                db = cls.TestSession()
                try:
                    yield db
                finally:
                    db.close()

            fastapi_app.dependency_overrides[get_db] = override_get_db
            cls.client = TestClient(fastapi_app)
        except Exception:
            # F-5: Restore dependency override and dispose engine on setup failure
            fastapi_app.dependency_overrides.pop(get_db, None)
            try:
                engine.dispose()
            except Exception:
                pass
            cls.test_engine = None
            raise

    @classmethod
    def tearDownClass(cls):
        # F-2: Restore only the specific dependency override owned by this test suite
        try:
            fastapi_app.dependency_overrides.pop(get_db, None)
        finally:
            if cls.test_engine is not None:
                safe_teardown_test_db(cls.test_engine)

        # Clean up any test artifacts or empty directories (F-1: do not delete logs directory)
        if os.path.exists("data"):
            try:
                os.rmdir("data")
            except OSError:
                pass

    def tearDown(self):
        if hasattr(self, "TestSession") and self.TestSession is not None and self.test_engine is not None:
            session = self.TestSession()
            try:
                safe_clean_test_tables(session, self.test_engine)
            finally:
                session.close()

    def test_health_endpoint_returns_ok_json(self):
        # Confirms /health returns 200 {"status": "ok"} and is not shadowed by catch-all
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertEqual(response.headers.get("content-type"), "application/json")
        self.assertIn("x-request-id", response.headers)
        self.assertIn("x-process-time", response.headers)

    def test_head_probes_succeed_for_platform_healthchecks(self):
        self.assertEqual(self.client.head("/health").status_code, 200)
        self.assertEqual(self.client.head("/").status_code, 200)

    def test_catch_all_blocks_static_path_traversal(self):
        response = self.client.get("/..%2F..%2Fapp%2Fmain.py")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("add_request_observability", response.text)

    def test_search_query_too_short_returns_400(self):
        response = self.client.post("/search", json={"query": "ab"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Query too short", response.text)

    @patch("app.agent.research_agent.ResearchAgent.run")
    def test_search_success_contract(self, mock_agent_run):
        mock_agent_run.return_value = (
            {
                "papers": [
                    {
                        "title": "Test Paper",
                        "authors": ["Test Author"],
                        "published": "2026-01-01",
                        "category": "cs.AI",
                        "url": "https://arxiv.org/abs/2601.00000",
                        "summary": {
                            "tldr": "A test paper.",
                            "key_contributions": ["Contribution 1"],
                            "methods": ["Method 1"],
                            "results": ["Result 1"],
                            "why_it_matters": "Matters.",
                            "citation": "Author et al., 2026"
                        }
                    }
                ],
                "query": "artificial intelligence"
            },
            "arxiv_gpt_test.pdf"
        )

        response = self.client.post(
            "/search",
            json={
                "query": "artificial intelligence",
                "max_results": 1,
                "generate_pdf": True
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["query"], "artificial intelligence")
        self.assertEqual(len(data["papers"]), 1)
        self.assertEqual(data["pdf_filename"], "arxiv_gpt_test.pdf")

    def test_download_pdf_missing_file_returns_404(self):
        response = self.client.get("/download_pdf", params={"filename": "nonexistent_file_xyz.pdf"})
        self.assertEqual(response.status_code, 404)
        self.assertIn("PDF not found", response.text)

    def test_download_pdf_existing_file_returns_pdf(self):
        os.makedirs("data", exist_ok=True)
        test_file_path = os.path.join("data", "test_mock_report.pdf")
        with open(test_file_path, "wb") as f:
            f.write(b"%PDF-1.4 mock pdf content")

        try:
            response = self.client.get("/download_pdf", params={"filename": "test_mock_report.pdf"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers.get("content-type"), "application/pdf")
            self.assertTrue(response.content.startswith(b"%PDF-1.4"))
        finally:
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
            try:
                os.rmdir("data")
            except OSError:
                pass

    def test_download_pdf_path_traversal_sanitized(self):
        response = self.client.get("/download_pdf", params={"filename": "../../app/main.py"})
        self.assertEqual(response.status_code, 404)

    def test_history_endpoint_requires_authentication(self):
        # Security test: Unauthenticated visitor must be rejected with 401
        response = self.client.get("/history")
        self.assertEqual(response.status_code, 401)
        self.assertIn("WWW-Authenticate", response.headers)

    def test_history_endpoint_returns_scoped_user_searches(self):
        test_user_id = uuid.uuid4()
        session = self.TestSession()
        try:
            from app.models.db_models import User
            from app.services.persistence_service import PersistenceService

            user = User(
                id=test_user_id,
                email="history_user@example.com",
                hashed_password=hash_password("Password123!"),
                is_active=True,
            )
            session.add(user)
            session.commit()

            PersistenceService.record_search(
                db=session,
                query="scoped user query",
                max_results=1,
                enriched_papers=[
                    {
                        "title": "Scoped Paper",
                        "url": "https://arxiv.org/abs/2601.12345",
                        "authors": ["Author"],
                        "summary": {"tldr": "TLDR", "citation": "Author 2026"},
                    }
                ],
                user_id=test_user_id,
            )
        finally:
            session.close()

        token = create_access_token(subject=str(test_user_id))
        response = self.client.get("/history", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["query"], "scoped user query")


if __name__ == "__main__":
    unittest.main()
