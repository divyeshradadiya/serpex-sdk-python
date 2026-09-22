"""
Serpex Python SDK

Official Python SDK for Serpex — a real-time web search API with page content
extraction (extract).
"""

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

__version__ = "2.10.3"
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