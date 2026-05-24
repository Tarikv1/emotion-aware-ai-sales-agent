# LIVE-DEMO-TRANSCRIPT-FAILURE-REPLAY-001

## Summary
- Status: `pass`
- Matrix size: `14`
- Pass count: `14`
- Failure count: `0`
- Runtime behavior changed in this phase: `false`
- Known reproduced-before-patch scenarios: `9`
- Preservation scenarios: `5`

## Classification Counts
- `reproduced_before_patch_then_fixed`: `9`
- `not_reproduced_on_current_runtime`: `0`
- `preservation_check_passed`: `5`

## Classification Meaning
- `reproduced_before_patch_then_fixed`: scenario failed during the 4F2A red replay and now passes on the current runtime.
- `not_reproduced_on_current_runtime`: scenario did not reproduce as a current runtime failure.
- `preservation_check_passed`: guard scenario for existing safe behavior; it was not one of the live transcript failures.

## Scenario Results
### routesignal_permission_repeated_ack
- Passed: `true`
- Classification: `reproduced_before_patch_then_fixed`
- Buyer move: `permission_acknowledgement`
- Source: `universal_response_shape`
- Call control: `continue-call`
- Response: Thanks. Is inbound demo follow-up slipping right now?

### routesignal_asr_near_miss_callbacks
- Passed: `true`
- Classification: `reproduced_before_patch_then_fixed`
- Buyer move: `pain_confirmed`
- Source: `universal_response_shape`
- Call control: `continue-call`
- Response: Got it, callbacks are the issue. Is that causing missed follow-up, or mostly extra tracking work?

### routesignal_near_miss_then_impact
- Passed: `true`
- Classification: `reproduced_before_patch_then_fixed`
- Buyer move: `implication_confirmed`
- Source: `universal_response_shape`
- Call control: `continue-call`
- Response: Got it. If callbacks is already causing delays, the next useful step is a short review with the verified implementation reviewer. What callback window works?

### routesignal_vague_followup_little_bit
- Passed: `true`
- Classification: `reproduced_before_patch_then_fixed`
- Buyer move: `implication_unclear`
- Source: `universal_response_shape`
- Call control: `continue-call`
- Response: A little bit, understood. Is it active enough to review, or more of a minor annoyance?

### routesignal_why_care_challenge
- Passed: `true`
- Classification: `reproduced_before_patch_then_fixed`
- Buyer move: `why_should_i_care`
- Source: `universal_response_shape`
- Call control: `continue-call`
- Response: Fair question. Only if inbound demo follow-up slipping is costing time, creating delays, or hurting follow-up quality. If that is happening, a short review can confirm whether it is worth fixing. Is that showing up now?

### insurance_false_assumption_correction
- Passed: `true`
- Classification: `reproduced_before_patch_then_fixed`
- Buyer move: `already_answered_challenge`
- Source: `universal_response_shape`
- Call control: `continue-call`
- Response: You're right, you did not mention premium pressure. I won't assume that. This call can only check whether a licensed coverage review is useful.

### insurance_repeated_product_detail_challenge
- Passed: `true`
- Classification: `reproduced_before_patch_then_fixed`
- Buyer move: `scope_limit_question`
- Source: `universal_response_shape`
- Call control: `continue-call`
- Response: Correct. I can explain the high-level purpose, but detailed advice belongs with the licensed insurance specialist. This call only checks whether a licensed coverage review is worth it. Do you want me to check whether a review is useful?

### telecom_vague_positive_after_prior_bad_experience
- Passed: `true`
- Classification: `reproduced_before_patch_then_fixed`
- Buyer move: `why_are_you_asking`
- Source: `contextual_buyer_semantics`
- Call control: `continue-call`
- Response: Good. Then I'll keep it to one concrete check: is plan fit or coverage or availability the issue?

### telecom_plan_fit_coverage_boundary
- Passed: `true`
- Classification: `reproduced_before_patch_then_fixed`
- Buyer move: `scope_limit_question`
- Source: `universal_response_shape`
- Call control: `continue-call`
- Response: Correct. I can answer the high-level scope, but detailed advice belongs with the telecom account specialist. The telecom account specialist would need to review plan fit and coverage or availability. Is that what you want them to check?

### preserve_driving_stop
- Passed: `true`
- Classification: `preservation_check_passed`
- Buyer move: `busy_or_distracted`
- Source: `universal_response_shape`
- Call control: `end-call`
- Response: No problem. I do not want to distract you while driving. I'll stop here.

### preserve_hospital_stop
- Passed: `true`
- Classification: `preservation_check_passed`
- Buyer move: `serious_hardship_bad_timing`
- Source: `universal_response_shape`
- Call control: `end-call`
- Response: I'm sorry to hear that. This is not the right time for this call. I'll stop here.

### preserve_direct_product_answer
- Passed: `true`
- Classification: `preservation_check_passed`
- Buyer move: `product_detail_question`
- Source: `universal_response_shape`
- Call control: `continue-call`
- Response: Sure. RouteSignal helps teams keep inbound demo follow-up from slipping through ownership, reminders, or handoffs. The quick check is whether that problem exists on your side.

### preserve_ai_disclosure
- Passed: `true`
- Classification: `preservation_check_passed`
- Buyer move: `are_you_ai_or_robot`
- Source: `universal_response_shape`
- Call control: `continue-call`
- Response: Fair to ask. Yes, I'm an AI voice agent calling for Northstar Workflow Labs. I'll keep it brief: is inbound demo follow-up slipping right now?

### preserve_callback_time_capture
- Passed: `true`
- Classification: `preservation_check_passed`
- Buyer move: `callback_time_provided`
- Source: `universal_response_shape`
- Call control: `schedule-and-end`
- Response: Got it. I'll note that time for the verified implementation reviewer to follow up.

