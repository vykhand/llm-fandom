"""Configuration management for wiki generator."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProviderConfig(BaseSettings):
    """Configuration for an LLM provider."""

    name: str = Field(description="Provider name (anthropic, openai)")
    model: str = Field(description="Model identifier")
    api_key_env: str = Field(description="Environment variable for API key")
    max_tokens: int = Field(default=4096, description="Max tokens per request")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    timeout: int = Field(default=60, description="Request timeout in seconds")


class LLMConfig(BaseSettings):
    """LLM configuration."""

    providers: List[Dict[str, Any]] = Field(default_factory=list)
    fallback_order: List[str] = Field(default_factory=list)
    chunk_size: int = Field(default=4000, description="Token chunk size for processing")
    max_retries: int = Field(default=3, description="Max retry attempts")
    retry_delay: int = Field(default=2, description="Retry delay in seconds")


class ImageConfig(BaseSettings):
    """Image acquisition configuration."""

    strategies: List[str] = Field(
        default_factory=lambda: ["extract", "search", "generate"],
        description="Image strategies in order of preference",
    )
    generate_provider: str = Field(default="dalle", description="AI generation provider")
    generate_model: str = Field(default="dall-e-3", description="AI generation model")
    max_width: int = Field(default=1024, description="Max image width")
    max_height: int = Field(default=1024, description="Max image height")
    format: str = Field(default="webp", description="Output image format")


class SiteConfig(BaseSettings):
    """Static site configuration."""

    generator: str = Field(default="mkdocs", description="Site generator")
    theme: str = Field(default="material", description="Theme name")
    output_dir: str = Field(default="./output/site", description="Output directory")
    site_name: str = Field(default="Generated Wiki", description="Site name")
    site_description: str = Field(
        default="AI-generated wiki", description="Site description"
    )


class ExtractionConfig(BaseSettings):
    """Entity extraction configuration."""

    chunk_size: int = Field(default=4000, description="Token chunk size")
    overlap: int = Field(default=200, description="Chunk overlap in tokens")
    entity_types: List[str] = Field(
        default_factory=lambda: [
            "character",
            "location",
            "organization",
            "concept",
            "event",
            "item",
        ]
    )
    min_confidence: float = Field(
        default=0.6, ge=0.0, le=1.0, description="Minimum extraction confidence"
    )


class Config(BaseSettings):
    """Main configuration for wiki generator."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM Configuration
    llm: LLMConfig = Field(default_factory=LLMConfig)

    # Image Configuration
    images: ImageConfig = Field(default_factory=ImageConfig)

    # Site Configuration
    site: SiteConfig = Field(default_factory=SiteConfig)

    # Extraction Configuration
    extraction: ExtractionConfig = Field(default_factory=ExtractionConfig)

    # Storage
    database_url: str = Field(
        default="sqlite:///./output/data/wiki.db", description="Database URL"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    # Paths
    output_dir: str = Field(default="./output", description="Base output directory")
    prompts_dir: str = Field(
        default="./config/prompts", description="Prompts directory"
    )

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Config":
        """Load configuration from YAML file."""
        path = Path(yaml_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {yaml_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def get_provider_config(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific provider."""
        for provider in self.llm.providers:
            if provider.get("name") == provider_name:
                return provider
        return None

    def get_api_key(self, env_var: str) -> Optional[str]:
        """Get API key from environment."""
        return os.getenv(env_var)


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from file or environment."""
    if config_path and Path(config_path).exists():
        return Config.from_yaml(config_path)

    # Try default config path
    default_path = Path("./config/default_config.yaml")
    if default_path.exists():
        return Config.from_yaml(str(default_path))

    # Fall back to environment variables only
    return Config()
