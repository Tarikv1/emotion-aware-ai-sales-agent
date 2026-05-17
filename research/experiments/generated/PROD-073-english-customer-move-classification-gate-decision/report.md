# PROD-073 English Customer-Move Classification Gate Decision

`PROD-073` decides what to do with the remaining broad `customer_move_classification_outside_selected_non_refusal_groups` gate.

No human review required. This is decision only, creates no review HTML, and does not approve classifier expansion.

## Decision

- Decision: `split_broad_customer_move_gate_before_probe`
- Remaining gate: `customer_move_classification_outside_selected_non_refusal_groups`
- Broad classifier patch allowed: `false`
- Narrow slice inventory required next: `true`
- Candidate slice count: `4`
- Decision only: `true`
- Review HTML created: `false`
- Recommended next checkpoint: `PROD-074-english-customer-move-classification-slice-inventory`
- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- Classifier behavior changed: `false`
- Retrieval enabled: `false`
- Production runtime promotion allowed: `false`

## Candidate Slices For Inventory

### specific_known_safe_non_refusal_turns

- Status: `candidate_for_inventory_only`
- Runtime patch allowed: `false`
- Why: Some already-reviewed non-refusal groups have strong evidence, but expanding beyond those groups needs exact branch inventory first.
- Risk: Could duplicate already-promoted safe-call-control behavior or accidentally widen approved branches.

### unreachable_existing_response_types

- Status: `candidate_for_inventory_only`
- Runtime patch allowed: `false`
- Why: Some localized responses may exist without classifier reachability; inventory can separate dead responses from intentionally blocked routes.
- Risk: Making dormant responses reachable without review can surface unapproved wording.

### unknown_runtime_signal_subtypes

- Status: `candidate_for_inventory_only`
- Runtime patch allowed: `false`
- Why: Unknown turns are currently safest as clarification. Splitting unknowns requires evidence that a subtype has a safer deterministic route.
- Risk: Over-classification could reduce clarification and force wrong branches.

### protected_boundary_false_positive_checks

- Status: `candidate_for_inventory_only`
- Runtime patch allowed: `false`
- Why: Any classifier expansion must prove it does not swallow support, do-not-call, payment, healthcare, coverage, voicemail, human-request, or email-only boundaries.
- Risk: False positives in protected boundaries are higher severity than missed sales opportunities.

## Boundary

- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- Classifier behavior changed: `false`
- Retrieval enabled: `false`
- Provider calls made: `false`
- LLM used: `false`
- LLM judging used: `false`
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
