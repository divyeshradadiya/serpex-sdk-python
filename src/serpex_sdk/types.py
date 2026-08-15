"""
Type definitions for the Serpex SERP API Python SDK.
"""

from typing import List, Optional, Dict, Any, Union, Literal
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Represents a single search result."""

    title: str
    url: str
    snippet: str
    position: int
    engine: str
    img_src: Optional[str] = None
    duration: Optional[str] = None
    score: Optional[float] = None
    # Present only when include_content was requested. Best-effort per-URL
    # extraction: a successful fetch sets content, a failed one sets
    # content_error instead — mutually exclusive, both absent when content
    # wasn't requested for this result.
    content: Optional[str] = None
    content_error: Optional[str] = None


@dataclass
class SearchMetadata:
    """Metadata for search results."""

    number_of_results: int
    response_time: int
    timestamp: str
    credits_used: int
    from_cache: Optional[bool] = None  # Whether this result was served from cache
    status: Optional[str] = None  # Result status: 'success' if results found, 'no_results' if none
    # Present only when include_content was requested.
    content_requested: Optional[int] = None
    content_delivered: Optional[int] = None


@dataclass
class SearchResponse:
    """Complete search response."""

    metadata: SearchMetadata
    id: str
    query: str
    engines: List[str]
    results: List[SearchResult]


@dataclass
class ExtractResult:
    """Represents a single extraction result."""

    url: str
    success: bool
    markdown: Optional[str] = None
    html: Optional[str] = None
    stealth: Optional[bool] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    status_code: Optional[int] = None
    crawled_at: Optional[str] = None
    extraction_mode: Optional[str] = None


@dataclass
class ExtractMetadata:
    """Metadata for extraction results."""

    total_urls: int
    processed_urls: int
    successful_crawls: int
    failed_crawls: int
    credits_used: int
    response_time: int
    timestamp: str
    cached_free: Optional[int] = None


@dataclass
class ExtractResponse:
    """Complete extraction response."""

    success: bool
    results: List[ExtractResult]
    metadata: ExtractMetadata


@dataclass
class ExtractParams:
    """Parameters for extraction requests."""

    # Required: URLs to extract (max 10)
    urls: List[str]

    # Optional: Route through premium unblocker for difficult-to-crawl pages (default: False)
    stealth: bool = False

    # Optional: Output format — 'markdown' (default) or 'html'
    format: str = "markdown"


@dataclass
class SearchParams:
    """Parameters for search requests."""

    # Required: search query
    q: str

    # Optional: also fetch page content (markdown) for top results (default: False)
    include_content: bool = False

    # Optional: number of top results to fetch content for — must be exactly
    # 5 or 10 (default: 5). Only relevant when include_content is True.
    content_results: Literal[5, 10] = 5
