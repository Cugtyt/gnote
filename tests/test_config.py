"""Tests for config module."""

from gctx.config import GctxConfig, TokenApproach


def test_gctx_config_defaults() -> None:
    """Test default configuration values."""
    config = GctxConfig()

    assert config.token_approach == TokenApproach.CHARDIV4
    assert config.token_limit == 8000


def test_gctx_config_custom() -> None:
    """Test custom configuration values."""
    config = GctxConfig(token_approach=TokenApproach.CHARDIV4, token_limit=10000)

    assert config.token_approach == TokenApproach.CHARDIV4
    assert config.token_limit == 10000


def test_gctx_config_validation() -> None:
    """Test configuration validation."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        GctxConfig(token_limit=0)

    with pytest.raises(ValidationError):
        GctxConfig(token_limit=-100)
