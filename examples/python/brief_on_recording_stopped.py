#!/usr/bin/env python3
"""Print a short brief each time a recording finishes.

Registers a recording.stopped webhook, verifies and dedups deliveries via
LocalWebhookReceiver, and on each new event fetches the meeting and its
transcript with the resolved token to print a preview. Deletes its own
webhook on exit.

Token: read-only is enough, so the loopback token works (turn on "Allow the
CLI on this computer" in Settings > Integrations). If you extend this to
record, write, or delete, create a key with that scope under Settings >
Integrations > Apps & scripts > Create key and export MEETILY_PRO_TOKEN.

Unsupported example code -- see meetily_agent/__init__.py. Run from anywhere;
this adds the repo root to sys.path so it can import the vendored helper
without installing anything.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from meetily_agent import (  # noqa: E402
    LocalWebhookReceiver,
    MeetilyApiError,
    MeetilyClient,
    discover_token,
)
from meetily_agent.client import TOKEN_HELP  # noqa: E402

RECEIVER_PORT = 9001
WEBHOOK_URL = f"http://127.0.0.1:{RECEIVER_PORT}/webhook"
# recording.stopped fires as soon as capture stops; the meeting's final title
# and transcript finish saving a few seconds later (seen live: ~5s). Wait a
# little before fetching. This runs after the delivery is acknowledged, so it
# does not hold up Meetily's 5-second delivery timeout.
SETTLE_SECONDS = 10


def print_brief(client: MeetilyClient, event: dict) -> None:
    meeting_id = event.get("resource", {}).get("id")
    if not meeting_id:
        print(f"event {event.get('event_id')} has no resource id, skipping")
        return

    time.sleep(SETTLE_SECONDS)
    meeting = client.get(f"/v1/meetings/{meeting_id}")
    title = meeting.get("title") or "(untitled meeting)"

    try:
        # Transcript shape (verified live): {meeting_id, title, segments: [{text, timestamp,
        # audio_start_time, audio_end_time, duration}, ...]}. Join the segment texts.
        transcript = client.get(f"/v1/meetings/{meeting_id}/transcript")
        segments = transcript.get("segments", []) if isinstance(transcript, dict) else []
        text = " ".join(s.get("text", "") for s in segments).strip()
        preview = text[:280] + ("..." if len(text) > 280 else "")
    except Exception as exc:  # transcript may not be ready yet, or fetch failed
        preview = f"(could not fetch transcript: {exc})"

    print(f"\n=== {title} ({meeting_id}) ===")
    print(preview or "(empty transcript)")


def main() -> None:
    client = MeetilyClient(token=discover_token())

    def on_event(event: dict) -> None:
        # LocalWebhookReceiver already deduped this on event_id.
        print(f"\n[event] {event.get('event')} event_id={event.get('event_id')}")
        print_brief(client, event)

    print(f"Registering recording.stopped webhook -> {WEBHOOK_URL}")
    try:
        registration = client.post(
            "/v1/webhooks",
            {"url": WEBHOOK_URL, "events": ["recording.stopped"], "delivery_mode": "at-least-once"},
        )
    except MeetilyApiError as exc:
        if exc.code == "webhooks_disabled":
            print(f"cannot register webhook (webhooks_disabled): {exc.message or exc.body}")
            print("Turn on 'Outgoing (webhooks)' under Settings > Integrations > Advanced.")
            return
        if exc.code == "bad_request" and "not allowed" in (exc.message or ""):
            print(f"cannot register webhook: {exc.message}")
            print(f"Add 127.0.0.1:{RECEIVER_PORT} under Settings > Integrations > Advanced > Local targets, then re-run.")
            return
        if exc.status in (401, 403):
            print(f"cannot register webhook ({exc.code}): {exc.message or exc.body}")
            print(TOKEN_HELP)
            return
        raise
    webhook_id = registration["id"]
    secret = registration["hmac_secret"]  # returned once; not persisted here
    print(f"Webhook id: {webhook_id}")

    status = client.get(f"/v1/webhooks/{webhook_id}")
    if status.get("approval_state") == "pending":
        print(
            "approval_state=pending -- this destination will deliver nothing until "
            "you Allow it in the 'Waiting for you' strip in Settings > Integrations "
            "(or later under Advanced > Destinations)."
        )

    receiver = LocalWebhookReceiver(secret=secret, on_event=on_event, port=RECEIVER_PORT)
    receiver.start()
    print(f"Listening on {receiver.url}. Ctrl-C to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        print("\nShutting down...")
        receiver.stop()
        client.delete_webhook(webhook_id)
        print(f"Deleted webhook {webhook_id}")


if __name__ == "__main__":
    main()
