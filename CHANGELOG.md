# Changelog

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
