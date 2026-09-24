# Python examples

Two small scripts built on the vendored `meetily_agent` helper
(`../../meetily_agent/`). Stdlib only, no dependencies to install.

## Prerequisites

- Meetily desktop app running with the Automation API turned on (main [README > Setup](../../README.md#setup-turn-it-on)).
- A token -- see [Token first](#token-first). `discover_token()` finds it
  automatically (`MEETILY_PRO_TOKEN`, then the loopback token file).
- If `127.0.0.1:9001` / `127.0.0.1:9002` are not already in the app's local
  webhook target allowlist, add them under **Settings > Integrations >
  Advanced > Local targets** *before* running the script -- it takes effect
  immediately, no restart needed. Without it, registration fails with
  `400 bad_request` ("url host is not allowed (loopback/private)").
- Python 3.9+.

## Token first

Every call needs a token, and the token decides what the script may do:

- **Read-only (these examples):** the loopback token works. Turn on **Allow
  the CLI on this computer** in **Settings > Integrations**; `discover_token()` then
  finds the loopback token file on its own.
- **Anything that records, writes, or deletes** (start/stop recording, save
  or regenerate a summary, control jobs, delete a meeting): the loopback
  token is Read-only and gets `403 insufficient_scope`. Create a key instead:
  1. **Settings > Integrations > Apps & scripts > Create key**; tick only the
     scope you need (Record / Write / Delete).
  2. Copy the secret -- it is shown once.
  3. Turn on the key's **Allow** switch (keys start off; an off key gets
     `403 consumer_disabled`).
  4. `export MEETILY_PRO_TOKEN='<the secret>'`, then check it with
     `meetily-pro whoami`.

Full table of which scope each route needs: main
[README > Tokens](../../README.md#tokens-pick-the-right-one-first).

## brief_on_recording_stopped.py

Subscribes to `recording.stopped` (the recording-ends trigger). On each new
event, waits 10 seconds (the meeting's title and transcript finish saving a
few seconds after capture stops), then fetches the meeting and its transcript
and prints a short preview. Idempotent on `event_id`. Deletes its webhook on
exit (Ctrl-C).

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
- `LocalWebhookReceiver` answers `200` as soon as a delivery's signature
  checks out, then runs your callback on a background thread. Meetily gives
  each delivery 5 seconds, so slow work in the callback (fetching, calling
  an LLM) won't cause timeouts or retries.
- The first webhook a token registers to a host starts as
  `approval_state=pending` and delivers nothing until approved under
  the **Waiting for you** strip at the top of **Settings > Integrations** (or
  later under **Advanced > Destinations**). Both scripts print a note if
  that's the case.
