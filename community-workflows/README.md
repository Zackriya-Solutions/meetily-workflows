# Community workflows

Metadata for standalone automations using the Meetily Agent API; there is no
workflow installer, execution engine, or promised manifest migration here.
Contributors link to their own code; the first-party example below lives here.
See [setup](../README.md) and [contributing](../CONTRIBUTING.md).

## Catalog

<!-- BEGIN CATALOG -->
| Workflow | Trigger | Language | Scopes | Author |
| --- | --- | --- | --- | --- |
| [Summary file backup](https://github.com/Zackriya-Solutions/meetily-workflows/blob/main/examples/python/summary_ready_backup.py) | `summary-ready` | python | read | Meetily (github.com/Zackriya-Solutions) |

_1 community workflow(s). Generated from `community-workflows/*/manifest.yaml` by `scripts/generate_catalog.py` -- do not edit this table by hand._
<!-- END CATALOG -->

## How it works

Follow the [Python guide](../examples/python/README.md) to run the first-party
summary backup; `summary-ready` is catalog metadata, not a subscription.
Each entry has a manifest validated against [`manifest.schema.json`](manifest.schema.json).
The table is generated; add entries using [CONTRIBUTING](../CONTRIBUTING.md).
