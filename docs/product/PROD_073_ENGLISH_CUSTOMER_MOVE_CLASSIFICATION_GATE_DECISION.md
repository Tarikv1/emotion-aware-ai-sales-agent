# PROD-073 English Customer-Move Classification Gate Decision

## Summary

`PROD-073` decides what to do with the remaining broad `customer_move_classification_outside_selected_non_refusal_groups` gate after autonomy, voicemail, and coverage-boundary work passed.

The decision is to split the broad customer-move gate before any probe or runtime patch. A broad classifier patch is not allowed.

No human review required. This checkpoint creates no review HTML because it does not ask Tarik to approve a concrete classifier behavior, spoken wording, product policy, or persuasion tactic.

## Source Evidence

- Source checkpoint: `PROD-072-english-coverage-knowledge-post-patch-regression`
- Priority source checkpoint: `PROD-061-english-product-policy-gate-prioritization`
- Remaining gate: `customer_move_classification_outside_selected_non_refusal_groups`
- Source validator command: `python scripts\validate_prod_072_english_coverage_knowledge_post_patch_regression.py`

## Local Commands

```powershell
python scripts\run_prod_073_english_customer_move_classification_gate_decision.py
python scripts\validate_prod_073_english_customer_move_classification_gate_decision.py
```

## Result

- Decision: `split_broad_customer_move_gate_before_probe`
- Split broad customer-move gate before probe: `true`
- Decision only: `true`
- Broad classifier patch allowed: `false`
- Narrow slice inventory required next: `true`
- Candidate slice count: `4`
- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- Classifier behavior changed: `false`
- Retrieval enabled: `false`
- Requires human review before next checkpoint: `false`
- Review HTML created: `false`
- Recommended next checkpoint: `PROD-074-english-customer-move-classification-slice-inventory`
- Production runtime promotion allowed: `false`

## Candidate Slices

The next checkpoint should inventory, not patch, these candidate slice families:

- `specific_known_safe_non_refusal_turns`
- `unreachable_existing_response_types`
- `unknown_runtime_signal_subtypes`
- `protected_boundary_false_positive_checks`

Each slice must define expected `sales_difficulty`, `next_action`, and `call_control` before any runtime patch. Each slice also needs protected-boundary controls.

## Outputs

Default output folder:

```text
research\experiments\generated\PROD-073-english-customer-move-classification-gate-decision\
```

Generated files:

- `result.json`
- `report.md`
- `customer_move_gate_decision.json`
- `classifier_slice_plan.json`
- `evidence_summary.json`

Case file:

```text
research\experiments\cases\prod-073-english-customer-move-classification-gate-decision.json
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

`PROD-074-english-customer-move-classification-slice-inventory` should inventory current classifier branches, unreachable response types, already-approved selected non-refusal groups, and protected-boundary controls before recommending any specific classifier probe.
