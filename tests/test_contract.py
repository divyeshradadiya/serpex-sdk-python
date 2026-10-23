"""Contract tests against sanitized responses captured from api.serpex.dev on
2026-10-23 (statuses that cannot be triggered safely use the exact body from
the backend code). tests/fixtures/manifest.json holds each status and headers.
No network: the HTTP session is stubbed."""

import json
import warnings
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
import requests

import serpex
from serpex import (
    AuthenticationError,
    InsufficientCreditsError,
    RateLimitError,
    SerpApiException,
    SerpexClient,
    ValidationError,
)

FIXTURES = Path(__file__).parent / "fixtures"
MANIFEST = json.loads((FIXTURES / "manifest.json").read_text())


def fixture(name):
    return json.loads((FIXTURES / f"{name}.json").read_text())


class FakeResponse:
    def __init__(self, name):
        meta = MANIFEST[name]
        self.status_code = meta["status"]
        self.ok = 200 <= self.status_code < 300
        self.reason = ""
        self.headers = requests.structures.CaseInsensitiveDict(meta["headers"])
        self._body = fixture(name)

    def json(self):
        return self._body


def serve(name):
    """Client whose session answers every request with one fixture; returns (client, sent)."""
    sent = []
    client = SerpexClient("test-key", base_url="https://example.invalid")

    def get(url, **kw):
        sent.append(("GET", url, kw))
        return FakeResponse(name)

    def post(url, **kw):
        sent.append(("POST", url, kw))
        return FakeResponse(name)

    client.session.get = get
    client.session.post = post
    return client, sent


def query_of(url):
    return {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}


def test_plain_search_typed_and_only_q_sent():
    client, sent = serve("search_plain")
    res = client.search({"q": "python asyncio tutorial"})
    assert query_of(sent[0][1]) == {"q": "python asyncio tutorial"}
    assert res.metadata.status == "success"
    assert res.metadata.credits_used == 1
    assert res.metadata.content_requested is None
    assert len(res.results) == 10
    assert all(r.content is None and r.content_error is None for r in res.results)
    assert isinstance(res.results[0].position, int)


def test_legacy_dict_options_are_dropped_not_typeerror():
    client, sent = serve("search_repeat_deprecated_engine")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        res = client.search({"q": "python asyncio tutorial", "engine": "legacy-value", "category": "web",
                             "time_range": "day", "num_results": 3, "language": "en"})
    assert query_of(sent[0][1]) == {"q": "python asyncio tutorial"}
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)
    assert res.metadata.credits_used == 0 and res.metadata.from_cache is True
    assert MANIFEST["search_repeat_deprecated_engine"]["headers"]["deprecation"] == "@1782000000"


def test_include_content_first_five_only():
    client, sent = serve("search_content")
    res = client.search({"q": "what is retrieval augmented generation", "include_content": True})
    q = query_of(sent[0][1])
    assert q["include_content"].lower() == "true"
    assert res.metadata.content_requested == 5 and res.metadata.content_delivered == 5
    assert res.metadata.credits_used == 3
    for i, r in enumerate(res.results):
        if i < 5:
            assert r.has_content and r.content_error is None
        else:
            assert r.content is None and r.content_error is None


def test_content_errors_are_mutually_exclusive_with_content():
    client, _ = serve("search_content_errors")
    res = client.search({"q": "x", "include_content": True, "content_results": 5})
    errs = [r for r in res.results if r.content_error is not None]
    assert len(errs) == 5 and {r.content_error for r in errs} == {"robots_disallowed"}
    assert all(r.content is None for r in errs)
    assert res.metadata.content_delivered == 0 and res.metadata.credits_used == 1


def test_no_results():
    client, _ = serve("search_no_results")
    res = client.search({"q": "x"})
    assert res.results == []
    assert res.metadata.status == "no_results"
    assert res.metadata.no_results_verified is False and res.metadata.charged is False
    assert res.metadata.credits_used == 0
    assert res.message == res.metadata.message


def test_extract_markdown_html_failure():
    client, sent = serve("extract_markdown")
    res = client.extract({"urls": ["https://example.com"]})
    assert sent[0][0] == "POST" and sent[0][2]["json"] == {"urls": ["https://example.com"]}
    assert res.results[0].success and "documentation examples" in res.results[0].markdown
    assert res.metadata.credits_used == 1

    client, sent = serve("extract_html")
    res = client.extract({"urls": ["https://example.com"], "format": "html"})
    assert sent[0][2]["json"]["format"] == "html"
    assert res.results[0].html.lower().startswith("<!doctype html>")

    client, _ = serve("extract_failed_404")
    res = client.extract({"urls": ["https://example.com/missing"]})
    r = res.results[0]
    assert not r.success and r.error_type == "http" and r.status_code == 404
    assert r.error_type in serpex.EXTRACT_ERROR_TYPES
    assert res.metadata.credits_used == 0


def test_stealth_warns_once_and_is_sent():
    client, sent = serve("extract_stealth")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        res = client.extract({"urls": ["https://example.com"], "stealth": True})
        client.extract({"urls": ["https://example.com"], "stealth": True})
    stealth_warnings = [w for w in caught if "2026-11-01" in str(w.message)]
    assert len(stealth_warnings) == 1
    assert sent[0][2]["json"]["stealth"] is True
    assert res.metadata.stealth is True and res.metadata.credits_used == 5


def test_usage_effective_days_and_recent_requests():
    client, sent = serve("usage_days7")
    res = client.usage({"days": 7})
    assert query_of(sent[0][1]) == {"days": "7"}
    assert res.period_days == 7 and res.effective_days == 7
    assert isinstance(res.credits.balance, int)
    assert set(res.statistics.engineStats) <= {"search", "crawl", "stealth"}
    assert res.recent_requests and "query" not in res.recent_requests[0]
    assert res.recent_requests[0]["searchEngine"] in ("search", "crawl", "stealth")


@pytest.mark.parametrize(
    "name,status,exc,message,retryable",
    [
        ("error_400_missing_q", 400, ValidationError, "Query parameter (q or query) is required", False),
        ("error_400_content_results", 400, ValidationError, "content_results must be 5 or 10", False),
        ("error_400_include_content", 400, ValidationError, "include_content must be a boolean (true or false)", False),
        ("error_401_bad_key", 401, AuthenticationError, "Invalid or inactive API key", False),
        ("error_401_no_key", 401, AuthenticationError, "API key required", False),
        ("error_402_search", 402, InsufficientCreditsError,
         "Insufficient credits. Please purchase more credits to continue.", False),
        ("error_429", 429, RateLimitError, "Rate limit exceeded", True),
        ("error_500_search", 500, SerpApiException, "Internal server error", True),
        ("error_503_search", 503, SerpApiException, "Search temporarily unavailable, please retry.", True),
        ("error_500_malformed_json", 500, SerpApiException, "Unexpected end of JSON input", True),
        ("error_404_news_route", 404, SerpApiException, "Route GET:/api/search/news not found", False),
    ],
)
def test_search_errors(name, status, exc, message, retryable):
    client, _ = serve(name)
    with pytest.raises(exc) as info:
        client.search({"q": "x"})
    e = info.value
    assert isinstance(e, SerpApiException)
    assert e.status_code == status
    assert e.args[0] == message
    assert e.retryable is retryable
    assert e.details == fixture(name)


def test_429_retry_hint_and_402_balance():
    client, _ = serve("error_429")
    with pytest.raises(RateLimitError) as info:
        client.search({"q": "x"})
    assert info.value.retry_after_ms == 292
    assert info.value.retry_after == pytest.approx(0.292)
    assert info.value.details["limit"] == 5

    client, _ = serve("error_402_search")
    with pytest.raises(InsufficientCreditsError) as info:
        client.search({"q": "x"})
    assert info.value.details.get("remainingCredits") == 0


@pytest.mark.parametrize(
    "name,status,retryable",
    [
        ("error_402_extract", 402, False),
        ("error_403_stealth_not_in_plan", 403, False),
        ("error_410_stealth_ended", 410, False),
        ("error_502_extract", 502, True),
        ("error_503_stealth_busy", 503, True),
        ("error_504_extract", 504, True),
        ("error_400_extract_invalid_url", 400, False),
    ],
)
def test_extract_errors(name, status, retryable):
    client, _ = serve(name)
    with pytest.raises(SerpApiException) as info:
        client.extract({"urls": ["https://example.com"]})
    e = info.value
    assert e.status_code == status and e.retryable is retryable
    assert e.args[0] == fixture(name)["error"]
    if status == 502:
        assert e.request_id and len(e.request_id) == 36


def test_timeout_and_network_errors_are_retryable():
    client = SerpexClient("test-key", base_url="https://example.invalid")

    def timeout(url, **kw):
        raise requests.Timeout("read timed out")

    client.session.get = timeout
    with pytest.raises(SerpApiException) as info:
        client.search({"q": "x"})
    assert info.value.status_code is None and info.value.retryable
    assert info.value.details["error"] == "timeout"

    def reset(url, **kw):
        raise requests.ConnectionError("connection reset")

    client.session.get = reset
    with pytest.raises(SerpApiException) as info:
        client.search({"q": "x"})
    assert info.value.retryable and info.value.details["error"] == "network"
