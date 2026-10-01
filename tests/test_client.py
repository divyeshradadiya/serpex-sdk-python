"""Offline tests — no network, no API key. The HTTP session is stubbed."""

import warnings

import pytest

import serpex
from serpex import SearchParams, SerpexClient

RESPONSE = {
    "metadata": {"number_of_results": 0, "response_time": 1, "timestamp": "t", "credits_used": 1},
    "id": "x",
    "query": "hello",
    "engines": ["auto"],
    "results": [],
}


class _Resp:
    status_code = 200
    ok = True
    headers = {}

    def json(self):
        return RESPONSE


def _client(sent):
    client = SerpexClient("test-key", base_url="https://example.invalid")

    def fake_request(method, url, **kwargs):
        sent.append((method, url, kwargs))
        return _Resp()

    client.session.request = fake_request
    client.session.get = lambda url, **kw: fake_request("GET", url, **kw)
    client.session.post = lambda url, **kw: fake_request("POST", url, **kw)
    return client


def test_public_surface_unchanged():
    for name in ("SerpexClient", "SerpApiException", "SearchParams", "SearchResponse",
                 "ExtractParams", "ExtractResponse", "UsageParams", "UsageResponse"):
        assert hasattr(serpex, name)
    for method in ("search", "extract", "usage"):
        assert callable(getattr(SerpexClient, method))


def test_engine_is_accepted_warned_and_not_sent():
    sent = []
    client = _client(sent)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = client.search({"q": "hello", "engine": "legacy-value"})
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)
    assert result.query == "hello"
    assert sent, "no request made"
    assert "engine" not in repr(sent[0])


def test_search_without_engine_does_not_warn():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        SearchParams(q="hello")


def test_version():
    assert serpex.__version__ == "2.11.0"


def test_user_agent_names_sdk_and_version():
    client = SerpexClient("test-key", base_url="https://example.invalid")
    assert client.session.headers["User-Agent"] == "serpex-python/2.11.0"


def test_response_without_deprecated_engine_fields_parses():
    global RESPONSE
    saved = RESPONSE
    RESPONSE = {
        "metadata": {"number_of_results": 1, "response_time": 1, "timestamp": "t",
                     "credits_used": 1},
        "id": "x",
        "query": "hello",
        "results": [{"title": "T", "url": "https://a.example", "snippet": "s",
                     "position": 1}],
    }
    try:
        result = _client([]).search({"q": "hello"})
    finally:
        RESPONSE = saved
    assert result.engines == ["auto"]
    assert result.results[0].engine is None
    assert result.results[0].title == "T"


def test_no_results_fields_are_parsed():
    global RESPONSE
    saved = RESPONSE
    RESPONSE = {
        "metadata": {"number_of_results": 0, "response_time": 1, "timestamp": "t",
                     "credits_used": 0, "status": "no_results",
                     "no_results_verified": True, "charged": False, "message": "m"},
        "id": "x",
        "query": "hello",
        "engines": ["auto"],
        "results": [],
        "message": "No results found",
    }
    try:
        result = _client([]).search({"q": "hello"})
    finally:
        RESPONSE = saved
    assert result.message == "No results found"
    assert result.metadata.charged is False
    assert result.metadata.no_results_verified is True


def test_include_content_is_sent_with_longer_timeout():
    sent = []
    _client(sent).search({"q": "hello", "include_content": True, "content_results": 10})
    method, url, kwargs = sent[0]
    assert "include_content=True" in url and "content_results=10" in url
    assert kwargs["timeout"] >= 60


def test_timeout_override_applies_to_every_call():
    sent = []
    client = _client(sent)
    client.timeout = 5
    client.search({"q": "hello"})
    assert sent[0][2]["timeout"] == 5
