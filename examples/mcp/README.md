# MCP example

Meetily can expose itself to an MCP-capable assistant (Claude Desktop,
Claude Code, or any other MCP client) as a local MCP server. No code needed
here, just the CLI command and a couple of prompts to try.

## Install

```bash
meetily-pro mcp install
```

This does not install anything by itself -- it is a handoff. Meetily is the
single owner of assistant registration, so `install` only prints the
`mcpServers` entry the app will write plus the name of the screen where you
actually connect an assistant: **Settings > Integrations > AI assistants
(MCP)**. It never mints a token or touches your client config, and its
`--record` / `--write` flags are accepted but do nothing.

Open that screen and press **Connect** next to your assistant. The app
mints a scoped, per-client token and writes the `mcpServers` entry for you.
The token starts read-only -- Record, Write, and Delete are each a separate
opt-in you make in the app, not on the command line. Restart the assistant
afterwards so it picks up the new server.

If you'd rather write the client config entry by hand, this is the shape
the app writes:

```json
{
  "mcpServers": {
    "meetily": {
      "command": "<path to the meetily-pro binary>",
      "args": ["mcp", "--server", "http://127.0.0.1:8420", "--token-file", "<path the app gives you>"]
    }
  }
}
```

The server is **read-first**: by default it exposes read-oriented resources
and tools (meetings, transcripts, summaries). Deletes are never exposed
through MCP, regardless of scope.

To run the server itself in strictly read-only mode (hide and refuse every
record/write tool, no matter what the token is scoped to), pass
`--read-only` to the serve command -- not to `install`, which has no such
flag:

```bash
meetily-pro mcp --read-only
```

For diagnostics (gateway reachable, Pro license tier, token scopes, with
remediation), run:

```bash
meetily-pro mcp doctor
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
