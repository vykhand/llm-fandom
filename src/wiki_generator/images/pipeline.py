"""Image acquisition pipeline with fallback strategies."""

from typing import List, Optional

from loguru import logger

from ..core.config import Config
from ..core.models import Entity


class ImagePipeline:
    """Orchestrates image acquisition using multiple strategies."""

    def __init__(self, config: Config):
        self.config = config

    async def acquire_image(self, entity: Entity) -> Optional[str]:
        """
        Acquire an image for an entity using fallback strategies.

        Returns:
            URL or path to the acquired image, or None if all strategies fail.
        """
        # This is a stub implementation
        # Full implementation would try: extract -> search -> generate
        logger.debug(f"Image acquisition for {entity.name} (not yet implemented)")
        return None

    async def acquire_images(self, entities: List[Entity]) -> List[Entity]:
        """Acquire images for multiple entities."""
        # Update entities with image URLs
        for entity in entities:
            image_url = await self.acquire_image(entity)
            if image_url:
                entity.image_url = image_url

        return entities
