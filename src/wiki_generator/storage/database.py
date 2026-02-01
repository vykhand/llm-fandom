"""Database models and initialization."""

from datetime import datetime
from pathlib import Path

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class EntityModel(Base):
    """Database model for entities."""

    __tablename__ = "entities"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    aliases = Column(JSON, default=list)
    attributes = Column(JSON, default=dict)
    relationships = Column(JSON, default=list)
    mentions = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ArticleModel(Base):
    """Database model for wiki articles."""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    frontmatter = Column(JSON, default=dict)
    sections = Column(JSON, default=list)
    image_url = Column(String, nullable=True)
    related_articles = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MetadataModel(Base):
    """Database model for processing metadata."""

    __tablename__ = "metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_path = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    total_entities = Column(Integer, default=0)
    total_articles = Column(Integer, default=0)
    processing_time = Column(Float, default=0.0)
    llm_provider = Column(String, default="unknown")
    errors = Column(JSON, default=list)
    warnings = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_database(database_url: str) -> sessionmaker:
    """Initialize database and return session maker."""
    # Ensure directory exists for SQLite
    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)

    return sessionmaker(bind=engine)
