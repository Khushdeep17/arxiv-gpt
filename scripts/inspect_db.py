"""
Database Inspection Utility for arXiv-GPT
Usage:
    python scripts/inspect_db.py
    python scripts/inspect_db.py --url "postgresql://..."
"""
import sys
import os
import argparse

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from app.models.db_models import User, SearchQuery, Paper, QueryPaperAssociation
from app.core.config import normalize_database_url


def inspect(db_url: str):
    print("=" * 60)
    print("  arXiv-GPT Database Inspector")
    print("=" * 60)

    clean_url = normalize_database_url(db_url, is_render=False)
    masked_url = clean_url
    if "@" in masked_url:
        prefix, rest = masked_url.split("@", 1)
        protocol = prefix.split("://")[0]
        masked_url = f"{protocol}://****:****@{rest}"

    print(f"Connecting to: {masked_url}")

    try:
        engine = create_engine(clean_url)
        Session = sessionmaker(bind=engine)
        session = Session()
    except Exception as e:
        print(f"❌ Failed to create engine: {e}")
        return

    try:
        # 1. Users
        user_count = session.scalar(select(func.count(User.id))) or 0
        users = session.scalars(select(User).order_by(User.created_at.desc()).limit(10)).all()
        print(f"\n👤 Users (Total: {user_count})")
        print("-" * 60)
        if not users:
            print("  (No users registered yet)")
        for u in users:
            print(f"  • {u.email} | Name: {u.full_name or 'N/A'} | Active: {u.is_active} | Joined: {u.created_at}")

        # 2. Queries
        query_count = session.scalar(select(func.count(SearchQuery.id))) or 0
        queries = session.scalars(select(SearchQuery).order_by(SearchQuery.timestamp.desc()).limit(10)).all()
        print(f"\n🔍 Search Queries (Total: {query_count})")
        print("-" * 60)
        if not queries:
            print("  (No search queries recorded yet)")
        for q in queries:
            print(f"  • [{q.timestamp.strftime('%Y-%m-%d %H:%M') if q.timestamp else 'N/A'}] '{q.query}' (User ID: {str(q.user_id)[:8]}...)")

        # 3. Papers
        paper_count = session.scalar(select(func.count(Paper.id))) or 0
        papers = session.scalars(select(Paper).order_by(Paper.created_at.desc()).limit(5)).all()
        print(f"\n📄 Canonical Papers Stored (Total: {paper_count})")
        print("-" * 60)
        if not papers:
            print("  (No papers stored yet)")
        for p in papers:
            print(f"  • [{p.arxiv_id}] {p.title[:65]}...")

        print("\n" + "=" * 60)
        print("  Database is healthy and fully accessible! ✅")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Query error: {e}")
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser(description="Inspect arXiv-GPT PostgreSQL / SQLite Database")
    parser.add_argument("--url", help="Database connection URL (defaults to DATABASE_URL in .env)")
    args = parser.parse_args()

    target_url = args.url or os.getenv("DATABASE_URL")
    if not target_url:
        # Check if local sqlite exists
        local_sqlite = os.path.join(os.path.dirname(__file__), "..", "data", "arxiv_gpt.db")
        if os.path.exists(local_sqlite):
            target_url = f"sqlite:///{os.path.abspath(local_sqlite)}"
        else:
            print("⚠️ No DATABASE_URL found in .env and no local SQLite database found.")
            print("Please pass --url <your-neon-database-url> or configure DATABASE_URL in .env")
            sys.exit(1)

    inspect(target_url)
