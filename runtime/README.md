# Runtime Boundary

This folder is the project home for files that can affect actual sales-agent runtime behavior.

Legacy `scripts/` files remain as thin compatibility wrappers because many commands, validators, and historical checkpoint docs reference those exact paths. Some old `docs/product/*` files are also compatibility stubs that point at canonical runtime Markdown. Edit runtime source and runtime-facing Markdown here, not in the wrappers or stubs.

Use `runtime/runtime_manifest.json` as the current source of truth for:

- `runtime/core/`: deterministic turn behavior.
- `runtime/architecture/`: runtime architecture and live-call critical-path guidance.
- `runtime/entrypoints/`: runtime-facing command implementations and entrypoint docs.
- `runtime/contracts/`: output, state, and campaign contracts.
- `runtime/policy/`: reusable sales delivery policy, language/call-control docs, and composer hooks.
- `runtime/retrieval/`: opt-in guarded retrieval behavior.
- `runtime/speech/` and `runtime/voice/`: spoken text and voice delivery behavior.
- `runtime/providers/`: provider boundary helpers and provider-run docs.
- `runtime/campaigns/`: runtime campaign/profile examples.
- `runtime/prompts/`: runtime-facing prompts.
- `runtime/config/`: runtime config examples. Real local IDs stay ignored.
- `runtime/persistence/`: runtime persistence prototypes and SQLite docs.

Files not listed in the manifest are not automatically safe to delete, but they are not part of the current runtime boundary unless a future checkpoint adds them.

Validate the boundary with:

```powershell
python scripts\validate_runtime_manifest.py
```
