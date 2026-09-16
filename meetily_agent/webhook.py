"""HMAC verification and a tiny local webhook receiver.

Unsupported example code. See meetily_agent/__init__.py.

Delivery from Meetily is best-effort at-least-once: duplicates are possible
and events can be lost. Callbacks driven through LocalWebhookReceiver are
deduped on event_id, but that only protects against re-delivery of an event
this process has already seen -- it is not durable across restarts. A real
integration that must not miss or double-process events should persist the
event_id set itself.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable

SIGNATURE_HEADER = "X-Meetily-Signature"
TIMESTAMP_HEADER = "X-Meetily-Timestamp"


def verify_signature(secret: str, timestamp: str, body: bytes, header_sig: str) -> bool:
    """Verify an X-Meetily-Signature header.

    The signature is HMAC-SHA256, hex-encoded, over the string
    "{timestamp}.{body}", sent as "sha256=<hex>". Uses hmac.compare_digest
    to avoid timing attacks.
    """
    if not header_sig:
        return False
    sig = header_sig[len("sha256=") :] if header_sig.startswith("sha256=") else header_sig

    if isinstance(body, str):
        body = body.encode("utf-8")

    signed_payload = timestamp.encode("utf-8") + b"." + body
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


class LocalWebhookReceiver:
    """A small loopback HTTP server that verifies and dedups Meetily webhook events.

    Runs on 127.0.0.1 only -- this is a receiver for local examples, not a
    production ingress. For any host other than loopback, "nothing leaves
    the machine" no longer holds.
    """

    def __init__(
        self,
        secret: str,
        on_event: Callable[[dict], None],
        host: str = "127.0.0.1",
        port: int = 0,
    ):
        self._secret = secret
        self._on_event = on_event
        self._seen_event_ids: set[str] = set()
        self._lock = threading.Lock()

        receiver = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802 (http.server naming convention)
                length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(length) if length else b""
                timestamp = self.headers.get(TIMESTAMP_HEADER, "")
                signature = self.headers.get(SIGNATURE_HEADER, "")

                if not verify_signature(receiver._secret, timestamp, raw_body, signature):
                    self.send_response(401)
                    self.end_headers()
                    self.wfile.write(b"invalid signature")
                    return

                try:
                    payload = json.loads(raw_body.decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"invalid body")
                    return

                event_id = payload.get("event_id")
                with receiver._lock:
                    already_seen = event_id in receiver._seen_event_ids
                    if event_id is not None:
                        receiver._seen_event_ids.add(event_id)

                if not already_seen:
                    receiver._on_event(payload)

                # A 2xx here means "accepted for processing", not that any
                # downstream automation triggered by this event has succeeded.
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"accepted")

            def log_message(self, fmt, *args):  # silence default stderr logging
                pass

        self._server = HTTPServer((host, port), Handler)
        self._thread: threading.Thread | None = None

    @property
    def url(self) -> str:
        host, port = self._server.server_address
        return f"http://{host}:{port}/webhook"

    def start(self) -> None:
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        if self._thread:
            self._thread.join(timeout=5)

    def __enter__(self) -> "LocalWebhookReceiver":
        self.start()
        return self

    def __exit__(self, *exc_info) -> None:
        self.stop()
