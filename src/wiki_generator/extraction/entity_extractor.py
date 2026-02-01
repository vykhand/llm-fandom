"""Entity extraction from content using LLMs."""

import asyncio
from pathlib import Path
from typing import Dict, List, Set

from jinja2 import Environment, FileSystemLoader
from loguru import logger

from ..core.config import Config
from ..core.models import Entity, EntityType, ParsedContent, Relationship, RelationType
from ..llm.orchestrator import LLMOrchestrator
from .schemas import EntityExtractionResult, ExtractedEntity


class EntityExtractor:
    """Extracts entities from parsed content using LLMs."""

    def __init__(self, llm: LLMOrchestrator, config: Config):
        self.llm = llm
        self.config = config

        # Load prompt templates
        prompts_dir = Path(config.prompts_dir)
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(prompts_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    async def extract_entities(self, content: ParsedContent) -> List[Entity]:
        """Extract all entities from parsed content."""
        logger.info("Starting entity extraction")

        # Chunk the content
        chunks = self._chunk_content(content.text)
        logger.info(f"Split content into {len(chunks)} chunks")

        # Extract entities from each chunk in parallel
        tasks = [
            self._extract_from_chunk(chunk, idx) for idx, chunk in enumerate(chunks)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out failed extractions
        valid_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Chunk {idx} extraction failed: {str(result)}")
            else:
                valid_results.append(result)

        # Merge and deduplicate entities
        entities = self._merge_entities(valid_results)

        # Analyze and link relationships
        entities = self._link_relationships(entities)

        logger.success(f"Extracted {len(entities)} unique entities")
        return entities

    def _chunk_content(self, text: str) -> List[str]:
        """Split content into chunks for processing."""
        chunk_size = self.config.extraction.chunk_size
        overlap = self.config.extraction.overlap

        # Simple word-based chunking
        words = text.split()
        chunks = []

        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk_words = words[start:end]
            chunks.append(" ".join(chunk_words))
            start = end - overlap if end < len(words) else end

        return chunks

    async def _extract_from_chunk(
        self, chunk: str, chunk_index: int
    ) -> EntityExtractionResult:
        """Extract entities from a single chunk."""
        logger.debug(f"Extracting from chunk {chunk_index}")

        # Load and render prompt template
        template = self.jinja_env.get_template("entity_extraction.jinja2")
        prompt = template.render(content=chunk)

        try:
            # Use structured output
            result = await self.llm.generate_structured(
                prompt=prompt,
                response_model=EntityExtractionResult,
                system_prompt="You are an expert at analyzing content and extracting structured entity information for wiki generation.",
            )

            result.chunk_index = chunk_index
            logger.debug(f"Chunk {chunk_index}: extracted {len(result.entities)} entities")
            return result

        except Exception as e:
            logger.error(f"Failed to extract from chunk {chunk_index}: {str(e)}")
            raise

    def _merge_entities(
        self, results: List[EntityExtractionResult]
    ) -> List[Entity]:
        """Merge and deduplicate entities from multiple chunks."""
        entity_map: Dict[str, Entity] = {}
        seen_names: Set[str] = set()

        for result in results:
            for extracted in result.entities:
                # Create a normalized key for deduplication
                normalized_name = extracted.name.lower().strip()

                # Check if we've seen this entity
                if normalized_name in seen_names:
                    # Merge with existing entity
                    existing_key = self._find_entity_key(entity_map, normalized_name)
                    if existing_key:
                        entity = entity_map[existing_key]
                        entity = self._merge_entity_data(entity, extracted)
                        entity_map[existing_key] = entity
                    continue

                # New entity
                seen_names.add(normalized_name)

                # Convert ExtractedEntity to Entity
                entity = Entity(
                    name=extracted.name,
                    type=extracted.type,
                    description=extracted.description,
                    aliases=extracted.aliases,
                    attributes=extracted.attributes,
                )

                # Store relationships for later linking
                entity.attributes["_extracted_relationships"] = [
                    {
                        "type": rel.relation_type,
                        "target": rel.target_name,
                        "description": rel.description,
                    }
                    for rel in extracted.relationships
                ]

                entity_map[entity.id] = entity

        return list(entity_map.values())

    def _find_entity_key(
        self, entity_map: Dict[str, Entity], normalized_name: str
    ) -> str | None:
        """Find entity key by normalized name."""
        for entity_id, entity in entity_map.items():
            if entity.name.lower().strip() == normalized_name:
                return entity_id
            # Check aliases too
            for alias in entity.aliases:
                if alias.lower().strip() == normalized_name:
                    return entity_id
        return None

    def _merge_entity_data(
        self, existing: Entity, new: ExtractedEntity
    ) -> Entity:
        """Merge new entity data into existing entity."""
        # Merge aliases
        for alias in new.aliases:
            if alias not in existing.aliases and alias.lower() != existing.name.lower():
                existing.aliases.append(alias)

        # Merge attributes (new values override)
        for key, value in new.attributes.items():
            if key not in existing.attributes:
                existing.attributes[key] = value

        # Keep longer description
        if len(new.description) > len(existing.description):
            existing.description = new.description

        return existing

    def _link_relationships(self, entities: List[Entity]) -> List[Entity]:
        """Link relationships between entities."""
        # Build name to ID mapping
        name_to_id: Dict[str, str] = {}
        for entity in entities:
            name_to_id[entity.name.lower().strip()] = entity.id
            for alias in entity.aliases:
                name_to_id[alias.lower().strip()] = entity.id

        # Process extracted relationships
        for entity in entities:
            extracted_rels = entity.attributes.pop("_extracted_relationships", [])

            for rel_data in extracted_rels:
                target_name = rel_data["target"].lower().strip()
                target_id = name_to_id.get(target_name)

                if not target_id:
                    logger.debug(
                        f"Relationship target not found: {rel_data['target']} "
                        f"for entity {entity.name}"
                    )
                    continue

                # Convert relation type string to enum
                try:
                    relation_type = RelationType(rel_data["type"].lower())
                except ValueError:
                    relation_type = RelationType.RELATED_TO

                # Create relationship
                relationship = Relationship(
                    source_id=entity.id,
                    target_id=target_id,
                    relation_type=relation_type,
                    description=rel_data.get("description", ""),
                )

                entity.relationships.append(relationship)

        return entities
