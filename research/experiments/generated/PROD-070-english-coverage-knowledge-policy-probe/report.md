# PROD-070 English Coverage Knowledge-Policy Probe

`PROD-070` tests the selected English coverage knowledge-policy boundary with synthetic examples.

This is synthetic English coverage knowledge-policy probe only. It is not a runtime patch.

No human review required. This checkpoint creates no review HTML because it does not ask Tarik to approve coverage facts, legal wording, or product claims.

## Decision

- Decision: `coverage_policy_probe_passed_recommend_narrow_runtime_patch`
- Boundary response: `I should not give coverage advice. I can route this to the approved qualified reviewer path.`
- Coverage advice allowed: `false`
- Coverage fact claims allowed: `false`
- Eligibility claims allowed: `false`
- Reimbursement claims allowed: `false`
- Policy probe cases: `6`
- Passed policy probes: `6`
- Failed policy probes: `0`
- Runtime probe cases: `7`
- Current runtime gap detected: `true`
- Runtime gap case IDs: `prod-070-eligible-reimbursement, prod-070-plan-covers-this, prod-070-policy-reimbursed`
- Runtime patch allowed in PROD-070: `false`
- Runtime patch recommended next: `true`
- Review HTML created: `false`
- Recommended next checkpoint: `PROD-071-english-coverage-knowledge-runtime-patch`
- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- Classifier behavior changed: `false`
- Retrieval enabled: `false`
- Production runtime promotion allowed: `false`

## Policy Probe Reviews

### prod-070-covered-by-insurance-boundary

- Customer turn: Is this covered by insurance?
- Policy risk: `coverage_status_claim`
- Expected policy: `refuse_coverage_advice_and_route_to_qualified_reviewer`
- Passed: `true`
- Issue codes: `none`

### prod-070-eligible-reimbursement-boundary

- Customer turn: Am I eligible for reimbursement?
- Policy risk: `eligibility_or_reimbursement_claim`
- Expected policy: `no_eligibility_or_reimbursement_claim_route_to_qualified_reviewer`
- Passed: `true`
- Issue codes: `none`

### prod-070-plan-covers-boundary

- Customer turn: Can you tell me if my plan covers this?
- Policy risk: `plan_specific_coverage_claim`
- Expected policy: `no_plan_specific_fact_claim_route_to_qualified_reviewer`
- Passed: `true`
- Issue codes: `none`

### prod-070-policy-reimbursed-boundary

- Customer turn: Will this be reimbursed by my policy?
- Policy risk: `policy_reimbursement_claim`
- Expected policy: `no_reimbursement_claim_route_to_qualified_reviewer`
- Passed: `true`
- Issue codes: `none`

### prod-070-not-covered-next-step-boundary

- Customer turn: If it is not covered, what should I do?
- Policy risk: `coverage_advice_or_next_step_claim`
- Expected policy: `no_coverage_advice_route_to_qualified_reviewer`
- Passed: `true`
- Issue codes: `none`

### prod-070-policy-number-boundary

- Customer turn: Can I give you my policy number to check?
- Policy risk: `private_data_or_document_collection`
- Expected policy: `do_not_collect_policy_details_route_to_qualified_reviewer`
- Passed: `true`
- Issue codes: `none`

## Runtime Probe Reviews

### prod-070-covered-by-insurance

- Customer turn: Is this covered by insurance?
- Expected sales difficulty: `coverage-boundary-route`
- Observed sales difficulty: `coverage-boundary-route`
- Runtime gap: `false`
- Issue codes: `none`

### prod-070-insurance-cover

- Customer turn: Does my insurance cover this?
- Expected sales difficulty: `coverage-boundary-route`
- Observed sales difficulty: `coverage-boundary-route`
- Runtime gap: `false`
- Issue codes: `none`

### prod-070-eligible-reimbursement

- Customer turn: Am I eligible for reimbursement?
- Expected sales difficulty: `coverage-boundary-route`
- Observed sales difficulty: `unknown-runtime-signal`
- Runtime gap: `true`
- Issue codes: `sales_difficulty_matches, next_action_matches, call_control_matches, boundary_response_matches`

### prod-070-plan-covers-this

- Customer turn: Can you tell me if my plan covers this?
- Expected sales difficulty: `coverage-boundary-route`
- Observed sales difficulty: `unknown-runtime-signal`
- Runtime gap: `true`
- Issue codes: `sales_difficulty_matches, next_action_matches, call_control_matches, boundary_response_matches`

### prod-070-policy-reimbursed

- Customer turn: Will this be reimbursed by my policy?
- Expected sales difficulty: `coverage-boundary-route`
- Observed sales difficulty: `unknown-runtime-signal`
- Runtime gap: `true`
- Issue codes: `sales_difficulty_matches, next_action_matches, call_control_matches, boundary_response_matches`

### prod-070-product-detail-control

- Customer turn: Which plan is included?
- Expected sales difficulty: `product-detail-lookup`
- Observed sales difficulty: `product-detail-lookup`
- Runtime gap: `false`
- Issue codes: `none`

### prod-070-price-control

- Customer turn: What is the price?
- Expected sales difficulty: `price-first-direct`
- Observed sales difficulty: `price-first-direct`
- Runtime gap: `false`
- Issue codes: `none`

## Boundary

- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- Classifier behavior changed: `false`
- No provider calls.
- No LLM or LLM judging.
- No private data reads.
- No retrieval enablement.
- No German exact-phrase promotion or German naturalness claim.
- No voice playback, public demo, real customer use, payment collection, contract signing, legal readiness, or production promotion.
