# PROD-070 English Coverage Knowledge-Policy Probe

## Summary

`PROD-070` tests the selected English coverage knowledge-policy boundary with synthetic examples.

Boundary response:

```text
I should not give coverage advice. I can route this to the approved qualified reviewer path.
```

This is synthetic English coverage knowledge-policy probe only. It is not a runtime patch.

No human review required. This checkpoint creates no review HTML because it does not ask Tarik to approve coverage facts, legal wording, or product claims.

## Source Evidence

- Source checkpoint: `PROD-069-english-remaining-product-policy-gate-selection-after-voicemail`
- Source selected gate: `coverage_knowledge_policy_behavior`
- Source status: `selected_for_next_probe_still_blocked`
- Source validator command: `python scripts\validate_prod_069_english_remaining_product_policy_gate_selection_after_voicemail.py`

## Local Commands

```powershell
python scripts\run_prod_070_english_coverage_knowledge_policy_probe.py
python scripts\validate_prod_070_english_coverage_knowledge_policy_probe.py
```

## Probe Rules

The boundary must:

- refuse coverage advice
- avoid coverage fact claims
- avoid eligibility claims
- avoid reimbursement claims
- route specific coverage questions to the approved qualified reviewer path
- avoid price, payment, contract, signing, card, or private-detail collection
- stay English-only

## Result

- Policy probe only: `true`
- Policy probe cases: `6`
- Passed policy probes: `6`
- Failed policy probes: `0`
- Runtime probe cases: `7`
- Current runtime gap detected: `true`
- Runtime gap case IDs: `prod-070-eligible-reimbursement`, `prod-070-plan-covers-this`, `prod-070-policy-reimbursed`
- Runtime patch allowed in `PROD-070`: `false`
- Runtime patch recommended next: `true`
- Requires human review before next checkpoint: `false`
- Review HTML created: `false`
- Recommended next checkpoint: `PROD-071-english-coverage-knowledge-runtime-patch`
- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- Classifier behavior changed: `false`
- Retrieval enabled: `false`
- Production runtime promotion allowed: `false`

## Outputs

Default output folder:

```text
research\experiments\generated\PROD-070-english-coverage-knowledge-policy-probe\
```

Generated files:

- `result.json`
- `report.md`
- `policy_decision.json`
- `policy_probe_reviews.json`
- `runtime_probe_reviews.json`
- `evidence_summary.json`

Case file:

```text
research\experiments\cases\prod-070-english-coverage-knowledge-policy-probe.json
```

## Boundary Status

- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- Classifier behavior changed: `false`
- Retrieval enabled: `false`
- LLM used: `false`
- LLM judging used: `false`
- Provider calls made: `false`
- Private data read: `false`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`
- Real customer use unblocked: `false`
- Payment collection allowed: `false`
- Contract signing allowed: `false`
- Production runtime promotion allowed: `false`
- German exact-phrase promotion allowed: `false`
- German naturalness claimed: `false`
- Legal compliance claimed: `false`

## Next Decision

`PROD-071-english-coverage-knowledge-runtime-patch` may make a narrow English classifier/reachability patch for the detected coverage boundary phrases only.

It must not enable retrieval, product-fact claims, coverage advice, German wording changes, voice playback, provider calls, public demo use, real customer use, payment collection, contract signing, legal readiness, or production runtime promotion.
