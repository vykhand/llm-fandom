"""Wiki article generator."""

import asyncio
from pathlib import Path
from typing import Dict, List

from jinja2 import Environment, FileSystemLoader
from loguru import logger

from ..core.config import Config
from ..core.models import Entity, WikiArticle
from ..llm.orchestrator import LLMOrchestrator


class WikiGenerator:
    """Generates wiki articles from entities."""

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

    async def generate_articles(
        self, entities: List[Entity]
    ) -> List[WikiArticle]:
        """Generate wiki articles for all entities."""
        logger.info(f"Generating wiki articles for {len(entities)} entities")

        # Create entity lookup for relationships
        entity_map = {e.id: e for e in entities}

        # Generate articles in parallel (with concurrency limit)
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent generations

        async def generate_with_limit(entity: Entity) -> WikiArticle:
            async with semaphore:
                return await self._generate_article(entity, entity_map)

        tasks = [generate_with_limit(entity) for entity in entities]
        articles = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out failed generations
        valid_articles = []
        for idx, article in enumerate(articles):
            if isinstance(article, Exception):
                logger.error(
                    f"Failed to generate article for {entities[idx].name}: {str(article)}"
                )
            else:
                valid_articles.append(article)

        logger.success(f"Generated {len(valid_articles)} wiki articles")
        return valid_articles

    async def _generate_article(
        self, entity: Entity, entity_map: Dict[str, Entity]
    ) -> WikiArticle:
        """Generate a single wiki article."""
        logger.debug(f"Generating article for: {entity.name}")

        # Get related entities for context
        related_entities = []
        for relationship in entity.relationships:
            related = entity_map.get(relationship.target_id)
            if related:
                related_entities.append(related)

        # Load and render prompt template
        template = self.jinja_env.get_template("wiki_generation.jinja2")
        prompt = template.render(
            entity=entity,
            related_entities=related_entities,
        )

        try:
            # Generate article content
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt="You are an expert wiki editor creating comprehensive, well-structured articles in an encyclopedic style.",
            )

            content = response.content

            # Parse sections from the generated content
            sections = self._parse_sections(content)

            # Generate frontmatter
            frontmatter = self._generate_frontmatter(entity)

            # Create article
            article = WikiArticle(
                entity_id=entity.id,
                title=entity.name,
                content=content,
                frontmatter=frontmatter,
                sections=sections,
                image_url=entity.image_url,
                related_articles=[rel.target_id for rel in entity.relationships],
            )

            logger.debug(f"Generated article for {entity.name}: {len(content)} chars")
            return article

        except Exception as e:
            logger.error(f"Failed to generate article for {entity.name}: {str(e)}")
            raise

    def _parse_sections(self, content: str) -> List[Dict[str, str]]:
        """Parse sections from markdown content."""
        sections = []
        current_section = None
        current_content = []

        for line in content.split("\n"):
            if line.startswith("## "):
                # Save previous section
                if current_section:
                    sections.append({
                        "title": current_section,
                        "content": "\n".join(current_content).strip(),
                    })

                # Start new section
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_section:
            sections.append({
                "title": current_section,
                "content": "\n".join(current_content).strip(),
            })

        return sections

    def _generate_frontmatter(self, entity: Entity) -> Dict[str, any]:
        """Generate YAML frontmatter for the article."""
        frontmatter = {
            "title": entity.name,
            "type": entity.type.value,
            "tags": entity.tags if entity.tags else [entity.type.value],
        }

        if entity.aliases:
            frontmatter["aliases"] = entity.aliases

        # Add type-specific metadata
        if entity.type.value == "character":
            if "occupation" in entity.attributes:
                frontmatter["occupation"] = entity.attributes["occupation"]
            if "status" in entity.attributes:
                frontmatter["status"] = entity.attributes["status"]

        elif entity.type.value == "location":
            if "type" in entity.attributes:
                frontmatter["location_type"] = entity.attributes["type"]
            if "region" in entity.attributes:
                frontmatter["region"] = entity.attributes["region"]

        return frontmatter
