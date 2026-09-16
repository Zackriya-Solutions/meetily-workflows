# MCP example

Meetily can expose itself to an MCP-capable assistant (Claude Desktop,
Claude Code, or any other MCP client) as a local MCP server. No code needed
here, just the CLI command and a couple of prompts to try.

## Install

```bash
meetily-pro mcp install
```

This merges a Meetily MCP server entry into your assistant's client config
and mints a scoped token for it. Restart the assistant afterwards so it
picks up the new server.

The server is **read-first**: by default it exposes read-oriented resources
and tools (meetings, transcripts, summaries). Deletes are never exposed
through MCP, regardless of scope.

To force a strictly read-only token (no record/write tools at all), install
with:

```bash
meetily-pro mcp install --read-only
```

## Example prompts

Once the server is installed and your assistant has been restarted, try:

- "Summarize my last meeting."
- "List action items from today's standup."

The assistant will use the Meetily MCP resources/tools to look up the
meeting, pull its summary or transcript, and answer from that -- no manual
API calls needed.

## Notes

- The same honest-copy caveats from the main [README](../../README.md) apply
  here: a 2xx / a successful tool call means the assistant got the data, not
  that any downstream automation you build on top of it "worked."
- Requesting a summary regeneration (rather than reading an existing one) can
  consume hosted LLM credits, same as it would from the app.
- This repo does not document enterprise-only MCP features.
