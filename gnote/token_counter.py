"""Token counting for context management.

Currently only supports the 'chardiv4' approach (characters divided by 4).
This provides a reasonable approximation for most text, though actual token
counts may vary by ±20% depending on the tokenizer used by the LLM.

For production use with specific LLMs, consider implementing:
- tiktoken for OpenAI models (GPT-3.5/4)
- transformers tokenizers for other models
- Custom token counter based on your specific LLM

The chardiv4 approach is intentionally simple to avoid external dependencies
and works well enough for token pressure monitoring.
"""

from gnote.config import TokenApproach


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
