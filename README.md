# Wiki Generator

> Transform any content into beautiful AI-powered wikis

An intelligent wiki generator that transforms books, websites, and documents into comprehensive, searchable wiki sites with automatically extracted entities, relationships, and beautiful formatting.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/dependency-uv-blue.svg)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

### Core Capabilities
- 📄 **Multi-Format Support** - PDFs, websites, plain text, and markdown
- 🤖 **AI-Powered Extraction** - Automatic entity and relationship extraction using LLMs
- 🔄 **Multi-Provider LLM** - Support for Anthropic Claude and OpenAI with automatic fallback
- 🎨 **Beautiful Output** - Fandom-style static sites using MkDocs Material theme
- 🔗 **Smart Linking** - Automatic cross-linking between related entities
- 💾 **Local Database** - SQLite storage for all extracted data
- 🛡️ **Robust Architecture** - Retry logic, error handling, and graceful fallback

### Entity Types
The system extracts and generates wiki articles for:
- 👤 **Characters** - People, protagonists, supporting roles
- 🗺️ **Locations** - Cities, buildings, regions, landmarks
- 🏛️ **Organizations** - Groups, companies, factions, institutions
- 💡 **Concepts** - Ideas, theories, systems, technologies
- ⚔️ **Events** - Major occurrences, battles, turning points
- ⚡ **Items** - Significant objects, artifacts, weapons

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- uv (dependency management)
- API key for Anthropic Claude or OpenAI

### Installation

```bash
# Clone the repository (if from git)
cd wiki-generator

# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies with uv
uv sync --extra dev

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys:
# ANTHROPIC_API_KEY=sk-ant-your-key-here
# or
# OPENAI_API_KEY=sk-your-key-here
```

### Verify Setup

```bash
uv run wiki-generator check-config
```

### Generate Your First Wiki

Try the included sample story:

```bash
uv run wiki-generator generate examples/sample_story.txt --output ./my-wiki --verbose
```

Then serve it locally:

```bash
uv run wiki-generator serve ./my-wiki
```

Open http://localhost:8000 to view your wiki!

## 📖 Usage

### Basic Commands

```bash
# Generate from a PDF
wiki-generator generate book.pdf --output ./book-wiki

# Generate from a website
wiki-generator generate https://example.com/article --output ./web-wiki

# Generate and serve immediately
wiki-generator generate source.txt --serve

# Use custom configuration
wiki-generator generate book.pdf --config custom-config.yaml

# Check configuration and API keys
wiki-generator check-config
```

### Command Options

```bash
wiki-generator generate [SOURCE] [OPTIONS]

Arguments:
  SOURCE              Path to PDF, URL, or text file

Options:
  -o, --output DIR    Output directory (default: ./output/site)
  -c, --config FILE   Configuration file path
  -v, --verbose       Enable verbose logging
  -s, --serve         Serve wiki after generation
  --help              Show help message
```

## 🏗️ Architecture

```
┌─────────────┐
│   Source    │  (PDF, Web, Text)
└──────┬──────┘
       │
┌──────▼──────────┐
│ Content Parser  │  Extract text and metadata
└──────┬──────────┘
       │
┌──────▼──────────┐
│ Entity Extractor│  AI-powered entity extraction
└──────┬──────────┘
       │
┌──────▼──────────┐
│ Wiki Generator  │  Create comprehensive articles
└──────┬──────────┘
       │
┌──────▼──────────┐
│  Site Builder   │  MkDocs static site generation
└──────┬──────────┘
       │
       ▼
  Beautiful Wiki
```

### Key Components

- **Content Parsers**: Handle PDF, web, and text sources
- **LLM Orchestrator**: Multi-provider support with automatic fallback
- **Entity Extractor**: Identifies and structures entities using AI
- **Wiki Generator**: Creates detailed, cross-linked articles
- **Site Builder**: Generates beautiful, searchable static sites
- **Storage Layer**: SQLite database for persistence

## ⚙️ Configuration

### Default Configuration

The system uses `config/default_config.yaml`. Key settings:

```yaml
llm:
  providers:
    - name: anthropic
      model: claude-3-5-sonnet-20241022
    - name: openai
      model: gpt-4-turbo-preview
  fallback_order:
    - anthropic
    - openai

extraction:
  chunk_size: 4000
  entity_types:
    - character
    - location
    - organization
    - concept
    - event
    - item

site:
  theme: material
  site_name: Generated Wiki
```

### Custom Configuration

Create your own YAML file to override defaults:

```yaml
# my-config.yaml
site:
  site_name: "My Fantasy World Wiki"
  site_description: "Complete guide to my story universe"

extraction:
  chunk_size: 6000
  min_confidence: 0.7
```

Use it with:
```bash
wiki-generator generate source.txt --config my-config.yaml
```

## 📊 Examples

### Sample Output

From the included `examples/sample_story.txt`, the generator creates:

```
📁 my-wiki/
├── 📄 index.html (home page with statistics)
├── 👤 characters/
│   ├── Queen Celestia.md
│   ├── Commander Theron Blackwood.md
│   ├── Elara Moonwhisper.md
│   └── ...
├── 🗺️ locations/
│   ├── Kingdom of Elendril.md
│   ├── Silverhaven.md
│   ├── Whispering Woods.md
│   └── ...
├── 🏛️ organizations/
│   ├── Shadow Council.md
│   ├── Royal Guard.md
│   └── ...
└── ⚡ items/
    ├── Starlight Amulet.md
    ├── Shadowbane.md
    └── ...
```

Each article includes:
- Comprehensive description
- Related entities (automatically linked)
- Type-specific sections
- Metadata and tags
- Cross-references

## 🧪 Testing

### Run Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_models.py
```

### Test Coverage

Current test coverage:
- ✅ Core data models
- ✅ Configuration loading
- ⏳ Integration tests (pending)
- ⏳ Parser tests (pending)

## 📚 Documentation

- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Comprehensive setup and usage guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and technical details
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Implementation status and features
- **[CHECKLIST.md](CHECKLIST.md)** - Development progress tracking

## 🔧 Development

### Project Structure

```
wiki-generator/
├── src/wiki_generator/     # Main package
│   ├── core/               # Models, config, pipeline
│   ├── llm/                # LLM providers and orchestration
│   ├── parsers/            # Content parsers
│   ├── extraction/         # Entity extraction
│   ├── generation/         # Wiki generation
│   ├── site/               # Static site building
│   └── storage/            # Database layer
├── config/                 # Configuration files
│   ├── default_config.yaml
│   └── prompts/            # Jinja2 templates
├── tests/                  # Unit tests
├── examples/               # Sample content
└── docs/                   # Documentation
```

### Contributing

Contributions are welcome! Areas for improvement:

1. **Image Pipeline** - Implement automatic image acquisition
2. **Integration Tests** - End-to-end testing
3. **Performance** - Optimization for large books
4. **Local LLMs** - Support for Ollama, llama.cpp
5. **UI Enhancements** - Custom themes, visualizations

## ⚠️ Known Limitations

1. **Images**: Automatic image acquisition not yet implemented (Phase 6)
   - Articles won't have images automatically
   - Can manually add images to markdown files

2. **Performance**: Optimized for books up to ~200 pages
   - Larger books work but may take longer
   - Consider chunking very large content

3. **LLM Dependency**: Requires API access to Claude or GPT
   - Local LLM support planned
   - API costs apply (typically $1-3 for a medium book)

## 📈 Performance

Typical processing times (with Claude Sonnet 4.5):

- **Short story** (10 pages): 2-5 minutes
- **Medium book** (100 pages): 15-30 minutes
- **Large book** (200 pages): 45-90 minutes

Cost estimates:
- **Small**: ~$0.10-0.30
- **Medium**: ~$1-3
- **Large**: ~$3-10

## 🗺️ Roadmap

### v0.2.0 (Planned)
- [ ] Image extraction from PDFs
- [ ] Web image search
- [ ] AI image generation (DALL-E)
- [ ] Integration tests
- [ ] Performance optimization

### v0.3.0 (Future)
- [ ] Local LLM support (Ollama)
- [ ] Multi-language wikis
- [ ] Custom entity types
- [ ] Relationship visualization
- [ ] Incremental updates

### v1.0.0 (Vision)
- [ ] Web UI
- [ ] Collaborative editing
- [ ] Export to Notion/Obsidian
- [ ] GitHub Pages auto-deploy
- [ ] Docker deployment

## 🙏 Acknowledgments

Built with excellent open-source tools:

- [Anthropic Claude](https://www.anthropic.com/) - AI entity extraction
- [OpenAI GPT-4](https://openai.com/) - Alternative LLM provider
- [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) - Beautiful documentation theme
- [Instructor](https://github.com/jxnl/instructor) - Structured LLM outputs
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- 📖 Read [GETTING_STARTED.md](GETTING_STARTED.md) for detailed setup instructions
- 🏗️ See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- 🐛 Report issues on GitHub
- 💬 Enable `--verbose` flag for debugging

---

**Made with ❤️ using AI and Python**

Transform your content into beautiful wikis today! 🚀
