# curl examples

Register and verify a Meetily webhook using only `curl` and `openssl` --
useful for a quick sanity check before writing any code.

## Prerequisites

- Meetily desktop app running with **Settings > Pro > Integrations** enabled.
- A key with the `read` scope in `MEETILY_PRO_TOKEN`. Mint one in the app
  (Settings > Pro > Integrations), or use the loopback token file directly
  for read-only testing (see the main [README](../../README.md)).
- `python3` on PATH (used only to pull `id` and `hmac_secret` out of the
  JSON response -- no other dependency).

## Files

- `subscribe-and-verify.sh` -- registers a `recording.stopped` webhook and
  saves the one-time `hmac_secret` to a `0600` file.
- `verify.sh` -- checks a received delivery's `X-Meetily-Signature` header
  against the saved secret, using `openssl dgst -hmac`.

## Run it

```bash
export MEETILY_PRO_TOKEN=...   # a key with the 'read' scope

./subscribe-and-verify.sh http://127.0.0.1:9000/webhook
```

If `127.0.0.1:9000` is not already in the app's local webhook target
allowlist, add it under **Settings > Pro > Integrations > Local webhook
targets** and **restart Meetily** -- the allowlist is only read at startup.

A destination that is not loopback/allowlisted starts as
`approval_state=pending` and delivers nothing until you approve it under
**Destinations** in the app. Check status with:

```bash
curl -H "Authorization: Bearer $MEETILY_PRO_TOKEN" \
  http://127.0.0.1:8420/v1/webhooks/<id>
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
