# PROD-061 English Product-Policy Gate Prioritization

`PROD-061` records the English-only product-policy gate order after Tarik accepted the `PROD-060` path decision.

This is prioritization only and not a runtime patch.

## Decision

- Decision: `prioritize_context_sensitive_autonomy_first`
- Selected first gate: `context_sensitive_autonomy_behavior`
- Selected first gate status: `selected_for_next_probe_still_blocked`
- Product-policy gate count: `4`
- Still-blocked blocker count: `14`
- Review HTML: not generated; no human review required for this prioritization checkpoint.
- Recommended next checkpoint: `PROD-062-english-context-sensitive-autonomy-policy-probe`
- Production runtime promotion allowed: `false`

## Ranked Gates

### Rank 1 - context_sensitive_autonomy_behavior

- Status: `selected_for_next_probe_still_blocked`
- Runtime patch allowed: `false`
- Why: It is the best first English-only policy probe because it can be tested with synthetic multi-turn examples, does not require regulated product facts, and does not alter call-control or broad classifier reachability.
- Risk: Can still become manipulative or over-personalized if autonomy language adapts too aggressively to customer hesitation.
- Next action: Open a targeted policy probe that defines allowed and forbidden autonomy-preserving follow-up patterns before any runtime patch.

### Rank 2 - voicemail_action_only_behavior

- Status: `deferred_still_blocked`
- Runtime patch allowed: `false`
- Why: It is important for English call quality, but it is call-control/action behavior rather than phrase quality, so it should follow a smaller policy probe.
- Risk: Could make the runtime take inappropriate same-loop actions after voicemail detection or blur message-taking versus selling behavior.
- Next action: Keep blocked until a call-control-specific checkpoint defines action-only voicemail behavior.

### Rank 3 - coverage_knowledge_policy_behavior

- Status: `deferred_still_blocked`
- Runtime patch allowed: `false`
- Why: Coverage and policy-knowledge responses risk unsupported regulated advice and need product/legal boundaries before runtime use.
- Risk: Could imply insurance coverage, eligibility, or legal/financial advice without a reviewed knowledge policy.
- Next action: Keep blocked until a separate knowledge-policy checkpoint defines allowed facts, uncertainty handling, and escalation.

### Rank 4 - customer_move_classification_outside_selected_non_refusal_groups

- Status: `deferred_still_blocked`
- Runtime patch allowed: `false`
- Why: Broadening customer-move classification has the largest blast radius because it changes reachability across many runtime branches.
- Risk: Could route customer turns into newly promoted behavior without enough evidence for each branch.
- Next action: Keep blocked until smaller policy gates provide clearer acceptance criteria for broader classifier reachability.

## Source Evidence

- Source checkpoint: `PROD-060-runtime-promotion-path-decision`
- Source selected path: `internal_guarded_english_baseline_only`
- Source allowed scope: `local_offline_synthetic_internal_regression_reference`
- Source validator passed: `true`
- English direction accepted: `true`

## Still Blocked

- `customer_move_classification_outside_selected_non_refusal_groups`
- `voicemail_action_only_behavior`
- `coverage_knowledge_policy_behavior`
- `context_sensitive_autonomy_behavior`
- `native_german_review`
- `voice_playback_quality`
- `retrieval_default`
- `provider_or_private_data_use`
- `legal_compliance_review`
- `public_demo_use`
- `real_customer_use`
- `payment_collection`
- `contract_signing`
- `production_runtime_promotion`

## Boundary

- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- No provider calls.
- No LLM or LLM judging.
- No private data reads.
- Retrieval remains default-off.
- Voice playback remains blocked.
- German exact-phrase promotion remains blocked.
- Public demo use remains blocked.
- Real customer use remains blocked.
- Payment collection remains blocked.
- Contract signing remains blocked.
- Production runtime promotion allowed: `false`

## Next Checkpoint

`PROD-062-english-context-sensitive-autonomy-policy-probe` should be a synthetic English policy probe for context-sensitive autonomy. It should define allowed and forbidden autonomy-preserving follow-up patterns before any runtime patch.
