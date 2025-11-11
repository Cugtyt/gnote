"""Configuration data model for gctx."""

from enum import Enum

from pydantic import BaseModel, Field


class TokenApproach(str, Enum):
    """Supported token counting approaches."""

    CHARDIV4 = "chardiv4"


class VectorConfig(BaseModel):
    """Vector search configuration.

    Attributes:
        model_name: Sentence transformer model for embeddings
        similarity_threshold: Minimum similarity score (0-1) for search results
        top_k: Number of results to return
        sync_interval_seconds: Daemon sync interval in seconds
    """

    model_name: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    similarity_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    top_k: int = Field(default=10, gt=0)
    sync_interval_seconds: int = Field(default=30, gt=0)


class GctxConfig(BaseModel):
    """Configuration data model.

    Attributes:
        token_approach: Token counting method (currently only chardiv4)
        token_limit: Maximum token threshold
        vector: Vector search configuration
    """

    token_approach: TokenApproach = Field(default=TokenApproach.CHARDIV4)
    token_limit: int = Field(default=8000, gt=0)
    vector: VectorConfig = Field(default_factory=VectorConfig)
