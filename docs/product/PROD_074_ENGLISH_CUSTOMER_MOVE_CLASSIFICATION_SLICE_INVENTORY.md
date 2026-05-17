# PROD-074 English Customer-Move Classification Slice Inventory

## Summary

`PROD-074` inventories the current deterministic classifier surface before any customer-move classifier expansion.

This is inventory only. It is not a runtime patch, not a classifier reachability change, not retrieval, and not a spoken-response review.

No human review required for this checkpoint. It creates no review HTML because it only identifies the next review item.

## Source Evidence

- Source checkpoint: `PROD-073-english-customer-move-classification-gate-decision`
- Source validator command: `python scripts\validate_prod_073_english_customer_move_classification_gate_decision.py`
- Runtime path inspected: `runtime/core/realtime_turns.py`
- Protected-boundary source: `PROD-051-safe-call-control-runtime-update`

## Local Commands

```powershell
python scripts\run_prod_074_english_customer_move_classification_slice_inventory.py
python scripts\validate_prod_074_english_customer_move_classification_slice_inventory.py
```

## Result

- Inventory only: `true`
- Unreachable localized response types: `provider-comparison`
- Selected next slice: `unreachable_existing_response_types`
- Selected next review item: `provider-comparison`
- Recommended next checkpoint requires human review: `true`
- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- Classifier behavior changed: `false`
- Retrieval enabled: `false`
- Requires human review before next checkpoint: `false`
- Review HTML created: `false`
- Recommended next checkpoint: `PROD-075-english-provider-comparison-reachability-review`
- Production runtime promotion allowed: `false`

## Why Provider Comparison Is Next

`provider-comparison` is the only localized English response type currently identified as unreachable from the deterministic classifier. It was explicitly left out of prior exact-phrase review until classifier reachability was clarified.

That makes it the smallest concrete review item. The next checkpoint should show examples and ask Tarik whether this branch should remain blocked, be rewritten before reachability, or become eligible for a narrow classifier probe.

## Outputs

Default output folder:

```text
research\experiments\generated\PROD-074-english-customer-move-classification-slice-inventory\
```

Generated files:

- `result.json`
- `report.md`
- `classifier_branch_inventory.json`
- `unreachable_response_inventory.json`
- `protected_boundary_inventory.json`
- `slice_inventory_decision.json`
- `evidence_summary.json`

Case file:

```text
research\experiments\cases\prod-074-english-customer-move-classification-slice-inventory.json
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

`PROD-075-english-provider-comparison-reachability-review` should create the human review packet with concrete examples. It should not patch runtime behavior unless the review is accepted and a later runtime checkpoint is opened.
