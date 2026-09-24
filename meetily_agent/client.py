"""Minimal stdlib-only client for the Meetily Agent API.

Unsupported example code. See meetily_agent/__init__.py.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_BASE = "http://127.0.0.1:8420"
DEFAULT_TIMEOUT = 10.0

# Shown with 401/403 errors. The loopback token file is Read-only, so any
# automation that records, writes, or deletes needs a key created in the app.
TOKEN_HELP = (
    "Read-only automations can use the loopback token (turn on 'Allow the CLI "
    "on this computer' in Settings > Integrations). To record, write, or "
    "delete: Settings > Integrations > Apps & scripts > Create key, tick the "
    "scope you need, copy the secret (shown once), turn on the key's Allow "
    "switch, then export MEETILY_PRO_TOKEN=<secret>. Check with "
    "`meetily-pro whoami`."
)


def _loopback_token_path() -> Path:
    """Return the per-OS path of the loopback gateway token file.

    This file is written by the desktop app, is loopback-only, and carries
    the Read scope only. It cannot record, write back (e.g. PUT a summary),
    or delete -- for those, create a key with that scope (see TOKEN_HELP) and
    pass it via MEETILY_PRO_TOKEN or --token-file.
    """
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "pro.meetily.ai" / "gateway-token"


def discover_token(token_file: str | None = None) -> str:
    """Resolve a token in the documented order.

    Order: an explicit --token-file argument (token_file), then the
    MEETILY_PRO_TOKEN env var, then the loopback token file for this OS.
    Raises RuntimeError if none produce a usable token.
    """
    if token_file:
        text = Path(token_file).read_text(encoding="utf-8").strip()
        if text:
            return text
        raise RuntimeError(f"token file {token_file} is empty")

    env_token = os.environ.get("MEETILY_PRO_TOKEN", "").strip()
    if env_token:
        return env_token

    loopback = _loopback_token_path()
    if loopback.exists():
        text = loopback.read_text(encoding="utf-8").strip()
        if text:
            return text

    raise RuntimeError(
        "no token found: pass --token-file, set MEETILY_PRO_TOKEN, or make sure "
        f"Meetily is running with the Automation API on (expected loopback file: {loopback}). "
        + TOKEN_HELP
    )


class MeetilyApiError(RuntimeError):
    """Raised when the Agent API returns a non-2xx response.

    The gateway's error envelope is {"error": {"code", "message", "retryable"}}
    (gateway/error.rs). When the body parses as that shape, code/message/
    retryable are set from it; otherwise they are None -- callers that only
    used .status/.body before still work unchanged.
    """

    def __init__(self, status: int, body: str):
        text = f"Meetily API error {status}: {body}"
        if status in (401, 403):
            # 401: token unknown/expired/revoked. 403 consumer_disabled: the
            # key's Allow switch is off. 403 insufficient_scope:
            # the token lacks the scope -- usually the Read-only loopback token
            # used for a record/write/delete call.
            text += f"\n{TOKEN_HELP}"
        super().__init__(text)
        self.status = status
        self.body = body
        self.code: str | None = None
        self.message: str | None = None
        self.retryable: bool | None = None
        try:
            parsed = json.loads(body)
        except ValueError:
            parsed = None
        if isinstance(parsed, dict):
            error = parsed.get("error")
            if isinstance(error, dict):
                self.code = error.get("code")
                self.message = error.get("message")
                self.retryable = error.get("retryable")


class MeetilyClient:
    """Tiny HTTP client for the local Meetily Agent API. urllib only, no deps."""

    def __init__(
        self,
        base: str = DEFAULT_BASE,
        token: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.base = base.rstrip("/")
        self.token = token or discover_token()
        self.timeout = timeout

    def _request(self, method: str, path: str, body: dict | None = None):
        url = f"{self.base}{path}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Authorization": f"Bearer {self.token}"}
        if data is not None:
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            raise MeetilyApiError(exc.code, raw) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"could not reach {url}: {exc}. Is Meetily running with the "
                "Automation API turned on (Settings > Integrations)?"
            ) from exc

    def get(self, path: str):
        return self._request("GET", path)

    def post(self, path: str, body: dict | None = None):
        return self._request("POST", path, body)

    def delete(self, path: str):
        return self._request("DELETE", path)

    def list_webhooks(self, include_all: bool = False) -> list[dict]:
        """GET /v1/webhooks. include_all=True needs a Delete-scoped, first-party
        token and lists every subscription, not just this token's own."""
        path = "/v1/webhooks?all=true" if include_all else "/v1/webhooks"
        return self.get(path)

    def get_webhook(self, webhook_id: str) -> dict:
        """GET /v1/webhooks/{id}: the subscription plus its live approval_state."""
        return self.get(f"/v1/webhooks/{webhook_id}")

    def delete_webhook(self, webhook_id: str) -> None:
        """DELETE /v1/webhooks/{id}. Owner-only; 404 if it doesn't exist."""
        self.delete(f"/v1/webhooks/{webhook_id}")
