import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings


def get_engine_kwargs(database_url: str):
    """
    Returns appropriate engine kwargs based on dialect (PostgreSQL vs SQLite).
    """
    kwargs = {
        "echo": False,
    }
    if database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        # Managed cloud PostgreSQL connection pooling and health checks
        kwargs["pool_pre_ping"] = True
        kwargs["pool_recycle"] = 300
        kwargs["pool_size"] = 10
        kwargs["max_overflow"] = 20
    return kwargs


def ensure_sqlite_dir(database_url: str):
    if database_url.startswith("sqlite:///") and not database_url.startswith("sqlite:///:memory:"):
        path = database_url.replace("sqlite:///", "")
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)


ensure_sqlite_dir(settings.DATABASE_URL)

engine = create_engine(settings.DATABASE_URL, **get_engine_kwargs(settings.DATABASE_URL))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency yielding an isolated database session.
    Transactions should be explicitly committed by service callers.
    """
    ensure_sqlite_dir(settings.DATABASE_URL)
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

