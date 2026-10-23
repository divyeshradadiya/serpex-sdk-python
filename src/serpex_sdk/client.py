"""
Main client for the Serpex Python SDK.
"""

import warnings
from dataclasses import fields as dataclass_fields
from typing import Optional, Dict, Any, Union, Type, TypeVar
from urllib.parse import urlencode

import requests

from . import __version__

from .types import (
    SearchResponse,
    SearchParams,
    ExtractResponse,
    ExtractParams,
    ExtractResult,
    ExtractMetadata,
    UsageParams,
    UsageResponse,
    UsageStatistics,
    UsageCredits,
)
from .exceptions import (
    SerpApiException,
    AuthenticationError,
    InsufficientCreditsError,
    RateLimitError,
    ValidationError,
)

_P = TypeVar("_P")

#: Stealth mode ends at this instant; from then the API answers stealth=True with HTTP 410.
STEALTH_END_DATE = "2026-11-01T00:00:00Z"

# One warning per process for each of these, not one per call.
_warned_ignored_params = False
_warned_stealth = False

_STATUS_MESSAGES = {
    400: "Bad request",
    401: "Invalid or missing API key",
    402: "Insufficient credits",
    403: "Not included in your plan",
    404: "Not found",
    410: "No longer available",
    429: "Rate limit exceeded",
    500: "Internal server error",
    502: "Extraction service error",
    503: "Temporarily unavailable",
    504: "Timed out upstream",
}

_STATUS_EXCEPTIONS = {
    400: ValidationError,
    401: AuthenticationError,
    402: InsufficientCreditsError,
    429: RateLimitError,
}


def _error_message(body: Any, status: int) -> str:
    """The API's error text, never a dict repr; a status default when there is none."""
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, str) and error:
            # Framework 404s put the useful text in `message`; `error` is "Not Found".
            if status == 404 and isinstance(body.get("message"), str) and body["message"]:
                return body["message"]
            return error
        if isinstance(error, dict) and isinstance(error.get("message"), str) and error["message"]:
            return error["message"]
        if isinstance(body.get("message"), str) and body["message"]:
            return body["message"]
    return _STATUS_MESSAGES.get(status, f"Serpex API error (HTTP {status})")


def _retry_after_ms(response: requests.Response) -> Optional[int]:
    raw = response.headers.get("Retry-After") if response.headers is not None else None
    try:
        return int(float(raw) * 1000) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _coerce_params(params: Union[_P, Dict[str, Any]], cls: Type[_P], method: str) -> _P:
    """Build the params dataclass from a dict, dropping keys the API does not read.

    Older code passes options the API ignores (category, time_range, num, ...).
    Those used to raise TypeError; now they are dropped with one DeprecationWarning
    per process. engine/engines keep their own warning in SearchParams.
    """
    global _warned_ignored_params
    if not isinstance(params, dict):
        return params
    known = {f.name for f in dataclass_fields(cls)}  # type: ignore[arg-type]  # cls is a params dataclass
    ignored = sorted(k for k in params if k not in known and params[k] is not None)
    if ignored and not _warned_ignored_params:
        _warned_ignored_params = True
        warnings.warn(
            f"{method}() option(s) {', '.join(ignored)} are ignored by the Serpex API and "
            "are not sent. Remove them.",
            DeprecationWarning,
            stacklevel=3,
        )
    return cls(**{k: v for k, v in params.items() if k in known})

# Client-side timeouts (seconds). Each is longer than the server's own budget
# for that request, so the client never gives up on a request the server
# still finishes and bills: plain search 30 s upstream, search with
# include_content 45 s, extract 55 s, stealth extract 80 s plus up to 15 s
# queue. Cloudflare closes origin responses at ~100 s.
SEARCH_TIMEOUT = 60
SEARCH_CONTENT_TIMEOUT = 100
EXTRACT_TIMEOUT = 100
STEALTH_EXTRACT_TIMEOUT = 120


class SerpexClient:
    """
    Official Python client for Serpex — the web search API and extract API for AI agents.

    ``search()`` returns real-time web results as JSON; ``extract()`` turns
    URLs into LLM-ready markdown or HTML; ``usage()`` reports credits.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.serpex.dev",
        timeout: Optional[float] = None,
    ):
        """
        Initialize the Serpex API client.

        Args:
            api_key: Your API key from the Serpex dashboard
            base_url: Base URL for the API (optional, defaults to production)
            timeout: Request timeout in seconds for every call. When omitted,
                each call uses a default sized above the server's own budget:
                60 s search, 100 s search with include_content, 100 s extract,
                120 s stealth extract.

        Raises:
            ValueError: If api_key is not provided or is not a string
        """
        if not api_key or not isinstance(api_key, str):
            raise ValueError("API key is required and must be a string")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": f"serpex-python/{__version__}",
            }
        )

    def _make_request(
        self,
        params: Dict[str, Any],
        endpoint: str = "/api/search",
        method: str = "GET",
        timeout: float = SEARCH_TIMEOUT,
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to the API.

        Args:
            params: Query parameters for GET, or body data for POST
            endpoint: API endpoint
            method: HTTP method ("GET" or "POST")
            timeout: Per-call default; ``self.timeout`` overrides it when set

        Returns:
            JSON response data

        Raises:
            SerpApiException: For API errors
        """
        url = f"{self.base_url}{endpoint}"
        timeout = self.timeout if self.timeout is not None else timeout

        try:
            if method.upper() == "POST":
                # For POST requests, send params as JSON body
                response = self.session.post(url, json=params, timeout=timeout)
            else:
                # For GET requests, send params as query parameters
                # Filter out None values and prepare query parameters
                filtered_params = {}
                for key, value in params.items():
                    if value is not None:
                        if isinstance(value, list):
                            # Handle array parameters
                            filtered_params[key] = value
                        else:
                            filtered_params[key] = value

                # Build query string
                query_string = urlencode(filtered_params, doseq=True)
                final_url = f"{url}?{query_string}" if query_string else url
                response = self.session.get(final_url, timeout=timeout)

            return self._handle_response(response)
        except requests.Timeout as e:
            raise SerpApiException(
                f"Request timed out after {timeout} s",
                details={"error": "timeout", "timeout": timeout},
                retryable=True,
            ) from e
        except requests.RequestException as e:
            # DNS, connection reset, TLS: nothing reached the API, safe to retry.
            raise SerpApiException(
                f"Request failed: {str(e)}", details={"error": "network"}, retryable=True
            ) from e

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and raise appropriate exceptions for errors.

        Args:
            response: Requests response object

        Returns:
            JSON response data

        Raises:
            SerpApiException: For various API errors
        """
        if not response.ok:
            status = response.status_code
            try:
                data = response.json()
            except ValueError:
                # Not JSON (e.g. a CDN error page).
                data = {"error": response.reason or f"HTTP {status}"}
            if not isinstance(data, dict):
                data = {"error": str(data)}
            exc_class = _STATUS_EXCEPTIONS.get(status, SerpApiException)
            raise exc_class(
                _error_message(data, status),
                status_code=status,
                details=data,
                retry_after_ms=_retry_after_ms(response),
            )

        try:
            return response.json()
        except ValueError:
            raise SerpApiException("Invalid JSON response from API")

    def search(self, params: Union[SearchParams, Dict[str, Any]]) -> SearchResponse:
        """
        Run a real-time web search.

        Args:
            params: SearchParams object or dictionary with query and options.
                ``engine`` / ``engines`` are deprecated: still accepted, ignored,
                and not sent to the API.

        Returns:
            SearchResponse object with results

        Raises:
            ValueError: If query is not provided
            SerpApiException: For API errors
        """
        # Convert dict to SearchParams if needed; unknown keys are dropped.
        params = _coerce_params(params, SearchParams, "search")

        # Validate required parameters
        if not params.q or not isinstance(params.q, str) or not params.q.strip():
            raise ValueError(
                "Query parameter (q) is required and must be a non-empty string"
            )

        if len(params.q) > 500:
            raise ValueError("Query too long (max 500 characters)")

        if params.content_results not in (5, 10):
            raise ValueError("content_results must be exactly 5 or 10")

        endpoint = "/api/search"

        # Prepare request parameters
        request_params: Dict[str, Any] = {
            "q": params.q,
        }

        if params.include_content:
            request_params["include_content"] = params.include_content

        if params.content_results and params.content_results != 5:
            request_params["content_results"] = params.content_results

        data = self._make_request(
            request_params,
            endpoint=endpoint,
            timeout=SEARCH_CONTENT_TIMEOUT if params.include_content else SEARCH_TIMEOUT,
        )

        # Convert response to SearchResponse object
        from .types import SearchResult, SearchMetadata

        # Defensive hydration: these dataclasses use strict kwargs, so any
        # backend response field not yet declared here would raise
        # TypeError("unexpected keyword argument") and break every installed
        # SDK the moment the backend ships a new field. Filter incoming keys
        # down to the dataclass's declared fields first so unknown fields are
        # silently dropped instead of crashing the caller.
        metadata = SearchMetadata(
            **{k: v for k, v in data["metadata"].items() if k in SearchMetadata.__dataclass_fields__}
        )
        results = [
            SearchResult(**{k: v for k, v in result.items() if k in SearchResult.__dataclass_fields__})
            for result in data.get("results") or []
        ]

        return SearchResponse(
            metadata=metadata,
            id=data["id"],
            query=data["query"],
            # Deprecated response field: tolerate its removal server-side.
            engines=data.get("engines", ["auto"]),
            results=results,
            message=data.get("message"),
        )

    def extract(self, params: Union[ExtractParams, Dict[str, Any]]) -> ExtractResponse:
        """
        Extract content from 1 to 10 web pages as markdown (default) or HTML.

        Each URL succeeds or fails on its own (``results[i].success``); failed
        URLs carry ``error`` and ``error_type`` and are never charged.
        ``stealth=True`` is deprecated: stealth mode ends on 2026-11-01, after
        which the API answers it with HTTP 410.

        Args:
            params: ExtractParams object or dictionary with URLs to extract

        Returns:
            ExtractResponse object with extraction results

        Raises:
            ValueError: If URLs are not provided or invalid
            SerpApiException: For API errors
        """
        # Convert dict to ExtractParams if needed; unknown keys are dropped.
        params = _coerce_params(params, ExtractParams, "extract")

        # Validate required parameters
        if (
            not params.urls
            or not isinstance(params.urls, list)
            or len(params.urls) == 0
        ):
            raise ValueError("URLs list is required and must contain at least one URL")

        if len(params.urls) > 10:
            raise ValueError("Maximum 10 URLs allowed per request")

        # Validate URLs
        invalid_urls = []
        for url in params.urls:
            if not isinstance(url, str):
                invalid_urls.append(url)
                continue
            try:
                from urllib.parse import urlparse

                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    invalid_urls.append(url)
            except:
                invalid_urls.append(url)

        if invalid_urls:
            raise ValueError(f"Invalid URLs provided: {invalid_urls}")

        # Prepare request parameters
        request_params: Dict[str, Any] = {"urls": params.urls}

        if params.stealth:
            request_params["stealth"] = params.stealth
            global _warned_stealth
            if not _warned_stealth:
                _warned_stealth = True
                warnings.warn(
                    "Stealth mode ends on 2026-11-01. From that date extract(stealth=True) "
                    "is rejected with HTTP 410 (not charged). Send the request without stealth.",
                    DeprecationWarning,
                    stacklevel=2,
                )

        if params.format and params.format != "markdown":
            request_params["format"] = params.format

        data = self._make_request(
            request_params,
            endpoint="/api/crawl",
            method="POST",
            timeout=STEALTH_EXTRACT_TIMEOUT if params.stealth else EXTRACT_TIMEOUT,
        )

        # Convert response to ExtractResponse object.
        # Same defensive filtering as search() — see comment there — so an
        # unrecognized backend field can't crash hydration here either.
        metadata = ExtractMetadata(
            **{k: v for k, v in data["metadata"].items() if k in ExtractMetadata.__dataclass_fields__}
        )
        results = [
            ExtractResult(**{k: v for k, v in result.items() if k in ExtractResult.__dataclass_fields__})
            for result in data["results"]
        ]

        return ExtractResponse(
            success=data["success"],
            results=results,
            metadata=metadata,
        )

    def usage(self, params: Union[UsageParams, Dict[str, Any], None] = None) -> UsageResponse:
        """
        Fetch usage statistics and the credit balance for your whole organization
        (every API key in it, not only the key making the call).

        Useful for checking your remaining balance before a large batch, or for
        surfacing consumption in your own dashboard.

        Args:
            params: Optional UsageParams (or dict) with `days` of history to
                summarise, 1-90 (default: 30; larger values are capped at 90).

        Returns:
            UsageResponse with per-product request counts (``engineStats``) and
            the credit balance.

        Raises:
            ValueError: If `days` is not a positive integer.
            SerpApiException: If the API returns an error.
        """
        if params is None:
            days = None
        elif isinstance(params, dict):
            days = params.get("days")
        else:
            days = params.days

        request_params: Dict[str, Any] = {}
        if days is not None:
            if not isinstance(days, int) or isinstance(days, bool) or days < 1:
                raise ValueError("days must be a positive integer")
            request_params["days"] = days

        data = self._make_request(request_params, endpoint="/api/usage")

        # Same defensive filtering as search()/extract(): an unrecognized
        # backend field must never crash hydration.
        statistics = UsageStatistics(
            **{k: v for k, v in (data.get("statistics") or {}).items()
               if k in UsageStatistics.__dataclass_fields__}
        )
        credits = UsageCredits(
            **{k: v for k, v in (data.get("credits") or {}).items()
               if k in UsageCredits.__dataclass_fields__}
        )

        return UsageResponse(
            api_key=data.get("api_key", ""),
            organization_id=data.get("organization_id", ""),
            period_days=data.get("period_days", 0),
            statistics=statistics,
            credits=credits,
            recent_requests=data.get("recent_requests") or [],
            effective_days=data.get("effective_days"),
        )
