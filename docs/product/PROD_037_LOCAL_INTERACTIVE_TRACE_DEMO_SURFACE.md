# PROD-037 Local Interactive Trace Demo Surface

PROD-037 builds the first local interactive trace demo surface from the accepted `PROD-036` readiness packet.

It is a static browser-openable replay view. It lets Tarik select the eight synthetic calls and inspect cold opening, exact customer turns, exact agent answers, customer follow-up responses, decision snapshots, state transitions, safety flags, and terminal outcomes.

## Local Commands

```powershell
python scripts\run_prod_037_local_interactive_trace_demo_surface.py
python scripts\validate_prod_037_local_interactive_trace_demo_surface.py
```

## Outputs

- `research/experiments/generated/PROD-037-local-interactive-trace-demo-surface/result.json`
- `research/experiments/generated/PROD-037-local-interactive-trace-demo-surface/report.md`
- `research/experiments/generated/PROD-037-local-interactive-trace-demo-surface/local_interactive_trace_demo_surface.html`
- `research/experiments/generated/PROD-037-local-interactive-trace-demo-surface/local_interactive_trace_demo_surface_data.json`

## Result

- Surface ready: `true`
- Visible calls: `8`
- Visible turns: `14`
- Selectable calls: `8`
- Selectable turns: `14`
- Static HTML ready: `true`
- Keyboard accessible controls: `true`
- Exact customer text visible: `true`
- Exact agent answer visible: `true`
- Decision process visible: `true`
- State transition visible: `true`
- Terminal outcome visible: `true`
- Safety flags visible: `true`
- Cold opening visible: `true`
- Replay controls visible: `true`
- Local synthetic trace replay: `true`

## Decision

The next checkpoint is `PROD-038-local-demo-surface-review`.

PROD-038 should review whether this surface is actually useful for Tarik's inspection workflow before adding voice playback, more call seeds, scenario branching, or customer-facing demo polish.

## Boundary

PROD-037 does not call providers, call an LLM, read private data, download datasets, start a server, collect payment, enable retrieval by default, enable composer hooks by default, change runtime behavior, or allow production runtime promotion.
