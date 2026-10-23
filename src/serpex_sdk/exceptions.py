"""
Exceptions for the Serpex Python SDK.

Every API error is raised as ``SerpApiException`` (or one of its subclasses,
so ``except SerpApiException`` keeps catching everything):

    400 -> ValidationError          401 -> AuthenticationError
    402 -> InsufficientCreditsError 429 -> RateLimitError
    anything else (403, 410, 5xx, timeout, network) -> SerpApiException
"""

from typing import Any, Dict, Optional

#: Statuses worth retrying: rate limit, our side, and the CDN's 52x timeouts.
RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504, 520, 521, 522, 523, 524})


class SerpApiException(Exception):
    """Base exception for Serpex API errors.

    Attributes:
        status_code: HTTP status, or None for a timeout or a network failure.
        details: the parsed error body, e.g. ``{"error": ..., "retryAfterMs": 292, "limit": 5}``
            for a 429 or ``{"error": ..., "remainingCredits": 0}`` for a 402.
        retryable: True when the same request can succeed on retry (429, 5xx,
            timeout, network). The body's own ``retryable`` wins when present.
        retry_after_ms: how long to wait before retrying (429), from the body or the
            ``Retry-After`` header.
        request_id: quote this to support (500 and 502 bodies).
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        *,
        retryable: Optional[bool] = None,
        retry_after_ms: Optional[int] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.details: Dict[str, Any] = details or {}
        body_retryable = self.details.get("retryable")
        if isinstance(body_retryable, bool):
            self.retryable = body_retryable
        elif retryable is not None:
            self.retryable = retryable
        else:
            self.retryable = status_code is None or status_code in RETRYABLE_STATUSES
        body_retry = self.details.get("retryAfterMs")
        self.retry_after_ms: Optional[int] = (
            body_retry if isinstance(body_retry, int) and not isinstance(body_retry, bool) else retry_after_ms
        )
        request_id = self.details.get("request_id")
        self.request_id: Optional[str] = request_id if isinstance(request_id, str) else None

    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {super().__str__()}"
        return super().__str__()


class AuthenticationError(SerpApiException):
    """401: the API key is missing, invalid or inactive."""


class RateLimitError(SerpApiException):
    """429: over the plan's per-second limit (5, 25 or 50 requests/s).

    ``retry_after`` is the wait in seconds (kept for existing code);
    ``retry_after_ms`` is the exact wait from the API.
    """

    def __init__(self, message: str, retry_after: Optional[float] = None, **kwargs: Any):
        super().__init__(message, **kwargs)
        if retry_after is None and self.retry_after_ms is not None:
            retry_after = self.retry_after_ms / 1000
        self.retry_after = retry_after


class InsufficientCreditsError(SerpApiException):
    """402: the organization does not have enough credits (``details["remainingCredits"]``)."""


class ValidationError(SerpApiException):
    """400: the request was rejected (missing q, content_results not 5/10, bad urls, bad days)."""
