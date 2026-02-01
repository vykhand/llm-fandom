"""Core data models for wiki generation."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class EntityType(str, Enum):
    """Types of entities that can be extracted."""

    CHARACTER = "character"
    LOCATION = "location"
    ORGANIZATION = "organization"
    CONCEPT = "concept"
    EVENT = "event"
    ITEM = "item"


class RelationType(str, Enum):
    """Types of relationships between entities."""

    BELONGS_TO = "belongs_to"
    WORKS_FOR = "works_for"
    LOCATED_IN = "located_in"
    PARTICIPATES_IN = "participates_in"
    OWNS = "owns"
    CREATES = "creates"
    RELATED_TO = "related_to"
    CHILD_OF = "child_of"
    PARENT_OF = "parent_of"
    ALLY_OF = "ally_of"
    ENEMY_OF = "enemy_of"


class Relationship(BaseModel):
    """A relationship between two entities."""

    source_id: str = Field(description="ID of the source entity")
    target_id: str = Field(description="ID of the target entity")
    relation_type: RelationType = Field(description="Type of relationship")
    description: Optional[str] = Field(
        default=None, description="Additional context about the relationship"
    )
    strength: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Strength/importance of relationship"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "source_id": "char_001",
                "target_id": "org_001",
                "relation_type": "works_for",
                "description": "Lead investigator",
                "strength": 0.9,
            }
        }


class Entity(BaseModel):
    """A wiki entity extracted from content."""

    id: str = Field(default_factory=lambda: f"ent_{uuid4().hex[:12]}")
    name: str = Field(description="Canonical name of the entity")
    type: EntityType = Field(description="Entity type")
    description: str = Field(description="Detailed description (2-3 sentences)")
    aliases: List[str] = Field(default_factory=list, description="Alternative names")
    attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Type-specific attributes"
    )
    relationships: List[Relationship] = Field(
        default_factory=list, description="Relationships to other entities"
    )
    mentions: List[str] = Field(
        default_factory=list, description="Quotes/excerpts mentioning this entity"
    )
    tags: List[str] = Field(default_factory=list, description="Categorization tags")
    image_url: Optional[str] = Field(default=None, description="URL or path to entity image")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Entity name cannot be empty")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Entity description cannot be empty")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "id": "char_001",
                "name": "Sherlock Holmes",
                "type": "character",
                "description": "A brilliant detective living in Victorian London. Known for his exceptional deductive reasoning and observational skills.",
                "aliases": ["Mr. Holmes", "The Detective"],
                "attributes": {
                    "occupation": "Consulting Detective",
                    "residence": "221B Baker Street",
                    "skills": ["Deduction", "Chemistry", "Violin"],
                },
                "tags": ["protagonist", "detective"],
            }
        }


class WikiArticle(BaseModel):
    """A generated wiki article for an entity."""

    entity_id: str = Field(description="ID of the entity this article describes")
    title: str = Field(description="Article title")
    content: str = Field(description="Markdown content")
    frontmatter: Dict[str, Any] = Field(
        default_factory=dict, description="YAML frontmatter metadata"
    )
    sections: List[Dict[str, str]] = Field(
        default_factory=list, description="Article sections with titles and content"
    )
    image_url: Optional[str] = Field(default=None, description="Featured image")
    related_articles: List[str] = Field(
        default_factory=list, description="IDs of related entity articles"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "entity_id": "char_001",
                "title": "Sherlock Holmes",
                "content": "# Sherlock Holmes\n\n...",
                "frontmatter": {
                    "tags": ["character", "detective"],
                    "type": "character",
                },
            }
        }


class ProcessingMetadata(BaseModel):
    """Metadata about the processing pipeline."""

    source_path: str = Field(description="Path to source content")
    source_type: str = Field(description="Type of source (pdf, web, text)")
    total_entities: int = Field(default=0, description="Total entities extracted")
    total_articles: int = Field(default=0, description="Total articles generated")
    processing_time: float = Field(default=0.0, description="Total processing time in seconds")
    llm_provider: str = Field(default="unknown", description="LLM provider used")
    errors: List[str] = Field(default_factory=list, description="Errors encountered")
    warnings: List[str] = Field(default_factory=list, description="Warnings")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "source_path": "./book.pdf",
                "source_type": "pdf",
                "total_entities": 42,
                "total_articles": 42,
                "processing_time": 245.3,
                "llm_provider": "anthropic",
            }
        }


class ParsedContent(BaseModel):
    """Content parsed from a source."""

    text: str = Field(description="Extracted text content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Source metadata")
    chunks: List[str] = Field(
        default_factory=list, description="Text chunks for processing"
    )
    images: List[str] = Field(
        default_factory=list, description="Paths to extracted images"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Chapter 1: The Beginning...",
                "metadata": {"title": "My Book", "author": "John Doe", "pages": 250},
                "chunks": ["Chapter 1: The Beginning...", "Chapter 2: ..."],
            }
        }
