# serpex

Official Python SDK for the Serpex SERP API - Fetch search results in JSON format.

## Installation

```bash
pip install serpex
```

Or with poetry:

```bash
poetry add serpex
```

## Quick Start

```python
from serpex import SerpexClient

# Initialize the client with your API key
client = SerpexClient('your-api-key-here')

# Search with auto-routing (recommended for simple use cases)
results = client.search({
    'q': 'python tutorial',
    'engine': 'auto'
})

# Or using SearchParams object for type safety
from serpex import SearchParams

params = SearchParams(q='python tutorial', engine='auto')
results = client.search(params)

print(results.results[0].title)
```

## API Reference

### SerpexClient

#### Constructor

```python
SerpexClient(api_key: str, base_url: str = "https://api.serpex.dev")
```

- `api_key`: Your API key from the Serpex dashboard
- `base_url`: Optional base URL (defaults to 'https://api.serpex.dev')

#### Methods

##### `search(params: SearchParams | Dict[str, Any]) -> SearchResponse`

Search using the SERP API with flexible parameters. Accepts either a SearchParams object or a dictionary.

```python
# Using dictionary (simple approach)
results = client.search({
    'q': 'javascript frameworks',
    'engine': 'google',
    'category': 'web',
    'time_range': 'week'
})

# Using SearchParams object (type-safe approach)
from serpex import SearchParams

params = SearchParams(
    q='javascript frameworks',
    engine='google',
    category='web',
    time_range='week'
)
results = client.search(params)
```

## Search Parameters

The `SearchParams` dataclass supports all search parameters:

```python
@dataclass
class SearchParams:
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
```

## Supported Engines

- **auto**: Automatically routes to the best available search engine
- **google**: Google's primary search engine
- **bing**: Microsoft's search engine
- **duckduckgo**: Privacy-focused search engine
- **brave**: Privacy-first search engine
- **yahoo**: Yahoo search engine
- **yandex**: Russian search engine

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
from serpex import SerpexClient, SerpApiException

try:
    results = client.search(SearchParams(q='test query'))
except SerpApiException as e:
    print(f"API error: {e}")
    print(f"Status code: {e.status_code}")
    print(f"Details: {e.details}")
```

## Examples

### Basic Search
```python
results = client.search({
    'q': 'coffee shops near me'
})
```

### Advanced Search with Filters
```python
results = client.search({
    'q': 'latest AI news',
    'engine': 'google',
    'time_range': 'day',
    'category': 'web'
})
```

### Using SearchParams Object
```python
from serpex import SearchParams

params = SearchParams(
    q='machine learning',
    engine='auto',
    time_range='month'
)
results = client.search(params)
```

### Using Different Engines
```python
# Auto-routing (recommended)
auto_results = client.search({
    'q': 'python programming',
    'engine': 'auto'
})

# Specific engine
google_results = client.search({
    'q': 'python programming',
    'engine': 'google'
})

# Privacy-focused search
ddg_results = client.search({
    'q': 'python programming',
    'engine': 'duckduckgo'
})
```

## Requirements

- Python 3.8+
- requests

## License

MIT