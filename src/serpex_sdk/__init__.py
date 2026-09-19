"""
Serpex SERP API Python SDK

Official Python SDK for the Serpex SERP API - Fetch search results in JSON format.
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

__version__ = "2.10.1"
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