import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import arxiv

from app.services.arxiv_service import ArxivService


class DummyResult:
    def __init__(self, title="Attention Is All You Need", summary="Transformer paper",
                 pdf_url="https://arxiv.org/pdf/1706.03762", authors=None,
                 published=None, primary_category="cs.CL"):
        self.title = title
        self.summary = summary
        self.pdf_url = pdf_url
        self.authors = authors or [MagicMock(name="Ashish Vaswani")]
        self.authors[0].name = "Ashish Vaswani"
        self.published = published or datetime(2017, 6, 12)
        self.primary_category = primary_category


class TestArxivService(unittest.TestCase):

    def setUp(self):
        ArxivService._cached_search.cache_clear()

    def tearDown(self):
        ArxivService._cached_search.cache_clear()

    @patch("arxiv.Client")
    def test_fetch_papers_success(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.results.return_value = [DummyResult()]

        papers = ArxivService.fetch_papers("transformer", max_results=1)

        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]["title"], "Attention Is All You Need")
        self.assertEqual(papers[0]["authors"], ["Ashish Vaswani"])
        self.assertEqual(papers[0]["category"], "cs.CL")
        self.assertEqual(papers[0]["published"], "2017-06-12")

    @patch("arxiv.Client")
    def test_fetch_papers_empty_results_cached(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.results.return_value = []

        # First call: query returns empty
        papers1 = ArxivService.fetch_papers("nonexistent topic 12345", max_results=3)
        self.assertEqual(papers1, [])
        self.assertEqual(mock_client.results.call_count, 1)

        # Second call: hits LRU cache and does not call client.results again
        papers2 = ArxivService.fetch_papers("nonexistent topic 12345", max_results=3)
        self.assertEqual(papers2, [])
        self.assertEqual(mock_client.results.call_count, 1)

    @patch("arxiv.Client")
    def test_fetch_papers_retry_on_transient_error(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Fast retry wait in tests
        with patch("tenacity.wait_exponential.__call__", return_value=0.01):
            # Attempt 1 raises transient ConnectionError; Attempt 2 succeeds
            mock_client.results.side_effect = [
                ConnectionError("Temporary network glitch"),
                [DummyResult(title="Recovered Paper")]
            ]

            papers = ArxivService.fetch_papers("recovery test", max_results=1)
            self.assertEqual(len(papers), 1)
            self.assertEqual(papers[0]["title"], "Recovered Paper")
            self.assertEqual(mock_client.results.call_count, 2)

    @patch("arxiv.Client")
    def test_fetch_papers_exhaustion_returns_empty_and_not_cached(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Fast retry wait in tests
        with patch("tenacity.wait_exponential.__call__", return_value=0.01):
            mock_client.results.side_effect = ConnectionError("Persistent network failure")

            # Exhausts 3 attempts, logs, and returns empty list
            papers = ArxivService.fetch_papers("outage test", max_results=1)
            self.assertEqual(papers, [])
            self.assertEqual(mock_client.results.call_count, 3)

            # Confirm transient failure was NOT cached in LRU cache
            cache_info = ArxivService._cached_search.cache_info()
            self.assertEqual(cache_info.currsize, 0)

            # Once network recovers, next search executes fresh and succeeds
            mock_client.results.side_effect = None
            mock_client.results.return_value = [DummyResult(title="Network Restored Paper")]
            papers_restored = ArxivService.fetch_papers("outage test", max_results=1)
            self.assertEqual(len(papers_restored), 1)
            self.assertEqual(papers_restored[0]["title"], "Network Restored Paper")

    @patch("arxiv.Client")
    def test_fetch_papers_permanent_error_does_not_retry(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.results.side_effect = ValueError("Invalid syntax query")

        papers = ArxivService.fetch_papers("bad query", max_results=1)
        self.assertEqual(papers, [])
        # Permanent error should NOT be retried
        self.assertEqual(mock_client.results.call_count, 1)


if __name__ == "__main__":
    unittest.main()
