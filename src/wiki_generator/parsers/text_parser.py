"""Plain text and markdown parser."""

from pathlib import Path

from loguru import logger

from ..core.models import ParsedContent
from .base import ContentParser


class TextParser(ContentParser):
    """Parser for plain text and markdown files."""

    @property
    def name(self) -> str:
        return "text"

    def can_parse(self, source: str) -> bool:
        """Check if source is a text file."""
        path = Path(source)
        return path.exists() and path.suffix.lower() in [".txt", ".md", ".markdown", ""]

    async def parse(self, source: str) -> ParsedContent:
        """Parse text file."""
        path = Path(source)

        # If it's not a file, treat as raw text
        if not path.exists():
            logger.info("Parsing raw text input")
            return ParsedContent(
                text=source,
                metadata={"source_type": "raw_text"},
            )

        logger.info(f"Parsing text file: {source}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()

            metadata = {
                "filename": path.name,
                "size": path.stat().st_size,
                "format": path.suffix.lower() or "txt",
            }

            logger.success(f"Parsed text file: {len(text)} characters")

            return ParsedContent(
                text=text,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Error parsing text file {source}: {str(e)}")
            raise
