import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_LOCAL_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]


def is_render_environment() -> bool:
    return os.getenv("RENDER", "").strip().lower() in ("true", "1", "yes")


def normalize_database_url(url: str | None, is_render: bool | None = None) -> str:
    """
    Normalizes database URL for psycopg v3 and validates production database configuration.
    In local development, defaults to SQLite if no URL is provided.
    On Render, requires a valid PostgreSQL connection string and fails fast if missing or invalid.
    """
    if is_render is None:
        is_render = is_render_environment()

    clean_url = url.strip().strip("'").strip('"') if url else ""

    if is_render:
        if not clean_url:
            raise RuntimeError(
                "DATABASE_URL environment variable is required on Render. "
                "SQLite fallback is not permitted in production."
            )
        if not (
            clean_url.startswith("postgresql://")
            or clean_url.startswith("postgres://")
            or clean_url.startswith("postgresql+")
        ):
            raise RuntimeError(
                "Production DATABASE_URL on Render must be a PostgreSQL connection string."
            )
        # Normalize Render and Heroku postgres URLs for SQLAlchemy + psycopg v3
        if clean_url.startswith("postgres://"):
            return clean_url.replace("postgres://", "postgresql+psycopg://", 1)
        if clean_url.startswith("postgresql://") and not clean_url.startswith("postgresql+"):
            return clean_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return clean_url

    # Local development behavior
    if not clean_url:
        return "sqlite:///./data/arxiv_gpt.db"
    if clean_url.startswith("postgres://"):
        return clean_url.replace("postgres://", "postgresql+psycopg://", 1)
    if clean_url.startswith("postgresql://") and not clean_url.startswith("postgresql+"):
        return clean_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return clean_url


def parse_cors_origins(origins_str: str | None, is_render: bool | None = None) -> list[str]:
    """
    Parses and validates CORS allowed origins.
    In local development, defaults to standard local frontend origins if unspecified.
    On Render, requires explicit allowed origins and strictly forbids wildcard '*'.
    """
    if is_render is None:
        is_render = is_render_environment()

    if origins_str and origins_str.strip():
        raw_items = [item.strip() for item in origins_str.split(",") if item.strip()]
        parsed = [item.rstrip("/") for item in raw_items]
    else:
        parsed = []

    if is_render:
        if not parsed:
            render_url = os.getenv("RENDER_EXTERNAL_URL", "").strip().rstrip("/")
            if render_url:
                parsed = [render_url]
        if not parsed:
            raise RuntimeError(
                "CORS_ORIGINS environment variable is required on Render. "
                "Configure explicit allowed origins (e.g. 'https://arxiv-gpt.onrender.com')."
            )
        if "*" in parsed:
            raise RuntimeError(
                "Wildcard CORS origin ('*') is not permitted on Render. "
                "Configure explicit allowed origins."
            )
        return parsed

    # Local development behavior
    if not parsed:
        return DEFAULT_LOCAL_CORS_ORIGINS.copy()
    return parsed


def parse_int_env(key: str, default: int) -> int:
    val = os.getenv(key)
    if not val or not val.strip():
        return default
    try:
        parsed = int(val.strip())
        return parsed if parsed > 0 else default
    except ValueError:
        return default


class Settings:
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
    DATABASE_URL: str = normalize_database_url(os.getenv("DATABASE_URL"))
    SUMMARY_MODEL_NAME: str = os.getenv("SUMMARY_MODEL_NAME", "openai/gpt-oss-120b")
    SUMMARY_PROMPT_VERSION: str = os.getenv("SUMMARY_PROMPT_VERSION", "v1.0")

    # Authentication & JWT configuration
    JWT_SECRET_KEY: str | None = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256").strip() or "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = parse_int_env("ACCESS_TOKEN_EXPIRE_MINUTES", 60)

    # Deployment & CORS configuration
    RENDER: bool = is_render_environment()
    CORS_ORIGINS: list[str] = parse_cors_origins(os.getenv("CORS_ORIGINS"))

    def __init__(
        self,
        database_url: str | None = None,
        cors_origins: str | None = None,
        is_render: bool | None = None,
    ):
        if is_render is not None:
            self.RENDER = is_render
        if database_url is not None or is_render is not None:
            raw_db = database_url if database_url is not None else os.getenv("DATABASE_URL")
            self.DATABASE_URL = normalize_database_url(raw_db, is_render=self.RENDER)
        if cors_origins is not None or is_render is not None:
            raw_cors = cors_origins if cors_origins is not None else os.getenv("CORS_ORIGINS")
            self.CORS_ORIGINS = parse_cors_origins(raw_cors, is_render=self.RENDER)

    def get_jwt_secret_key(self) -> str:
        """
        Returns the validated JWT signing secret key.
        Raises RuntimeError if the key is missing or blank, preventing silent fallback to insecure defaults.
        """
        if not self.JWT_SECRET_KEY or not self.JWT_SECRET_KEY.strip():
            raise RuntimeError(
                "JWT_SECRET_KEY environment variable is not configured. "
                "Authentication operations require a valid signing key. "
                "Configure JWT_SECRET_KEY in your environment or .env file."
            )
        return self.JWT_SECRET_KEY.strip()


settings = Settings()
