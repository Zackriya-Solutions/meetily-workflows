<!--
Adding a community workflow? Keep this template.
Fixing an example or the helper? You can delete the checklist below and just
describe the change.
-->

## What is this?

<!-- One or two lines. For a catalog entry: what the workflow does and where its code lives. -->

## Community workflow checklist

Fill this in if you are adding a `community-workflows/<id>/manifest.yaml`.

- [ ] Code lives in **my own repo**; this PR only adds a manifest (no workflow code hosted here).
- [ ] `manifest.yaml` is in a folder whose name equals its `id`.
- [ ] Uses **only** the shipping Agent API / CLI / MCP / webhooks (nothing unshipped, no app integration).
- [ ] Event workflows follow **subscribe → verify HMAC → dedup on `event_id` → fetch → act**.
- [ ] **Idempotent**; safe against duplicate and lost deliveries.
- [ ] Handles a **`pending`** destination (delivers nothing until approved).
- [ ] Declares the **real `scopes`** it needs, and nothing more.
- [ ] Runs **standalone**; setup (token, local webhook target, etc.) is documented at `source_url`.
- [ ] **Tested against a real Meetily instance.**
- [ ] Ran `python scripts/generate_catalog.py` and committed the updated catalog tables.
- [ ] `trigger` is a live id (`recording-ends` / `summary-ready` / `import-finishes`) or `manual` / `scheduled` (not `transcript-ready`).

## Notes for the maintainer

<!-- Anything the reviewer should know: how to run it, what it connects to, etc. -->
