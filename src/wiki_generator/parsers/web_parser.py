"""Web content parser."""

from typing import List

import requests
import trafilatura
from bs4 import BeautifulSoup
from loguru import logger

from ..core.models import ParsedContent
from .base import ContentParser


class WebParser(ContentParser):
    """Parser for web content."""

    @property
    def name(self) -> str:
        return "web"

    def can_parse(self, source: str) -> bool:
        """Check if source is a URL."""
        return source.startswith(("http://", "https://"))

    async def parse(self, source: str) -> ParsedContent:
        """Parse web content."""
        if not self.can_parse(source):
            raise ValueError(f"Invalid URL: {source}")

        logger.info(f"Fetching web content: {source}")

        try:
            # Fetch the page
            response = requests.get(
                source,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; WikiGenerator/1.0)"
                },
                timeout=30,
            )
            response.raise_for_status()
            html = response.text

            # Extract main content using trafilatura
            text = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                include_images=False,
            )

            if not text:
                # Fallback to basic extraction
                soup = BeautifulSoup(html, "html.parser")
                text = soup.get_text(separator="\n", strip=True)

            # Extract metadata
            soup = BeautifulSoup(html, "html.parser")
            metadata = {
                "url": source,
                "title": "",
                "description": "",
            }

            if soup.title:
                metadata["title"] = soup.title.string or ""

            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                metadata["description"] = meta_desc["content"]

            # Extract image URLs
            images: List[str] = []
            for img in soup.find_all("img"):
                src = img.get("src")
                if src:
                    # Convert relative URLs to absolute
                    if src.startswith("//"):
                        src = "https:" + src
                    elif src.startswith("/"):
                        from urllib.parse import urljoin

                        src = urljoin(source, src)
                    images.append(src)

            logger.success(
                f"Parsed web content: {len(text)} characters, {len(images)} images"
            )

            return ParsedContent(
                text=text or "",
                metadata=metadata,
                images=images[:20],  # Limit to first 20 images
            )

        except Exception as e:
            logger.error(f"Error parsing web content {source}: {str(e)}")
            raise
