# PROD-062 English Context-Sensitive Autonomy Policy Probe

`PROD-062` tests the autonomy wording candidate with synthetic English policy probes.

This is synthetic English autonomy policy probe only. It is not a runtime patch.

## Decision

- Decision: `autonomy_policy_probe_passed_recommend_narrow_runtime_patch`
- Candidate response: `Okay, no rush. We can keep this low-pressure and only clarify what you need.`
- Probe cases: `5`
- Passed probes: `5`
- Failed probes: `0`
- Runtime patch allowed in PROD-062: `false`
- No human review required before next checkpoint: `true`
- Recommended next checkpoint: `PROD-063-english-autonomy-check-runtime-wording-patch`
- Production runtime promotion allowed: `false`

## Probe Reviews

### prod-062-time-to-think

- Customer turn: I need time to think. Do not rush.
- Context state: `basic_need_known`
- Expected policy: `acknowledge_no_rush_and_offer_clarification_only`
- Passed: `true`
- Issue codes: `none`

### prod-062-no-decision-today

- Customer turn: I do not want to decide today.
- Context state: `customer_boundary_explicit`
- Expected policy: `preserve_choice_without_commitment`
- Passed: `true`
- Issue codes: `none`

### prod-062-explain-before-next-step

- Customer turn: I still do not really understand it.
- Context state: `basic_context_missing`
- Expected policy: `clarify_only_what_customer_needs`
- Passed: `true`
- Issue codes: `none`

### prod-062-overpressure-negative-control

- Customer turn: You keep pushing.
- Context state: `pressure_risk`
- Expected policy: `no_urgency_no_rebuttal_no_commitment`
- Passed: `true`
- Issue codes: `none`

### prod-062-leave-it-there

- Customer turn: Can we just leave it there for now?
- Context state: `stop_or_pause_request`
- Expected policy: `allow_pause_without_new_obligation`
- Passed: `true`
- Issue codes: `none`

## Boundary

- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- No provider calls.
- No LLM or LLM judging.
- No private data reads.
- No retrieval enablement.
- No German exact-phrase promotion or German naturalness claim.
- No voice playback, public demo, real customer use, payment collection, contract signing, legal readiness, or production promotion.
