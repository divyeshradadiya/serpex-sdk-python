# serpex

Official Python SDK for Serpex.

Serpex is a real-time web search API and extract API for AI agents. Search returns ranked web
results, optionally with page content as markdown; Extract turns known URLs into clean markdown
or HTML. Every search is routed automatically: there is no engine to choose.

## Installation

```bash
pip install serpex
```

## Quick Start

```python
from serpex import SerpexClient, SearchParams

client = SerpexClient("your-api-key-here")

results = client.search({"q": "python tutorial"})
# or, typed:
results = client.search(SearchParams(q="python tutorial"))

print(results.results[0].title)
print(results.metadata.credits_used)
```

## SerpexClient

```python
SerpexClient(api_key: str, base_url: str = "https://api.serpex.dev", timeout: float | None = None)
```

`timeout` (seconds) overrides every call. By default each call waits longer than the server's
own budget for it: 60 s search, 100 s search with `include_content`, 100 s extract, 120 s
stealth extract. Every request sends `User-Agent: serpex-python/<version>`.

## Search

```python
@dataclass
class SearchParams:
    q: str                          # required, 1-500 characters
    include_content: bool = False   # also fetch page content (markdown) for the top results
    content_results: Literal[5, 10] = 5
    engine: Optional[str] = None    # deprecated: ignored by the API, not sent
    engines: Optional[Any] = None   # deprecated: ignored by the API, not sent
```

Only `q`, `include_content` and `content_results` are sent. Search operators go inside `q`:
`site:`, `-site:`, `after:YYYY-MM-DD` and `before:YYYY-MM-DD`. A dict with other keys (for
example `category`, `time_range` or `num_results` from older code) still works: those keys are
dropped with one `DeprecationWarning`.

```python
@dataclass
class SearchResponse:
    metadata: SearchMetadata
    id: str
    query: str
    engines: List[str] = ["auto"]       # deprecated
    results: List[SearchResult] = []
    message: Optional[str] = None       # no_results only

@dataclass
class SearchMetadata:
    number_of_results: int
    response_time: int                  # ms
    timestamp: str                      # ISO 8601
    credits_used: int                   # 0, 1, 3 or 6
    from_cache: Optional[bool] = None
    status: Optional[Literal["success", "no_results"]] = None
    content_requested: Optional[int] = None    # include_content only (5 or 10)
    content_delivered: Optional[int] = None    # include_content only
    no_results_verified: Optional[bool] = None # no_results only
    charged: Optional[bool] = None             # no_results only
    message: Optional[str] = None              # no_results only

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    position: int
    engine: Optional[str] = None        # deprecated, always "auto"
    img_src: Optional[str] = None
    duration: Optional[str] = None
    score: Optional[float] = None
    content: Optional[str] = None       # page markdown
    content_error: Optional[str] = None # why content is missing, e.g. "robots_disallowed"
```

`content` and `content_error` are mutually exclusive. They exist only with
`include_content=True`, and only on the first `content_results` results; every other result has
both set to `None`. `result.has_content` is a shortcut.

A search that finds nothing returns `results == []` with `metadata.status == "no_results"`. It is
charged (1 credit) only when `metadata.no_results_verified` is true.

```python
results = client.search({
    "q": "best espresso machines 2025",
    "include_content": True,
    "content_results": 10,
})

print(f"{results.metadata.content_delivered}/{results.metadata.content_requested} pages delivered")
for result in results.results:
    if result.content is not None:
        print(result.url, len(result.content))
    elif result.content_error is not None:
        print(result.url, "no content:", result.content_error)
```

Credits with `include_content`: 1 when no page came back, 3 for 1-5 pages, 6 for 6-10 pages.

## Extract

```python
@dataclass
class ExtractParams:
    urls: List[str]          # 1-10 absolute URLs
    format: str = "markdown" # or "html"
    stealth: bool = False    # deprecated: stealth mode ends on 2026-11-01
```

```python
response = client.extract({"urls": ["https://example.com", "https://example.com/missing"]})

for r in response.results:
    if r.success:
        print(r.url, len(r.markdown or ""))
    else:
        print(r.url, r.error_type, r.error)   # e.g. "http", "HTTP 404: Not Found"

print(response.metadata.credits_used)          # 1 per extracted URL; failures are free
```

`ExtractResult`: `url`, `success`, then `markdown` or `html` on success, or `error` and
`error_type` on failure (always both). `status_code` when known. `error_type` is one of
`serpex.EXTRACT_ERROR_TYPES`: `timeout`, `connection`, `dns_unresolved`, `ssl_error`, `http`,
`blocked`, `robots_disallowed`, `server_error`, `unsupported_content_type`, `too_large`,
`unknown`. `ExtractMetadata`: `total_urls`, `processed_urls`, `successful_crawls`,
`failed_crawls`, `credits_used`, `response_time`, `timestamp`, plus `cached_free` (free repeats,
omitted when 0) and `stealth` (stealth requests only).

### Stealth mode (ends 2026-11-01)

`stealth=True` renders the page in a full browser for 5 credits per URL. **It ends on
2026-11-01.** From that date the API rejects it with HTTP 410 (not charged); send the request
without `stealth`. The SDK emits one `DeprecationWarning` per process when you use it.

A failed stealth result says `"This page could not be rendered. Not charged."` and may carry an
`error_code`: `stealth_target_unreachable` (domain gone), `stealth_target_status` (error status,
see `status_code`), `stealth_target_empty`, `stealth_timeout`, `stealth_network`,
`stealth_unconfigured`. Failures on our side carry `error_type == "server_error"` without a code
(`stealth_provider_unavailable` is never returned).

## Usage & credit balance

Statistics and credits cover your whole organization (every API key in it); `usage.api_key` is
the NAME of the key that made the call. Free (no credits), but it counts against your
per-second rate limit.

```python
usage = client.usage()              # last 30 days
week = client.usage({"days": 7})    # 1-90

print(usage.credits.balance)
print(usage.effective_days)         # days actually covered (history is kept 30 days)
print(usage.statistics.engineStats) # {"search": 120, "crawl": 30, "stealth": 5}
print(usage.recent_requests[0]["status"])  # 10 newest requests, see serpex.RecentRequest
```

## Errors

Every API error raises `SerpApiException` or a subclass:

| Status | Exception | When | Retry |
|---|---|---|---|
| 400 | `ValidationError` | missing or invalid `q`, `include_content`, `content_results`, `urls` or `days` | no |
| 401 | `AuthenticationError` | missing or invalid API key | no |
| 402 | `InsufficientCreditsError` | not enough credits (`e.details["remainingCredits"]`) | no |
| 403 | `SerpApiException` | stealth not included in your plan | no |
| 410 | `SerpApiException` | stealth after 2026-11-01 | no |
| 429 | `RateLimitError` | over your per-second limit: 5, 25 or 50 requests/s by plan | yes, after `e.retry_after_ms` |
| 500, 502, 503, 504 | `SerpApiException` | our side, never charged (`e.request_id` on 500/502) | yes |
| none | `SerpApiException` | timeout (`e.details["error"] == "timeout"`) or network failure | yes |

Every exception has `status_code`, `details` (the parsed error body), `retryable`,
`retry_after_ms` and `request_id`. A search with page content counts as more than one request
toward the rate limit: 2 with `content_results=5`, 3 with `content_results=10`.

```python
import time
from serpex import SerpexClient, SerpApiException, RateLimitError, InsufficientCreditsError

try:
    results = client.search({"q": "test query"})
except RateLimitError as e:
    time.sleep((e.retry_after_ms or 1000) / 1000)
except InsufficientCreditsError as e:
    print("Out of credits:", e.details.get("remainingCredits"))
except SerpApiException as e:
    print(f"API error {e.status_code}: {e} (retryable={e.retryable})")
```

## The `engine` parameter (deprecated)

There is nothing to select. `engine` / `engines` are ignored by the API (since 2026-06);
requests that still send them get a `Deprecation` response header. The SDK still accepts them,
emits a `DeprecationWarning` and does not send them. The `engines` / `engine` response fields
are deprecated too: always `"auto"`.

## Requirements

- Python 3.8+
- requests

## License

MIT
