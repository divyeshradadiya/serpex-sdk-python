# Changelog

## 2.12.0 — 2026-10-23

Errors and types now match the API exactly (checked against the backend and live responses). Minor release: errors now raise status-specific subclasses (still `SerpApiException`), otherwise additive.

- Errors keep the API's body for every status. Before, 401, 402 and 429 dropped it, so `e.details.get("retryAfterMs")` and `e.details.get("remainingCredits")` (as shown in the API docs) returned `None`. The message is the API's error text, never a dict repr.
- Status-specific exceptions are raised (all subclass `SerpApiException`, so existing `except` clauses still work) and exported: `ValidationError` (400), `AuthenticationError` (401), `InsufficientCreditsError` (402), `RateLimitError` (429, with `retry_after_ms` and `retry_after`).
- Every exception has `retryable`, `retry_after_ms` and `request_id`. A timeout raises `SerpApiException` with `details["error"] == "timeout"`; a network failure `details["error"] == "network"`; both retryable.
- `search({...})` / `extract({...})` with a key the API does not read (`category`, `time_range`, `num_results`, ...) no longer raises `TypeError`: the key is dropped with one `DeprecationWarning`.
- `ExtractParams.stealth` is deprecated: stealth mode ends on 2026-11-01, after which the API answers HTTP 410. `extract(stealth=True)` emits one `DeprecationWarning`. `STEALTH_END_DATE` exported.
- Types: `SearchMetadata.status` is `Literal["success", "no_results"]`; `UsageResponse.effective_days` added; `recent_requests` typed as `RecentRequest` (TypedDict); `ErrorBody` TypedDict for `details`; `EXTRACT_ERROR_TYPES` (now with `dns_unresolved`); `SearchResult.has_content`. `SearchResult`, `SearchMetadata`, `ExtractResult`, `ExtractMetadata`, `UsageStatistics`, `UsageCredits` exported.
- Docs: `stealth_provider_unavailable` is never returned (the API drops codes that name its rendering service).
- Ships `py.typed` (PEP 561), so type checkers use the SDK's annotations instead of treating it as untyped.
- Offline contract tests against sanitized live fixtures (`tests/fixtures/`).
- `User-Agent: serpex-python/2.12.0`.

## 2.11.0 — 2026-10-01

- `SearchResult.engine` and `SearchResponse.engines` are now optional (defaults `None` / `["auto"]`) and documented as deprecated, so a response without them can't crash parsing.
- New response fields: `SearchResponse.message`, `SearchMetadata.no_results_verified` / `charged` / `message` (no-results responses), `ExtractMetadata.stealth`, `UsageStatistics.noResultsRequests`.
- `ExtractResult.crawled_at` / `extraction_mode` marked deprecated (the API never returns them); removed in 3.0.
- Timeouts: new `SerpexClient(timeout=...)`; defaults are now longer than the server's own budget (60 s search, 100 s with `include_content`, 100 s extract, 120 s stealth extract) instead of 30 s everywhere.
- Every request sends `User-Agent: serpex-python/<version>`.
- Docs: `usage()` covers the whole organization, and `UsageResponse.api_key` is the key's name.

## 2.10.3 — 2026-09-22

- docs: positioning — Serpex is a real-time web search API with page content extraction (`extract`).
- `engine` deprecated (ignored by the API since 2026-06). `SearchParams` accepts `engine` / `engines` again (they were removed in 2.8.0 / 2.7.0, which made old calls raise `TypeError`); passing them emits a `DeprecationWarning` and nothing is sent. No methods, exports or response fields changed.
- Removed stale live-API scripts (`simple_test.py`, `test_sdk.py`, `PYTHON-SDK-TEST-RESULTS.md`); added offline unit tests (`tests/`).
- package description and keywords updated.
