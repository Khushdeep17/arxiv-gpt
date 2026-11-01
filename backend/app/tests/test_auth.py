import os
import unittest
import uuid
from datetime import timedelta
from unittest.mock import patch
from starlette.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import jwt

# Provide test-isolated environment variables
os.environ.setdefault("GROQ_API_KEY", "mock_groq_key_for_testing")
os.environ.setdefault("JWT_SECRET_KEY", "mock_test_jwt_secret_key_auth_suite_32b_len!")

from app.db.base import Base
from app.db.session import get_db
from app.models.db_models import User, Search
from app.main import app as fastapi_app
from app.core.security import create_access_token, decode_access_token
from app.services.persistence_service import PersistenceService
from app.tests.db_test_utils import create_test_engine, safe_clean_test_tables, safe_teardown_test_db


class TestAuth(unittest.TestCase):

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
            fastapi_app.dependency_overrides.pop(get_db, None)
            try:
                engine.dispose()
            except Exception:
                pass
            cls.test_engine = None
            raise

    @classmethod
    def tearDownClass(cls):
        try:
            fastapi_app.dependency_overrides.pop(get_db, None)
        finally:
            if cls.test_engine is not None:
                safe_teardown_test_db(cls.test_engine)

    def tearDown(self):
        if hasattr(self, "TestSession") and self.TestSession is not None and self.test_engine is not None:
            session = self.TestSession()
            try:
                safe_clean_test_tables(session, self.test_engine)
            finally:
                session.close()

    # -------------------------------------------------------------
    # 1. Successful Registration
    # -------------------------------------------------------------
    def test_01_successful_registration(self):
        response = self.client.post(
            "/auth/register",
            json={
                "email": "researcher@lab.edu",
                "password": "SecurePassword123!",
                "full_name": "Dr. Researcher",
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], "researcher@lab.edu")
        self.assertEqual(data["user"]["full_name"], "Dr. Researcher")
        self.assertTrue(data["user"]["is_active"])
        self.assertIn("id", data["user"])

    # -------------------------------------------------------------
    # 2. Email Normalization
    # -------------------------------------------------------------
    def test_02_email_normalization(self):
        # Register with mixed case and leading/trailing whitespace
        response = self.client.post(
            "/auth/register",
            json={
                "email": "   ALAN.TURING@Cambridge.EDU  ",
                "password": "EnigmaPassword123!",
                "full_name": "Alan Turing",
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["user"]["email"], "alan.turing@cambridge.edu")

        # Verify persisted record in DB has normalized lowercase email
        session = self.TestSession()
        try:
            user = session.scalar(select(User).where(User.email == "alan.turing@cambridge.edu"))
            self.assertIsNotNone(user)
            self.assertEqual(user.email, "alan.turing@cambridge.edu")
        finally:
            session.close()

    # -------------------------------------------------------------
    # 3. Duplicate Email Rejection (including case variations)
    # -------------------------------------------------------------
    def test_03_duplicate_email_rejection_case_variations(self):
        self.client.post(
            "/auth/register",
            json={
                "email": "curie@radium.fr",
                "password": "Password123!",
                "full_name": "Marie Curie",
            },
        )

        # Exact duplicate
        dup_exact = self.client.post(
            "/auth/register",
            json={
                "email": "curie@radium.fr",
                "password": "AnotherPassword123!",
            },
        )
        self.assertEqual(dup_exact.status_code, 409)
        self.assertIn("Email already registered", dup_exact.json()["detail"])

        # Case variation duplicate
        dup_case = self.client.post(
            "/auth/register",
            json={
                "email": "CURIE@RADIUM.FR",
                "password": "ThirdPassword123!",
            },
        )
        self.assertEqual(dup_case.status_code, 409)
        self.assertIn("Email already registered", dup_case.json()["detail"])

    # -------------------------------------------------------------
    # 4. Password Stored Hashed, Never Plaintext
    # -------------------------------------------------------------
    def test_04_password_stored_hashed_never_plaintext(self):
        raw_password = "MySuperSecretPassword123!"
        response = self.client.post(
            "/auth/register",
            json={
                "email": "einstein@princeton.edu",
                "password": raw_password,
            },
        )
        self.assertEqual(response.status_code, 201)

        session = self.TestSession()
        try:
            user = session.scalar(select(User).where(User.email == "einstein@princeton.edu"))
            self.assertIsNotNone(user)
            self.assertNotEqual(user.hashed_password, raw_password)
            self.assertTrue(user.hashed_password.startswith("$argon2id$"))
        finally:
            session.close()

    # -------------------------------------------------------------
    # 5. Password Hash Not Returned in Responses
    # -------------------------------------------------------------
    def test_05_password_hash_not_returned_in_responses(self):
        res = self.client.post(
            "/auth/register",
            json={
                "email": "noether@gottingen.de",
                "password": "SymmetryPassword123!",
            },
        )
        data = res.json()
        self.assertNotIn("hashed_password", data)
        self.assertNotIn("password", data)
        self.assertNotIn("hashed_password", data["user"])
        self.assertNotIn("password", data["user"])

    # -------------------------------------------------------------
    # 6. Successful Login
    # -------------------------------------------------------------
    def test_06_successful_login(self):
        self.client.post(
            "/auth/register",
            json={
                "email": "login_user@example.com",
                "password": "ValidPassword123!",
            },
        )

        login_res = self.client.post(
            "/auth/login",
            json={
                "email": "LOGIN_USER@EXAMPLE.COM",  # Test case-insensitivity on login
                "password": "ValidPassword123!",
            },
        )
        self.assertEqual(login_res.status_code, 200)
        data = login_res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["user"]["email"], "login_user@example.com")

    # -------------------------------------------------------------
    # 7. Incorrect Password Rejection
    # -------------------------------------------------------------
    def test_07_incorrect_password_rejection(self):
        self.client.post(
            "/auth/register",
            json={
                "email": "secure_user@example.com",
                "password": "CorrectPassword123!",
            },
        )

        res = self.client.post(
            "/auth/login",
            json={
                "email": "secure_user@example.com",
                "password": "WrongPassword123!",
            },
        )
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["detail"], "Invalid email or password")

        # Unknown email returns the same generic 401 error (no user enumeration)
        unknown_res = self.client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "AnyPassword123!",
            },
        )
        self.assertEqual(unknown_res.status_code, 401)
        self.assertEqual(unknown_res.json()["detail"], "Invalid email or password")

    # -------------------------------------------------------------
    # 8. Inactive User Rejection
    # -------------------------------------------------------------
    def test_08_inactive_user_rejection(self):
        reg = self.client.post(
            "/auth/register",
            json={
                "email": "inactive@example.com",
                "password": "Password123!",
            },
        )
        user_id = uuid.UUID(reg.json()["user"]["id"])

        # Manually deactivate user in DB
        session = self.TestSession()
        try:
            user = session.get(User, user_id)
            user.is_active = False
            session.commit()
        finally:
            session.close()

        # Login must be rejected
        login_res = self.client.post(
            "/auth/login",
            json={
                "email": "inactive@example.com",
                "password": "Password123!",
            },
        )
        self.assertEqual(login_res.status_code, 401)
        self.assertIn("Inactive user account", login_res.json()["detail"])

        # /auth/me with previous token must also be rejected
        token = reg.json()["access_token"]
        me_res = self.client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me_res.status_code, 401)
        self.assertIn("Inactive user account", me_res.json()["detail"])

    # -------------------------------------------------------------
    # 9. Valid /auth/me
    # -------------------------------------------------------------
    def test_09_valid_auth_me(self):
        reg = self.client.post(
            "/auth/register",
            json={
                "email": "me_user@example.com",
                "password": "Password123!",
                "full_name": "Me User",
            },
        )
        token = reg.json()["access_token"]

        response = self.client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], "me_user@example.com")
        self.assertEqual(data["full_name"], "Me User")
        self.assertTrue(data["is_active"])

    # -------------------------------------------------------------
    # 10. Missing Token Rejection
    # -------------------------------------------------------------
    def test_10_missing_token_rejection(self):
        res_me = self.client.get("/auth/me")
        self.assertEqual(res_me.status_code, 401)
        self.assertIn("WWW-Authenticate", res_me.headers)

        res_history = self.client.get("/history")
        self.assertEqual(res_history.status_code, 401)

    # -------------------------------------------------------------
    # 11. Expired Token Rejection
    # -------------------------------------------------------------
    def test_11_expired_token_rejection(self):
        reg = self.client.post(
            "/auth/register",
            json={"email": "expired_test@example.com", "password": "Password123!"},
        )
        user_id = reg.json()["user"]["id"]

        expired_token = create_access_token(
            subject=user_id,
            expires_delta=timedelta(seconds=-10),
        )

        res = self.client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        self.assertEqual(res.status_code, 401)
        self.assertIn("Token has expired", res.json()["detail"])

    # -------------------------------------------------------------
    # 12. Invalid Signature Rejection
    # -------------------------------------------------------------
    def test_12_invalid_signature_rejection(self):
        reg = self.client.post(
            "/auth/register",
            json={"email": "tamper_test@example.com", "password": "Password123!"},
        )
        token = reg.json()["access_token"]
        tampered_token = token[:-4] + "wxyz"

        res = self.client.get("/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
        self.assertEqual(res.status_code, 401)

    # -------------------------------------------------------------
    # 13. Invalid Token Type Rejection
    # -------------------------------------------------------------
    def test_13_invalid_token_type_rejection(self):
        reg = self.client.post(
            "/auth/register",
            json={"email": "tokentype_test@example.com", "password": "Password123!"},
        )
        user_id = reg.json()["user"]["id"]

        # Create token with type 'refresh_token' instead of 'access'
        secret = os.environ["JWT_SECRET_KEY"]
        now = jwt.api_jwt.datetime.now(jwt.api_jwt.timezone.utc)
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(minutes=60),
            "type": "refresh_token",
        }
        refresh_token = jwt.encode(payload, secret, algorithm="HS256")

        res = self.client.get("/auth/me", headers={"Authorization": f"Bearer {refresh_token}"})
        self.assertEqual(res.status_code, 401)

    # -------------------------------------------------------------
    # 14. User-Specific History
    # -------------------------------------------------------------
    def test_14_user_specific_history(self):
        reg = self.client.post(
            "/auth/register",
            json={"email": "history_user_a@example.com", "password": "Password123!"},
        )
        token = reg.json()["access_token"]
        user_id = uuid.UUID(reg.json()["user"]["id"])

        # Seed 2 searches for user A
        session = self.TestSession()
        try:
            PersistenceService.record_search(
                db=session,
                query="quantum computing",
                max_results=1,
                enriched_papers=[{"title": "Quantum Paper", "url": "https://arxiv.org/abs/2601.11111"}],
                user_id=user_id,
            )
            PersistenceService.record_search(
                db=session,
                query="quantum algorithms",
                max_results=1,
                enriched_papers=[{"title": "Algo Paper", "url": "https://arxiv.org/abs/2601.22222"}],
                user_id=user_id,
            )
        finally:
            session.close()

        res = self.client.get("/history", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 200)
        history = res.json()
        self.assertEqual(len(history), 2)
        queries = [h["query"] for h in history]
        self.assertIn("quantum computing", queries)
        self.assertIn("quantum algorithms", queries)

    # -------------------------------------------------------------
    # 15. User A Cannot Retrieve User B's History
    # -------------------------------------------------------------
    def test_15_cross_user_isolation(self):
        # Register User A
        reg_a = self.client.post(
            "/auth/register",
            json={"email": "user_a@example.com", "password": "Password123!"},
        )
        token_a = reg_a.json()["access_token"]
        user_a_id = uuid.UUID(reg_a.json()["user"]["id"])

        # Register User B
        reg_b = self.client.post(
            "/auth/register",
            json={"email": "user_b@example.com", "password": "Password123!"},
        )
        token_b = reg_b.json()["access_token"]
        user_b_id = uuid.UUID(reg_b.json()["user"]["id"])

        # Seed search for User A
        session = self.TestSession()
        try:
            PersistenceService.record_search(
                db=session,
                query="User A Secret Topic",
                max_results=1,
                enriched_papers=[{"title": "A Paper", "url": "https://arxiv.org/abs/2601.33333"}],
                user_id=user_a_id,
            )
            PersistenceService.record_search(
                db=session,
                query="User B Public Topic",
                max_results=1,
                enriched_papers=[{"title": "B Paper", "url": "https://arxiv.org/abs/2601.44444"}],
                user_id=user_b_id,
            )
        finally:
            session.close()

        # User B fetches history: MUST NOT see User A's searches
        res_b = self.client.get("/history", headers={"Authorization": f"Bearer {token_b}"})
        self.assertEqual(res_b.status_code, 200)
        history_b = res_b.json()
        self.assertEqual(len(history_b), 1)
        self.assertEqual(history_b[0]["query"], "User B Public Topic")
        self.assertNotIn("User A Secret Topic", [h["query"] for h in history_b])

    # -------------------------------------------------------------
    # 16. Anonymous Search Remains Functional
    # -------------------------------------------------------------
    @patch("app.agent.research_agent.ArxivService.fetch_papers")
    @patch("app.agent.research_agent.SummarizerService.summarize")
    def test_16_anonymous_search_remains_functional(self, mock_summarize, mock_fetch):
        mock_fetch.return_value = [
            {
                "title": "Anonymous Paper",
                "authors": ["Guest Author"],
                "published": "2026-01-01",
                "category": "cs.AI",
                "url": "https://arxiv.org/abs/2601.55555",
            }
        ]
        mock_summarize.return_value = {
            "tldr": "Guest TLDR",
            "key_contributions": ["Guest Work"],
            "methods": ["Guest Method"],
            "results": ["Guest Result"],
            "why_it_matters": "Matters",
            "citation": "Guest 2026",
        }

        # Search without Authorization header
        response = self.client.post(
            "/search",
            json={"query": "guest unauthenticated search", "max_results": 1},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["papers"]), 1)
        self.assertEqual(data["query"], "guest unauthenticated search")

        # Verify search in DB has user_id = NULL
        session = self.TestSession()
        try:
            search_record = session.scalar(
                select(Search).where(Search.query == "guest unauthenticated search")
            )
            self.assertIsNotNone(search_record)
            self.assertIsNone(search_record.user_id)
        finally:
            session.close()

    # -------------------------------------------------------------
    # 17. Authenticated Search is Linked to Correct User
    # -------------------------------------------------------------
    @patch("app.agent.research_agent.ArxivService.fetch_papers")
    @patch("app.agent.research_agent.SummarizerService.summarize")
    def test_17_authenticated_search_linked_to_user(self, mock_summarize, mock_fetch):
        reg = self.client.post(
            "/auth/register",
            json={"email": "auth_searcher@example.com", "password": "Password123!"},
        )
        token = reg.json()["access_token"]
        user_id = uuid.UUID(reg.json()["user"]["id"])

        mock_fetch.return_value = [
            {
                "title": "Auth User Paper",
                "authors": ["Auth Author"],
                "published": "2026-01-01",
                "category": "cs.AI",
                "url": "https://arxiv.org/abs/2601.66666",
            }
        ]
        mock_summarize.return_value = {
            "tldr": "Auth TLDR",
            "key_contributions": ["Auth Work"],
            "methods": ["Auth Method"],
            "results": ["Auth Result"],
            "why_it_matters": "Matters",
            "citation": "Auth 2026",
        }

        # Search WITH Authorization header
        response = self.client.post(
            "/search",
            json={"query": "authenticated user search query", "max_results": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)

        # Verify search in DB is linked to user_id
        session = self.TestSession()
        try:
            search_record = session.scalar(
                select(Search).where(Search.query == "authenticated user search query")
            )
            self.assertIsNotNone(search_record)
            self.assertEqual(search_record.user_id, user_id)
        finally:
            session.close()

        # Verify it appears in user's history
        history_res = self.client.get("/history", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(history_res.status_code, 200)
        self.assertEqual(len(history_res.json()), 1)
        self.assertEqual(history_res.json()[0]["query"], "authenticated user search query")

    # -------------------------------------------------------------
    # 18. Invalid Supplied Bearer Token is Rejected
    # -------------------------------------------------------------
    def test_18_invalid_supplied_bearer_token_rejected(self):
        # Even on /search which is optional, an explicitly invalid token must raise 401
        invalid_search = self.client.post(
            "/search",
            json={"query": "test query", "max_results": 1},
            headers={"Authorization": "Bearer invalid.malformed.token"},
        )
        self.assertEqual(invalid_search.status_code, 401)
        self.assertIn("Could not validate credentials", invalid_search.json()["detail"])


if __name__ == "__main__":
    unittest.main()

