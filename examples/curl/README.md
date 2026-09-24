# curl examples

Register and verify a Meetily webhook using only `curl` and `openssl` --
useful for a quick sanity check before writing any code.

## Prerequisites

- Meetily desktop app running with the Automation API turned on (main [README > Setup](../../README.md#setup-turn-it-on)).
- A token in `MEETILY_PRO_TOKEN` -- see [Token first](#token-first).
- `python3` on PATH (used only to pull `id` and `hmac_secret` out of the
  JSON response -- no other dependency).

## Token first

Every call needs a token, and the token decides what the script may do:

- **Read-only (these examples):** the loopback token works. Turn on **Allow
  the CLI on this computer** in **Settings > Integrations**, then load the
  loopback token file into the variable the scripts read:
  ```bash
  # macOS; Windows: %APPDATA%\pro.meetily.ai\gateway-token,
  # Linux: $XDG_DATA_HOME/pro.meetily.ai/gateway-token
  export MEETILY_PRO_TOKEN="$(cat ~/Library/Application\ Support/pro.meetily.ai/gateway-token)"
  ```
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

## Files

- `subscribe-and-verify.sh` -- registers a `recording.stopped` webhook and
  saves the one-time `hmac_secret` to a `0600` file.
- `verify.sh` -- checks a received delivery's `X-Meetily-Signature` header
  against the saved secret, using `openssl dgst -hmac`.

## Run it

```bash
export MEETILY_PRO_TOKEN=...   # loopback token or a key you created (see Token first)

./subscribe-and-verify.sh http://127.0.0.1:9000/webhook
```

Before running it, add `127.0.0.1:9000` under **Settings > Integrations >
Advanced > Local targets** -- it takes effect immediately, no restart needed.
A loopback or private receiver that isn't listed there is refused at
registration with `400 bad_request` ("url host is not allowed
(loopback/private)").

If the subscribe call fails, the response body is the real error envelope,
`{"error":{"code":"...","message":"...","retryable":false}}`. The script
prints the failing code for you; the ones you'll hit while wiring this up:

- `401 unauthorized` -- the token is missing, unknown, expired, or revoked.
  Create a key in **Settings > Integrations > Apps & scripts**.
- `403 consumer_disabled` -- the key exists but its **Allow** switch is off
  (every key starts off). Turn it on in **Settings > Integrations**.
- `409 webhooks_disabled` -- the **Webhook delivery** door is off. Turn it
  on under **Settings > Integrations > Advanced**.

None of these is retryable by itself (`retryable: false`) -- fix the setting, then
re-run the script.

Registering does not wait for approval. The first webhook a token registers
to a host comes back `201` with `approval_state=pending` and delivers nothing
until you **Allow** it in
the **Waiting for you** strip at the top of **Settings > Integrations** (or
later under **Advanced > Destinations**). Approval is per token and host, so
later webhooks from the same token to that host come back `allowed` right
away. Check status with:

```bash
curl -H "Authorization: Bearer $MEETILY_PRO_TOKEN" \
  http://127.0.0.1:8420/v1/webhooks/<id>
```

Once it is `allowed`, you can fire a test delivery. Before approval this
returns `409 host_not_approved`:

```bash
curl -X POST -H "Authorization: Bearer $MEETILY_PRO_TOKEN" \
  http://127.0.0.1:8420/v1/webhooks/<id>/test
```

When an event arrives at your receiver, capture the raw request body and the
`X-Meetily-Signature` / `X-Meetily-Timestamp` headers, then check the
signature by hand:

```bash
./verify.sh ./webhook-secret.txt "$TIMESTAMP" ./payload.json "$SIGNATURE"
```

Clean up your webhook when you're done:

```bash
curl -X DELETE -H "Authorization: Bearer $MEETILY_PRO_TOKEN" \
  http://127.0.0.1:8420/v1/webhooks/<id>
```

## Notes

- Delivery is best-effort, at-least-once, up to 6 attempts while the app
  runs. You may see duplicate deliveries of the same `event_id`; a real
  receiver must be idempotent on it.
- A 2xx response from your receiver means "accepted", not "your automation
  succeeded".
- The event body carries no transcript or summary text -- fetch content with
  your token, e.g. `GET /v1/meetings/{id}`.
