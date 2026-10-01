"""
Serpex Python SDK

Official Python SDK for Serpex — the web search API and extract API for AI agents.
"""

# Defined before the submodule imports: client.py reads it for the User-Agent.
__version__ = "2.11.0"

from .client import SerpexClient
from .exceptions import SerpApiException
from .types import (
    SearchParams,
    SearchResponse,
    ExtractParams,
    ExtractResponse,
    UsageParams,
    UsageResponse,
)

__all__ = [
    "SerpexClient",
    "SerpApiException",
    "SearchParams",
    "SearchResponse",
    "ExtractParams",
    "ExtractResponse",
    "UsageParams",
    "UsageResponse",
]