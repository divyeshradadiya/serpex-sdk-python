"""
Serpex Python SDK

Official Python SDK for Serpex — the web search API and extract API for AI agents.
"""

# Defined before the submodule imports: client.py reads it for the User-Agent.
__version__ = "2.12.0"

from .client import SerpexClient, STEALTH_END_DATE
from .exceptions import (
    SerpApiException,
    AuthenticationError,
    InsufficientCreditsError,
    RateLimitError,
    ValidationError,
)
from .types import (
    SearchParams,
    SearchResponse,
    SearchResult,
    SearchMetadata,
    SearchStatus,
    ExtractParams,
    ExtractResponse,
    ExtractResult,
    ExtractMetadata,
    UsageParams,
    UsageResponse,
    UsageStatistics,
    UsageCredits,
    RecentRequest,
    ErrorBody,
    EXTRACT_ERROR_TYPES,
)

__all__ = [
    "SerpexClient",
    "SerpApiException",
    "AuthenticationError",
    "InsufficientCreditsError",
    "RateLimitError",
    "ValidationError",
    "SearchParams",
    "SearchResponse",
    "SearchResult",
    "SearchMetadata",
    "SearchStatus",
    "ExtractParams",
    "ExtractResponse",
    "ExtractResult",
    "ExtractMetadata",
    "UsageParams",
    "UsageResponse",
    "UsageStatistics",
    "UsageCredits",
    "RecentRequest",
    "ErrorBody",
    "EXTRACT_ERROR_TYPES",
    "STEALTH_END_DATE",
]
