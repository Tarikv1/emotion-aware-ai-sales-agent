# PROD-031 Interactive Grounded Call Simulation

PROD-031 replaces static scenario replay with deterministic reactive customer simulation. Customer replies are generated from customer state after each agent answer instead of from a fixed follow-up script.

## Result

- Checkpoint id: `PROD-031-interactive-grounded-call-simulation`
- Deterministic simulator: `true`
- Call seed count: `8`
- Call count: `8`
- Total turn count: `26`
- Reactive customer turn count: `18`
- Reactive state transition count: `26`
- Customer reply depends on prior agent answer: `true`
- Safe close rate: `1.0`
- Non-sale correctness: `1.0`
- Interactive realism score: `1.0`
- Average trust delta: `1.875`
- Average interest delta: `1.5`
- Average clarity delta: `3.0`
- Average friction delta: `-0.5`
- Hard failures: `0`
- Payment collection count: `0`
- Unsupported claim count: `0`
- Leakage findings: `0`
- Provider calls made: `false`
- LLM used: `false`
- Runtime behavior changed: `false`
- Retrieval default enabled: `false`
- Composer hook default enabled: `false`
- Production runtime promotion allowed: `false`
- Next checkpoint: `PROD-032-interactive-simulation-review`

## Outputs

- `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/result.json`
- `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/report.md`
- `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/interactive_call_traces.json`
- `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/interactive_call_trace.html`

## Evaluation Shape

Each call records exact customer turns, exact agent answers, state before, state after, state deltas, customer reaction reasons, terminal outcome, and safety flags.

The simulator tracks:

- interest
- trust
- clarity
- friction
- patience
- emotion
- commitment
- active objection

The first seed set covers price sensitivity, product confusion, trust gaps, busy callback requests, existing-provider comparison, stakeholder review, support handoff, and do-not-call boundaries.

## Interpretation

This checkpoint is stronger than the static PROD-027 to PROD-030 scenario lane because the next customer message changes based on the prior agent answer and updated state. It is still deterministic and local, so it is appropriate for regression evidence and thesis tracing. It is not production-readiness evidence.

## Boundary

This checkpoint is local-only. It does not call providers, call an LLM, read private data, download datasets, collect payment, start a server, enable retrieval by default, enable composer hooks by default, or promote production runtime behavior.

## Commands

```powershell
python scripts\run_prod_031_interactive_grounded_call_simulation.py
python scripts\validate_prod_031_interactive_grounded_call_simulation.py
```
