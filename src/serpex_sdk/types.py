"""
Type definitions for the Serpex SERP API Python SDK.
"""

from typing import List, Optional, Dict, Any, Union, Literal
from dataclasses import dataclass, field


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
    #: Human-readable failure reason, e.g. "target returned HTTP 404".
    error: Optional[str] = None
    #: Stable machine-readable failure code (stealth extractions only).
    #: Separates a problem with YOUR url from a problem on OUR side:
    #:   stealth_target_unreachable   - domain did not resolve / refused us
    #:   stealth_target_status        - page answered with an error status
    #:   stealth_target_empty         - 200 with no usable body (anti-bot page)
    #:   stealth_timeout              - page did not finish rendering in time
    #:   stealth_provider_unavailable - our unblocker was unavailable: retry
    #:   stealth_network              - network error reaching our unblocker
    #:   stealth_unconfigured         - stealth not enabled on this deployment
    error_code: Optional[str] = None
    #: Failure category, shared by normal and stealth extraction.
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


@dataclass
class UsageParams:
    """Parameters for usage requests."""

    # Optional: how many days of history to summarise (default: 30)
    days: int = 30


@dataclass
class UsageStatistics:
    """Request counts over the requested period."""

    totalRequests: int = 0
    successfulRequests: int = 0
    failedRequests: int = 0
    #: Requests per search engine over the period.
    engineStats: Dict[str, int] = field(default_factory=dict)


@dataclass
class UsageCredits:
    """Workspace credit position."""

    #: Credits remaining on the workspace.
    balance: int = 0
    #: Credits consumed to date.
    totalUsed: Optional[int] = None


@dataclass
class UsageResponse:
    """Usage statistics and credit balance for an API key."""

    #: Name of the API key the request was made with.
    api_key: str
    organization_id: str
    period_days: int
    statistics: UsageStatistics
    credits: UsageCredits
    #: The 10 most recent requests, newest first. Shape is intentionally loose —
    #: these are diagnostic records and may gain fields without a major version.
    recent_requests: List[Dict[str, Any]] = field(default_factory=list)
