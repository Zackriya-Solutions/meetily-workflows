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


def _loopback_token_path() -> Path:
    """Return the per-OS path of the loopback gateway token file.

    This file is written by the desktop app, is loopback-only, and is
    read-only from a client's perspective. It cannot be used to write data
    back (e.g. PUT a summary) -- mint a Write-scoped key in the app and pass
    it via MEETILY_PRO_TOKEN for that.
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
        f"Meetily is running with Integrations enabled (expected loopback file: {loopback})"
    )


class MeetilyApiError(RuntimeError):
    """Raised when the Agent API returns a non-2xx response."""

    def __init__(self, status: int, body: str):
        super().__init__(f"Meetily API error {status}: {body}")
        self.status = status
        self.body = body


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
                f"could not reach {url}: {exc}. Is Meetily running with "
                "Settings > Pro > Integrations enabled?"
            ) from exc

    def get(self, path: str):
        return self._request("GET", path)

    def post(self, path: str, body: dict | None = None):
        return self._request("POST", path, body)

    def delete(self, path: str):
        return self._request("DELETE", path)
