"""Schemas for entity extraction structured outputs."""

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from ..core.models import EntityType


class ExtractedRelationship(BaseModel):
    """A relationship extracted from content."""

    relation_type: str = Field(description="Type of relationship")
    target_name: str = Field(description="Name of the target entity")
    description: str = Field(default="", description="Optional description")


class ExtractedEntity(BaseModel):
    """An entity extracted from content using structured output."""

    name: str = Field(description="Canonical name of the entity")
    type: EntityType = Field(description="Entity type")
    description: str = Field(description="Detailed description (2-4 sentences)")
    aliases: List[str] = Field(default_factory=list, description="Alternative names")
    attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Type-specific attributes"
    )
    relationships: List[ExtractedRelationship] = Field(
        default_factory=list, description="Key relationships to other entities"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Sherlock Holmes",
                "type": "character",
                "description": "A brilliant consulting detective in Victorian London known for his deductive reasoning and keen observation skills. He solves complex criminal cases that baffle Scotland Yard.",
                "aliases": ["Mr. Holmes", "The Detective"],
                "attributes": {
                    "occupation": "Consulting Detective",
                    "residence": "221B Baker Street",
                    "skills": ["Deduction", "Chemistry", "Violin"],
                    "status": "alive",
                },
                "relationships": [
                    {
                        "relation_type": "works_with",
                        "target_name": "Dr. Watson",
                        "description": "Close friend and chronicler",
                    },
                    {
                        "relation_type": "located_in",
                        "target_name": "221B Baker Street",
                    },
                ],
            }
        }


class EntityExtractionResult(BaseModel):
    """Result of entity extraction from a chunk of content."""

    entities: List[ExtractedEntity] = Field(
        default_factory=list, description="Extracted entities"
    )
    chunk_index: int = Field(default=0, description="Index of the processed chunk")
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence in extraction quality"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "entities": [
                    {
                        "name": "Sherlock Holmes",
                        "type": "character",
                        "description": "A brilliant detective...",
                        "aliases": ["Mr. Holmes"],
                        "attributes": {"occupation": "Detective"},
                        "relationships": [],
                    }
                ],
                "chunk_index": 0,
                "confidence": 0.95,
            }
        }
