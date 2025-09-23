"""
Main client for the Serpex SERP API Python SDK.
"""

import requests
from typing import Optional, Dict, Any, Union
from urllib.parse import urlencode

from .types import SearchResponse, SearchParams
from .exceptions import SerpApiException


class SerpApiClient:
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
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make an authenticated request to the API.

        Args:
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            SerpApiException: For API errors
        """
        url = f"{self.base_url}/api/search"

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

        try:
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
                    data.get("error", "Validation error"),
                    status_code=400,
                    details=data
                )
            except ValueError:
                raise SerpApiException("Bad request", status_code=400)
        elif not response.ok:
            try:
                data = response.json()
                raise SerpApiException(
                    data.get("error", f"API error: {response.reason}"),
                    status_code=response.status_code,
                    details=data
                )
            except ValueError:
                raise SerpApiException(
                    f"API error: {response.reason}",
                    status_code=response.status_code
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
        search_query = params.q or params.query
        if not search_query or not isinstance(search_query, str) or not search_query.strip():
            raise ValueError("Query parameter (q or query) is required and must be a non-empty string")

        if len(search_query) > 500:
            raise ValueError("Query too long (max 500 characters)")

        # Prepare request parameters
        request_params = {}

        # Convert SearchParams to dict, excluding None values
        for key, value in params.__dict__.items():
            if value is not None:
                request_params[key] = value

        # Ensure we have a query parameter
        request_params['q'] = search_query

        # Handle engine parameter - must be specified
        if not params.engine:
            raise ValueError('Engine parameter is required (google, bing, duckduckgo, or brave)')
        request_params['engine'] = params.engine

        data = self._make_request(request_params)

        # Convert response to SearchResponse object
        from .types import SearchResult, SearchMetadata

        metadata = SearchMetadata(**data["metadata"])
        results = [SearchResult(**result) for result in data["results"]]

        return SearchResponse(
            metadata=metadata,
            id=data["id"],
            query=data["query"],
            engines=data["engines"],
            results=results,
            answers=data["answers"],
            corrections=data["corrections"],
            infoboxes=data["infoboxes"],
            suggestions=data["suggestions"],
        )