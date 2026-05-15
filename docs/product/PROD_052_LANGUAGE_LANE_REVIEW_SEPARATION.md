# PROD-052 Language Lane Review Separation

## Summary

PROD-052 separates exact spoken-response review by language after PROD-051.

English exact responses are the current owner-review lane because Tarik can judge whether the spoken phrase sounds natural enough to keep, revise, or reject. German exact wording is separated into a pending lane and must not be treated as accepted until native German or source-backed wording review exists.

Shared multilingual naturalness rules remain useful as style and safety policy. They can constrain how the agent speaks across languages, but they do not prove that a specific German phrase sounds natural.

## Local Commands

```powershell
python scripts\run_prod_052_language_lane_review_separation.py
python scripts\validate_prod_052_language_lane_review_separation.py
```

Recommended guard commands:

```powershell
python scripts\validate_prod_051_safe_call_control_runtime_update.py
python scripts\validate_prod_050_safe_call_control_softening_regression.py
python scripts\validate_prod_049_safe_end_call_bridge_continue_review.py
python scripts\validate_realtime_turn_cli.py
python scripts\check_project_drift.py
python scripts\check_thesis_update_gate.py
python scripts\check_thesis_reference_registry.py
python scripts\check_setup.py
git diff --check
```

## Review Lanes

English spoken review:

- exact phrase review is allowed
- Tarik review is required before acceptance
- naturalness comments should focus on what the agent actually says

This lane currently has only the four English cases inherited from the PROD-051 call-control update. It is not the full English policy surface. Later English expansion checkpoints own broader review and runtime promotion status.

German pending review:

- exact phrase acceptance is not allowed
- native German or source-backed wording review is required
- the current German items can be used only as policy-shape evidence
- no German naturalness or native approval claim is made

## Shared Policy Rules

The reusable multilingual rules are:

- answer or acknowledge the customer move before continuing
- frame continuation as optional help, not pressure
- avoid terminal close wording when the call should continue
- avoid customer-facing internal jargon
- keep spoken turns short and sentence-bounded
- tie continuation to the customer's hesitation
- keep the response language consistent
- avoid pressure, payment handling, contract signing, or unsupported claims

These rules constrain behavior across English and German. They do not transfer exact phrase acceptance from one language to another.

## Outputs

Generated output directory:

```text
research\experiments\generated\PROD-052-language-lane-review-separation\
```

Artifacts:

- `result.json`
- `report.md`
- `english_spoken_review_items.json`
- `german_pending_review_items.json`
- `multilingual_policy_rules.json`
- `legacy_mixed_review_surfaces.json`
- `prod_052_language_lane_review.html`

## Older Mixed Files

Older mixed English/German review pages are not deleted or rewritten as evidence snapshots. PROD-052 inventories the currently relevant mixed files and marks them as historical evidence or superseded by the separated PROD-052 page.

Use the separated PROD-052 page as language-lane evidence. Use later promotion checkpoints for current exact phrase acceptance. Reopen an older mixed file only through a future checkpoint that creates a separated review lane for it.

## Boundary Status

- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- Native German approval claimed: `false`
- German naturalness claimed: `false`
- LLM judging used: `false`
- Retrieval enabled: `false`
- Provider calls made: `false`
- Private data read: `false`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`
- Payment collection allowed: `false`
- Contract signing allowed: `false`
- Production runtime promotion allowed: `false`
