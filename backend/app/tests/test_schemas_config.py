import os
import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch
from pydantic import ValidationError

from app.core.config import (
    Settings,
    normalize_database_url,
    parse_cors_origins,
    DEFAULT_LOCAL_CORS_ORIGINS,
)
from app.core.security import create_access_token, decode_access_token
from app.models.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    TokenData,
)


class DummyUserORM:
    """Mock object mimicking SQLAlchemy User model instance."""
    def __init__(self, id, email, full_name, is_active, created_at, hashed_password):
        self.id = id
        self.email = email
        self.full_name = full_name
        self.is_active = is_active
        self.created_at = created_at
        self.hashed_password = hashed_password  # Sensitive field that should NOT leak into UserResponse


class TestSchemasAndConfig(unittest.TestCase):

    # -------------------------------------------------------------
    # Schema Tests
    # -------------------------------------------------------------

    def test_user_create_normalizes_email(self):
        # Email is trimmed and lowercased
        user = UserCreate(email="  Researcher.Jane@Example.COM  ", password="Password123!")
        self.assertEqual(user.email, "researcher.jane@example.com")
        self.assertEqual(user.password, "Password123!")
        self.assertIsNone(user.full_name)

    def test_user_create_invalid_email_raises_validation_error(self):
        invalid_emails = ["not-an-email", "@example.com", "user@", "user@.com", ""]
        for bad_email in invalid_emails:
            with self.assertRaises(ValidationError):
                UserCreate(email=bad_email, password="Password123!")

    def test_user_create_password_min_length_enforced(self):
        # Passwords shorter than 8 characters must be rejected
        short_passwords = ["123", "short", "1234567"]
        for short_pw in short_passwords:
            with self.assertRaises(ValidationError):
                UserCreate(email="user@example.com", password=short_pw)

    def test_user_create_whitespace_password_rejected(self):
        # Whitespace-only passwords must be rejected even if 8+ chars
        with self.assertRaises(ValidationError):
            UserCreate(email="user@example.com", password="        ")

    def test_user_login_normalizes_email(self):
        login = UserLogin(email="  USER@TEST.ORG  ", password="SecretPassword")
        self.assertEqual(login.email, "user@test.org")

    def test_user_response_from_orm_excludes_hashed_password(self):
        user_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        orm_user = DummyUserORM(
            id=user_id,
            email="marie.curie@radium.fr",
            full_name="Marie Curie",
            is_active=True,
            created_at=now,
            hashed_password="$argon2id$v=19$m=65536,t=3,p=4$secret_hash_not_for_client",
        )

        response_dto = UserResponse.model_validate(orm_user)
        dumped = response_dto.model_dump()

        self.assertEqual(dumped["id"], user_id)
        self.assertEqual(dumped["email"], "marie.curie@radium.fr")
        self.assertEqual(dumped["full_name"], "Marie Curie")
        self.assertTrue(dumped["is_active"])
        self.assertNotIn("hashed_password", dumped)
        self.assertNotIn("password", dumped)

    def test_token_schema_defaults(self):
        token = Token(access_token="sample.jwt.token")
        self.assertEqual(token.access_token, "sample.jwt.token")
        self.assertEqual(token.token_type, "bearer")

    def test_token_data_synchronizes_sub_and_uuid(self):
        test_uuid = uuid.uuid4()
        # From string sub -> user_id UUID
        td1 = TokenData(sub=str(test_uuid))
        self.assertEqual(td1.user_id, test_uuid)

        # From user_id UUID -> string sub
        td2 = TokenData(user_id=test_uuid)
        self.assertEqual(td2.sub, str(test_uuid))

        # Arbitrary non-UUID sub remains string without crashing
        td3 = TokenData(sub="non-uuid-username")
        self.assertEqual(td3.sub, "non-uuid-username")
        self.assertIsNone(td3.user_id)

    # -------------------------------------------------------------
    # Configuration Tests
    # -------------------------------------------------------------

    def test_settings_defaults(self):
        settings = Settings()
        self.assertEqual(settings.JWT_ALGORITHM, "HS256")
        self.assertEqual(settings.ACCESS_TOKEN_EXPIRE_MINUTES, 60)

    def test_missing_jwt_secret_key_raises_runtime_error(self):
        settings = Settings()
        settings.JWT_SECRET_KEY = None
        with self.assertRaises(RuntimeError) as ctx:
            settings.get_jwt_secret_key()
        self.assertIn("JWT_SECRET_KEY environment variable is not configured", str(ctx.exception))

    def test_empty_jwt_secret_key_raises_runtime_error(self):
        settings = Settings()
        settings.JWT_SECRET_KEY = "   "
        with self.assertRaises(RuntimeError):
            settings.get_jwt_secret_key()

    def test_valid_jwt_secret_key_retrieval(self):
        settings = Settings()
        settings.JWT_SECRET_KEY = "mock_super_secret_signing_key_32bytes!"
        self.assertEqual(settings.get_jwt_secret_key(), "mock_super_secret_signing_key_32bytes!")

    def test_security_utilities_use_settings_secret_when_configured(self):
        mock_key = "mock_settings_jwt_secret_32_bytes_length!"
        with patch.object(Settings, "JWT_SECRET_KEY", mock_key):
            token = create_access_token(subject="user_settings_test")
            self.assertIsInstance(token, str)

            payload = decode_access_token(token)
            self.assertEqual(payload["sub"], "user_settings_test")
            self.assertEqual(payload["type"], "access")

    def test_security_utilities_raise_when_settings_secret_missing(self):
        with patch.object(Settings, "JWT_SECRET_KEY", None):
            with self.assertRaises(RuntimeError):
                create_access_token(subject="user_fail_test")

    # -------------------------------------------------------------
    # Database URL & CORS Configuration Tests
    # -------------------------------------------------------------

    def test_database_url_local_fallback(self):
        # When no URL provided in local dev, fallback to SQLite
        self.assertEqual(normalize_database_url(None, is_render=False), "sqlite:///./data/arxiv_gpt.db")
        self.assertEqual(normalize_database_url("", is_render=False), "sqlite:///./data/arxiv_gpt.db")
        self.assertEqual(normalize_database_url("   ", is_render=False), "sqlite:///./data/arxiv_gpt.db")

    def test_database_url_normalization_postgres(self):
        # postgres:// and postgresql:// normalized to postgresql+psycopg://
        self.assertEqual(
            normalize_database_url("postgres://u:p@localhost:5432/db", is_render=False),
            "postgresql+psycopg://u:p@localhost:5432/db"
        )
        self.assertEqual(
            normalize_database_url("postgresql://u:p@localhost:5432/db", is_render=False),
            "postgresql+psycopg://u:p@localhost:5432/db"
        )
        self.assertEqual(
            normalize_database_url("postgresql+psycopg://u:p@localhost:5432/db", is_render=False),
            "postgresql+psycopg://u:p@localhost:5432/db"
        )

    def test_database_url_render_fail_fast_when_missing(self):
        # On Render, missing or blank DATABASE_URL must raise RuntimeError
        with self.assertRaises(RuntimeError) as ctx:
            normalize_database_url(None, is_render=True)
        self.assertIn("DATABASE_URL environment variable is required on Render", str(ctx.exception))

        with self.assertRaises(RuntimeError) as ctx:
            normalize_database_url("   ", is_render=True)
        self.assertIn("DATABASE_URL environment variable is required on Render", str(ctx.exception))

    def test_database_url_render_rejects_non_postgres(self):
        # On Render, SQLite or invalid database schemas must be rejected
        with self.assertRaises(RuntimeError) as ctx:
            normalize_database_url("sqlite:///./data/arxiv_gpt.db", is_render=True)
        self.assertIn("Production DATABASE_URL on Render must be a PostgreSQL connection string", str(ctx.exception))
        # Ensure credentials/url are not leaked
        self.assertNotIn("sqlite", str(ctx.exception))

    def test_database_url_render_normalizes_postgres(self):
        # On Render, valid PostgreSQL URL is normalized
        result = normalize_database_url("postgres://app_user:secret_pw@dpg-abc:5432/arxiv_gpt", is_render=True)
        self.assertEqual(result, "postgresql+psycopg://app_user:secret_pw@dpg-abc:5432/arxiv_gpt")

    def test_cors_origins_local_default(self):
        # Local development defaults to standard local ports
        origins = parse_cors_origins(None, is_render=False)
        self.assertEqual(origins, DEFAULT_LOCAL_CORS_ORIGINS)
        self.assertIn("http://localhost:3000", origins)

    def test_cors_origins_parsing(self):
        origins = parse_cors_origins("http://localhost:3000, http://127.0.0.1:8000/", is_render=False)
        self.assertEqual(origins, ["http://localhost:3000", "http://127.0.0.1:8000"])

    def test_cors_origins_render_fail_fast_when_missing(self):
        with self.assertRaises(RuntimeError) as ctx:
            parse_cors_origins(None, is_render=True)
        self.assertIn("CORS_ORIGINS environment variable is required on Render", str(ctx.exception))

    def test_cors_origins_render_rejects_wildcard(self):
        with self.assertRaises(RuntimeError) as ctx:
            parse_cors_origins("*", is_render=True)
        self.assertIn("Wildcard CORS origin ('*') is not permitted on Render", str(ctx.exception))

        with self.assertRaises(RuntimeError):
            parse_cors_origins("https://arxiv-gpt.onrender.com, *", is_render=True)

    def test_cors_origins_render_valid_explicit(self):
        origins = parse_cors_origins("https://arxiv-gpt.onrender.com, https://arxiv-gpt-custom.com/", is_render=True)
        self.assertEqual(origins, ["https://arxiv-gpt.onrender.com", "https://arxiv-gpt-custom.com"])

    def test_cors_origins_render_falls_back_to_render_external_url(self):
        with patch.dict(os.environ, {"RENDER_EXTERNAL_URL": "https://arxiv-gpt-auto.onrender.com"}):
            origins = parse_cors_origins(None, is_render=True)
            self.assertEqual(origins, ["https://arxiv-gpt-auto.onrender.com"])


if __name__ == "__main__":
    unittest.main()

