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
    assert serpex.__version__ == "2.10.3"
