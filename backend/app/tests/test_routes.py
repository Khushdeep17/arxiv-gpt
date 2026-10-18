import os
import unittest
from unittest.mock import patch
from starlette.testclient import TestClient

# Provide placeholder for Groq import requirement in test environment
os.environ.setdefault("GROQ_API_KEY", "mock_groq_key_for_testing")

from app.main import app


class TestRoutes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        # Clean up any test artifacts or empty directories
        if os.path.exists("data"):
            try:
                os.rmdir("data")
            except OSError:
                pass
        if os.path.exists("logs"):
            try:
                import shutil
                shutil.rmtree("logs", ignore_errors=True)
            except OSError:
                pass

    def test_health_endpoint_returns_ok_json(self):
        # Confirms /health returns 200 {"status": "ok"} and is not shadowed by catch-all
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertEqual(response.headers.get("content-type"), "application/json")

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


if __name__ == "__main__":
    unittest.main()
