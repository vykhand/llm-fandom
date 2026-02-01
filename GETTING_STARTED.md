# Getting Started with Wiki Generator

This guide will help you set up and use the Wiki Generator to create beautiful AI-powered wikis from any content source.

## Prerequisites

- Python 3.10 or higher
- uv (for dependency management)
- API keys for LLM providers (Anthropic Claude or OpenAI)

## Installation

### 1. Install uv

If you don't have uv installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install Dependencies

```bash
cd wiki-generator
uv sync --extra dev
```

This will create a virtual environment and install all required dependencies.

### 3. Set Up API Keys

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# At minimum, provide one of these:
ANTHROPIC_API_KEY=sk-ant-your-key-here
# or
OPENAI_API_KEY=sk-your-key-here
```

### 4. Verify Setup

Check that everything is configured correctly:

```bash
uv run wiki-generator check-config
```

This will show which API keys are found and validate your configuration.

## Quick Start

### Generate a Wiki from the Sample Story

Try the included sample story to see how it works:

```bash
uv run wiki-generator generate examples/sample_story.txt --output ./my-first-wiki --verbose
```

This will:
1. Parse the sample story
2. Extract entities (characters, locations, organizations, etc.)
3. Generate comprehensive wiki articles for each entity
4. Build a beautiful static website with navigation

### View Your Wiki

After generation completes, you can view the wiki:

```bash
uv run wiki-generator serve ./my-first-wiki
```

Then open your browser to http://localhost:8000

## Usage Examples

### Generate from a PDF

```bash
uv run wiki-generator generate book.pdf --output ./book-wiki
```

### Generate from a Website

```bash
uv run wiki-generator generate https://example.com/article --output ./web-wiki
```

### Generate and Serve Immediately

```bash
uv run wiki-generator generate source.txt --serve
```

### Use Custom Configuration

Create a custom config file (e.g., `my-config.yaml`):

```yaml
llm:
  providers:
    - name: anthropic
      model: claude-3-5-sonnet-20241022
      api_key_env: ANTHROPIC_API_KEY

  fallback_order:
    - anthropic

site:
  site_name: My Custom Wiki
  site_description: A wiki about my favorite topic

extraction:
  chunk_size: 6000
  min_confidence: 0.7
```

Then use it:

```bash
uv run wiki-generator generate source.txt --config my-config.yaml
```

## Understanding the Output

The wiki generator creates the following structure:

```
output/
├── data/
│   └── wiki.db              # SQLite database with all entities and articles
├── site/                    # Built static website (ready to deploy)
│   ├── index.html
│   ├── character/
│   ├── location/
│   └── ...
└── mkdocs.yml              # MkDocs configuration
```

### Output Directories

- **data/**: Contains the SQLite database with all extracted entities and generated articles
- **site/**: The built static website (HTML, CSS, JS) ready to be deployed anywhere
- **docs/**: Markdown source files organized by entity type

### Entity Types

The generator extracts these entity types:

- **Characters**: People, protagonists, antagonists, supporting characters
- **Locations**: Cities, buildings, regions, landmarks
- **Organizations**: Groups, companies, factions, institutions
- **Concepts**: Ideas, theories, systems, technologies
- **Events**: Major occurrences, battles, ceremonies
- **Items**: Significant objects, artifacts, weapons

## Tips for Best Results

### 1. Content Quality

- Longer, more detailed content produces better results
- Well-structured content (chapters, sections) helps entity extraction
- Include descriptive details about characters, places, and objects

### 2. Processing Large Books

For books over 100 pages, consider:

- Increasing chunk size in config: `extraction.chunk_size: 6000`
- Processing in sections if needed
- Allowing sufficient processing time (30-60 minutes for a full novel)

### 3. Cost Management

LLM API calls can add up for large books:

- Start with small samples to test
- Use caching (automatic for repeated entities)
- Monitor API usage in your provider dashboard
- Consider using GPT-4-turbo (faster/cheaper) for initial testing

### 4. Customizing the Wiki

After generation, you can:

- Edit the markdown files in `docs/` directory
- Customize the theme by editing `mkdocs.yml`
- Add custom CSS in `docs/stylesheets/`
- Rebuild with: `mkdocs build` (from the output directory)

## Troubleshooting

### No API Key Found

```
Error: No API key found for provider anthropic
```

**Solution**: Make sure you've created a `.env` file with your API keys.

### MkDocs Not Found

```
Error: mkdocs command not found
```

**Solution**: Reinstall dependencies with `uv sync --extra dev`

### Empty Extraction

If no entities are extracted:

- Check that your source file has readable content
- Try with the sample story first to verify setup
- Enable verbose logging with `--verbose` flag
- Check the logs for LLM errors

### Rate Limiting

If you hit rate limits:

- The system will automatically retry with exponential backoff
- Consider reducing `chunk_size` to make smaller requests
- Add delays between requests in config (future feature)

## Advanced Usage

### Programmatic Usage

You can use the wiki generator as a library:

```python
import asyncio
from wiki_generator.core.config import Config
from wiki_generator.core.pipeline import WikiPipeline

async def main():
    config = Config()
    pipeline = WikiPipeline(config)

    try:
        site_path = await pipeline.generate_wiki("book.pdf")
        print(f"Wiki generated at: {site_path}")
    finally:
        await pipeline.close()

asyncio.run(main())
```

### Custom Prompts

You can customize the entity extraction and wiki generation prompts:

1. Copy the templates from `config/prompts/`
2. Modify them to suit your needs
3. Update `prompts_dir` in your config

### Database Access

The generated SQLite database can be queried directly:

```python
from wiki_generator.storage.database import init_database
from wiki_generator.storage.repository import Repository

session_maker = init_database("sqlite:///./output/data/wiki.db")
repo = Repository(session_maker())

# Get all entities
entities = repo.get_all_entities()
for entity in entities:
    print(f"{entity.name} ({entity.type})")
```

## Next Steps

- Read the full documentation in `README.md`
- Explore the code structure in `src/wiki_generator/`
- Check the implementation plan for upcoming features
- Report issues or contribute at the GitHub repository

## Getting Help

If you encounter issues:

1. Check this guide and the README
2. Enable verbose logging: `--verbose`
3. Review the logs in the console output
4. Check your API keys and configuration
5. Try the sample story to isolate issues

Happy wiki generating! 🎉
