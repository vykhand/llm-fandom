"""Data access layer for entities and articles."""

from typing import List, Optional

from sqlalchemy.orm import Session

from ..core.models import Entity, ProcessingMetadata, WikiArticle
from .database import ArticleModel, EntityModel, MetadataModel


class Repository:
    """Repository for accessing stored data."""

    def __init__(self, session: Session):
        self.session = session

    def save_entity(self, entity: Entity) -> None:
        """Save an entity to the database."""
        model = EntityModel(
            id=entity.id,
            name=entity.name,
            type=entity.type.value,
            description=entity.description,
            aliases=entity.aliases,
            attributes=entity.attributes,
            relationships=[
                {
                    "source_id": rel.source_id,
                    "target_id": rel.target_id,
                    "relation_type": rel.relation_type.value,
                    "description": rel.description,
                    "strength": rel.strength,
                }
                for rel in entity.relationships
            ],
            mentions=entity.mentions,
            tags=entity.tags,
            image_url=entity.image_url,
        )

        self.session.merge(model)
        self.session.commit()

    def save_entities(self, entities: List[Entity]) -> None:
        """Save multiple entities."""
        for entity in entities:
            self.save_entity(entity)

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID."""
        model = self.session.query(EntityModel).filter_by(id=entity_id).first()
        if not model:
            return None

        return self._entity_from_model(model)

    def get_all_entities(self) -> List[Entity]:
        """Get all entities."""
        models = self.session.query(EntityModel).all()
        return [self._entity_from_model(m) for m in models]

    def save_article(self, article: WikiArticle) -> None:
        """Save a wiki article."""
        model = ArticleModel(
            entity_id=article.entity_id,
            title=article.title,
            content=article.content,
            frontmatter=article.frontmatter,
            sections=article.sections,
            image_url=article.image_url,
            related_articles=article.related_articles,
        )

        self.session.add(model)
        self.session.commit()

    def save_articles(self, articles: List[WikiArticle]) -> None:
        """Save multiple articles."""
        for article in articles:
            self.save_article(article)

    def get_article_by_entity(self, entity_id: str) -> Optional[WikiArticle]:
        """Get article for an entity."""
        model = (
            self.session.query(ArticleModel).filter_by(entity_id=entity_id).first()
        )
        if not model:
            return None

        return self._article_from_model(model)

    def save_metadata(self, metadata: ProcessingMetadata) -> None:
        """Save processing metadata."""
        model = MetadataModel(
            source_path=metadata.source_path,
            source_type=metadata.source_type,
            total_entities=metadata.total_entities,
            total_articles=metadata.total_articles,
            processing_time=metadata.processing_time,
            llm_provider=metadata.llm_provider,
            errors=metadata.errors,
            warnings=metadata.warnings,
        )

        self.session.add(model)
        self.session.commit()

    def _entity_from_model(self, model: EntityModel) -> Entity:
        """Convert database model to Entity."""
        from ..core.models import EntityType, Relationship, RelationType

        return Entity(
            id=model.id,
            name=model.name,
            type=EntityType(model.type),
            description=model.description,
            aliases=model.aliases or [],
            attributes=model.attributes or {},
            relationships=[
                Relationship(
                    source_id=rel["source_id"],
                    target_id=rel["target_id"],
                    relation_type=RelationType(rel["relation_type"]),
                    description=rel.get("description"),
                    strength=rel.get("strength", 1.0),
                )
                for rel in (model.relationships or [])
            ],
            mentions=model.mentions or [],
            tags=model.tags or [],
            image_url=model.image_url,
        )

    def _article_from_model(self, model: ArticleModel) -> WikiArticle:
        """Convert database model to WikiArticle."""
        return WikiArticle(
            entity_id=model.entity_id,
            title=model.title,
            content=model.content,
            frontmatter=model.frontmatter or {},
            sections=model.sections or [],
            image_url=model.image_url,
            related_articles=model.related_articles or [],
        )
