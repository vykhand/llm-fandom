"""PDF content parser."""

from pathlib import Path
from typing import List

import pdfplumber
from loguru import logger

from ..core.models import ParsedContent
from .base import ContentParser


class PDFParser(ContentParser):
    """Parser for PDF files."""

    @property
    def name(self) -> str:
        return "pdf"

    def can_parse(self, source: str) -> bool:
        """Check if source is a PDF file."""
        path = Path(source)
        return path.exists() and path.suffix.lower() == ".pdf"

    async def parse(self, source: str) -> ParsedContent:
        """Parse PDF file."""
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {source}")

        logger.info(f"Parsing PDF: {source}")

        text_parts: List[str] = []
        metadata = {}
        images: List[str] = []

        try:
            with pdfplumber.open(path) as pdf:
                # Extract metadata
                if pdf.metadata:
                    metadata = {
                        "title": pdf.metadata.get("Title", ""),
                        "author": pdf.metadata.get("Author", ""),
                        "creator": pdf.metadata.get("Creator", ""),
                        "producer": pdf.metadata.get("Producer", ""),
                        "subject": pdf.metadata.get("Subject", ""),
                    }

                metadata["pages"] = len(pdf.pages)

                # Extract text from each page
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        text_parts.append(f"--- Page {page_num} ---\n{text}")

                    # Extract images (store paths for later processing)
                    # Note: pdfplumber doesn't directly extract images,
                    # we'll use pdf2image in the image pipeline if needed

        except Exception as e:
            logger.error(f"Error parsing PDF {source}: {str(e)}")
            raise

        full_text = "\n\n".join(text_parts)

        logger.success(
            f"Parsed PDF: {len(text_parts)} pages, {len(full_text)} characters"
        )

        return ParsedContent(
            text=full_text,
            metadata=metadata,
            images=images,
        )
