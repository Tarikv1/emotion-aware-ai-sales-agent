# PROD-035 Runtime Decision-Trace Alignment

PROD-035 fixes the visible decision-trace issue found by `PROD-034-interactive-post-fix-review`.

It uses the same `PROD-033` interactive calls and preserves the spoken answers. The checkpoint only aligns the logged decision snapshot so a direct answer is not falsely shown as `ask-follow-up`, and visible objection states are not left as `unknown-runtime-signal`.

## Local Commands

```powershell
python scripts\run_prod_035_runtime_decision_trace_alignment.py
python scripts\validate_prod_035_runtime_decision_trace_alignment.py
```

## Outputs

- `research/experiments/generated/PROD-035-runtime-decision-trace-alignment/result.json`
- `research/experiments/generated/PROD-035-runtime-decision-trace-alignment/report.md`
- `research/experiments/generated/PROD-035-runtime-decision-trace-alignment/aligned_interactive_call_traces.json`
- `research/experiments/generated/PROD-035-runtime-decision-trace-alignment/aligned_interactive_call_trace.html`

## Result

- Spoken answer changed count: `0`
- Customer response changed count: `0`
- Terminal outcome changed count: `0`
- Decision snapshot mismatches before: `13`
- Decision snapshot mismatches after: `0`
- Unknown-objection decisions before: `6`
- Unknown-objection decisions after: `0`
- Terminal call-control mismatches after: `0`
- Direct-answer next actions: `11`
- Objections mapped: `7`
- Hard failures: `0`
- Payment collection count: `0`
- Unsupported claim count: `0`
- Leakage findings: `0`
- Runtime decision trace default changed: `false`

## Decision

Keep PROD-035 as the opt-in runtime decision-trace alignment fix. It proves the decision process can become honest without making the agent ask more questions or changing the accepted spoken answers.

The next checkpoint is `PROD-036-interactive-demo-readiness-review`.

## Boundary

PROD-035 does not overwrite PROD-033 or PROD-034, call providers, call an LLM, read private data, download datasets, collect payment, start a server, enable retrieval by default, enable composer hooks by default, change decision-trace defaults globally, or allow production runtime promotion.
