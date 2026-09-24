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
`mcpServers` entry the app will write plus a pointer to the app screen. It
never mints a token or touches your client config, and its `--record` /
`--write` flags are accepted but do nothing.

## Token: Connect mints it for you

The MCP server needs a token like every other client, but you don't create
it by hand. In **Settings > Integrations > AI assistants (MCP)**, press
**Connect** next to your assistant. The app mints a scoped token just for
that assistant and writes the `mcpServers` entry for you. Restart the
assistant afterwards so it picks up the new server.

That token starts **read-only**. If you want the assistant to start/stop
recording or to write (rename meetings, save or regenerate summaries,
control jobs), turn on **Record (start/stop mic)** and/or **Write** for that assistant in the
app -- there is no command-line flag for it. Delete is never available
through MCP. A tool call the token isn't scoped for fails with
`insufficient_scope`.

If you'd rather write the client config entry by hand, this is the shape
the app writes (macOS path shown). The token file is the one the app minted for that
assistant, so it's simplest to let **Connect** write it:

```json
{
  "mcpServers": {
    "meetily": {
      "command": "/Applications/Meetily Pro.app/Contents/MacOS/meetily-pro",
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
