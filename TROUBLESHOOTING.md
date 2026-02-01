# Troubleshooting Guide

Common issues and solutions for the Wiki Generator.

## Installation Issues

### uv Not Found

**Error**: `command not found: uv`

**Solution**:
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH (usually automatic, but if needed add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.cargo/bin:$PATH"

# Verify installation
uv --version
```

### Python Version Error

**Error**: `The currently activated Python version X.X is not supported`

**Solution**:
```bash
# Check Python version (need 3.10+)
python --version

# Use pyenv to install correct version
pyenv install 3.10
pyenv local 3.10

# Retry installation
uv sync --extra dev
```

### Dependency Installation Fails

**Error**: Various dependency installation errors

**Solution**:
```bash
# Clear uv cache
uv cache clean

# Remove lock file
rm uv.lock

# Reinstall
uv sync --extra dev
```

## API Key Issues

### No API Key Found

**Error**: `No API key found for provider anthropic`

**Solution**:
```bash
# Ensure .env file exists
ls -la .env

# If not, copy from example
cp .env.example .env

# Edit with your actual key
# ANTHROPIC_API_KEY=sk-ant-your-actual-key-here

# Verify configuration
uv run wiki-generator check-config
```

### Invalid API Key

**Error**: `Authentication failed` or `Invalid API key`

**Solution**:
1. Check key format:
   - Anthropic keys start with `sk-ant-`
   - OpenAI keys start with `sk-`
2. Verify key is active in provider dashboard
3. Check for extra spaces or quotes in .env file
4. Keys should be bare, not in quotes:
   ```bash
   # Correct
   ANTHROPIC_API_KEY=sk-ant-abc123

   # Wrong
   ANTHROPIC_API_KEY="sk-ant-abc123"
   ```

### Rate Limiting

**Error**: `Rate limit exceeded`

**Solution**:
- System will automatically retry with backoff
- Wait a few minutes and try again
- Consider reducing chunk size in config:
  ```yaml
  extraction:
    chunk_size: 3000  # Smaller chunks
  ```
- Check your usage tier in provider dashboard

## Generation Issues

### No Entities Extracted

**Problem**: Wiki generates but has no entities

**Solutions**:
1. Check content has sufficient detail:
   ```bash
   # Try with sample story first
   uv run wiki-generator generate examples/sample_story.txt --verbose
   ```

2. Enable verbose logging to see LLM responses:
   ```bash
   wiki-generator generate source.txt --verbose
   ```

3. Check LLM provider is working:
   ```bash
   wiki-generator check-config
   ```

4. Lower confidence threshold in config:
   ```yaml
   extraction:
     min_confidence: 0.5  # Lower from 0.6
   ```

### Poor Quality Extraction

**Problem**: Entities are incomplete or incorrect

**Solutions**:
1. Increase chunk size for more context:
   ```yaml
   extraction:
     chunk_size: 6000
     overlap: 300
   ```

2. Try different LLM provider:
   ```yaml
   llm:
     fallback_order:
       - openai  # Try GPT-4 instead
       - anthropic
   ```

3. Adjust prompts in `config/prompts/entity_extraction.jinja2`

### Generation Hangs or Freezes

**Problem**: Process appears stuck

**Solutions**:
1. Enable verbose mode to see progress:
   ```bash
   wiki-generator generate source.txt --verbose
   ```

2. Check network connection (LLM API calls)

3. Reduce concurrent requests in code:
   ```python
   # In generation/wiki_generator.py
   semaphore = asyncio.Semaphore(3)  # Reduce from 5
   ```

4. Check API status:
   - Anthropic: https://status.anthropic.com/
   - OpenAI: https://status.openai.com/

### Memory Issues

**Error**: `MemoryError` or system freezes

**Solutions**:
1. Process in smaller chunks:
   ```yaml
   extraction:
     chunk_size: 3000
   ```

2. For very large PDFs, extract text first:
   ```bash
   # Extract to text file
   pdftotext large_book.pdf book.txt

   # Then process
   wiki-generator generate book.txt
   ```

3. Increase system swap/memory

## File Processing Issues

### PDF Parsing Fails

**Error**: `Error parsing PDF` or empty text extracted

**Solutions**:
1. Check PDF is text-based (not scanned images):
   ```bash
   # Try opening PDF in a viewer
   # If text is selectable, it should work
   ```

2. For scanned PDFs, use OCR first:
   ```bash
   # Install tesseract
   brew install tesseract  # macOS

   # Use ocrmypdf
   pip install ocrmypdf
   ocrmypdf input.pdf output.pdf
   ```

3. Try converting to text manually:
   ```bash
   pdftotext book.pdf book.txt
   wiki-generator generate book.txt
   ```

### Website Scraping Fails

**Error**: Failed to fetch or parse website

**Solutions**:
1. Check URL is accessible:
   ```bash
   curl -I https://example.com
   ```

2. Some sites block scrapers - try downloading HTML:
   ```bash
   curl https://example.com > page.html
   # Extract text manually and save as .txt
   ```

3. Use Wayback Machine for blocked sites:
   - Go to web.archive.org
   - Find archived version
   - Use that URL

### Empty or Corrupt Output

**Problem**: Generated files are empty or malformed

**Solutions**:
1. Check disk space:
   ```bash
   df -h
   ```

2. Verify write permissions:
   ```bash
   ls -la ./output/
   chmod -R u+w ./output/
   ```

3. Check for filesystem errors in logs

4. Try different output directory:
   ```bash
   wiki-generator generate source.txt --output ~/Desktop/test-wiki
   ```

## Site Building Issues

### MkDocs Not Found

**Error**: `mkdocs command not found`

**Solutions**:
```bash
# Verify installation
uv pip list mkdocs

# If missing, reinstall dependencies
uv sync --extra dev

# Verify mkdocs is available
uv run mkdocs --version
```

### Site Build Fails

**Error**: `Failed to build site` or MkDocs errors

**Solutions**:
1. Check mkdocs.yml syntax:
   ```bash
   cd output_directory
   uv run mkdocs build --verbose
   ```

2. Check for invalid characters in article titles

3. Ensure all markdown files are valid:
   ```bash
   # Check for syntax errors
   find docs/ -name "*.md" -exec head -1 {} \;
   ```

4. Manually build to see detailed errors:
   ```bash
   cd output_directory
   mkdocs build --verbose --strict
   ```

### Serve Command Fails

**Error**: `Failed to serve site` or port already in use

**Solutions**:
1. Check if port 8000 is in use:
   ```bash
   lsof -i :8000
   # Kill process if needed
   kill -9 PID
   ```

2. Use different port:
   ```bash
   cd output_directory
   mkdocs serve --dev-addr=localhost:8001
   ```

3. Check firewall settings

## Database Issues

### Database Lock

**Error**: `database is locked`

**Solutions**:
1. Close any other processes using the database

2. Delete lock file:
   ```bash
   rm output/data/wiki.db-journal
   ```

3. Use new database:
   ```bash
   rm output/data/wiki.db
   # Regenerate wiki
   ```

### Database Corruption

**Error**: `database disk image is malformed`

**Solutions**:
1. Try to recover:
   ```bash
   sqlite3 output/data/wiki.db
   .recover
   .quit
   ```

2. Start fresh:
   ```bash
   rm output/data/wiki.db
   # Regenerate
   ```

## Performance Issues

### Very Slow Processing

**Problem**: Generation takes too long

**Solutions**:
1. Check chunk size (larger = fewer API calls):
   ```yaml
   extraction:
     chunk_size: 6000  # Increase from 4000
   ```

2. Use faster model:
   ```yaml
   llm:
     providers:
       - name: openai
         model: gpt-4-turbo  # Faster than Claude
   ```

3. Reduce entity types:
   ```yaml
   extraction:
     entity_types:
       - character
       - location
       # Remove less important types
   ```

4. Process in sections for large books

### High API Costs

**Problem**: Unexpected high costs

**Solutions**:
1. Monitor usage:
   - Anthropic: https://console.anthropic.com/
   - OpenAI: https://platform.openai.com/usage

2. Set API usage limits in provider dashboard

3. Test with small samples first:
   ```bash
   # Extract first 20 pages
   head -n 1000 book.txt > sample.txt
   wiki-generator generate sample.txt
   ```

4. Use cheaper models for testing:
   ```yaml
   llm:
     providers:
       - name: openai
         model: gpt-3.5-turbo  # Much cheaper
   ```

## Debugging Tips

### Enable Verbose Logging

Always use `--verbose` when troubleshooting:
```bash
wiki-generator generate source.txt --verbose
```

### Check Log Output

Look for specific error messages:
```bash
wiki-generator generate source.txt --verbose 2>&1 | tee debug.log
```

### Test Individual Components

Test components separately:

```python
# Test parser
from wiki_generator.parsers.text_parser import TextParser
import asyncio

async def test():
    parser = TextParser()
    result = await parser.parse("sample.txt")
    print(f"Extracted {len(result.text)} characters")

asyncio.run(test())
```

### Verify Configuration

```bash
# Check all settings
wiki-generator check-config

# Verify API keys are loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('ANTHROPIC_API_KEY')[:10])"
```

### Check Dependencies

```bash
# List all installed packages
uv pip list

# Check specific package
uv pip list anthropic

# Update dependencies
uv sync --upgrade
```

## Getting Help

If issues persist:

1. **Check documentation**:
   - README.md
   - GETTING_STARTED.md
   - ARCHITECTURE.md

2. **Enable verbose logging**:
   ```bash
   wiki-generator generate source.txt --verbose > debug.log 2>&1
   ```

3. **Gather information**:
   - Python version: `python --version`
   - uv version: `uv --version`
   - OS version
   - Error messages
   - Steps to reproduce

4. **Test with sample**:
   ```bash
   wiki-generator generate examples/sample_story.txt --verbose
   ```

5. **Report issue** with:
   - Error message
   - Debug log
   - System information
   - Steps to reproduce

## Common Error Messages

### `ModuleNotFoundError: No module named 'wiki_generator'`

**Solution**: Install package in development mode:
```bash
uv sync --extra dev
# Always use: uv run wiki-generator
```

### `ValidationError: X validation error(s) for Entity`

**Solution**: Check data model compatibility. This usually means the LLM returned invalid data. Enable verbose mode to see the response.

### `RuntimeError: All LLM providers failed`

**Solutions**:
1. Check API keys
2. Verify network connection
3. Check provider status pages
4. Try with single provider:
   ```yaml
   llm:
     fallback_order:
       - anthropic  # Only one
   ```

### `FileNotFoundError: Config file not found`

**Solution**: Run from project root or specify config:
```bash
cd wiki-generator
wiki-generator generate source.txt --config ./config/default_config.yaml
```

## Prevention Tips

1. **Always test with sample first**:
   ```bash
   wiki-generator generate examples/sample_story.txt --verbose
   ```

2. **Start small**: Test with 10-20 pages before processing whole books

3. **Monitor costs**: Check API usage regularly

4. **Keep backups**: Save generated wikis before regenerating

5. **Use version control**: Track configuration changes

6. **Update regularly**:
   ```bash
   git pull
   uv sync --upgrade
   ```

## Still Having Issues?

Create a minimal reproducible example:

```bash
# Create test file
echo "Once upon a time, in the kingdom of Eldoria, lived a brave knight named Sir Roland." > test.txt

# Try generating
wiki-generator generate test.txt --verbose

# If this works, the issue is with your source file
# If this fails, the issue is with the installation/configuration
```
