"""Base content parser interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ..core.models import ParsedContent


class ContentParser(ABC):
    """Abstract base class for content parsers."""

    @abstractmethod
    async def parse(self, source: str) -> ParsedContent:
        """Parse content from source."""
        pass

    @abstractmethod
    def can_parse(self, source: str) -> bool:
        """Check if this parser can handle the source."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Parser name."""
        pass


def detect_parser(source: str) -> Optional[str]:
    """Detect the appropriate parser for a source."""
    # Check if it's a URL
    if source.startswith(("http://", "https://")):
        return "web"

    # Check if it's a file
    path = Path(source)
    if path.exists() and path.is_file():
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return "pdf"
        elif suffix in [".txt", ".md", ".markdown"]:
            return "text"

    # Default to text parser
    return "text"
