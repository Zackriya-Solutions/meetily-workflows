# Contributing

There are two ways to contribute:

1. **Add a community workflow** to the catalog (a manifest that points to your own code).
2. **Improve the examples** (`examples/`) or the vendored helper (`meetily_agent/`).

Most contributions are the first kind. This guide covers it.

## Add a community workflow

Your workflow's **code lives in your own repo**. Here you add a small **manifest**
that catalogs it. The catalog table in the READMEs is generated from these
manifests -- you never edit the table by hand.

### 1. Build a workflow that runs against the shipping API

Use only what ships today -- the HTTP API, the `meetily-pro` CLI, the MCP server,
or webhooks (see the main [README](README.md)). It runs standalone; it does
**not** integrate with the Meetily app in this version.

Follow the standard shape: **subscribe -> verify the HMAC -> dedup on `event_id`
-> fetch content with your token -> act.** Handle a `pending` destination, be
idempotent, and remember a `2xx` from your receiver means "accepted," not
"succeeded."

### 2. Add a manifest

Create `community-workflows/<your-id>/manifest.yaml` (the folder name must equal
`id`). It is validated against
[`manifest.schema.json`](community-workflows/manifest.schema.json).

```yaml
manifest_version: 1
id: my-workflow                 # unique slug == folder name
name: My Workflow
description: One line on what it does.
author: you (github.com/you)
language: python                # python | typescript | bash | other
trigger: summary-ready          # recording-ends | summary-ready | import-finishes | manual | scheduled
scopes: [read]                  # read | record | write | delete
source_url: https://github.com/you/your-repo
ref: v1.0.0                     # optional: pin a tag/commit
entry: run.py                   # path within source_url
run: "python run.py"            # how to run it standalone
meetily_min_version: "1.9.3"    # optional
tags: [slack, summary]          # optional
license: MIT                    # optional
```

Notes:
- **`trigger`** must be a live frozen id (`recording-ends`, `summary-ready`,
  `import-finishes`) or `manual` / `scheduled` for non-event tools.
  `transcript-ready` is **not accepted yet** -- it is dormant (no producer in this
  release).
- **Any language** is fine as long as it speaks the shipping surface; declare it
  in `language` and give the exact `run` command.

### 3. Regenerate the catalog

```bash
pip install pyyaml jsonschema
python scripts/generate_catalog.py
```

This validates your manifest and rewrites the catalog table in the root README
and `community-workflows/README.md`. Commit the result.

### 4. Open a PR and complete the checklist

The PR template includes a **conformance checklist** -- fill it in. A maintainer
reviews the manifest and your linked code (and may run it) before listing it.

## Conformance checklist (what "runs properly" means here)

- [ ] Uses only the shipping Agent API / CLI / MCP / webhooks (nothing unshipped or app-integrated).
- [ ] Follows subscribe -> verify HMAC -> dedup on `event_id` -> fetch -> act (for event workflows).
- [ ] Idempotent; safe against duplicate and lost deliveries.
- [ ] Handles a `pending` destination (delivers nothing until approved).
- [ ] Declares the real `scopes` it needs; nothing more.
- [ ] Runs standalone; documents its setup (token, local webhook target, etc.).
- [ ] If `scopes` includes `record`, `write`, or `delete`: the README walks through creating that key (**Settings > Integrations > Apps & scripts > Create key**, tick the scope, copy the secret, turn on **Allow**, pass it via `MEETILY_PRO_TOKEN` or `--token-file`). The loopback token is Read-only and will get `403 insufficient_scope`.
- [ ] Tested against a real Meetily instance.
- [ ] `manifest.yaml` validates; `scripts/generate_catalog.py` run and committed.

## Validation

`scripts/generate_catalog.py --check` validates every manifest against the schema
and fails if the generated table is stale. It is wired as a **manually triggered**
CI workflow (`Validate catalog`, `workflow_dispatch`) that a maintainer runs
before merging; you can also run it locally. **CI never executes contributor code.**

## Out of scope

The catalog manifest is **metadata only**. Do **not** add a workflow *execution
engine*, a connector framework, or the full `wf/` execution manifest -- those are
the separate, next-release Workflows product. This repo catalogs workflows and
demonstrates the shipped API/CLI/MCP/webhook layer; it does not run workflows for
you.

## Improving examples or the helper

Small, stdlib-only, honest about limits. The `meetily_agent/` helper is
**unsupported** example code, not a published SDK. Keep changes minimal and match
the existing style.

## Where the contracts come from

- https://docs.meetily.ai/developers
- `GET /openapi.json` on a running instance

If this repo disagrees with those, the docs and the live `openapi.json` win.
