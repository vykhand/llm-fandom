"""Tests for core models."""

import pytest
from pydantic import ValidationError

from wiki_generator.core.models import Entity, EntityType, Relationship, RelationType


def test_entity_creation():
    """Test creating a basic entity."""
    entity = Entity(
        name="Test Entity",
        type=EntityType.CHARACTER,
        description="A test character for unit testing.",
    )

    assert entity.name == "Test Entity"
    assert entity.type == EntityType.CHARACTER
    assert entity.description == "A test character for unit testing."
    assert entity.aliases == []
    assert entity.relationships == []


def test_entity_validation():
    """Test entity validation."""
    # Empty name should fail
    with pytest.raises(ValidationError):
        Entity(
            name="",
            type=EntityType.CHARACTER,
            description="Test",
        )

    # Empty description should fail
    with pytest.raises(ValidationError):
        Entity(
            name="Test",
            type=EntityType.CHARACTER,
            description="",
        )


def test_relationship_creation():
    """Test creating a relationship."""
    rel = Relationship(
        source_id="entity_1",
        target_id="entity_2",
        relation_type=RelationType.ALLY_OF,
        description="Close allies",
        strength=0.9,
    )

    assert rel.source_id == "entity_1"
    assert rel.target_id == "entity_2"
    assert rel.relation_type == RelationType.ALLY_OF
    assert rel.strength == 0.9


def test_entity_with_relationships():
    """Test entity with relationships."""
    entity = Entity(
        name="Hero",
        type=EntityType.CHARACTER,
        description="The main hero.",
        relationships=[
            Relationship(
                source_id="hero_1",
                target_id="villain_1",
                relation_type=RelationType.ENEMY_OF,
            )
        ],
    )

    assert len(entity.relationships) == 1
    assert entity.relationships[0].relation_type == RelationType.ENEMY_OF
