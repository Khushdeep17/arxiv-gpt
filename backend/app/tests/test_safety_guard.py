import os
import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker, Session

from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app
from app.tests.db_test_utils import (
    validate_test_db_url,
    get_test_db_url,
    create_test_engine,
    extract_bind_url,
    safe_clean_test_tables,
    safe_teardown_test_db,
    PERMITTED_TEST_PG_DB,
)


class TestDatabaseSafetyGuard(unittest.TestCase):
    """
    Unit tests for the test database safety guard to ensure that test cleanup
    and test engine execution can NEVER target the development or production databases.
    """

    def test_default_resolves_to_sqlite_in_memory(self):
        self.assertEqual(validate_test_db_url(None), "sqlite:///:memory:")
        self.assertEqual(validate_test_db_url(""), "sqlite:///:memory:")
        self.assertEqual(validate_test_db_url("   "), "sqlite:///:memory:")
        self.assertEqual(validate_test_db_url("sqlite:///:memory:"), "sqlite:///:memory:")
        self.assertEqual(validate_test_db_url("sqlite://"), "sqlite:///:memory:")

    def test_never_falls_back_to_development_database_url(self):
        # Even if DATABASE_URL is explicitly pointing to the dev database,
        # get_test_db_url() MUST NOT read it when TEST_DATABASE_URL is unset.
        with patch.dict(
            os.environ,
            {"DATABASE_URL": "postgresql+psycopg://postgres:pass@localhost:5432/arxiv_gpt"},
            clear=False,
        ):
            if "TEST_DATABASE_URL" in os.environ:
                del os.environ["TEST_DATABASE_URL"]

            self.assertEqual(get_test_db_url(), "sqlite:///:memory:")

    def test_accept_permitted_test_database_arxiv_gpt_test(self):
        localhost_url = f"postgresql+psycopg://postgres:postgres_dev_password@localhost:5432/{PERMITTED_TEST_PG_DB}"
        self.assertEqual(validate_test_db_url(localhost_url), localhost_url)

        compose_url = f"postgresql+psycopg://postgres:postgres_dev_password@db:5432/{PERMITTED_TEST_PG_DB}"
        self.assertEqual(validate_test_db_url(compose_url), compose_url)

        # Verify automatic normalization of bare postgresql:// to postgresql+psycopg://
        bare_url = f"postgresql://postgres:postgres_dev_password@localhost:5432/{PERMITTED_TEST_PG_DB}"
        expected_normalized = f"postgresql+psycopg://postgres:postgres_dev_password@localhost:5432/{PERMITTED_TEST_PG_DB}"
        self.assertEqual(validate_test_db_url(bare_url), expected_normalized)

        # Verify automatic normalization of legacy postgres://
        legacy_url = f"postgres://postgres:postgres_dev_password@localhost:5432/{PERMITTED_TEST_PG_DB}"
        self.assertEqual(validate_test_db_url(legacy_url), expected_normalized)

    def test_reject_development_database_arxiv_gpt(self):
        dev_urls = [
            "postgresql+psycopg://postgres:pass@localhost:5432/arxiv_gpt",
            "postgresql+psycopg://postgres:pass@db:5432/arxiv_gpt",
            "postgresql://postgres:pass@localhost:5432/arxiv_gpt",
            "postgres://postgres:pass@localhost:5432/arxiv_gpt",
        ]
        for url in dev_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError) as ctx:
                    validate_test_db_url(url)
                self.assertIn("refusing to run tests against the development database 'arxiv_gpt'", str(ctx.exception))

    def test_reject_unexpected_postgres_database_names(self):
        unsafe_urls = [
            "postgresql+psycopg://postgres:pass@localhost:5432/production",
            "postgresql+psycopg://postgres:pass@localhost:5432/prod_arxiv_gpt",
            "postgresql+psycopg://postgres:pass@localhost:5432/arxiv_gpt_production",
            "postgresql+psycopg://postgres:pass@localhost:5432/test_arxiv_gpt",  # exact match required
            "postgresql+psycopg://postgres:pass@localhost:5432/my_custom_db",
            "postgresql+psycopg://postgres:pass@localhost:5432/",               # empty database
        ]
        for url in unsafe_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError) as ctx:
                    validate_test_db_url(url)
                self.assertIn("strictly restricted to 'arxiv_gpt_test'", str(ctx.exception))

    def test_reject_file_based_sqlite(self):
        unsafe_sqlite_urls = [
            "sqlite:///./data/arxiv_gpt.db",
            "sqlite:///data/arxiv_gpt.db",
            "sqlite:///arxiv_gpt.db",
            "sqlite:///arxiv_gpt_test.db",
            "sqlite:////absolute/path/test.db",
        ]
        for url in unsafe_sqlite_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError) as ctx:
                    validate_test_db_url(url)
                self.assertIn("file-based SQLite database", str(ctx.exception))

    def test_reject_unsupported_dialects(self):
        unsafe_dialects = [
            f"mysql://root:pass@localhost:3306/{PERMITTED_TEST_PG_DB}",
            f"mariadb://root:pass@localhost:3306/{PERMITTED_TEST_PG_DB}",
            f"oracle://root:pass@localhost:1521/{PERMITTED_TEST_PG_DB}",
            f"mssql+pyodbc://sa:pass@localhost:1433/{PERMITTED_TEST_PG_DB}",
        ]
        for url in unsafe_dialects:
            with self.subTest(url=url):
                with self.assertRaises(ValueError) as ctx:
                    validate_test_db_url(url)
                self.assertIn("Unsupported test database dialect", str(ctx.exception))

    def test_create_test_engine_fails_fast_before_engine_creation(self):
        with self.assertRaises(ValueError) as ctx:
            create_test_engine("postgresql+psycopg://postgres:pass@localhost:5432/arxiv_gpt")
        self.assertIn("refusing to run tests against the development database 'arxiv_gpt'", str(ctx.exception))

    def test_safe_teardown_fails_fast_on_unapproved_engine(self):
        mock_engine = MagicMock()
        mock_engine.url = make_url("postgresql+psycopg://postgres:pass@localhost:5432/arxiv_gpt")

        with self.assertRaises(ValueError) as ctx:
            safe_teardown_test_db(mock_engine)

        self.assertIn("refusing to run tests against the development database 'arxiv_gpt'", str(ctx.exception))
        # Ensure drop_all was NEVER called
        self.assertEqual(mock_engine.execute.call_count, 0)
        self.assertEqual(mock_engine.dispose.call_count, 0)

    def test_safe_clean_fails_fast_on_unapproved_engine(self):
        mock_engine = MagicMock()
        mock_engine.url = make_url("postgresql+psycopg://postgres:pass@localhost:5432/arxiv_gpt")
        mock_session = MagicMock()

        with self.assertRaises(ValueError) as ctx:
            safe_clean_test_tables(mock_session, mock_engine)

        self.assertIn("refusing to run tests against the development database 'arxiv_gpt'", str(ctx.exception))
        # Ensure delete was NEVER executed on session
        self.assertEqual(mock_session.execute.call_count, 0)
        self.assertEqual(mock_session.commit.call_count, 0)

    # -------------------------------------------------------------------------
    # F-4: Session Bind Validation Safety Tests
    # -------------------------------------------------------------------------

    def test_safe_clean_rejects_session_bound_to_development_database(self):
        """
        F-4: A session bound to the development database cannot be cleaned even if
        a valid test engine is separately supplied as the engine parameter.
        """
        mock_dev_bind = MagicMock()
        mock_dev_bind.url = make_url("postgresql+psycopg://postgres:pass@localhost:5432/arxiv_gpt")

        mock_session = MagicMock()
        mock_session.get_bind.return_value = mock_dev_bind

        valid_test_engine = MagicMock()
        valid_test_engine.url = make_url(f"postgresql+psycopg://postgres:pass@localhost:5432/{PERMITTED_TEST_PG_DB}")

        with self.assertRaises(ValueError) as ctx:
            safe_clean_test_tables(mock_session, valid_test_engine)

        self.assertIn("refusing to run tests against the development database 'arxiv_gpt'", str(ctx.exception))
        # Verify NO rollback, execute (delete), or commit occurred on the development session
        self.assertEqual(mock_session.rollback.call_count, 0)
        self.assertEqual(mock_session.execute.call_count, 0)
        self.assertEqual(mock_session.commit.call_count, 0)

    def test_safe_clean_rejects_session_bound_to_unexpected_database(self):
        """
        F-4: A session bound to a non-whitelisted/unexpected database cannot be cleaned.
        """
        mock_unexpected_bind = MagicMock()
        mock_unexpected_bind.url = make_url("postgresql+psycopg://postgres:pass@localhost:5432/production_backup")

        mock_session = MagicMock()
        mock_session.get_bind.return_value = mock_unexpected_bind

        valid_test_engine = MagicMock()
        valid_test_engine.url = make_url(f"postgresql+psycopg://postgres:pass@localhost:5432/{PERMITTED_TEST_PG_DB}")

        with self.assertRaises(ValueError) as ctx:
            safe_clean_test_tables(mock_session, valid_test_engine)

        self.assertIn("strictly restricted to 'arxiv_gpt_test'", str(ctx.exception))
        self.assertEqual(mock_session.execute.call_count, 0)

    def test_safe_clean_rejects_mismatched_session_bind_and_engine(self):
        """
        F-4: A session bound to a different database target than the supplied engine
        must be rejected before executing any operations.
        """
        # Session bound to SQLite in-memory, but engine claims to be PostgreSQL arxiv_gpt_test
        mock_sqlite_bind = MagicMock()
        mock_sqlite_bind.url = make_url("sqlite:///:memory:")

        mock_session = MagicMock()
        mock_session.get_bind.return_value = mock_sqlite_bind

        valid_pg_engine = MagicMock()
        valid_pg_engine.url = make_url(f"postgresql+psycopg://postgres:pass@localhost:5432/{PERMITTED_TEST_PG_DB}")

        with self.assertRaises(ValueError) as ctx:
            safe_clean_test_tables(mock_session, valid_pg_engine)

        self.assertIn("Mismatched test database targets", str(ctx.exception))
        self.assertEqual(mock_session.execute.call_count, 0)

    def test_safe_clean_inspects_connection_bind_safely(self):
        """
        F-4: Handles SQLAlchemy Connection bind objects safely by inspecting bind.engine.url.
        """
        # Connection bind pointing to dev database
        mock_conn = MagicMock(spec=["engine"])
        mock_conn.engine = MagicMock()
        mock_conn.engine.url = make_url("postgresql+psycopg://postgres:pass@localhost:5432/arxiv_gpt")

        mock_session = MagicMock()
        mock_session.get_bind.return_value = mock_conn

        valid_test_engine = MagicMock()
        valid_test_engine.url = make_url(f"postgresql+psycopg://postgres:pass@localhost:5432/{PERMITTED_TEST_PG_DB}")

        with self.assertRaises(ValueError) as ctx:
            safe_clean_test_tables(mock_session, valid_test_engine)

        self.assertIn("refusing to run tests against the development database 'arxiv_gpt'", str(ctx.exception))
        self.assertEqual(mock_session.execute.call_count, 0)

    def test_safe_clean_accepts_valid_test_session_and_engine(self):
        """
        F-4: A real session and engine bound to the permitted test target executes cleanly.
        """
        test_engine = create_test_engine("sqlite:///:memory:")
        Base.metadata.create_all(test_engine)
        SessionLocal = sessionmaker(bind=test_engine)
        session = SessionLocal()
        try:
            # Table cleanup should execute cleanly without raising ValueError
            safe_clean_test_tables(session, test_engine)
        finally:
            session.close()
            safe_teardown_test_db(test_engine)

    # -------------------------------------------------------------------------
    # F-2 & F-5: Lifecycle and Isolation Regression Tests
    # -------------------------------------------------------------------------

    def test_unrelated_dependency_overrides_survive_teardown(self):
        """
        F-2: Selective removal via pop(get_db, None) preserves other dependency overrides.
        """
        dummy_dep = object()
        fastapi_app.dependency_overrides[dummy_dep] = lambda: "custom_service"
        fastapi_app.dependency_overrides[get_db] = lambda: "test_db_override"

        try:
            # Simulate selective teardown (as implemented in test_routes.py)
            fastapi_app.dependency_overrides.pop(get_db, None)

            # Unrelated override must survive
            self.assertIn(dummy_dep, fastapi_app.dependency_overrides)
            self.assertEqual(fastapi_app.dependency_overrides[dummy_dep](), "custom_service")
            # get_db must be removed
            self.assertNotIn(get_db, fastapi_app.dependency_overrides)
        finally:
            fastapi_app.dependency_overrides.pop(dummy_dep, None)
            fastapi_app.dependency_overrides.pop(get_db, None)

    def test_setup_failure_engine_disposal(self):
        """
        F-5: If Base.metadata.create_all() fails during setup, engine.dispose() is called
        and the original exception is re-raised.
        """
        from app.tests.test_persistence import TestPersistence
        mock_engine = MagicMock()

        with patch("app.tests.test_persistence.create_test_engine", return_value=mock_engine):
            with patch("app.db.base.Base.metadata.create_all", side_effect=RuntimeError("Simulated DDL failure")):
                with self.assertRaises(RuntimeError) as ctx:
                    TestPersistence.setUpClass()

                self.assertIn("Simulated DDL failure", str(ctx.exception))
                self.assertEqual(mock_engine.dispose.call_count, 1)
                self.assertIsNone(TestPersistence.engine)

    def test_routes_setup_failure_cleans_overrides_and_disposes_engine(self):
        """
        F-5: If TestRoutes setup fails after creating engine, engine is disposed
        and dependency override is cleaned up.
        """
        from app.tests.test_routes import TestRoutes
        mock_engine = MagicMock()

        with patch("app.tests.test_routes.create_test_engine", return_value=mock_engine):
            with patch("app.db.base.Base.metadata.create_all", side_effect=RuntimeError("Simulated Route DDL failure")):
                with self.assertRaises(RuntimeError) as ctx:
                    TestRoutes.setUpClass()

                self.assertIn("Simulated Route DDL failure", str(ctx.exception))
                self.assertEqual(mock_engine.dispose.call_count, 1)
                self.assertIsNone(TestRoutes.test_engine)
                self.assertNotIn(get_db, fastapi_app.dependency_overrides)


if __name__ == "__main__":
    unittest.main()
