# Community workflows

A catalog of community-built automations for the Meetily Agent API. Each entry
is a **manifest** (metadata) that points to the contributor's own code -- **the
code is not hosted here**. The workflows run standalone against the shipping
Agent API / CLI / MCP / webhooks; they do **not** integrate with the app in this
version (no auto-install, no engine). See the repo [README](../README.md) for
the API, and [CONTRIBUTING](../CONTRIBUTING.md) to add your own.

> The manifest format is a forward-compatible subset of the future Workflows
> execution manifest, so entries carry over when that product ships.

## Catalog

<!-- BEGIN CATALOG -->
| Workflow | Trigger | Language | Scopes | Author |
| --- | --- | --- | --- | --- |
| [Summary file backup](https://github.com/Zackriya-Solutions/meetily-workflows) | `summary-ready` | python | read | Meetily (github.com/Zackriya-Solutions) |

_1 community workflow(s). Generated from `community-workflows/*/manifest.yaml` by `scripts/generate_catalog.py` -- do not edit this table by hand._
<!-- END CATALOG -->

## How it works

- Each workflow is one folder: `community-workflows/<id>/manifest.yaml`,
  validated against [`manifest.schema.json`](manifest.schema.json).
- The table above is **generated** from those manifests by
  `scripts/generate_catalog.py`; do not edit it by hand.
- To add a workflow, submit a manifest via PR -- full steps in
  [CONTRIBUTING](../CONTRIBUTING.md).
