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

##### `extract(params: ExtractParams | Dict[str, Any]) -> ExtractResponse`

Extract content from web pages and convert them to LLM-ready markdown data. Accepts up to 10 URLs per request.

```python
# Basic usage
results = client.extract({
    'urls': [
        'https://example.com',
        'https://httpbin.org'
    ]
})

# With stealth mode and HTML output
results = client.extract({
    'urls': ['https://example.com'],
    'stealth': True,
    'format': 'html'
})

# Using ExtractParams object (type-safe approach)
from serpex import ExtractParams

params = ExtractParams(
    urls=['https://example.com'],
    stealth=True,
    format='html'
)
results = client.extract(params)
```

## Extract Parameters

The `ExtractParams` dataclass supports extraction parameters:

```python
@dataclass
class ExtractParams:
    # Required: URLs to extract (max 10)
    urls: List[str]

    # Optional: Route through premium unblocker for difficult-to-crawl pages (default: False)
    stealth: bool = False

    # Optional: Output format — 'markdown' (default) or 'html'
    format: str = 'markdown'
```

## Extract Response Format

```python
@dataclass
class ExtractResponse:
    success: bool
    results: List[ExtractResult]
    metadata: ExtractMetadata

@dataclass
class ExtractResult:
    url: str
    success: bool
    markdown: Optional[str] = None
    html: Optional[str] = None         # Populated when format='html'
    stealth: Optional[bool] = None     # Whether stealth mode was used for this result
    error: Optional[str] = None
    status_code: Optional[int] = None

@dataclass
class ExtractMetadata:
    total_urls: int
    processed_urls: int
    successful_crawls: int
    failed_crawls: int
    credits_used: int
    response_time: int
    timestamp: str
    cached_free: Optional[int] = None  # URLs served from cache (no credit charge)
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

    # Optional: also fetch page content (markdown) for top results (default: False)
    include_content: bool = False

    # Optional: number of top results to fetch content for — must be exactly
    # 5 or 10 (default: 5). Only relevant when include_content is True.
    content_results: Literal[5, 10] = 5
```

| Param | Type | Default | Notes |
|---|---|---|---|
| `q` | `str` | — | Required search query (max 500 chars) |
| `include_content` | `bool` | `False` | Also fetch page content (markdown) for top results |
| `content_results` | `Literal[5, 10]` | `5` | How many top results to fetch content for; must be exactly `5` or `10` |

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
class SearchMetadata:
    number_of_results: int
    response_time: int
    timestamp: str
    credits_used: int
    from_cache: Optional[bool] = None
    status: Optional[str] = None
    # Present only when include_content was requested
    content_requested: Optional[int] = None
    content_delivered: Optional[int] = None

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    position: int
    engine: str
    img_src: Optional[str] = None
    duration: Optional[str] = None
    score: Optional[float] = None
    # Present only when include_content was requested. Best-effort — a
    # failed extraction sets content_error instead of content.
    content: Optional[str] = None
    content_error: Optional[str] = None

@dataclass
class SearchResponse:
    metadata: SearchMetadata
    id: str
    query: str
    engines: List[str]
    results: List[SearchResult]
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

### Search with Page Content

Fetch page content (markdown) for the top results inline with the search —
best-effort, so check each result for `content` vs `content_error`.

```python
results = client.search({
    'q': 'best espresso machines 2025',
    'include_content': True,
    'content_results': 10,  # must be exactly 5 or 10
})

print(
    f"Content delivered for {results.metadata.content_delivered}/"
    f"{results.metadata.content_requested} requested results"
)

for result in results.results:
    if result.content:
        print(f"✅ {result.url}: {len(result.content)} chars of markdown")
    elif result.content_error:
        print(f"❌ {result.url}: {result.content_error}")
```

### Extract Web Content to LLM-Ready Data

#### Extract from a Single URL

```python
# Extract content from one website (markdown, default)
result = client.extract({
    'urls': ['https://example.com']
})

if result.results[0].success:
    print(f"✅ Extracted {len(result.results[0].markdown)} characters")
    print("Markdown content:", result.results[0].markdown[:200] + "...")

# Extract with stealth mode and HTML output
stealth_result = client.extract({
    'urls': ['https://example.com'],
    'stealth': True,
    'format': 'html'
})

if stealth_result.results[0].success:
    print("HTML content:", stealth_result.results[0].html[:200])
```

#### Extract from Multiple URLs (up to 10 at once)

```python
# Extract content from multiple websites (up to 10 URLs)
extract_results = client.extract({
    'urls': [
        'https://example.com',
        'https://httpbin.org',
        'https://github.com'
    ]
})

print(f"Successfully extracted {extract_results.metadata.successful_crawls} pages")
print(f"Total credits used: {extract_results.metadata.credits_used}")

for result in extract_results.results:
    if result.success:
        print(f"✅ {result.url}: {len(result.markdown)} characters")
        # Use result.markdown for LLM processing
    else:
        print(f"❌ {result.url}: {result.error}")
```

#### Sample Response

```python
# Example response structure
{
    'success': True,
    'results': [
        {
            'url': 'https://example.com',
            'success': True,
            'markdown': '# Example Domain\n\nThis domain is for use in...',
            'stealth': False,
            'status_code': 200
        }
    ],
    'metadata': {
        'total_urls': 1,
        'processed_urls': 1,
        'successful_crawls': 1,
        'failed_crawls': 0,
        'credits_used': 3,
        'cached_free': 0,
        'response_time': 255,
        'timestamp': '2025-11-13T10:30:00.000Z'
    }
}
```

### Using ExtractParams Object

```python
from serpex import ExtractParams

params = ExtractParams(urls=[
    'https://example.com',
    'https://httpbin.org'
])
results = client.extract(params)
```

## Requirements

- Python 3.8+
- requests

## License

MIT
