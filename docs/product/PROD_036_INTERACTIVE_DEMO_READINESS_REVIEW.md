# PROD-036 Interactive Demo Readiness Review

PROD-036 reviews the aligned `PROD-035` traces as the first local interactive demo evidence set.

It does not build the final demo UI yet. It decides whether the next checkpoint should build a local trace replay surface where Tarik can inspect exact customer turns, exact agent answers, decision process, state transitions, safety flags, and terminal outcomes.

## Local Commands

```powershell
python scripts\run_prod_036_interactive_demo_readiness_review.py
python scripts\validate_prod_036_interactive_demo_readiness_review.py
```

## Outputs

- `research/experiments/generated/PROD-036-interactive-demo-readiness-review/result.json`
- `research/experiments/generated/PROD-036-interactive-demo-readiness-review/report.md`
- `research/experiments/generated/PROD-036-interactive-demo-readiness-review/interactive_demo_readiness_packet.json`
- `research/experiments/generated/PROD-036-interactive-demo-readiness-review/interactive_demo_readiness_preview.html`

## Result

- Reviewed calls: `8`
- Reviewed turns: `14`
- Demo-ready calls: `8`
- Demo blocker count: `0`
- Local interactive demo ready: `true`
- Exact customer text visible: `true`
- Exact agent answer visible: `true`
- Decision process visible: `true`
- State transition visible: `true`
- Terminal outcome visible: `true`
- Safety flags visible: `true`
- Cold opening visible: `true`
- Decision snapshot mismatches: `0`
- Unknown-objection decisions: `0`
- Hard failures: `0`
- Payment collection count: `0`
- Unsupported claim count: `0`
- Leakage findings: `0`
- First build recommendation: `local_interactive_trace_demo_surface`

## Decision

The next checkpoint is `PROD-037-local-interactive-trace-demo-surface`.

That demo should remain local and synthetic. It should replay the eight aligned calls as inspectable traces, not claim production readiness or contact real customers.

## Boundary

PROD-036 does not start a server, build the final demo UI, call providers, call an LLM, read private data, download datasets, collect payment, enable retrieval by default, enable composer hooks by default, change runtime behavior, or allow production runtime promotion.
