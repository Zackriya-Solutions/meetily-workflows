# curl snippets

These scripts register a webhook and verify a delivery captured by **your own
HTTP receiver**. They do not start a receiver. For an example that registers
and listens without extra code, use the [Python summary backup](../python/README.md);
it creates its own webhook and cannot receive deliveries for this one.

## Prerequisites

- Meetily Pro 1.11.0+ with the Automation API and **Outgoing (webhooks)** on.
  See [Setup](../../README.md#setup-turn-it-on).
- A Read-scoped token exported as `MEETILY_PRO_TOKEN` ([token setup](../../README.md#tokens-pick-the-right-one-first)).
- A receiver already listening at your chosen URL that can save the **raw**
  request body and the `X-Meetily-Timestamp` and `X-Meetily-Signature` headers.
  For a loopback/private URL, add its `host:port` under **Settings >
  Integrations > Advanced > Local targets** before registration.
- Bash, curl, OpenSSL, and Python 3. On Windows use Git Bash; if Python is
  installed as `python`, run `export PYTHON=python` first.

## Register

From the repo root, replace the URL with your receiver's address:

```bash
cd examples/curl
./subscribe-and-verify.sh http://127.0.0.1:9000/webhook
```

The script prints a webhook ID and saves its one-time secret to
`./webhook-secret.txt` without printing it. On POSIX it uses mode `0600`;
on Windows keep the file in a directory private to your account.
The first destination for a token/host starts `pending`: **Allow** it under
**Settings > Integrations > Waiting for you** (or **Advanced > Destinations**).
Registration alone does not deliver anything.

## Verify a delivery

Use the printed webhook ID to send a test event after approval:

```bash
WEBHOOK_ID='<printed webhook id>'
curl -sS -X POST -H "Authorization: Bearer $MEETILY_PRO_TOKEN" \
  "http://127.0.0.1:8420/v1/webhooks/$WEBHOOK_ID/test"
```

Your receiver must capture the delivered body **byte for byte**, without
re-serializing JSON, for example as `payload.json`. Copy the literal header
values it received, then check them locally:

```bash
TIMESTAMP='<X-Meetily-Timestamp value>'
SIGNATURE='<X-Meetily-Signature value>'
./verify.sh ./webhook-secret.txt "$TIMESTAMP" ./payload.json "$SIGNATURE"
```

`OK: signature matches` verifies those bytes. A test event contains no
meeting content. A real `recording.stopped` event means capture ended, not
that the transcript is ready; fetch content separately with your token.
Deliveries may repeat, so production receivers must deduplicate `event_id`.

## Clean up

```bash
curl -sS -X DELETE -H "Authorization: Bearer $MEETILY_PRO_TOKEN" \
  "http://127.0.0.1:8420/v1/webhooks/$WEBHOOK_ID"
rm -f webhook-secret.txt payload.json
```

The default secret and example payload filename are Git-ignored, but keep
secrets and meeting-content exports outside this repository for regular use.
