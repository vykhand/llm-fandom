# Wiki Generator Architecture

## Overview

The Wiki Generator follows a pipeline architecture with clearly separated concerns and extensible components.

## Component Overview

```
┌─────────────┐
│   CLI       │  Command-line interface
└──────┬──────┘
       │
┌──────▼──────┐
│  Pipeline   │  Main orchestrator
└──────┬──────┘
       │
       ├─────► Content Parser  (PDF, Web, Text)
       │
       ├─────► LLM Orchestrator (Multi-provider with fallback)
       │           │
       │           ├─── Anthropic Provider
       │           └─── OpenAI Provider
       │
       ├─────► Entity Extractor (LLM-powered with structured output)
       │
       ├─────► Wiki Generator (Article creation)
       │
       ├─────► Image Pipeline (Extract → Search → Generate)
       │
       ├─────► Site Builder (MkDocs static site)
       │
       └─────► Repository (SQLite storage)
```

## Core Components

### 1. Pipeline (`core/pipeline.py`)

**Responsibility**: Orchestrates the entire wiki generation workflow

**Key Methods**:
- `generate_wiki(source)`: Main entry point
- `_parse_source()`: Delegates to appropriate parser
- Coordinates all phases sequentially

**Flow**:
1. Parse source content
2. Extract entities
3. Generate articles
4. Acquire images (optional)
5. Build static site
6. Save metadata

### 2. LLM Layer (`llm/`)

**Responsibility**: Provides unified interface to multiple LLM providers with automatic fallback

**Components**:
- `LLMOrchestrator`: Manages providers and fallback logic
- `LLMProvider` (base): Abstract interface
- `AnthropicProvider`: Claude implementation
- `OpenAIProvider`: GPT implementation

**Key Features**:
- Automatic provider fallback on errors
- Retry logic with exponential backoff (via `tenacity`)
- Structured output support (via `instructor`)
- Rate limiting and error handling

**Usage**:
```python
response = await llm.generate(prompt, system_prompt)
entities = await llm.generate_structured(prompt, EntityExtractionResult)
```

### 3. Content Parsers (`parsers/`)

**Responsibility**: Extract text and metadata from various sources

**Components**:
- `ContentParser` (base): Abstract interface
- `PDFParser`: Extract from PDF files (via `pdfplumber`)
- `WebParser`: Scrape websites (via `trafilatura`)
- `TextParser`: Handle plain text/markdown

**Output**: `ParsedContent` with text, metadata, and extracted images

### 4. Entity Extraction (`extraction/`)

**Responsibility**: Extract structured entities from content using LLMs

**Components**:
- `EntityExtractor`: Main extraction engine
- `schemas.py`: Pydantic models for structured output
- `entity_extraction.jinja2`: Prompt template

**Process**:
1. Chunk content (configurable size with overlap)
2. Extract entities from each chunk in parallel
3. Merge and deduplicate entities
4. Link relationships between entities

**Entity Types**: Character, Location, Organization, Concept, Event, Item

### 5. Wiki Generation (`generation/`)

**Responsibility**: Generate comprehensive wiki articles from entities

**Components**:
- `WikiGenerator`: Article generation engine
- `wiki_generation.jinja2`: Prompt template

**Features**:
- Type-specific article sections
- Relationship linking
- Frontmatter generation
- Parallel article generation

### 6. Storage Layer (`storage/`)

**Responsibility**: Persist entities and articles

**Components**:
- `database.py`: SQLAlchemy models
- `repository.py`: Data access layer

**Models**:
- `EntityModel`: Stores extracted entities
- `ArticleModel`: Stores generated articles
- `MetadataModel`: Processing metadata

### 7. Site Builder (`site/`)

**Responsibility**: Generate static MkDocs site

**Components**:
- `SiteBuilder`: Main builder
- `nav_generator.py`: Navigation structure

**Process**:
1. Create content directory structure
2. Write markdown files (organized by type)
3. Generate navigation config
4. Create `mkdocs.yml`
5. Build static HTML site

### 8. Image Pipeline (`images/`)

**Responsibility**: Acquire images for entities (Phase 6 - stub)

**Planned Strategies**:
1. Extract from source (PDFs, web pages)
2. Web search (DuckDuckGo)
3. AI generation (DALL-E)

## Data Models

### Core Models (`core/models.py`)

#### Entity
```python
Entity(
    id: str,              # Unique identifier
    name: str,            # Canonical name
    type: EntityType,     # CHARACTER, LOCATION, etc.
    description: str,     # 2-4 sentence description
    aliases: List[str],   # Alternative names
    attributes: Dict,     # Type-specific attributes
    relationships: List,  # Links to other entities
    mentions: List[str],  # Text excerpts
    tags: List[str],      # Categories
    image_url: str,       # Optional image
)
```

#### Relationship
```python
Relationship(
    source_id: str,           # Source entity ID
    target_id: str,           # Target entity ID
    relation_type: RelationType,  # Type of relationship
    description: str,         # Optional context
    strength: float,          # 0.0-1.0 importance
)
```

#### WikiArticle
```python
WikiArticle(
    entity_id: str,              # Associated entity
    title: str,                  # Article title
    content: str,                # Markdown content
    frontmatter: Dict,           # YAML metadata
    sections: List[Dict],        # Parsed sections
    image_url: str,              # Featured image
    related_articles: List[str], # Related entity IDs
)
```

## Configuration

### Config Structure (`core/config.py`)

```yaml
llm:
  providers:             # List of LLM providers
    - name: anthropic
      model: claude-3-5-sonnet-20241022
      api_key_env: ANTHROPIC_API_KEY
  fallback_order:        # Provider fallback sequence
    - anthropic
    - openai
  chunk_size: 4000       # Tokens per chunk
  max_retries: 3         # Retry attempts

extraction:
  chunk_size: 4000       # Text chunk size
  overlap: 200           # Chunk overlap
  entity_types:          # Types to extract
    - character
    - location
    # ...
  min_confidence: 0.6    # Extraction threshold

images:
  strategies:            # Image fallback order
    - extract
    - search
    - generate

site:
  generator: mkdocs      # Site generator
  theme: material        # MkDocs theme
  site_name: "..."       # Wiki title
```

## Extensibility Points

### Adding a New LLM Provider

1. Create provider class in `llm/providers/`
2. Inherit from `LLMProvider`
3. Implement `generate()` and `generate_structured()`
4. Register in `LLMOrchestrator._create_provider()`

### Adding a New Content Parser

1. Create parser class in `parsers/`
2. Inherit from `ContentParser`
3. Implement `parse()` and `can_parse()`
4. Register in `Pipeline.parsers`

### Customizing Prompts

1. Edit templates in `config/prompts/`
2. Use Jinja2 syntax for dynamic content
3. Variables available: `content`, `entity`, `related_entities`

### Adding Entity Types

1. Add to `EntityType` enum in `models.py`
2. Update `config/default_config.yaml`
3. Add type-specific sections in `wiki_generation.jinja2`

## Error Handling

### Retry Strategy

- **LLM calls**: 3 retries with exponential backoff (1s, 2s, 4s)
- **Provider fallback**: Automatic switch to next provider on failure
- **Chunk processing**: Individual chunk failures logged but don't stop pipeline

### Error Logging

- `loguru` for structured logging
- Verbose mode available via CLI flag
- Errors saved to database metadata

## Performance Optimizations

### Parallel Processing

- Entity extraction: Chunks processed in parallel
- Article generation: Entities processed in parallel (5 concurrent max)
- Image acquisition: Entities processed in parallel (planned)

### Caching

- LLM responses: Not implemented (future enhancement)
- Images: File-based caching (future enhancement)

### Database

- SQLite for simplicity (can switch to PostgreSQL for scale)
- Indexed queries on entity name and type

## Testing Strategy

### Unit Tests

- Core models validation
- Parser functionality
- Configuration loading

### Integration Tests

- End-to-end pipeline with sample content
- Multi-provider fallback
- Error recovery

### Test Structure

```
tests/
├── test_models.py          # Core model tests
├── test_parsers.py         # Parser tests
├── test_extraction.py      # Entity extraction tests
├── test_generation.py      # Article generation tests
└── conftest.py             # Fixtures
```

## Future Enhancements

### Phase 6: Image Pipeline
- Extract images from PDFs/websites
- Web search integration (DuckDuckGo)
- AI generation (DALL-E 3)

### Phase 7: Advanced Features
- Local LLM support (Ollama, llama.cpp)
- Multi-language wikis
- Interactive relationship graphs
- Custom entity types
- Collaborative editing export

### Phase 8: Optimization
- Response caching
- Incremental updates
- Streaming generation
- Progress indicators

## Dependencies

### Core
- `pydantic`: Data validation
- `click`: CLI framework
- `loguru`: Logging
- `jinja2`: Template rendering
- `pyyaml`: Configuration

### LLM
- `anthropic`: Claude API
- `openai`: GPT API
- `instructor`: Structured outputs
- `tenacity`: Retry logic

### Content Processing
- `pdfplumber`: PDF parsing
- `trafilatura`: Web scraping
- `beautifulsoup4`: HTML parsing

### Site Generation
- `mkdocs`: Static site generator
- `mkdocs-material`: Theme
- `pymdown-extensions`: Markdown extensions

### Storage
- `sqlalchemy`: ORM
- `aiosqlite`: Async SQLite
