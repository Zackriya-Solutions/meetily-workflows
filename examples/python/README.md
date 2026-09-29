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
- Turn on **Outgoing (webhooks)** under **Settings > Integrations > Advanced**.
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

`recording.stopped` means capture ended, **not** that the transcript is ready.
This script waits 10 seconds and prints a best-effort preview; text or title
may still be missing or partial. From the repository root:

```bash
python3 examples/python/brief_on_recording_stopped.py
```

Leave it running and stop a recording. If the destination is `pending`, allow
it in **Settings > Integrations > Waiting for you**. The output is a snapshot,
not confirmation of saved content. For a finished summary, watch
`summary.completed` instead; there is no callable saved-recording observation
route yet. Ctrl-C deletes the webhook.

## summary_ready_backup.py

The runnable first-party [catalog example](../../community-workflows/README.md)
listens for `summary.completed` and saves `./summaries/<meeting_id>.json` in
your working directory. It only needs Read access. From the repository root:

```bash
python3 examples/python/summary_ready_backup.py
```

Allow a `pending` destination in **Settings > Integrations > Waiting for you**,
then generate a summary. Look for `saved summary for <id> -> ...`; a
regeneration warning means the file contains the prior summary. Ctrl-C deletes
the webhook. Exports contain meeting content: use a private location outside
the repo for regular use (`OUTPUT_DIR` in the script). The default `summaries/`
directory is Git-ignored, not encrypted.

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
