"""Main pipeline orchestrator for wiki generation."""

import time
from pathlib import Path
from typing import Optional

from loguru import logger

from ..extraction.entity_extractor import EntityExtractor
from ..generation.wiki_generator import WikiGenerator
from ..llm.orchestrator import LLMOrchestrator
from ..parsers.base import detect_parser
from ..parsers.pdf_parser import PDFParser
from ..parsers.text_parser import TextParser
from ..parsers.web_parser import WebParser
from ..site.builder import SiteBuilder
from ..storage.database import init_database
from ..storage.repository import Repository
from .config import Config
from .models import ProcessingMetadata


class WikiPipeline:
    """Main pipeline for wiki generation."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

        # Initialize components
        self.llm = LLMOrchestrator(self.config)
        self.entity_extractor = EntityExtractor(self.llm, self.config)
        self.wiki_generator = WikiGenerator(self.llm, self.config)
        self.site_builder = SiteBuilder(self.config)

        # Initialize parsers
        self.parsers = {
            "pdf": PDFParser(),
            "web": WebParser(),
            "text": TextParser(),
        }

        # Initialize database
        session_maker = init_database(self.config.database_url)
        self.repository = Repository(session_maker())

    async def generate_wiki(
        self,
        source: str,
        output_dir: Optional[str] = None,
    ) -> str:
        """
        Generate a complete wiki from a source.

        Args:
            source: Path to PDF, URL, or text file
            output_dir: Optional output directory override

        Returns:
            Path to the generated wiki site
        """
        start_time = time.time()
        metadata = ProcessingMetadata(
            source_path=source,
            source_type="unknown",
        )

        try:
            logger.info(f"Starting wiki generation from: {source}")

            # Step 1: Parse source content
            logger.info("Step 1: Parsing source content")
            parsed_content = await self._parse_source(source)
            metadata.source_type = detect_parser(source) or "text"
            logger.success(f"Parsed {len(parsed_content.text)} characters")

            # Step 2: Extract entities
            logger.info("Step 2: Extracting entities")
            entities = await self.entity_extractor.extract_entities(parsed_content)
            metadata.total_entities = len(entities)
            logger.success(f"Extracted {len(entities)} entities")

            # Save entities to database
            self.repository.save_entities(entities)
            logger.debug("Saved entities to database")

            # Step 3: Generate wiki articles
            logger.info("Step 3: Generating wiki articles")
            articles = await self.wiki_generator.generate_articles(entities)
            metadata.total_articles = len(articles)
            logger.success(f"Generated {len(articles)} articles")

            # Save articles to database
            self.repository.save_articles(articles)
            logger.debug("Saved articles to database")

            # Step 4: Build static site
            logger.info("Step 4: Building static site")
            site_path = await self.site_builder.build_site(
                entities=entities,
                articles=articles,
                output_dir=output_dir or self.config.site.output_dir,
            )
            logger.success(f"Built wiki site at: {site_path}")

            # Record metadata
            metadata.processing_time = time.time() - start_time
            metadata.llm_provider = self._get_primary_provider()
            self.repository.save_metadata(metadata)

            logger.success(
                f"Wiki generation complete in {metadata.processing_time:.2f}s"
            )
            return site_path

        except Exception as e:
            logger.error(f"Wiki generation failed: {str(e)}")
            metadata.errors.append(str(e))
            metadata.processing_time = time.time() - start_time
            self.repository.save_metadata(metadata)
            raise

    async def _parse_source(self, source: str):
        """Parse source content using appropriate parser."""
        parser_name = detect_parser(source)
        parser = self.parsers.get(parser_name)

        if not parser:
            raise ValueError(f"No parser available for: {source}")

        return await parser.parse(source)

    def _get_primary_provider(self) -> str:
        """Get the primary LLM provider name."""
        if self.config.llm.fallback_order:
            return self.config.llm.fallback_order[0]
        return "unknown"

    async def close(self) -> None:
        """Clean up resources."""
        await self.llm.close()
