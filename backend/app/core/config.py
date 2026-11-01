import os
from dotenv import load_dotenv

load_dotenv()


def normalize_database_url(url: str | None) -> str:
    if not url:
        return "sqlite:///./data/arxiv_gpt.db"
    clean_url = url.strip().strip("'").strip('"')
    if not clean_url:
        return "sqlite:///./data/arxiv_gpt.db"
    # Normalize Render and Heroku postgres URLs for SQLAlchemy + psycopg v3
    if clean_url.startswith("postgres://"):
        return clean_url.replace("postgres://", "postgresql+psycopg://", 1)
    if clean_url.startswith("postgresql://") and not clean_url.startswith("postgresql+"):
        return clean_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return clean_url


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
