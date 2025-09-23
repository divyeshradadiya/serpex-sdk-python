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
    # Required: query (use either q or query)
    q: Optional[str] = None
    query: Optional[str] = None

    # Engine selection (only one engine allowed)
    engine: Optional[str] = None

    # Common parameters
    language: Optional[str] = None
    pageno: Optional[int] = None
    page: Optional[int] = None
    time_range: Optional[str] = None
    safesearch: Optional[int] = None

    # Google specific
    hl: Optional[str] = None  # language
    lr: Optional[str] = None  # language restrict
    cr: Optional[str] = None  # country restrict

    # Bing specific
    mkt: Optional[str] = None  # market

    # DuckDuckGo specific
    region: Optional[str] = None

    # Brave specific
    category: Optional[str] = None
    spellcheck: Optional[bool] = None
    ui_lang: Optional[str] = None
    country: Optional[str] = None

    # Legacy support
    maxResults: Optional[int] = None