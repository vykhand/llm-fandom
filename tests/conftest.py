"""Pytest configuration and fixtures."""

import pytest

from wiki_generator.core.config import Config


@pytest.fixture
def test_config():
    """Create a test configuration."""
    return Config(
        database_url="sqlite:///:memory:",
        output_dir="./test_output",
        prompts_dir="./config/prompts",
    )


@pytest.fixture
def sample_text():
    """Sample text for testing parsers."""
    return """
    # The Adventure of Sherlock Holmes

    Sherlock Holmes is a brilliant detective who lives at 221B Baker Street in London.
    He works with his friend Dr. Watson to solve complex criminal cases.

    Holmes is known for his exceptional deductive reasoning and keen observation skills.
    """
