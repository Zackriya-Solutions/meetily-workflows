# Python examples

Two small scripts built on the vendored `meetily_agent` helper
(`../../meetily_agent/`). Stdlib only, no dependencies to install.

## Prerequisites

- Meetily desktop app running with **Settings > Pro > Integrations** enabled.
- A token available via `MEETILY_PRO_TOKEN` or the loopback token file (see
  the main [README](../../README.md)). `discover_token()` finds it
  automatically.
- If `127.0.0.1:9001` / `127.0.0.1:9002` are not already in the app's local
  webhook target allowlist, add them under **Settings > Pro > Integrations >
  Local webhook targets** and **restart Meetily** first -- the allowlist is
  only read at startup.
- Python 3.9+.

## brief_on_recording_stopped.py

Subscribes to `recording.stopped` (the recording-ends trigger). On each new
event, fetches the meeting and its transcript and prints a short preview.
Idempotent on `event_id`. Deletes its webhook on exit (Ctrl-C).

```bash
python3 brief_on_recording_stopped.py
```

## summary_ready_backup.py

Subscribes to `summary.completed` (the summary-ready trigger). On each new
event, fetches the summary and writes it to `./summaries/<meeting_id>.json`.
Read-only against Meetily -- no write-scoped token needed. This is a stub:
extend `save_summary()` if you want to do more than save a file.

```bash
python3 summary_ready_backup.py
```

## Notes

- Both scripts run from any directory; they add the repo root to `sys.path`
  themselves to import `meetily_agent` without installing it.
- Delivery is best-effort at-least-once. You may see the same `event_id`
  more than once; both scripts rely on `LocalWebhookReceiver`'s in-memory
  dedup, which only protects against re-delivery within one run.
- A destination that is not loopback/allowlisted starts as
  `approval_state=pending` and delivers nothing until approved under
  **Destinations** in the app. Both scripts print a note if that's the case.
