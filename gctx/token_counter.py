"""Token counting for context management."""

from gctx.config import TokenApproach


class TokenCounter:
    """Simple chardiv4 token counter."""

    def __init__(self, approach: TokenApproach) -> None:
        """Initialize token counter.

        Args:
            approach: Token counting approach (only CHARDIV4 supported)

        Raises:
            ValueError: If approach is not CHARDIV4
        """
        if approach != TokenApproach.CHARDIV4:
            raise ValueError(f"Only chardiv4 supported, got: {approach.value}")
        self.divisor = 4

    def count(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count (len(text) // 4)
        """
        return len(text) // self.divisor

    def calculate_pressure(self, count: int, limit: int) -> dict[str, int | float]:
        """Calculate token pressure metrics.

        Args:
            count: Current token count
            limit: Maximum token limit

        Returns:
            Dictionary with token_count, token_limit, and token_pressure_percentage
        """
        percentage = count / limit if limit > 0 else 0.0
        return {
            "token_count": count,
            "token_limit": limit,
            "token_pressure_percentage": round(percentage, 4),
        }
