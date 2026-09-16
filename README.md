# Meetily Workflows Examples

This repo is an examples hub for building automations against the **Meetily
Agent API as it ships today** -- the local HTTP API, CLI, MCP server, and
webhooks that already exist in the Pro app. It shows the patterns (subscribe
to an event, verify it, fetch the content you need, act on it) with small,
runnable examples in a few languages/tools.

It is **not** the Workflows product. Meetily Workflows (workflow
definitions, connectors, a manifest schema, an execution engine) is a
separate, next-release product. This repo does not scaffold any of that --
see [Open question](#open-question-whats-next) below.

## The frozen trigger catalogue

These are the trigger ids you can build on today, the backing event each one
maps to, and whether that event actually fires in the current release.

| Trigger id | Backing event | State |
|---|---|---|
| recording-ends | `recording.stopped` | LIVE |
| summary-ready | `summary.completed` | LIVE |
| import-finishes | `job.completed` (for an import job) | LIVE |
| transcript-ready | `transcription.completed` | **DORMANT** -- no producer this release |

Do not subscribe to `transcription.completed` expecting it to fire. It is a
reserved trigger id with no event producer behind it in this release.

## Build against the API today

Every example in this repo follows the same shape:

1. **Subscribe** -- `POST /v1/webhooks` with the URL you want events
   delivered to and the events you want (`recording.stopped`,
   `summary.completed`, `job.completed`, ...).
2. **Verify** -- check `X-Meetily-Signature` (HMAC-SHA256 over
   `"{timestamp}.{body}"`, using the `X-Meetily-Timestamp` header) against
   the `hmac_secret` you got back at registration, with a constant-time
   comparison.
3. **Dedup** -- key on the event's `event_id`. Delivery is at-least-once, so
   you can and will see the same event more than once.
4. **Fetch content** -- the event body is notification-only; it has no
   transcript or summary text. Use your token to fetch what you need, e.g.
   `GET /v1/meetings/{id}`, its transcript, or its summary.
5. **Act** -- do whatever your automation does with that content.

### Event envelope

```json
{
  "schema_version": "...",
  "event_id": "...",
  "event": "recording.stopped",
  "occurred_at": "...",
  "resource": { "kind": "meeting", "id": "..." },
  "delivery_id": "..."
}
```

`event_id` is the dedup key. `resource.id` is what you fetch content for.

## Prerequisites

1. Meetily Pro.
2. Enable **Settings > Pro > Integrations**.
3. Get a token, either:
   - the `meetily-pro` CLI (reads the loopback token automatically), or
   - mint a scoped key in the app (Settings > Pro > Integrations) for
     anything that needs to write, since the loopback token file is
     read-only.
4. If you're registering a webhook to a non-public destination, add its
   `host:port` to **Local webhook targets** in Settings > Pro > Integrations
   and **restart Meetily** -- that allowlist is read once at startup.
5. Approve the destination under **Destinations** in the app. Any
   destination that isn't loopback/pre-approved starts as
   `approval_state=pending` (`GET /v1/webhooks/{id}`) and delivers nothing
   until you approve it.

### Token resolution order

1. `--token-file` (an explicit path, if the tool you're using takes one)
2. `MEETILY_PRO_TOKEN` environment variable
3. The loopback token file for your OS:
   - macOS: `~/Library/Application Support/pro.meetily.ai/gateway-token`
   - Windows: `%APPDATA%\pro.meetily.ai\gateway-token`
   - Linux: `$XDG_DATA_HOME/pro.meetily.ai/gateway-token`

The loopback token file is loopback-only and read-only. To write anything
back (for example `PUT /v1/meetings/{id}/summary`), mint a `write`-scoped
key in the app and pass it via `MEETILY_PRO_TOKEN`.

### Scopes

`read`, `record`, `write`, `delete`. There is no `admin` scope. Subscribing
to a webhook needs `read`; writing a summary back needs `write`.

## Where the contracts come from

This README and these examples are a convenience layer, not the source of
truth. When in doubt, check:

- https://docs.meetily.ai/developers
- `GET /openapi.json` on your running instance

## Unsupported: the vendored helper

`meetily_agent/` is a small, stdlib-only Python helper vendored into this
repo so the Python examples don't need a dependency. It is **not**
published to PyPI, has no versioning or support guarantees, and is not the
supported way to talk to the Agent API. The supported client is the
`meetily-pro` CLI. Copy what you need out of `meetily_agent/` into your own
project; don't depend on it as a package.

## Honest copy

A few things worth saying plainly, because they're easy to assume away:

- **"Nothing leaves the machine" is only true for a loopback receiver.** A
  LAN or remote receiver means events (and whatever your automation does
  with the content it fetches) leave the machine.
- **Delivery is best-effort, at-least-once, up to 6 attempts** (backoff
  1/2/4/8/16s) while the app is running. Duplicates are possible, events can
  be lost, and nothing is ever replayed after a restart. Handlers must be
  idempotent, keyed on `event_id`.
- **A 2xx from your receiver means "accepted," not "your automation
  succeeded."** Meetily doesn't know or care what you did after you returned
  200.
- **Write-back can cost money.** Consenting to a write (for example
  regenerating and saving a summary) can consume hosted LLM credits.
- **This does not make recording faster or slower.** No automation built on
  this API can affect the audio/transcription pipeline's speed -- don't
  claim otherwise in anything you build on top of it.
- **Enterprise features are out of scope here.** This repo only documents
  what's available in Meetily Pro.

## Open question: what's next

The long-term shape of "workflows" for Meetily -- workflow definitions or
templates, a connector model, a manifest schema, an execution engine -- is
deferred to the Workflows product, which ships in a later release. This
repo intentionally does not guess at that shape. When it ships, expect this
repo's scope to either fold into that product's own examples or stay
focused on the raw API/CLI/MCP/webhook layer underneath it.

## License

MIT, see [LICENSE](LICENSE).
