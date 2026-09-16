# Meetily Workflows Examples

This repo is an examples hub for building automations against the **Meetily
Agent API as it ships today** -- the local HTTP API, `meetily-pro` CLI, MCP
server, and webhooks that already exist in the Pro app. It shows the pattern
(subscribe to an event, verify it, fetch the content you need, act on it) with
small, runnable examples.

It is **not** the Workflows product. Meetily Workflows (workflow definitions,
connectors, a manifest schema, an execution engine) is a separate, next-release
product. This repo does not scaffold any of that -- see
[Open question](#open-question-whats-next).

> **Availability:** the Meetily Agent API (and the automations you build on it)
> is a **Meetily Pro** feature today. Support for the **Community (open-source)
> edition** is coming soon.

> Full developer documentation: **https://docs.meetily.ai/developers**. The
> tables below are a quick reference; the docs site and `GET /openapi.json` are
> the source of truth.

## Setup: turn it on

Everything is under **Settings > Integrations** (its own tab; it is a Pro
feature). The screenshots below are macOS; the Windows layout is equivalent.

**1. Turn on the Automation API.** Expand **Advanced** and flip the **Automation
API** master switch, then **restart Meetily**. Turning it off later closes the
ports and stops every assistant and key, but recording/transcription/summary
keep running.

![Automation API master switch and the doors panel](docs/images/enable-automation-api.png)

**2. Allow the CLI.** Under **Apps & scripts**, the auto-created **`loopback`**
key (Meetily's own, Read) starts **"Not allowed yet"**. Turn on its **Allow**
toggle so the `meetily-pro` CLI on this computer can connect.

![Apps & scripts: the loopback key with its Allow toggle](docs/images/allow-cli.png)

**3. Create a scoped key** (for a script/app). Click **+ Create key**, choose
permissions (Read is always on; add Record/Write/Delete as needed), and set
reach + expiry under **More options**.

![Create a key dialog](docs/images/create-key.png)

The secret is shown **once** -- copy it now. Then turn on **Allow** for the new
key too (every key starts off).

![The new key's one-time secret](docs/images/new-key-secret.png)

**4. Enable webhook delivery.** In **Advanced**, turn on the **Webhook
delivery** door. To deliver to a receiver on this machine, add its `host:port`
(e.g. `127.0.0.1:8787`) under **Local targets** and **restart Meetily** -- the
allowlist is read once at startup.

![Webhook delivery door and Local targets](docs/images/webhook-delivery.png)

**5. Approve the destination.** After a key registers a webhook, Meetily shows a
**"Waiting for you"** banner. Approve it so its `approval_state` becomes
`allowed` -- only `allowed` delivers, and a `pending` destination fails
silently.

![Approve the webhook destination](docs/images/approve-destination.png)

To connect an AI assistant instead, use the **AI assistants (MCP)** section and
click **Connect** on a detected client (Claude Desktop, Claude Code, Cursor, ...).

![AI assistants Connect list](docs/images/connect-assistant.png)

Full walkthrough (both platforms, plus pairing a remote device):
**https://docs.meetily.ai/developers/enable-and-connect**

## The frozen trigger catalogue

The trigger ids you can build on today, the backing event each maps to, and
whether that event fires in the current release:

| Trigger id | Backing event | State |
|---|---|---|
| `recording-ends` | `recording.stopped` | LIVE |
| `summary-ready` | `summary.completed` | LIVE |
| `import-finishes` | `job.completed` (import job) | LIVE |
| `transcript-ready` | `transcription.completed` | **DORMANT** -- no producer this release |

Do not subscribe to `transcription.completed` expecting it to fire; it is
reserved with no producer behind it yet.

## Build against the API today

Every example follows the same shape:

1. **Subscribe** -- `POST /v1/webhooks` with your receiver URL and the events you want.
2. **Verify** -- check `X-Meetily-Signature` (HMAC-SHA256 over `"{timestamp}.{body}"`, using `X-Meetily-Timestamp`) against the `hmac_secret` from registration, constant-time.
3. **Dedup** -- key on `event_id`. Delivery is at-least-once; you can see an event more than once.
4. **Fetch content** -- the event is notification-only. Use your token to fetch, e.g. `GET /v1/meetings/{id}`, its transcript, or its summary.
5. **Act** -- do whatever your automation does.

### Event envelope

```json
{
  "schema_version": 1,
  "event_id": "...",
  "event": "recording.stopped",
  "occurred_at": "...",
  "resource": { "kind": "meeting", "id": "..." },
  "delivery_id": "..."
}
```

`event_id` is the dedup key; `resource.id` is what you fetch content for. No
transcript or summary text is ever in the envelope.

## Quick reference

Brief tables; full detail on the docs site linked under each.

### Scopes

| Scope | Grants | Notes |
|---|---|---|
| `read` | See meetings, transcripts, summaries, status, and receive notifications | Always on for any key |
| `record` | Start / stop / pause / resume recording | Implies `read` |
| `write` | Edit titles/labels, set/regenerate summaries, control jobs, run imports, change some settings | Implies `read`; regeneration can spend hosted LLM credits |
| `delete` | Delete a meeting (audio/video files are a separate opt-in) | Stands alone; never on a paired device; never an MCP tool |

There is **no `admin` scope** -- administration is desktop-UI only. Every key
(and paired device) is off until you turn on its **Allow** toggle.
Full: https://docs.meetily.ai/developers/authentication

### CLI (`meetily-pro`)

A thin HTTP client -- one gateway call per command. Token: `--token-file` >
`MEETILY_PRO_TOKEN` > the loopback token file.

| Exit code | Meaning |
|---|---|
| `0` | Success |
| `1` | Error (incl. parse/usage) |
| `2` | Timeout |
| `3` | Cannot connect |
| `4` | Denied (401/403) |

Common commands: `meetily-pro whoami`, `meetings list|get|export`,
`transcript get`, `summary get|set|regenerate`, `jobs list|...`,
`recording start|stop|pause|resume`, `config get|set`, `pair`, `mcp`.
Full: https://docs.meetily.ai/developers/cli

### MCP (`meetily-pro mcp`)

A local stdio Model Context Protocol server wrapping the same gateway (never
touches the DB); inherits the Pro gate and per-route scopes.

| Aspect | Detail |
|---|---|
| Tools | ~34 (read / write / 2 bounded-wait); ~29 advertised by default (webhook tools behind `--allow-webhooks`) |
| Read-only | `meetily-pro mcp --read-only` hides and refuses write tools |
| Delete | Never exposed as a tool, in any mode |
| Install | `meetily-pro mcp install [--write]` mints a scoped per-client token |
| Resources | `meetily://meetings`, `meetily://meeting/{id}`, `meetily://transcript/{id}`, `meetily://summary/{id}` |

`meetily://` (MCP resources) is not `meetilypro://` (the OS deep-link scheme).
Full: https://docs.meetily.ai/developers/mcp

### HTTP API

Base `http://127.0.0.1:8420`. Canonical machine-readable reference:
`GET /openapi.json`.

| Route | Scope | Use |
|---|---|---|
| `GET /v1/whoami` | read | Token identity + scopes |
| `GET /v1/meetings` | read | List meetings |
| `GET /v1/meetings/{id}` | read | One meeting (`{id, title, created_at, updated_at}`) |
| `GET /v1/meetings/{id}/transcript` | read | `{meeting_id, title, segments:[{text, timestamp, ...}]}` |
| `GET /v1/meetings/{id}/summary` | read | `{meeting_id, status, result, updated_at}` |
| `POST /v1/webhooks` | read | Register a webhook |
| `GET /v1/jobs/{id}/wait` (SSE) | read | Wait for a job to finish |
| `GET /v1/recording/wait` (SSE) | read | Wait for recording start/stop |

Error envelope: `{"error":{"code":"...","message":"..."}}` with codes
`not_found`, `bad_request`, `forbidden`, `insufficient_scope`, `conflict`,
`license_required`, `invalid_request`, `internal`.
Full: https://docs.meetily.ai/developers/api-reference

### Webhooks & events

| Aspect | Detail |
|---|---|
| Register | `POST /v1/webhooks` `{"url","events":[...],"delivery_mode":"at-least-once"\|"at-most-once"}` |
| Secret | `hmac_secret` returned once in the `201` |
| Approval | `GET /v1/webhooks/{id}` -> `approval_state` `pending`/`allowed`/`denied`; only `allowed` delivers |
| Signature | `X-Meetily-Signature: sha256=<hex>` over `"{timestamp}.{body}"` + `X-Meetily-Timestamp` |
| Delivery | Best-effort at-least-once, up to 6 attempts (1/2/4/8/16s) while the app runs; duplicates possible; no replay after restart |

The 17 events (all `read`-scoped, notification-only):
`recording.{started,stopped,paused,resumed,failed,error,stop_failed}`,
`job.{submitted,completed,failed,cancelled,paused,resumed,removed}`,
`summary.{completed,failed}`, `transcript.updated`. (`meeting.*` is not
subscribable.) A content-preserving summary-regeneration failure rides
`summary.completed` with a `content_preserved` marker, not `summary.failed`.
Full: https://docs.meetily.ai/developers/webhooks-and-sse and
https://docs.meetily.ai/developers/events

## Prerequisites (recap)

1. Meetily Pro, with **Settings > Integrations** enabled (see [Setup](#setup-turn-it-on)).
2. A token via `MEETILY_PRO_TOKEN` or the loopback token file (`discover_token()` finds it).
3. For a non-public receiver: add its `host:port` to **Local webhook targets** and restart.
4. Approve the destination under **Destinations** (it starts `pending`).

### Token resolution order

1. `--token-file` (explicit path)
2. `MEETILY_PRO_TOKEN` environment variable
3. The loopback token file for your OS:
   - macOS: `~/Library/Application Support/pro.meetily.ai/gateway-token`
   - Windows: `%APPDATA%\pro.meetily.ai\gateway-token`
   - Linux: `$XDG_DATA_HOME/pro.meetily.ai/gateway-token`

The loopback token file is loopback-only and read-only. To write back (e.g.
`PUT /v1/meetings/{id}/summary`), mint a `write`-scoped key and pass it via
`MEETILY_PRO_TOKEN`.

## Unsupported: the vendored helper

`meetily_agent/` is a small, stdlib-only Python helper vendored into this repo
so the Python examples need no dependency. It is **not** on PyPI, has no support
or versioning guarantees, and is **not** the supported client (that's the
`meetily-pro` CLI). Copy what you need out of it; don't depend on it as a
package.

## Honest copy

- **"Nothing leaves the machine" is only true for a loopback receiver.** A LAN/remote receiver means events and any content your automation fetches leave the machine.
- **Delivery is best-effort at-least-once** (6 attempts, 1/2/4/8/16s) while the app runs; duplicates possible, events can be lost, no replay after restart. Handlers must be idempotent on `event_id`.
- **A 2xx from your receiver means "accepted," not "your automation succeeded."**
- **Write-back can cost money** -- regenerating and saving a summary can consume hosted LLM credits.
- **This cannot make recording faster or slower** -- automations run off the hot path; don't claim otherwise.
- **Enterprise/fleet features are out of scope here.**

## Where the contracts come from

This README and the examples are a convenience layer, not the source of truth:

- **https://docs.meetily.ai/developers**
- `GET /openapi.json` on your running instance

## Open question: what's next

The long-term shape of "workflows" for Meetily -- definitions/templates, a
connector model, a manifest schema, an execution engine -- is deferred to the
Workflows product in a later release. This repo does not guess at that shape;
when it ships, expect this repo to either fold into that product's examples or
stay focused on the raw API/CLI/MCP/webhook layer underneath it.

## License

MIT, see [LICENSE](LICENSE).
