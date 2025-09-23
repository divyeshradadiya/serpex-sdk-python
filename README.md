# serpex-sdk

Official Python SDK for the Serpex SERP API - Fetch search results in JSON format.

## Installation

```bash
pip install serpex-sdk
```

Or with poetry:

```bash
poetry add serpex-sdk
```

## Quick Start

```python
from serpex-sdk import SerpApiClient

# Initialize the client with your API key
client = SerpApiClient('your-api-key-here')

# Search using a dictionary (recommended for simple use cases)
results = client.search({
    'q': 'python tutorial',
    'engine': 'google',
    'language': 'en'
})

# Or using SearchParams object for type safety
from serpex-sdk import SearchParams

params = SearchParams(q='python tutorial', engine='google', language='en')
results = client.search(params)

print(results.results)

```

## API Reference

### SerpApiClient

#### Constructor

```python
SerpApiClient(api_key: str, base_url: str = "https://api.serpex.dev")
```

- `api_key`: Your API key from the Serpex dashboard
- `base_url`: Optional base URL (defaults to 'https://api.serpex.dev')

#### Methods

##### `search(params: SearchParams | Dict[str, Any]) -> SearchResponse`

Search using the SERP API with flexible parameters. Accepts either a SearchParams object or a dictionary. Engine parameter is required.

```python
# Using dictionary (simple approach)
results = client.search({
    'q': 'javascript frameworks',
    'engine': 'brave',
    'category': 'search',
    'country': 'US'
})

# Using SearchParams object (type-safe approach)
from serpex-sdk import SearchParams

params = SearchParams(
    q='javascript frameworks',
    engine='brave',
    category='search',
    country='US'
)
results = client.search(params)
```

## Search Parameters

The `SearchParams` dataclass supports all search parameters:

```python
@dataclass
class SearchParams:
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
```

## Response Format

```python
@dataclass
class SearchResponse:
    metadata: SearchMetadata
    id: str
    query: str
    engines: List[str]
    results: List[SearchResult]
    answers: List[Any]
    corrections: List[str]
    infoboxes: List[Any]
    suggestions: List[str]
```

## Error Handling

The SDK raises `SerpApiException` for API errors:

```python
from serpex-sdk import SerpApiClient, SerpApiException

try:
    results = client.search(SearchParams(q='test query'))
except SerpApiException as e:
    print(f"API error: {e}")
    print(f"Status code: {e.status_code}")
    print(f"Details: {e.details}")
```

## Requirements

- Python 3.8+
- requests

## License

MIT