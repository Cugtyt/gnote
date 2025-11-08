"""Configuration data model for gctx."""

from enum import Enum

from pydantic import BaseModel, Field


class TokenApproach(str, Enum):
    """Supported token counting approaches."""

    CHARDIV4 = "chardiv4"


class GctxConfig(BaseModel):
    """Configuration data model.

    Attributes:
        token_approach: Token counting method (currently only chardiv4)
        token_limit: Maximum token threshold
    """

    token_approach: TokenApproach = Field(default=TokenApproach.CHARDIV4)
    token_limit: int = Field(default=8000, gt=0)
