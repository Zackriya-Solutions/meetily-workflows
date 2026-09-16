# Contributing

This repo collects small, working examples of building automations against the
Meetily Agent API as it exists today. It is not a framework and it is not a
preview of the Workflows product.

## Adding an example

1. Pick a directory under `examples/` that matches the language or tool
   (`curl/`, `python/`, `mcp/`, or a new one if none fits).
2. Keep it self-contained: one README explaining what it does and how to run
   it, plus the minimum code or script needed.
3. Use only real, frozen contract values: the endpoints, event names, and
   scopes documented in the main [README](README.md) trigger catalogue. Do
   not invent endpoints, event names, or fields that are not in the docs.
4. If your example needs a webhook, show the full lifecycle: register, verify
   the HMAC signature, dedup on `event_id`, and delete the webhook when done.
5. Call out any caveat from the honest-copy section of the README that
   applies to your example (loopback vs. remote receivers, at-least-once
   delivery, "accepted" vs "done", credit usage on write-back).

## Frozen contracts only, no manifest or engine

Do not add a workflow manifest schema, a workflow definition format, a
connector abstraction, or anything resembling an execution engine. Those
belong to the Workflows product, which ships separately and is out of scope
here. This repo only demonstrates calling the API, CLI, MCP server, and
webhooks that are already shipped.

## Where the contracts come from

The source of truth for endpoints, scopes, and event payloads is:

- https://docs.meetily.ai/developers
- `GET /v1/openapi.json` on a running instance

If something in this repo disagrees with those, the docs and the live
`openapi.json` win. Please file an issue or fix the example instead of
extending it to cover the gap.
