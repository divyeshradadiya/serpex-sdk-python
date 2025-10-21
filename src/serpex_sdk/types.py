"""
Type definitions for the Serpex SERP API Python SDK.
"""

from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Represents a single search result."""
    title: str
    url: str
    snippet: str
    position: int
    engine: str
    published_date: Optional[str] = None
    img_src: Optional[str] = None
    duration: Optional[str] = None
    score: Optional[float] = None


@dataclass
class SearchMetadata:
    """Metadata for search results."""
    number_of_results: int
    response_time: int
    timestamp: str
    credits_used: int


@dataclass
class SearchResponse:
    """Complete search response."""
    metadata: SearchMetadata
    id: str
    query: str
    engines: List[str]
    results: List[SearchResult]
    answers: List[Any]
    corrections: List[str]
    infoboxes: List[Any]
    suggestions: List[str]


@dataclass
class SearchParams:
    """Parameters for search requests."""
    # Required: search query
    q: str

    # Optional: Engine selection (defaults to 'auto')
    engine: Optional[str] = 'auto'

    # Optional: Search category (currently only 'web' supported)
    category: Optional[str] = 'web'

    # Optional: Time range filter
    time_range: Optional[str] = 'all'

    # Optional: Response format
    format: Optional[str] = 'json'