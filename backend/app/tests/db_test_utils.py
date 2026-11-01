import os
import re
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base

PERMITTED_TEST_PG_DB = "arxiv_gpt_test"


def normalize_test_url(url: str) -> str:
    """
    Normalizes Postgres driver prefixes for SQLAlchemy + psycopg v3.
    """
    clean_url = url.strip().strip("'").strip('"')
    if clean_url.startswith("postgres://"):
        return clean_url.replace("postgres://", "postgresql+psycopg://", 1)
    if clean_url.startswith("postgresql://") and not clean_url.startswith("postgresql+"):
        return clean_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return clean_url


def validate_test_db_url(raw_url: str | None) -> str:
    """
    Validates a database URL for test execution.
    - None or empty string resolves safely to in-memory SQLite ('sqlite:///:memory:').
    - 'sqlite:///:memory:' and 'sqlite://' are permitted.
    - File-based SQLite URLs are strictly rejected to prevent modifying local SQLite database files.
    - PostgreSQL URLs are ONLY permitted if the targeted database is exactly 'arxiv_gpt_test'.
    - 'arxiv_gpt', production, or any other database names are rejected with ValueError.
    - Unsupported dialects (mysql, oracle, etc.) are rejected with ValueError.
    """
    if raw_url is None:
        return "sqlite:///:memory:"

    trimmed = raw_url.strip()
    if not trimmed:
        return "sqlite:///:memory:"

    normalized = normalize_test_url(trimmed)

    if normalized in ("sqlite:///:memory:", "sqlite://"):
        return "sqlite:///:memory:"

    try:
        parsed = make_url(normalized)
    except Exception as exc:
        raise ValueError(f"Invalid test database URL format: {exc}") from exc

    backend = parsed.get_backend_name()

    if backend == "sqlite":
        db = parsed.database or ""
        if db not in (":memory:", ""):
            raise ValueError(
                f"Unsafe test database: file-based SQLite database '{db}' is forbidden in tests. "
                "Only in-memory SQLite ('sqlite:///:memory:') is permitted."
            )
        return "sqlite:///:memory:"

    elif backend == "postgresql":
        db_name = (parsed.database or "").strip("/").strip()
        if not db_name:
            raise ValueError(
                "Unsafe test database: missing database name in PostgreSQL URL. "
                f"Tests are strictly restricted to '{PERMITTED_TEST_PG_DB}'."
            )
        if db_name == "arxiv_gpt":
            raise ValueError(
                "Unsafe test database: refusing to run tests against the development database 'arxiv_gpt'! "
                f"Test database must be '{PERMITTED_TEST_PG_DB}'."
            )
        if db_name != PERMITTED_TEST_PG_DB:
            raise ValueError(
                f"Unsafe test database '{db_name}': PostgreSQL tests are strictly restricted "
                f"to '{PERMITTED_TEST_PG_DB}'."
            )
        return normalized

    else:
        raise ValueError(
            f"Unsupported test database dialect '{backend}'. "
            f"Only in-memory SQLite or PostgreSQL '{PERMITTED_TEST_PG_DB}' is permitted."
        )


def get_test_db_url() -> str:
    """
    Returns the validated test database URL.
    Reads exclusively from TEST_DATABASE_URL environment variable.
    NEVER falls back to DATABASE_URL (the development database).
    Defaults strictly to 'sqlite:///:memory:'.
    """
    raw_url = os.getenv("TEST_DATABASE_URL")
    return validate_test_db_url(raw_url)


def create_test_engine(test_url: str | None = None) -> Engine:
    """
    Creates and returns an isolated SQLAlchemy engine for tests.
    Validates the target URL before engine creation.
    """
    target_url = validate_test_db_url(test_url) if test_url is not None else get_test_db_url()

    if target_url.startswith("sqlite"):
        return create_engine(
            target_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
    else:
        return create_engine(
            target_url,
            pool_pre_ping=True,
            echo=False,
        )


def extract_bind_url(bind) -> str:
    """
    Extracts the database URL string from a SQLAlchemy Engine or Connection object.
    """
    if hasattr(bind, "url") and bind.url is not None:
        return str(bind.url)
    elif hasattr(bind, "engine") and hasattr(bind.engine, "url") and bind.engine.url is not None:
        return str(bind.engine.url)
    raise ValueError(
        f"Unsafe test session: unable to extract database URL from bind object of type '{type(bind).__name__}'."
    )


def safe_clean_test_tables(session: Session, engine: Engine) -> None:
    """
    Safely deletes all records from application tables between tests.
    Validates that:
    1. The supplied engine URL targets an approved test database.
    2. The session's actual bind (Engine or Connection) targets an approved test database.
    3. The session bind and the supplied engine point to the exact same database target.
    Rejects mismatched or unapproved binds before executing rollback, DELETE, or commit.
    """
    if engine is None:
        raise ValueError("Unsafe test cleanup: engine parameter cannot be None.")

    if session is None:
        raise ValueError("Unsafe test cleanup: session parameter cannot be None.")

    # 1. Validate the supplied engine URL
    validated_engine_url = validate_test_db_url(str(engine.url))

    # 2. Independently inspect session.get_bind()
    try:
        session_bind = session.get_bind()
    except Exception as exc:
        raise ValueError(f"Unsafe test session: unable to determine database bind: {exc}") from exc

    if session_bind is None:
        raise ValueError("Unsafe test session: session has no active database bind.")

    bind_url_str = extract_bind_url(session_bind)

    # 3. Validate the session's actual bind URL using the strict whitelist
    validated_bind_url = validate_test_db_url(bind_url_str)

    # 4. Ensure session bind and supplied engine refer to the exact same database target
    parsed_engine = make_url(validated_engine_url)
    parsed_bind = make_url(validated_bind_url)

    if parsed_engine.get_backend_name() != parsed_bind.get_backend_name():
        raise ValueError(
            f"Mismatched test database targets: supplied engine dialect '{parsed_engine.get_backend_name()}' "
            f"does not match session bind dialect '{parsed_bind.get_backend_name()}'."
        )

    engine_db = (parsed_engine.database or "").strip("/").strip()
    bind_db = (parsed_bind.database or "").strip("/").strip()
    if engine_db != bind_db:
        raise ValueError(
            f"Mismatched test database targets: supplied engine database '{engine_db}' "
            f"does not match session bind database '{bind_db}'."
        )

    if parsed_engine.host != parsed_bind.host or parsed_engine.port != parsed_bind.port:
        raise ValueError(
            f"Mismatched test database targets: supplied engine host/port "
            f"'{parsed_engine.host}:{parsed_engine.port}' does not match session bind host/port "
            f"'{parsed_bind.host}:{parsed_bind.port}'."
        )

    # 5. Clean tables only after all validations pass
    session.rollback()
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()


def safe_teardown_test_db(engine: Engine) -> None:
    """
    Safely drops all tables and disposes of the test engine.
    Validates that the engine targets an approved test database before drop_all.
    """
    if engine is None:
        return
    validate_test_db_url(str(engine.url))
    Base.metadata.drop_all(engine)
    engine.dispose()

