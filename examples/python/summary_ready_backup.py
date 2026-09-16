#!/usr/bin/env python3
"""Save each meeting summary to a local file as soon as it's ready.

Subscribes to summary.completed (the summary-ready trigger), and on each new
event fetches the summary with the resolved token and writes it to
./summaries/<meeting_id>.json. This only reads and saves locally -- no
write-back to Meetily is involved, so no write-scoped token is needed.

Unsupported example code -- see meetily_agent/__init__.py. This is a stub:
extend on_event() if you need something more than "save it to a file".
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from meetily_agent import LocalWebhookReceiver, MeetilyClient, discover_token  # noqa: E402

RECEIVER_PORT = 9002
WEBHOOK_URL = f"http://127.0.0.1:{RECEIVER_PORT}/webhook"
OUTPUT_DIR = Path("./summaries")


def save_summary(client: MeetilyClient, event: dict) -> None:
    meeting_id = event.get("resource", {}).get("id")
    if not meeting_id:
        print(f"event {event.get('event_id')} has no resource id, skipping")
        return

    summary = client.get(f"/v1/meetings/{meeting_id}/summary")

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
    registration = client.post(
        "/v1/webhooks",
        {"url": WEBHOOK_URL, "events": ["summary.completed"], "delivery_mode": "at-least-once"},
    )
    webhook_id = registration["id"]
    secret = registration["hmac_secret"]  # returned once; not persisted here
    print(f"Webhook id: {webhook_id}")

    status = client.get(f"/v1/webhooks/{webhook_id}")
    if status.get("approval_state") == "pending":
        print(
            "approval_state=pending -- this destination will deliver nothing until "
            "you approve it under Destinations in the app."
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
        client.delete(f"/v1/webhooks/{webhook_id}")
        print(f"Deleted webhook {webhook_id}")


if __name__ == "__main__":
    main()
