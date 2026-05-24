# ADVERSARIAL-STABILITY-GUARD-CLUSTER-001

## Summary
- Status: `pass`
- Scenario count: `9`
- Pass count: `9`
- Failure count: `0`

## Failure Types

## Scenarios
### insurance-coverage-thing-impact
- Status: `pass`
- Campaign: `synthetic-insurance-review`
- Category: `near_miss_configured_gap`
- Source: `universal_response_shape`
- Call control: `continue-call`
- Failures: ``
- Final response: Got it. If coverage fit is already costing time, the next useful step is a short review with the licensed insurance specialist. What callback window works?

### insurance-payment-pressure-impact
- Status: `pass`
- Campaign: `synthetic-insurance-review`
- Category: `near_miss_configured_gap`
- Source: `universal_response_shape`
- Call control: `continue-call`
- Failures: ``
- Final response: Got it. If premium pressure is already costing time, the next useful step is a short review with the licensed insurance specialist. What callback window works?

### b2b-integration-thing
- Status: `pass`
- Campaign: `synthetic-b2b-saas-operations`
- Category: `near_miss_configured_gap`
- Source: `universal_response_shape`
- Call control: `continue-call`
- Failures: ``
- Final response: Understood, integration is the unclear part. What part is confusing: what it means, what the implementation specialist would check, or whether it matters here?

### b2b-visibility-thing-impact
- Status: `pass`
- Campaign: `synthetic-b2b-saas-operations`
- Category: `near_miss_configured_gap`
- Source: `universal_response_shape`
- Call control: `continue-call`
- Failures: ``
- Final response: Got it. If visibility issue is already costing time, the next useful step is a short review with the implementation specialist. What callback window works?

### telecom-plane-fit
- Status: `pass`
- Campaign: `synthetic-telecom-plan-review`
- Category: `near_miss_configured_gap`
- Source: `universal_response_shape`
- Call control: `continue-call`
- Failures: ``
- Final response: Understood, plan fit is the unclear part. What part is confusing: what it means, what the telecom account specialist would check, or whether it matters here?

### membership-plan-thing
- Status: `pass`
- Campaign: `synthetic-membership-plan-review`
- Category: `near_miss_configured_gap`
- Source: `universal_response_shape`
- Call control: `continue-call`
- Failures: ``
- Final response: Understood, plan fit is the unclear part. What part is confusing: what it means, what the account support specialist would check, or whether it matters here?

### routesignal-coverage-mismatch-boundary
- Status: `pass`
- Campaign: `routesignal_live_demo`
- Category: `customer_facing_scope_boundary`
- Source: `contextual_buyer_semantics`
- Call control: `continue-call`
- Failures: ``
- Final response: I can't give coverage advice on this call; that is outside this call's scope. This call is about inbound demo follow-up, so the useful check is whether follow-up is slipping now.

### telecom-plan-fit-coverage-boundary
- Status: `pass`
- Campaign: `synthetic-telecom-plan-review`
- Category: `customer_facing_scope_boundary`
- Source: `universal_response_shape`
- Call control: `continue-call`
- Failures: ``
- Final response: Correct. I can answer the high-level scope, but detailed advice belongs with the telecom account specialist. The telecom account specialist would need to review plan fit and coverage or availability. Is that what you want them to check?

### b2b-integration-boundary
- Status: `pass`
- Campaign: `synthetic-b2b-saas-operations`
- Category: `customer_facing_scope_boundary`
- Source: `universal_response_shape`
- Call control: `continue-call`
- Failures: ``
- Final response: Understood, integration is the unclear part. What part is confusing: what it means, what the implementation specialist would check, or whether it matters here?

