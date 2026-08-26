"""
Main client for the Serpex SERP API Python SDK.
"""

import requests
from typing import Optional, Dict, Any, Union
from urllib.parse import urlencode

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
from .exceptions import SerpApiException


class SerpexClient:
    """
    Official Python client for the Serpex SERP API.

    Provides methods to interact with the Serpex SERP API for fetching
    search results in JSON format from Google, Bing, DuckDuckGo, and Brave.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.serpex.dev"):
        """
        Initialize the SERP API client.

        Args:
            api_key: Your API key from the Serpex dashboard
            base_url: Base URL for the API (optional, defaults to production)

        Raises:
            ValueError: If api_key is not provided or is not a string
        """
        if not api_key or not isinstance(api_key, str):
            raise ValueError("API key is required and must be a string")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

    def _make_request(
        self, params: Dict[str, Any], endpoint: str = "/api/search", method: str = "GET"
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to the API.

        Args:
            params: Query parameters for GET, or body data for POST
            endpoint: API endpoint
            method: HTTP method ("GET" or "POST")

        Returns:
            JSON response data

        Raises:
            SerpApiException: For API errors
        """
        url = f"{self.base_url}{endpoint}"

        try:
            if method.upper() == "POST":
                # For POST requests, send params as JSON body
                response = self.session.post(url, json=params, timeout=30)
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
                response = self.session.get(final_url, timeout=30)

            return self._handle_response(response)
        except requests.RequestException as e:
            raise SerpApiException(f"Request failed: {str(e)}")

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
        if response.status_code == 401:
            raise SerpApiException("Invalid API key", status_code=401)
        elif response.status_code == 402:
            raise SerpApiException("Insufficient credits", status_code=402)
        elif response.status_code == 429:
            raise SerpApiException("Rate limit exceeded", status_code=429)
        elif response.status_code == 400:
            try:
                data = response.json()
                raise SerpApiException(
                    data.get("error", "Validation error"), status_code=400, details=data
                )
            except ValueError:
                raise SerpApiException("Bad request", status_code=400)
        elif not response.ok:
            try:
                data = response.json()
                raise SerpApiException(
                    data.get("error", f"API error: {response.reason}"),
                    status_code=response.status_code,
                    details=data,
                )
            except ValueError:
                raise SerpApiException(
                    f"API error: {response.reason}", status_code=response.status_code
                )

        try:
            return response.json()
        except ValueError:
            raise SerpApiException("Invalid JSON response from API")

    def search(self, params: Union[SearchParams, Dict[str, Any]]) -> SearchResponse:
        """
        Search using the SERP API.

        Args:
            params: SearchParams object or dictionary with query and options

        Returns:
            SearchResponse object with results

        Raises:
            ValueError: If query is not provided
            SerpApiException: For API errors
        """
        # Convert dict to SearchParams if needed
        if isinstance(params, dict):
            params = SearchParams(**params)

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

        data = self._make_request(request_params, endpoint=endpoint)

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
            for result in data["results"]
        ]

        return SearchResponse(
            metadata=metadata,
            id=data["id"],
            query=data["query"],
            engines=data["engines"],
            results=results,
        )

    def extract(self, params: Union[ExtractParams, Dict[str, Any]]) -> ExtractResponse:
        """
        Extract content from web pages.

        Args:
            params: ExtractParams object or dictionary with URLs to extract

        Returns:
            ExtractResponse object with extraction results

        Raises:
            ValueError: If URLs are not provided or invalid
            SerpApiException: For API errors
        """
        # Convert dict to ExtractParams if needed
        if isinstance(params, dict):
            params = ExtractParams(**params)

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

        if params.format and params.format != "markdown":
            request_params["format"] = params.format

        data = self._make_request(request_params, endpoint="/api/crawl", method="POST")

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
        Fetch usage statistics and the current credit balance for this API key.

        Useful for checking your remaining balance before a large batch, or for
        surfacing consumption in your own dashboard.

        Args:
            params: Optional UsageParams (or dict) with `days` of history to
                summarise (default: 30).

        Returns:
            UsageResponse with per-engine request counts and the credit balance.

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
        )
