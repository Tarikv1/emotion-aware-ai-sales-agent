# PROD-033 Interactive Simulator Termination Fix

PROD-033 fixes the PROD-032 simulator realism gaps by adding cold-call entrances and ending calls by customer acceptance or rejection instead of a fixed number of turns.

## Result

- Checkpoint id: `PROD-033-interactive-simulator-termination-fix`
- Source checkpoint: `PROD-032-interactive-simulation-review`
- Cold-call openings: `8`
- Identity disclosures: `8`
- Company disclosures: `8`
- Reason-for-call disclosures: `8`
- Permission-to-continue checks: `8`
- All calls start with agent opening: `true`
- All calls end by customer decision: `true`
- Fixed turn limit used: `false`
- Loop guard triggered: `false`
- Max-turn terminal count: `0`
- Accepted deals: `4`
- Rejected deals: `4`
- Expected terminal matches: `8`
- Callback converted to sale-ready: `0`
- Repeated agent answers: `0`
- Repeated customer messages: `0`
- Hard failures: `0`
- Payment collection count: `0`
- Unsupported claim count: `0`
- Leakage findings: `0`
- Provider calls made: `false`
- Runtime behavior changed: `false`
- Retrieval default enabled: `false`
- Composer hook default enabled: `false`
- Production runtime promotion allowed: `false`
- Next checkpoint: `PROD-034-interactive-post-fix-review`

## Outputs

- `research/experiments/generated/PROD-033-interactive-simulator-termination-fix/result.json`
- `research/experiments/generated/PROD-033-interactive-simulator-termination-fix/report.md`
- `research/experiments/generated/PROD-033-interactive-simulator-termination-fix/interactive_call_traces.json`
- `research/experiments/generated/PROD-033-interactive-simulator-termination-fix/interactive_call_trace.html`

## Interpretation

The simulator now starts each call like an outbound cold call: greeting, caller identity, company disclosure, reason for call, and permission to continue. The customer then reacts with realistic cold-call responses such as skepticism, busy rejection, existing-provider objection, support boundary, or stop-contact request.

The simulator no longer uses a fixed turn target as a normal ending rule. Calls end when the customer accepts a non-binding sales outcome or rejects the deal. An internal loop guard remains as a failure detector only; it was not triggered in this checkpoint.

This checkpoint fixes the two highest-priority PROD-032 simulator-design limits: repeated answers/customer messages and callback or terminal-state drift. It does not claim production readiness and does not change the runtime default behavior.

## Boundary

PROD-033 is local-only. It does not overwrite PROD-031 or PROD-032, call providers, call an LLM, read private data, download datasets, collect payment, start a server, enable retrieval by default, enable composer hooks by default, or allow production runtime promotion.

## Commands

```powershell
python scripts\run_prod_033_interactive_simulator_termination_fix.py
python scripts\validate_prod_033_interactive_simulator_termination_fix.py
```
