"""Tests for token_counter module."""

from gctx.config import TokenApproach
from gctx.token_counter import TokenCounter


def test_token_counter_chardiv4() -> None:
    """Test token counting with chardiv4 approach."""
    counter = TokenCounter(TokenApproach.CHARDIV4)

    assert counter.count("") == 0
    assert counter.count("test") == 1
    assert counter.count("hello world") == 2
    assert counter.count("a" * 100) == 25


def test_calculate_pressure() -> None:
    """Test token pressure calculation."""
    counter = TokenCounter(TokenApproach.CHARDIV4)

    result = counter.calculate_pressure(100, 1000)
    assert result["token_pressure_percentage"] == 0.1

    result = counter.calculate_pressure(500, 1000)
    assert result["token_pressure_percentage"] == 0.5

    result = counter.calculate_pressure(0, 1000)
    assert result["token_pressure_percentage"] == 0.0

    result = counter.calculate_pressure(1000, 1000)
    assert result["token_pressure_percentage"] == 1.0
