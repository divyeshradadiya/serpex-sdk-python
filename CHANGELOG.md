# Changelog

## 2.10.3 — 2026-09-22

- docs: positioning — Serpex is a real-time web search API with page content extraction (`extract`).
- `engine` deprecated (ignored by the API since 2026-06). `SearchParams` accepts `engine` / `engines` again (they were removed in 2.8.0 / 2.7.0, which made old calls raise `TypeError`); passing them emits a `DeprecationWarning` and nothing is sent. No methods, exports or response fields changed.
- Removed stale live-API scripts (`simple_test.py`, `test_sdk.py`, `PYTHON-SDK-TEST-RESULTS.md`); added offline unit tests (`tests/`).
- package description and keywords updated.
