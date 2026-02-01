"""Command-line interface for wiki generator."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from loguru import logger

from .core.config import Config, load_config
from .core.pipeline import WikiPipeline


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    logger.remove()  # Remove default handler

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<level>{message}</level>"
    )

    level = "DEBUG" if verbose else "INFO"

    logger.add(
        sys.stderr,
        format=log_format,
        level=level,
        colorize=True,
    )


@click.group()
@click.version_option(version="0.1.0")
def main() -> None:
    """Wiki Generator - Transform any content into a beautiful wiki."""
    pass


@main.command()
@click.argument("source", type=str)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output directory for the wiki",
    default=None,
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file",
    default=None,
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
@click.option(
    "--serve",
    "-s",
    is_flag=True,
    help="Serve the wiki after generation",
)
def generate(
    source: str,
    output: Optional[str],
    config: Optional[str],
    verbose: bool,
    serve: bool,
) -> None:
    """
    Generate a wiki from SOURCE.

    SOURCE can be:
    - Path to a PDF file
    - URL to a website
    - Path to a text/markdown file
    """
    setup_logging(verbose)

    logger.info("Wiki Generator v0.1.0")
    logger.info(f"Source: {source}")

    try:
        # Load configuration
        cfg = load_config(config) if config else Config()

        # Override output directory if specified
        if output:
            cfg.site.output_dir = output

        # Run the pipeline
        asyncio.run(run_pipeline(source, cfg, serve))

    except KeyboardInterrupt:
        logger.warning("Generation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        if verbose:
            logger.exception(e)
        sys.exit(1)


async def run_pipeline(source: str, config: Config, serve: bool) -> None:
    """Run the wiki generation pipeline."""
    pipeline = WikiPipeline(config)

    try:
        # Generate the wiki
        with logger.contextualize():
            site_path = await pipeline.generate_wiki(source)

        logger.success(f"\n✨ Wiki generated successfully!")
        logger.info(f"📁 Location: {site_path}")

        # Serve if requested
        if serve:
            logger.info("\n🚀 Starting local server...")
            serve_site(Path(site_path).parent)

    finally:
        await pipeline.close()


def serve_site(project_dir: Path) -> None:
    """Serve the MkDocs site locally."""
    import subprocess

    try:
        logger.info("Press Ctrl+C to stop the server")
        subprocess.run(
            ["mkdocs", "serve"],
            cwd=str(project_dir),
            check=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to serve site: {e}")
    except FileNotFoundError:
        logger.error("mkdocs command not found. Install with: pip install mkdocs mkdocs-material")
    except KeyboardInterrupt:
        logger.info("\nServer stopped")


@main.command()
@click.argument("project_dir", type=click.Path(exists=True))
def serve(project_dir: str) -> None:
    """Serve an existing wiki site locally."""
    setup_logging(False)
    logger.info(f"Serving wiki from: {project_dir}")
    serve_site(Path(project_dir))


@main.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file",
    default=None,
)
def check_config(config: Optional[str]) -> None:
    """Validate configuration and check API keys."""
    setup_logging(True)

    try:
        cfg = load_config(config) if config else Config()

        logger.info("Configuration loaded successfully")
        logger.info(f"Database: {cfg.database_url}")
        logger.info(f"Output directory: {cfg.output_dir}")
        logger.info(f"Prompts directory: {cfg.prompts_dir}")

        logger.info("\nLLM Providers:")
        for provider in cfg.llm.providers:
            name = provider["name"]
            api_key_env = provider["api_key_env"]
            api_key = cfg.get_api_key(api_key_env)

            if api_key:
                logger.success(f"  ✓ {name}: API key found ({api_key_env})")
            else:
                logger.warning(f"  ✗ {name}: API key not found ({api_key_env})")

        logger.info(f"\nFallback order: {' -> '.join(cfg.llm.fallback_order)}")
        logger.info(f"Image strategies: {' -> '.join(cfg.images.strategies)}")

    except Exception as e:
        logger.error(f"Configuration check failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
