"""
Type definitions for the Serpex Python SDK.
"""

import warnings
from typing import List, Optional, Dict, Any, Union, Literal, TypedDict
from dataclasses import dataclass, field

#: Outcome of a search that returned HTTP 200. A search that could not be
#: completed returns HTTP 503 instead and raises SerpApiException.
SearchStatus = Literal["success", "no_results"]

#: Canonical per-URL extraction failure categories (other strings may appear later).
EXTRACT_ERROR_TYPES = (
    "timeout", "connection", "dns_unresolved", "ssl_error", "http", "blocked",
    "robots_disallowed", "server_error", "unsupported_content_type", "too_large", "unknown",
)


@dataclass
class SearchResult:
    """One search result.

    ``content`` and ``content_error`` are mutually exclusive and exist only on
    requests with ``include_content=True``, and only on the first
    ``content_results`` results: a successful page fetch sets ``content``
    (markdown), a failed one sets ``content_error`` (for example
    ``"robots_disallowed"``, ``"timeout"``, ``"blocked"``). Every other result has
    both set to None.
    """

    title: str
    url: str
    snippet: str
    position: int
    #: Deprecated: always "auto" (every search is routed automatically) and may
    #: be removed from responses later. Optional so its absence can't crash parsing.
    engine: Optional[str] = None
    img_src: Optional[str] = None
    duration: Optional[str] = None
    score: Optional[float] = None
    #: Page content as markdown (include_content only, successful fetch).
    content: Optional[str] = None
    #: Why page content is missing (include_content only, failed fetch).
    content_error: Optional[str] = None

    @property
    def has_content(self) -> bool:
        """True when this result carries page content."""
        return self.content is not None


@dataclass
class SearchMetadata:
    """Metadata for search results."""

    number_of_results: int
    response_time: int
    timestamp: str
    #: Credits charged for this request: 0, 1, 3 or 6. 0 for your organization's own
    #: repeat within 5 minutes and for an empty result that could not be confirmed.
    credits_used: int
    #: Served from the content cache (informational, not a billing flag).
    from_cache: Optional[bool] = None
    #: "success" or "no_results".
    status: Optional[SearchStatus] = None
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
    #: Failure only: human-readable reason, e.g. "HTTP 404: Not Found".
    error: Optional[str] = None
    #: Failure only, stealth extractions only: a stable code.
    #:   stealth_target_unreachable - domain did not resolve / refused us
    #:   stealth_target_status      - page answered with an error status
    #:   stealth_target_empty       - 200 with no usable content
    #:   stealth_timeout            - page did not finish rendering in time
    #:   stealth_network, stealth_unconfigured
    #: Failures on our side carry error_type "server_error" and no code
    #: ("stealth_provider_unavailable" is never returned).
    error_code: Optional[str] = None
    #: Failure only, always set: one of EXTRACT_ERROR_TYPES. Branch on this.
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

    # Deprecated: stealth mode ends on 2026-11-01. From that date the API rejects
    # stealth=True with HTTP 410 (not charged). Until then: full-browser render,
    # 5 credits per URL.
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

    # Deprecated: ignored by the API since 2026-06 (every search is routed
    # automatically). Still accepted so existing code keeps working; not sent.
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
    #: The 10 most recent requests, newest first (plain dicts, see RecentRequest).
    recent_requests: List["RecentRequest"] = field(default_factory=list)
    #: Days the counts actually cover: history is kept for 30 days, so this is the
    #: smaller of period_days and the retention window.
    effective_days: Optional[int] = None


class RecentRequest(TypedDict, total=False):
    """One entry of ``UsageResponse.recent_requests`` (a plain dict at runtime)."""

    id: int
    organizationId: Optional[str]
    #: "search", "crawl" or "stealth".
    searchEngine: str
    #: "auto" for searches, "crawl"/"stealth" for extract; None on older records.
    requestedEngine: Optional[str]
    resultsCount: Optional[int]
    #: "success", "no_results" or "error".
    status: str
    responseTime: Optional[int]
    fromCache: bool
    contentRequested: bool
    contentPagesRequested: Optional[int]
    contentPagesDelivered: Optional[int]
    createdAt: Optional[str]


class ErrorBody(TypedDict, total=False):
    """An API error body (``SerpApiException.details``). Fields depend on the status."""

    #: A string on every Serpex error; ``{"message", "status"}`` from the framework
    #: error handler (e.g. malformed JSON).
    error: Union[str, Dict[str, Any]]
    message: str
    status: str
    retryable: bool
    request_id: str
    remainingCredits: int
    limit: int
    retryAfterMs: int
    invalid_urls: List[str]
    example: str
