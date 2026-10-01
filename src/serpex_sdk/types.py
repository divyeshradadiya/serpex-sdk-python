"""
Type definitions for the Serpex Python SDK.
"""

import warnings
from typing import List, Optional, Dict, Any, Union, Literal
from dataclasses import dataclass, field


@dataclass
class SearchResult:
    """Represents a single search result."""

    title: str
    url: str
    snippet: str
    position: int
    #: Deprecated: always "auto" today and may be removed from responses in a
    #: later API version. Optional so a response without it can't crash parsing.
    engine: Optional[str] = None
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
    # Present only when status == "no_results".
    no_results_verified: Optional[bool] = None
    charged: Optional[bool] = None
    message: Optional[str] = None


@dataclass
class SearchResponse:
    """Complete search response."""

    metadata: SearchMetadata
    id: str
    query: str
    #: Deprecated: always ["auto"] today and may be removed from responses in a
    #: later API version. Defaults to ["auto"] when absent.
    engines: List[str] = field(default_factory=lambda: ["auto"])
    results: List[SearchResult] = field(default_factory=list)
    #: Present only when no results were found.
    message: Optional[str] = None


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
    #:   stealth_target_empty         - 200 with no usable content
    #:   stealth_timeout              - page did not finish rendering in time
    #:   stealth_provider_unavailable - our stealth extraction service was unavailable: retry
    #:   stealth_network              - network error inside our stealth extraction service
    #:   stealth_unconfigured         - stealth not enabled on this deployment
    error_code: Optional[str] = None
    #: Failure category, shared by normal and stealth extraction.
    error_type: Optional[str] = None
    status_code: Optional[int] = None
    #: Deprecated: never returned by the API; always None. Removed in 3.0.
    crawled_at: Optional[str] = None
    #: Deprecated: never returned by the API; always None. Removed in 3.0.
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
    #: URLs served free as a same-workspace repeat (present only when > 0).
    cached_free: Optional[int] = None
    #: True when the request used stealth extraction.
    stealth: Optional[bool] = None


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

    # Optional: premium extraction mode for pages that standard extraction can't read (default: False)
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

    # Deprecated: ignored by the API since 2026-06 (Serpex is a single search
    # engine). Still accepted so existing code keeps working; not sent.
    engine: Optional[str] = None
    engines: Optional[Any] = None

    def __post_init__(self) -> None:
        if self.engine is not None or self.engines is not None:
            warnings.warn(
                "SearchParams 'engine'/'engines' are deprecated and ignored by the "
                "Serpex API; remove them from your call.",
                DeprecationWarning,
                stacklevel=3,
            )


@dataclass
class UsageParams:
    """Parameters for usage requests."""

    # Optional: how many days of history to summarise, 1-90 (default: 30)
    days: int = 30


@dataclass
class UsageStatistics:
    """Request counts over the requested period."""

    totalRequests: int = 0
    successfulRequests: int = 0
    failedRequests: int = 0
    #: Zero-result searches (also counted in successfulRequests). 0 when absent.
    noResultsRequests: int = 0
    #: Requests per product over the period: search, crawl, stealth (only those used).
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
    """Usage statistics and credit balance for the organization that owns the API key."""

    #: NAME of the API key the request was made with (not the key itself).
    #: Statistics and credits cover the whole organization, not only this key.
    api_key: str
    organization_id: str
    period_days: int
    statistics: UsageStatistics
    credits: UsageCredits
    #: The 10 most recent requests, newest first. Shape is intentionally loose —
    #: these are diagnostic records and may gain fields without a major version.
    recent_requests: List[Dict[str, Any]] = field(default_factory=list)
