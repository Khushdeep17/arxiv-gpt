import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    JSON,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    searches: Mapped[List["Search"]] = relationship(back_populates="user")
    collections: Mapped[List["Collection"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    saved_papers: Mapped[List["SavedPaper"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("uq_users_lower_email", func.lower(email), unique=True),
    )


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    arxiv_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(512), index=True, nullable=False)
    authors: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    published: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    url: Mapped[str] = mapped_column(String(1024), unique=True, index=True, nullable=False)
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    summaries: Mapped[List["Summary"]] = relationship(
        back_populates="paper", cascade="all, delete-orphan"
    )
    search_associations: Mapped[List["SearchPaper"]] = relationship(
        back_populates="paper", cascade="all, delete-orphan"
    )
    collection_associations: Mapped[List["CollectionPaper"]] = relationship(
        back_populates="paper", cascade="all, delete-orphan"
    )
    saved_instances: Mapped[List["SavedPaper"]] = relationship(
        back_populates="paper", cascade="all, delete-orphan"
    )


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    paper_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    tldr: Mapped[str] = mapped_column(Text, nullable=False)
    key_contributions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    methods: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    results: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    why_it_matters: Mapped[str] = mapped_column(Text, nullable=False)
    citation: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    paper: Mapped["Paper"] = relationship(back_populates="summaries")

    __table_args__ = (
        UniqueConstraint("paper_id", "model_name", "prompt_version", name="uq_paper_model_prompt_version"),
        Index("idx_summary_lookup", "paper_id", "model_name", "prompt_version"),
    )


class Search(Base):
    __tablename__ = "searches"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    query: Mapped[str] = mapped_column(String(512), index=True, nullable=False)
    optimized_query: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    max_results: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    pdf_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    user: Mapped[Optional["User"]] = relationship(back_populates="searches")
    search_papers: Mapped[List["SearchPaper"]] = relationship(
        back_populates="search", cascade="all, delete-orphan", order_by="SearchPaper.rank"
    )


class SearchPaper(Base):
    __tablename__ = "search_papers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    search_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("searches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rank: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    search: Mapped["Search"] = relationship(back_populates="search_papers")
    paper: Mapped["Paper"] = relationship(back_populates="search_associations")

    __table_args__ = (
        UniqueConstraint("search_id", "paper_id", name="uq_search_paper"),
        Index("idx_search_rank", "search_id", "rank"),
    )


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    user: Mapped[Optional["User"]] = relationship(back_populates="collections")
    collection_papers: Mapped[List["CollectionPaper"]] = relationship(
        back_populates="collection", cascade="all, delete-orphan"
    )


class CollectionPaper(Base):
    __tablename__ = "collection_papers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    collection_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("collections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    collection: Mapped["Collection"] = relationship(back_populates="collection_papers")
    paper: Mapped["Paper"] = relationship(back_populates="collection_associations")

    __table_args__ = (
        UniqueConstraint("collection_id", "paper_id", name="uq_collection_paper"),
    )


class SavedPaper(Base):
    __tablename__ = "saved_papers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    user: Mapped[Optional["User"]] = relationship(back_populates="saved_papers")
    paper: Mapped["Paper"] = relationship(back_populates="saved_instances")

    __table_args__ = (
        UniqueConstraint("user_id", "paper_id", name="uq_user_saved_paper"),
    )
