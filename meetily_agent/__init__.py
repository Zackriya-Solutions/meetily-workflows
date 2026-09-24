"""Unsupported, vendored example helper. Not published to PyPI.

The supported client is the meetily-pro CLI. This package exists only so the
examples in this repo have a small, stdlib-only way to talk to the Meetily
Agent API without pulling in a third-party dependency. Treat it as example
code, not a library: no versioning guarantees, no support, copy what you need.

Contract source of truth: https://docs.meetily.ai/developers and
GET /openapi.json on a running instance.
"""

from .client import MeetilyApiError, MeetilyClient, discover_token
from .webhook import LocalWebhookReceiver, verify_signature

__all__ = [
    "discover_token",
    "MeetilyApiError",
    "MeetilyClient",
    "verify_signature",
    "LocalWebhookReceiver",
]
