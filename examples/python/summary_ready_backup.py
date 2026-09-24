#!/usr/bin/env python3
"""Save each meeting summary to a local file as soon as it's ready.

Subscribes to summary.completed (the summary-ready trigger), and on each new
event fetches the summary with the resolved token and writes it to
./summaries/<meeting_id>.json. This only reads and saves locally -- no
write-back to Meetily is involved, so no write-scoped token is needed: the
loopback token works (turn on "Allow the CLI on this computer" in Settings >
Integrations). To write back (e.g. PUT /v1/meetings/{id}/summary), create a
key with the Write scope under Settings > Integrations > Apps & scripts >
Create key and export MEETILY_PRO_TOKEN.

Unsupported example code -- see meetily_agent/__init__.py. This is a stub:
extend on_event() if you need something more than "save it to a file".
"""

from __future__ import annotations

import json
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

RECEIVER_PORT = 9002
WEBHOOK_URL = f"http://127.0.0.1:{RECEIVER_PORT}/webhook"
OUTPUT_DIR = Path("./summaries")


def save_summary(client: MeetilyClient, event: dict) -> None:
    meeting_id = event.get("resource", {}).get("id")
    if not meeting_id:
        print(f"event {event.get('event_id')} has no resource id, skipping")
        return

    summary = client.get(f"/v1/meetings/{meeting_id}/summary")

    # regeneration_failed=true means the latest regenerate attempt failed and
    # this is the prior (stale) summary, not a fresh one; status still reads
    # "completed". error is set when the stored result couldn't be parsed at
    # all. Back it up either way, but say so instead of backing up silently.
    if summary.get("regeneration_failed"):
        print(f"WARNING: {meeting_id} -- regeneration failed; backing up the prior summary, not a fresh one")
    if summary.get("error"):
        print(f"WARNING: {meeting_id} -- summary has error={summary['error']!r}")

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / f"{meeting_id}.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"saved summary for {meeting_id} -> {out_path}")


def main() -> None:
    client = MeetilyClient(token=discover_token())

    def on_event(event: dict) -> None:
        # LocalWebhookReceiver already deduped this on event_id.
        print(f"[event] {event.get('event')} event_id={event.get('event_id')}")
        save_summary(client, event)

    print(f"Registering summary.completed webhook -> {WEBHOOK_URL}")
    try:
        registration = client.post(
            "/v1/webhooks",
            {"url": WEBHOOK_URL, "events": ["summary.completed"], "delivery_mode": "at-least-once"},
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
