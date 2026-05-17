# PROD-071 English Coverage Knowledge Runtime Patch

## Summary

`PROD-071` applies a narrow English coverage knowledge classifier reachability patch for the three `PROD-070` runtime gap phrases:

- `eligible`
- `reimbursement`
- `plan covers`

This is an English coverage knowledge classifier reachability patch only. It is not a response-text patch, not retrieval, and not coverage advice.

No human review required. This checkpoint creates no review HTML because it applies an already-probed boundary route and does not ask Tarik to approve product/legal wording or coverage facts.

## Source Evidence

- Source checkpoint: `PROD-070-english-coverage-knowledge-policy-probe`
- Source selected gate: `coverage_knowledge_policy_behavior`
- Source runtime gap case IDs: `prod-070-eligible-reimbursement`, `prod-070-plan-covers-this`, `prod-070-policy-reimbursed`
- Source validator command: `python scripts\validate_prod_070_english_coverage_knowledge_policy_probe.py`

## Local Commands

```powershell
python scripts\run_prod_071_english_coverage_knowledge_runtime_patch.py
python scripts\validate_prod_071_english_coverage_knowledge_runtime_patch.py
```

## Result

- Runtime behavior changed: `true`
- Classifier behavior changed: `true`
- Response text behavior changed: `false`
- Call-control behavior changed for patched phrases: `true`
- Next-action behavior changed for patched phrases: `true`
- Runtime patch cases: `6`
- Patched phrase cases: `3`
- Control cases: `3`
- Failed runtime patch cases: `0`
- Coverage advice allowed: `false`
- Coverage fact claims allowed: `false`
- Eligibility claims allowed: `false`
- Reimbursement claims allowed: `false`
- Retrieval enabled: `false`
- Requires human review before next checkpoint: `false`
- Review HTML created: `false`
- Recommended next checkpoint: `PROD-072-english-coverage-knowledge-post-patch-regression`
- Production runtime promotion allowed: `false`

## Future Persuasion-Tactics Checkpoint

`guided_option_selection` is recorded as a future persuasion-tactics checkpoint candidate, not as `PROD-071` runtime behavior.

Definition: after fit and interest are established, present two real paid options with clear tradeoffs and let the customer choose.

Guardrails:

- both options must be real and fairly described
- `neither`, `not now`, and `explain the difference` remain valid customer choices
- no fake urgency
- no pretending the customer already agreed

## Outputs

Default output folder:

```text
research\experiments\generated\PROD-071-english-coverage-knowledge-runtime-patch\
```

Generated files:

- `result.json`
- `report.md`
- `patch_decision.json`
- `runtime_patch_reviews.json`
- `evidence_summary.json`

Case file:

```text
research\experiments\cases\prod-071-english-coverage-knowledge-runtime-patch.json
```

## Boundary Status

- Response text behavior changed: `false`
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

`PROD-072-english-coverage-knowledge-post-patch-regression` should verify the patched coverage boundary phrases, adjacent product-detail controls, healthcare controls, pricing controls, voicemail behavior, and the stable English multi-turn guard before any broad customer-move classifier expansion.
