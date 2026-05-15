# PROD-053A English Sales Psychology Deep Dive

## Summary

PROD-053A is a research-only checkpoint for the English conversation psychology layer. It gathers source-backed sales psychology and general human psychology findings that are actually useful for a live English sales call, then compresses them into candidate rules for a later `PROD-053B` review.

The checkpoint does not change runtime behavior, response text, retrieval, voice, provider usage, or production readiness.

## Local Commands

```powershell
python scripts\run_prod_053a_english_sales_psychology_deep_dive.py
python scripts\validate_prod_053a_english_sales_psychology_deep_dive.py
```

## Research Focus

The packet focuses on:

- adaptive selling and customer-oriented response selection
- salesperson listening, reflective listening, and mirroring limits
- buyer confidence, no-decision risk, status quo bias, and choice overload
- autonomy support and reactance-safe language
- behavior friction diagnosis before pressure
- trust repair through ability, benevolence, and integrity gaps
- conversation repair and targeted clarification
- spoken brevity for live voice interfaces
- ethical insight-led selling without manipulation

## Outputs

Generated output directory:

```text
research\experiments\generated\PROD-053A-english-sales-psychology-deep-dive\
```

Artifacts:

- `result.json`
- `report.md`
- `source_register.json`
- `topic_findings.json`
- `compact_candidate_rules.json`
- `rejected_or_deferred_tactics.json`

## Boundary Status

- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- Retrieval enabled: `false`
- Provider calls made: `false`
- LLM judging used: `false`
- Private data read: `false`
- Source excerpt text stored: `false`
- Copied scripts stored: `false`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`
- Payment collection allowed: `false`
- Contract signing allowed: `false`
- Production runtime promotion allowed: `false`

## Next Gate

`PROD-053B` should turn only reviewed candidate rules into a compact English psychology layer. The layer should stay small in the live path: no large runtime planner, no hidden emotion diagnosis, no fake urgency, no commitment traps, and no exact German phrase promotion.
