# PROD-071 English Coverage Knowledge Runtime Patch

`PROD-071` applies a narrow English coverage knowledge classifier reachability patch for the three `PROD-070` runtime gap phrases.

This is an English coverage knowledge classifier reachability patch only. It is not a response-text patch, not retrieval, and not coverage advice.

No human review required. This checkpoint creates no review HTML because it applies an already-probed boundary route and does not ask Tarik to approve product/legal wording or coverage facts.

## Decision

- Decision: `english_coverage_knowledge_runtime_patch_applied`
- Runtime path: `runtime/core/realtime_turns.py`
- Patched sales difficulty: `coverage-boundary-route`
- Patched trigger markers: `eligible, reimbursement, reimbursed, plan covers`
- Runtime behavior changed: `true`
- Classifier behavior changed: `true`
- Response text behavior changed: `false`
- Call-control behavior changed for patched phrases: `true`
- Next-action behavior changed for patched phrases: `true`
- Retrieval enabled: `false`
- Coverage advice allowed: `false`
- Review HTML created: `false`
- Recommended next checkpoint: `PROD-072-english-coverage-knowledge-post-patch-regression`
- Production runtime promotion allowed: `false`

## Runtime Patch Reviews

### prod-071-eligible-reimbursement

- Case type: `patched_boundary_phrase`
- Customer turn: Am I eligible for reimbursement?
- Passed: `true`
- Issue codes: `none`
- Sales difficulty: `coverage-boundary-route`
- Next action: `escalate`
- Call control: `transfer-or-escalate`

### prod-071-plan-covers-this

- Case type: `patched_boundary_phrase`
- Customer turn: Can you tell me if my plan covers this?
- Passed: `true`
- Issue codes: `none`
- Sales difficulty: `coverage-boundary-route`
- Next action: `escalate`
- Call control: `transfer-or-escalate`

### prod-071-policy-reimbursed

- Case type: `patched_boundary_phrase`
- Customer turn: Will this be reimbursed by my policy?
- Passed: `true`
- Issue codes: `none`
- Sales difficulty: `coverage-boundary-route`
- Next action: `escalate`
- Call control: `transfer-or-escalate`

### prod-071-product-detail-control

- Case type: `control`
- Customer turn: Which plan is included?
- Passed: `true`
- Issue codes: `none`
- Sales difficulty: `product-detail-lookup`
- Next action: `continue`
- Call control: `bridge-then-continue`

### prod-071-price-control

- Case type: `control`
- Customer turn: What is the price?
- Passed: `true`
- Issue codes: `none`
- Sales difficulty: `price-first-direct`
- Next action: `answer-and-continue`
- Call control: `bridge-then-continue`

### prod-071-healthcare-control

- Case type: `control`
- Customer turn: I need a doctor to diagnose this.
- Passed: `true`
- Issue codes: `none`
- Sales difficulty: `healthcare-boundary-route`
- Next action: `escalate`
- Call control: `transfer-or-escalate`

## Future Persuasion-Tactics Checkpoint

`guided_option_selection` is recorded as a future persuasion-tactics checkpoint candidate, not as PROD-071 runtime behavior.

Definition: after fit and interest are established, present two real paid options with clear tradeoffs and let the customer choose.

Guardrails: both options must be real and fairly described; neither, not now, and explain the difference remain valid choices; no fake urgency; no pretending the customer already agreed.

## Boundary

- Response text behavior changed: `false`
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
