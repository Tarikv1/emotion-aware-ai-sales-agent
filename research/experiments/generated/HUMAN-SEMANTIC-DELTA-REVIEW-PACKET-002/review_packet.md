# Human Semantic Delta Review Packet 002

## Executive Summary For Reviewer

This packet was generated after the 5A1 targeted patch. It uses fresh current-runtime outputs, not stale pre-patch evidence. The runtime is deterministic, local, and designed for appointment-setting and lead qualification, not full sale closure.

Conversations: 50
Turn records: 323

## What To Review

- Did the 5A1 fixes actually improve the failure class?
- Is appointment pressure appropriate for uncertainty, confusion, pain, info-first, callback, no-need, and refusal states?
- Do support/account/order/warranty/cancellation requests stay within safe boundaries?
- Do long conversations preserve cleared gaps, confirmed gaps, contact capture, callback time, and stop state?
- Do final response, TTS input, and provider-rendered dry-run text preserve the same business meaning?

## Campaign And Vertical Coverage

- `automotive_service`: 5 conversations
- `b2b_saas`: 5 conversations
- `healthcare_admin_or_medical_equipment`: 5 conversations
- `home_services`: 5 conversations
- `insurance`: 5 conversations
- `membership_or_subscription`: 5 conversations
- `retail_or_ecommerce_support_sales`: 5 conversations
- `routesignal_live_demo`: 10 conversations
- `telecom`: 5 conversations

## Focus Areas

- `5a1_replayed_fixes`: 9 conversations
- `appointment_pressure_calibration`: 28 conversations
- `confusion_explanation_quality`: 10 conversations
- `long_state_drift`: 9 conversations
- `regulated_caution`: 2 conversations
- `routesignal_preservation`: 10 conversations
- `support_out_of_scope_boundaries`: 14 conversations

## Review Rubric

1 to 5, where 1 is poor and 5 is ready for gated live-audio review.

Score dimensions:
- buyer meaning understood
- acknowledgement quality
- next action correctness
- appointment pressure appropriateness
- naturalness
- safety/compliance
- state consistency
- overall readiness

Failure categories:
- `missed_buyer_meaning`
- `wrong_semantic`
- `wrong_next_action`
- `too_pushy`
- `too_passive`
- `repeated_question`
- `unnatural_wording`
- `campaign_leakage`
- `unsafe_claim`
- `state_drift`
- `contact_capture_issue`
- `right_person_issue`
- `support_boundary_issue`
- `stop_refusal_issue`
- `tts_meaning_drift`
- `validator_gap`
- `copy_polish_only`

## Conversation Records

### delta-generic-b2b-saas-post-5a1-fix-replay-001

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-b2b-saas-regression-001`
- Vertical: `b2b_saas`
- Scenario: `post_5a1_fix_replay`
- Focus areas: 5a1_replayed_fixes, support_out_of_scope_boundaries
- Risk tags: hard_case, edge_case, post_patch_replay
- Expected behavior: Right-person email capture should remain useful, and the password request should stay a support boundary.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do y... | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a sho... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | I do not handle this | Understood. Who is the right person or team for operations fit review, or should I stop here? | Understood. Who is the right person or team for operations fit review, or should I stop here? | Understood. Who is the right person or team for operations fit review, or should I stop here? | wrong_person_or_wrong_department |  |  |  | contextual_buyer_semantics | continue-call |
| 4 | operations handles it | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I... | wrong_person_or_wrong_department |  |  |  | contextual_buyer_semantics | continue-call |
| 5 | send it to <email:sha256_12:af3c82544f64> | Got it. I will note that contact for operations so a human can follow up through the right path. I will not send anything from this call. | Got it. I will note that contact for operations so a human can follow up through the right path. I will not send anything from this call. | Got it. I will note that contact for operations so a human can follow up through the right path. I will not send anyt... | right_person_email_provided |  |  |  | contextual_buyer_semantics | continue-call |
| 6 | can you help with my password? | I cannot help with account support on this call. If useful, an implementation specialist can follow up separately, or I can stop here. | I cannot help with account support on this call. If useful, an implementation specialist can follow up separately, or I can stop here. | I cannot help with account support on this call. If useful, an implementation specialist can follow up separately, or... | account_support_boundary |  |  |  | pre_speech_conversation_stability_guard | continue-call |

### delta-generic-b2b-saas-appointment-pressure-calibration-002

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-b2b-saas-regression-001`
- Vertical: `b2b_saas`
- Scenario: `appointment_pressure_calibration`
- Focus areas: appointment_pressure_calibration
- Risk tags: hard_case, edge_case, appointment_pressure
- Expected behavior: Agent should calibrate pressure across maybe, not sure, info-first, maybe-later, and callback timing.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do y... | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a sho... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | maybe | No problem. If you are not sure about manual work, integration risk, or visibility gap, I can ask one simpler question or stop here. | No problem. If you are not sure about manual work, integration risk, or visibility gap, I can ask one simpler question or stop here. | No problem. If you are not sure about manual work, integration risk, or visibility gap, I can ask one simpler questio... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 4 | not sure | I am checking manual work, integration risk, or visibility gap for a possible operations fit review. Which part should I ask about first, if any? | I am checking manual work, integration risk, or visibility gap for a possible operations fit review. Which part should I ask about first, if any? | I am checking manual work, integration risk, or visibility gap for a possible operations fit review. Which part shoul... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 5 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | contextual_buyer_semantics | continue-call |
| 6 | maybe later | No problem. What time should I call back? | No problem. What time should I call back? | No problem. What time should I call back? | callback_scheduling_request |  |  |  | contextual_buyer_semantics | continue-call |
| 7 | tomorrow at 3 works | Confirmed. I will record that callback time for an implementation specialist about the operations fit review. Goodbye. | Confirmed. I will record that callback time for an implementation specialist about the operations fit review. Goodbye. | Confirmed. I will record that callback time for an implementation specialist about the operations fit review. Goodbye. | callback_time_provided |  |  |  | contextual_buyer_semantics | schedule-and-end |

### delta-generic-b2b-saas-support-out-of-scope-boundary-003

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-b2b-saas-regression-001`
- Vertical: `b2b_saas`
- Scenario: `support_out_of_scope_boundary`
- Focus areas: support_out_of_scope_boundaries
- Risk tags: hard_case, edge_case, support_boundary
- Expected behavior: Support, account, order, claim, warranty, or department turns should not become fake support actions.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do y... | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a sho... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | what is included? | For Operations Workflow Review, I should stick to approved details. I am only checking whether manual work, integration risk, or visibility gap should go to a short operations fit review. | For Operations Workflow Review, I should stick to approved details. I am only checking whether manual work, integration risk, or visibility gap should go to... | For Operations Workflow Review, I should stick to approved details. I am only checking whether manual work, integrati... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 4 | can you help with my password? | I cannot help with account support on this call. If useful, an implementation specialist can follow up separately, or I can stop here. | I cannot help with account support on this call. If useful, an implementation specialist can follow up separately, or I can stop here. | I cannot help with account support on this call. If useful, an implementation specialist can follow up separately, or... | account_support_boundary |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 5 | wrong department | Understood. Who is the right person or team for operations fit review, or should I stop here? | Understood. Who is the right person or team for operations fit review, or should I stop here? | Understood. Who is the right person or team for operations fit review, or should I stop here? | wrong_person_or_wrong_department |  |  |  | contextual_buyer_semantics | continue-call |
| 6 | talk to support | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | wrong_person_or_wrong_department |  |  |  | contextual_buyer_semantics | continue-call |

### delta-generic-b2b-saas-confusion-explanation-quality-004

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-b2b-saas-regression-001`
- Vertical: `b2b_saas`
- Scenario: `confusion_explanation_quality`
- Focus areas: confusion_explanation_quality, appointment_pressure_calibration
- Risk tags: hard_case, edge_case, explanation_quality
- Expected behavior: Confusion and process questions should be answered in campaign terms without repeating the same diagnostic loop.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do y... | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a sho... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | I don't understand | Sorry, I meant the areas in this fit check: manual work, integration risk, or visibility gap. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: manual work, integration risk, or visibility gap. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: manual work, integration risk, or visibility gap. Which part causes troub... | confusion_not_clear |  |  |  | contextual_buyer_semantics | continue-call |
| 4 | what do you mean? | I am checking manual work, integration risk, or visibility gap for a possible operations fit review. Which part should I ask about first, if any? | I am checking manual work, integration risk, or visibility gap for a possible operations fit review. Which part should I ask about first, if any? | I am checking manual work, integration risk, or visibility gap for a possible operations fit review. Which part shoul... | previous_question_clarification |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 5 | what are you asking? | I am checking manual work, integration risk, or visibility gap for a possible operations fit review. Which part should I ask about first, if any? | I am checking manual work, integration risk, or visibility gap for a possible operations fit review. Which part should I ask about first, if any? | I am checking manual work, integration risk, or visibility gap for a possible operations fit review. Which part shoul... | confusion_not_clear |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 6 | what happens next? | If manual work, integration risk, or visibility gap are actually relevant, an implementation specialist can do a short operations fit review. If not, I can stop here; should I ask one qui... | If manual work, integration risk, or visibility gap are actually relevant, an implementation specialist can do a short operations fit review. If not, I can s... | If manual work, integration risk, or visibility gap are actually relevant, an implementation specialist can do a shor... | no_contextual_semantic |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 7 | what is included? | For Operations Workflow Review, I should stick to approved details. I am only checking whether manual work, integration risk, or visibility gap should go to a short operations fit review. | For Operations Workflow Review, I should stick to approved details. I am only checking whether manual work, integration risk, or visibility gap should go to... | For Operations Workflow Review, I should stick to approved details. I am only checking whether manual work, integrati... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 8 | is it expensive? | I do not have approved pricing to quote here. An implementation specialist should confirm cost and terms before any next step. | I do not have approved pricing to quote here. An implementation specialist should confirm cost and terms before any next step. | I do not have approved pricing to quote here. An implementation specialist should confirm cost and terms before any n... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |

### delta-generic-b2b-saas-long-state-drift-delta-005

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-b2b-saas-regression-001`
- Vertical: `b2b_saas`
- Scenario: `long_state_drift_delta`
- Focus areas: long_state_drift, appointment_pressure_calibration
- Risk tags: hard_case, edge_case, state_drift
- Expected behavior: Long conversation should preserve clear, pain, contact/callback, support boundary, and terminal state.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do y... | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a sho... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah go ahead | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | manual work is handled | Got it, manual work is clear. Should I check integration risk or visibility gap, or stop here? | Got it, manual work is clear. Should I check integration risk or visibility gap, or stop here? | Got it, manual work is clear. Should I check integration risk or visibility gap, or stop here? | current_gap_clear | manual_work | manual_work |  | contextual_buyer_semantics | continue-call |
| 4 | visibility is the problem | Got it, visibility into workflow status is the real gap. The next step would be a short operations fit review; what time works for that review? | Got it, visibility into workflow status is the real gap. The next step would be a short operations fit review; what time works for that review? | Got it, visibility into workflow status is the real gap. The next step would be a short operations fit review; what t... | pain_confirmed | visibility_gap | manual_work | visibility_gap | contextual_buyer_semantics | continue-call |
| 5 | send me details first | No problem. I can send a short summary focused on visibility into workflow status. What email or callback time should I note? | No problem. I can send a short summary focused on visibility into workflow status. What email or callback time should I note? | No problem. I can send a short summary focused on visibility into workflow status. What email or callback time should... | send_info_with_confirmed_pain | visibility_gap | manual_work | visibility_gap | contextual_buyer_semantics | continue-call |
| 6 | send it to <email:sha256_12:af3c82544f64> | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | email_provided |  | manual_work | visibility_gap | contextual_buyer_semantics | continue-call |
| 7 | can you help with my password? | I cannot help with account support on this call. If useful, an implementation specialist can follow up separately, or I can stop here. | I cannot help with account support on this call. If useful, an implementation specialist can follow up separately, or I can stop here. | I cannot help with account support on this call. If useful, an implementation specialist can follow up separately, or... | account_support_boundary |  | manual_work | visibility_gap | pre_speech_conversation_stability_guard | continue-call |
| 8 | stop calling | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | stop_request |  | manual_work | visibility_gap | contextual_buyer_semantics | end-call |

### delta-generic-insurance-post-5a1-fix-replay-001

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-insurance-regression-001`
- Vertical: `insurance`
- Scenario: `post_5a1_fix_replay`
- Focus areas: 5a1_replayed_fixes, support_out_of_scope_boundaries
- Risk tags: hard_case, edge_case, post_patch_replay
- Expected behavior: Next-step explanation after confirmed pain should explain process before any further diagnostic.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you h... | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short lice... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | premium is a problem | Got it, premium and budget pressure is the real gap. The next step would be a short licensed coverage review; what time works for that review? | Got it, premium and budget pressure is the real gap. The next step would be a short licensed coverage review; what time works for that review? | Got it, premium and budget pressure is the real gap. The next step would be a short licensed coverage review; what ti... | pain_confirmed | premium_or_budget |  | premium_or_budget | contextual_buyer_semantics | continue-call |
| 4 | what happens next? | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | no_contextual_semantic |  |  | premium_or_budget | pre_speech_conversation_stability_guard | continue-call |
| 5 | can you handle my claim? | I am checking coverage fit, premium or budget, or renewal or timing for a possible licensed coverage review. Which part should I ask about first, if any? | I am checking coverage fit, premium or budget, or renewal or timing for a possible licensed coverage review. Which part should I ask about first, if any? | I am checking coverage fit, premium or budget, or renewal or timing for a possible licensed coverage review. Which pa... | no_contextual_semantic |  |  | premium_or_budget | pre_speech_conversation_stability_guard | continue-call |

### delta-generic-insurance-appointment-pressure-calibration-002

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-insurance-regression-001`
- Vertical: `insurance`
- Scenario: `appointment_pressure_calibration`
- Focus areas: appointment_pressure_calibration
- Risk tags: hard_case, edge_case, appointment_pressure
- Expected behavior: Agent should calibrate pressure across maybe, not sure, info-first, maybe-later, and callback timing.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you h... | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short lice... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | maybe | No problem. If you are not sure about coverage fit, premium or budget, or renewal or timing, I can ask one simpler question or stop here. | No problem. If you are not sure about coverage fit, premium or budget, or renewal or timing, I can ask one simpler question or stop here. | No problem. If you are not sure about coverage fit, premium or budget, or renewal or timing, I can ask one simpler qu... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 4 | not sure | I am checking coverage fit, premium or budget, or renewal or timing for a possible licensed coverage review. Which part should I ask about first, if any? | I am checking coverage fit, premium or budget, or renewal or timing for a possible licensed coverage review. Which part should I ask about first, if any? | I am checking coverage fit, premium or budget, or renewal or timing for a possible licensed coverage review. Which pa... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 5 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | contextual_buyer_semantics | continue-call |
| 6 | maybe later | No problem. What time should I call back? | No problem. What time should I call back? | No problem. What time should I call back? | callback_scheduling_request |  |  |  | contextual_buyer_semantics | continue-call |
| 7 | tomorrow at 3 works | Confirmed. I will record that callback time for a licensed insurance specialist about the licensed coverage review. Goodbye. | Confirmed. I will record that callback time for a licensed insurance specialist about the licensed coverage review. Goodbye. | Confirmed. I will record that callback time for a licensed insurance specialist about the licensed coverage review. G... | callback_time_provided |  |  |  | contextual_buyer_semantics | schedule-and-end |

### delta-generic-insurance-support-out-of-scope-boundary-003

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-insurance-regression-001`
- Vertical: `insurance`
- Scenario: `support_out_of_scope_boundary`
- Focus areas: support_out_of_scope_boundaries
- Risk tags: hard_case, edge_case, support_boundary
- Expected behavior: Support, account, order, claim, warranty, or department turns should not become fake support actions.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you h... | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short lice... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | what is included? | For Policy Review Call, I should stick to approved details. I am only checking whether coverage fit, premium or budget, or renewal or timing should go to a short licensed coverage review. | For Policy Review Call, I should stick to approved details. I am only checking whether coverage fit, premium or budget, or renewal or timing should go to a s... | For Policy Review Call, I should stick to approved details. I am only checking whether coverage fit, premium or budge... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 4 | can you handle my claim? | I am checking coverage fit, premium or budget, or renewal or timing for a possible licensed coverage review. Which part should I ask about first, if any? | I am checking coverage fit, premium or budget, or renewal or timing for a possible licensed coverage review. Which part should I ask about first, if any? | I am checking coverage fit, premium or budget, or renewal or timing for a possible licensed coverage review. Which pa... | no_contextual_semantic |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 5 | wrong department | Understood. Who is the right person or team for licensed coverage review, or should I stop here? | Understood. Who is the right person or team for licensed coverage review, or should I stop here? | Understood. Who is the right person or team for licensed coverage review, or should I stop here? | wrong_person_or_wrong_department |  |  |  | contextual_buyer_semantics | continue-call |
| 6 | talk to support | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | wrong_person_or_wrong_department |  |  |  | contextual_buyer_semantics | continue-call |

### delta-generic-insurance-confusion-explanation-quality-004

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-insurance-regression-001`
- Vertical: `insurance`
- Scenario: `confusion_explanation_quality`
- Focus areas: confusion_explanation_quality, appointment_pressure_calibration
- Risk tags: hard_case, edge_case, explanation_quality
- Expected behavior: Confusion and process questions should be answered in campaign terms without repeating the same diagnostic loop.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you h... | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short lice... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | I don't understand | Sorry, I meant the areas in this fit check: coverage fit, premium or budget, or renewal or timing. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: coverage fit, premium or budget, or renewal or timing. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: coverage fit, premium or budget, or renewal or timing. Which part causes... | confusion_not_clear |  |  |  | contextual_buyer_semantics | continue-call |
| 4 | what do you mean? | I am checking coverage fit, premium or budget, or renewal or timing for a possible licensed coverage review. Which part should I ask about first, if any? | I am checking coverage fit, premium or budget, or renewal or timing for a possible licensed coverage review. Which part should I ask about first, if any? | I am checking coverage fit, premium or budget, or renewal or timing for a possible licensed coverage review. Which pa... | previous_question_clarification |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 5 | what are you asking? | I am checking coverage fit, premium or budget, or renewal or timing for a possible licensed coverage review. Which part should I ask about first, if any? | I am checking coverage fit, premium or budget, or renewal or timing for a possible licensed coverage review. Which part should I ask about first, if any? | I am checking coverage fit, premium or budget, or renewal or timing for a possible licensed coverage review. Which pa... | confusion_not_clear |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 6 | what happens next? | If coverage fit, premium or budget, or renewal or timing are actually relevant, a licensed insurance specialist can do a short licensed coverage review. If not, I can stop here; should I... | If coverage fit, premium or budget, or renewal or timing are actually relevant, a licensed insurance specialist can do a short licensed coverage review. If n... | If coverage fit, premium or budget, or renewal or timing are actually relevant, a licensed insurance specialist can d... | no_contextual_semantic |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 7 | what is included? | For Policy Review Call, I should stick to approved details. I am only checking whether coverage fit, premium or budget, or renewal or timing should go to a short licensed coverage review. | For Policy Review Call, I should stick to approved details. I am only checking whether coverage fit, premium or budget, or renewal or timing should go to a s... | For Policy Review Call, I should stick to approved details. I am only checking whether coverage fit, premium or budge... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 8 | is it expensive? | I do not have approved pricing to quote here. A licensed insurance specialist should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A licensed insurance specialist should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A licensed insurance specialist should confirm cost and terms before an... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |

### delta-generic-insurance-long-state-drift-delta-005

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-insurance-regression-001`
- Vertical: `insurance`
- Scenario: `long_state_drift_delta`
- Focus areas: long_state_drift, appointment_pressure_calibration
- Risk tags: hard_case, edge_case, state_drift
- Expected behavior: Long conversation should preserve clear, pain, contact/callback, support boundary, and terminal state.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you h... | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short lice... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | coverage fit is handled | Got it, coverage fit is clear. Should I check premium or budget or renewal or timing, or stop here? | Got it, coverage fit is clear. Should I check premium or budget or renewal or timing, or stop here? | Got it, coverage fit is clear. Should I check premium or budget or renewal or timing, or stop here? | current_gap_clear | coverage_fit | coverage_fit |  | contextual_buyer_semantics | continue-call |
| 4 | premium is a problem | Got it, premium and budget pressure is the real gap. The next step would be a short licensed coverage review; what time works for that review? | Got it, premium and budget pressure is the real gap. The next step would be a short licensed coverage review; what time works for that review? | Got it, premium and budget pressure is the real gap. The next step would be a short licensed coverage review; what ti... | pain_confirmed | premium_or_budget | coverage_fit | premium_or_budget | contextual_buyer_semantics | continue-call |
| 5 | send me details first | No problem. I can send a short summary focused on premium and budget pressure. What email or callback time should I note? | No problem. I can send a short summary focused on premium and budget pressure. What email or callback time should I note? | No problem. I can send a short summary focused on premium and budget pressure. What email or callback time should I n... | send_info_with_confirmed_pain | premium_or_budget | coverage_fit | premium_or_budget | contextual_buyer_semantics | continue-call |
| 6 | send it to <email:sha256_12:6db61e6dcbcf> | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | email_provided |  | coverage_fit | premium_or_budget | contextual_buyer_semantics | continue-call |
| 7 | what happens next? | That sounds like the area to review, so the next step would be a short licensed coverage review. A licensed insurance specialist can review premium and budget pressure against the details... | That sounds like the area to review, so the next step would be a short licensed coverage review. A licensed insurance specialist can review premium and budge... | That sounds like the area to review, so the next step would be a short licensed coverage review. A licensed insurance... | no_contextual_semantic |  | coverage_fit | premium_or_budget | dialogue_pragmatics | continue-call |
| 8 | can you handle my claim? | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | no_contextual_semantic |  | coverage_fit | premium_or_budget | pre_speech_conversation_stability_guard | continue-call |
| 9 | stop calling | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | stop_request |  | coverage_fit | premium_or_budget | contextual_buyer_semantics | end-call |

### delta-generic-telecom-post-5a1-fix-replay-001

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-telecom-regression-001`
- Vertical: `telecom`
- Scenario: `post_5a1_fix_replay`
- Focus areas: 5a1_replayed_fixes, support_out_of_scope_boundaries
- Risk tags: hard_case, edge_case, post_patch_replay
- Expected behavior: Next-step explanation after confirmed pain should explain process before any further diagnostic.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you hav... | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan a... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | coverage is the issue | Got it, coverage and availability fit is the real gap. The next step would be a short plan and coverage review; what time works for that review? | Got it, coverage and availability fit is the real gap. The next step would be a short plan and coverage review; what time works for that review? | Got it, coverage and availability fit is the real gap. The next step would be a short plan and coverage review; what... | pain_confirmed | coverage_or_availability |  | coverage_or_availability | contextual_buyer_semantics | continue-call |
| 4 | what happens next? | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | no_contextual_semantic |  |  | coverage_or_availability | pre_speech_conversation_stability_guard | continue-call |
| 5 | can you change my plan? | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. Which part should I ask about first, if any? | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. Which part should I ask about first, if any? | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. W... | no_contextual_semantic |  |  | coverage_or_availability | pre_speech_conversation_stability_guard | continue-call |

### delta-generic-telecom-appointment-pressure-calibration-002

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-telecom-regression-001`
- Vertical: `telecom`
- Scenario: `appointment_pressure_calibration`
- Focus areas: appointment_pressure_calibration
- Risk tags: hard_case, edge_case, appointment_pressure
- Expected behavior: Agent should calibrate pressure across maybe, not sure, info-first, maybe-later, and callback timing.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you hav... | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan a... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | maybe | No problem. If you are not sure about coverage or availability, plan fit, or contract or switching, I can ask one simpler question or stop here. | No problem. If you are not sure about coverage or availability, plan fit, or contract or switching, I can ask one simpler question or stop here. | No problem. If you are not sure about coverage or availability, plan fit, or contract or switching, I can ask one sim... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 4 | not sure | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. Which part should I ask about first, if any? | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. Which part should I ask about first, if any? | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. W... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 5 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | contextual_buyer_semantics | continue-call |
| 6 | maybe later | No problem. What time should I call back? | No problem. What time should I call back? | No problem. What time should I call back? | callback_scheduling_request |  |  |  | contextual_buyer_semantics | continue-call |
| 7 | tomorrow at 3 works | Confirmed. I will record that callback time for a telecom plan specialist about the plan and coverage review. Goodbye. | Confirmed. I will record that callback time for a telecom plan specialist about the plan and coverage review. Goodbye. | Confirmed. I will record that callback time for a telecom plan specialist about the plan and coverage review. Goodbye. | callback_time_provided |  |  |  | contextual_buyer_semantics | schedule-and-end |

### delta-generic-telecom-support-out-of-scope-boundary-003

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-telecom-regression-001`
- Vertical: `telecom`
- Scenario: `support_out_of_scope_boundary`
- Focus areas: support_out_of_scope_boundaries
- Risk tags: hard_case, edge_case, support_boundary
- Expected behavior: Support, account, order, claim, warranty, or department turns should not become fake support actions.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you hav... | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan a... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | what is included? | For Plan Review Call, I should stick to approved details. I am only checking whether coverage or availability, plan fit, or contract or switching should go to a short plan and coverage re... | For Plan Review Call, I should stick to approved details. I am only checking whether coverage or availability, plan fit, or contract or switching should go t... | For Plan Review Call, I should stick to approved details. I am only checking whether coverage or availability, plan f... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 4 | can you change my plan? | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. Which part should I ask about first, if any? | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. Which part should I ask about first, if any? | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. W... | no_contextual_semantic |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 5 | wrong department | Understood. Who is the right person or team for plan and coverage review, or should I stop here? | Understood. Who is the right person or team for plan and coverage review, or should I stop here? | Understood. Who is the right person or team for plan and coverage review, or should I stop here? | wrong_person_or_wrong_department |  |  |  | contextual_buyer_semantics | continue-call |
| 6 | talk to support | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | wrong_person_or_wrong_department |  |  |  | contextual_buyer_semantics | continue-call |

### delta-generic-telecom-confusion-explanation-quality-004

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-telecom-regression-001`
- Vertical: `telecom`
- Scenario: `confusion_explanation_quality`
- Focus areas: confusion_explanation_quality, appointment_pressure_calibration
- Risk tags: hard_case, edge_case, explanation_quality
- Expected behavior: Confusion and process questions should be answered in campaign terms without repeating the same diagnostic loop.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you hav... | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan a... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | I don't understand | Sorry, I meant the areas in this fit check: coverage or availability, plan fit, or contract or switching. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: coverage or availability, plan fit, or contract or switching. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: coverage or availability, plan fit, or contract or switching. Which part... | confusion_not_clear |  |  |  | contextual_buyer_semantics | continue-call |
| 4 | what do you mean? | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. Which part should I ask about first, if any? | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. Which part should I ask about first, if any? | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. W... | previous_question_clarification |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 5 | what are you asking? | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. Which part should I ask about first, if any? | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. Which part should I ask about first, if any? | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. W... | confusion_not_clear |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 6 | what happens next? | If coverage or availability, plan fit, or contract or switching are actually relevant, a telecom plan specialist can do a short plan and coverage review. If not, I can stop here; should I... | If coverage or availability, plan fit, or contract or switching are actually relevant, a telecom plan specialist can do a short plan and coverage review. If... | If coverage or availability, plan fit, or contract or switching are actually relevant, a telecom plan specialist can... | no_contextual_semantic |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 7 | what is included? | For Plan Review Call, I should stick to approved details. I am only checking whether coverage or availability, plan fit, or contract or switching should go to a short plan and coverage re... | For Plan Review Call, I should stick to approved details. I am only checking whether coverage or availability, plan fit, or contract or switching should go t... | For Plan Review Call, I should stick to approved details. I am only checking whether coverage or availability, plan f... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 8 | is it expensive? | I do not have approved pricing to quote here. A telecom plan specialist should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A telecom plan specialist should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A telecom plan specialist should confirm cost and terms before any next... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |

### delta-generic-telecom-long-state-drift-delta-005

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-telecom-regression-001`
- Vertical: `telecom`
- Scenario: `long_state_drift_delta`
- Focus areas: long_state_drift, appointment_pressure_calibration
- Risk tags: hard_case, edge_case, state_drift
- Expected behavior: Long conversation should preserve clear, pain, contact/callback, support boundary, and terminal state.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you hav... | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan a... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | okay quick | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | coverage is sometimes an issue | Got it, coverage and availability fit is the real gap. The next step would be a short plan and coverage review; what time works for that review? | Got it, coverage and availability fit is the real gap. The next step would be a short plan and coverage review; what time works for that review? | Got it, coverage and availability fit is the real gap. The next step would be a short plan and coverage review; what... | pain_confirmed | coverage_or_availability |  | coverage_or_availability | contextual_buyer_semantics | continue-call |
| 4 | what do you mean? | Sorry, I meant the areas in this fit check: coverage or availability, plan fit, or contract or switching. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: coverage or availability, plan fit, or contract or switching. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: coverage or availability, plan fit, or contract or switching. Which part... | previous_question_clarification |  |  | coverage_or_availability | contextual_buyer_semantics | continue-call |
| 5 | coverage is the issue | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. Which part should I ask about first, if any? | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. Which part should I ask about first, if any? | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. W... | pain_confirmed | coverage_or_availability |  | coverage_or_availability | duplicate_response_repair | continue-call |
| 6 | call me next Tuesday at 10 | Confirmed. I will note that time for the plan and coverage review. Goodbye. | Confirmed. I will note that time for the plan and coverage review. Goodbye. | Confirmed. I will note that time for the plan and coverage review. Goodbye. | appointment_time_given | coverage_or_availability |  | coverage_or_availability | contextual_buyer_semantics | schedule-and-end |
| 7 | can you change my plan? | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | no_contextual_semantic |  |  | coverage_or_availability | terminal_call_control | end-call |
| 8 | stop calling | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | stop_request |  |  | coverage_or_availability | terminal_call_control | end-call |

### delta-generic-home-services-post-5a1-fix-replay-001

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-home-services-regression-001`
- Vertical: `home_services`
- Scenario: `post_5a1_fix_replay`
- Focus areas: 5a1_replayed_fixes, regulated_caution
- Risk tags: hard_case, edge_case, post_patch_replay
- Expected behavior: Risky claims after confirmed pain should stay cautious and process-aware.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you ha... | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short serv... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | estimate is unclear | Got it, estimate details and property context is the real gap. The next step would be a short service estimate review; what time works for that review? | Got it, estimate details and property context is the real gap. The next step would be a short service estimate review; what time works for that review? | Got it, estimate details and property context is the real gap. The next step would be a short service estimate review... | pain_confirmed | estimate_or_property_details |  | estimate_or_property_details | contextual_buyer_semantics | continue-call |
| 4 | what happens next? | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | no_contextual_semantic |  |  | estimate_or_property_details | pre_speech_conversation_stability_guard | continue-call |
| 5 | can you quote exact price now? | I cannot give an exact price without property details or inspection. A service advisor needs verified details before quoting. Is estimate details and property context what you want reviewed? | I cannot give an exact price without property details or inspection. A service advisor needs verified details before quoting. Is estimate details and propert... | I cannot give an exact price without property details or inspection. A service advisor needs verified details before... | campaign_claim_boundary_caution | estimate_or_property_details |  | estimate_or_property_details | contextual_buyer_semantics | continue-call |

### delta-generic-home-services-appointment-pressure-calibration-002

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-home-services-regression-001`
- Vertical: `home_services`
- Scenario: `appointment_pressure_calibration`
- Focus areas: appointment_pressure_calibration
- Risk tags: hard_case, edge_case, appointment_pressure
- Expected behavior: Agent should calibrate pressure across maybe, not sure, info-first, maybe-later, and callback timing.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you ha... | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short serv... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | maybe | No problem. If you are not sure about service need, scheduling urgency, or estimate or property details, I can ask one simpler question or stop here. | No problem. If you are not sure about service need, scheduling urgency, or estimate or property details, I can ask one simpler question or stop here. | No problem. If you are not sure about service need, scheduling urgency, or estimate or property details, I can ask on... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 4 | not sure | I am checking service need, scheduling urgency, or estimate or property details for a possible service estimate review. Which part should I ask about first, if any? | I am checking service need, scheduling urgency, or estimate or property details for a possible service estimate review. Which part should I ask about first,... | I am checking service need, scheduling urgency, or estimate or property details for a possible service estimate revie... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 5 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | contextual_buyer_semantics | continue-call |
| 6 | maybe later | No problem. What time should I call back? | No problem. What time should I call back? | No problem. What time should I call back? | callback_scheduling_request |  |  |  | contextual_buyer_semantics | continue-call |
| 7 | tomorrow at 3 works | Confirmed. I will record that callback time for a service advisor about the service estimate review. Goodbye. | Confirmed. I will record that callback time for a service advisor about the service estimate review. Goodbye. | Confirmed. I will record that callback time for a service advisor about the service estimate review. Goodbye. | callback_time_provided |  |  |  | contextual_buyer_semantics | schedule-and-end |

### delta-generic-home-services-support-out-of-scope-boundary-003

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-home-services-regression-001`
- Vertical: `home_services`
- Scenario: `support_out_of_scope_boundary`
- Focus areas: support_out_of_scope_boundaries
- Risk tags: hard_case, edge_case, support_boundary
- Expected behavior: Support, account, order, claim, warranty, or department turns should not become fake support actions.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you ha... | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short serv... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | what is included? | For Service Estimate Call, I should stick to approved details. I am only checking whether service need, scheduling urgency, or estimate or property details should go to a short service es... | For Service Estimate Call, I should stick to approved details. I am only checking whether service need, scheduling urgency, or estimate or property details s... | For Service Estimate Call, I should stick to approved details. I am only checking whether service need, scheduling ur... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 4 | talk to support | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | wrong_person_or_wrong_department |  |  |  | contextual_buyer_semantics | continue-call |
| 5 | wrong department | Understood. Who is the right person or team for service estimate review, or should I stop here? | Understood. Who is the right person or team for service estimate review, or should I stop here? | Understood. Who is the right person or team for service estimate review, or should I stop here? | wrong_person_or_wrong_department |  |  |  | contextual_buyer_semantics | continue-call |
| 6 | talk to support | I am checking service need, scheduling urgency, or estimate or property details for a possible service estimate review. Which part should I ask about first, if any? | I am checking service need, scheduling urgency, or estimate or property details for a possible service estimate review. Which part should I ask about first,... | I am checking service need, scheduling urgency, or estimate or property details for a possible service estimate revie... | wrong_person_or_wrong_department |  |  |  | duplicate_response_repair | continue-call |

### delta-generic-home-services-confusion-explanation-quality-004

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-home-services-regression-001`
- Vertical: `home_services`
- Scenario: `confusion_explanation_quality`
- Focus areas: confusion_explanation_quality, appointment_pressure_calibration
- Risk tags: hard_case, edge_case, explanation_quality
- Expected behavior: Confusion and process questions should be answered in campaign terms without repeating the same diagnostic loop.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you ha... | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short serv... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | I don't understand | Sorry, I meant the areas in this fit check: service need, scheduling urgency, or estimate or property details. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: service need, scheduling urgency, or estimate or property details. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: service need, scheduling urgency, or estimate or property details. Which... | confusion_not_clear |  |  |  | contextual_buyer_semantics | continue-call |
| 4 | what do you mean? | I am checking service need, scheduling urgency, or estimate or property details for a possible service estimate review. Which part should I ask about first, if any? | I am checking service need, scheduling urgency, or estimate or property details for a possible service estimate review. Which part should I ask about first,... | I am checking service need, scheduling urgency, or estimate or property details for a possible service estimate revie... | previous_question_clarification |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 5 | what are you asking? | I am checking service need, scheduling urgency, or estimate or property details for a possible service estimate review. Which part should I ask about first, if any? | I am checking service need, scheduling urgency, or estimate or property details for a possible service estimate review. Which part should I ask about first,... | I am checking service need, scheduling urgency, or estimate or property details for a possible service estimate revie... | confusion_not_clear |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 6 | what happens next? | If service need, scheduling urgency, or estimate or property details are actually relevant, a service advisor can do a short service estimate review. If not, I can stop here; should I ask... | If service need, scheduling urgency, or estimate or property details are actually relevant, a service advisor can do a short service estimate review. If not,... | If service need, scheduling urgency, or estimate or property details are actually relevant, a service advisor can do... | no_contextual_semantic |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 7 | what is included? | For Service Estimate Call, I should stick to approved details. I am only checking whether service need, scheduling urgency, or estimate or property details should go to a short service es... | For Service Estimate Call, I should stick to approved details. I am only checking whether service need, scheduling urgency, or estimate or property details s... | For Service Estimate Call, I should stick to approved details. I am only checking whether service need, scheduling ur... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 8 | is it expensive? | I do not have approved pricing to quote here. A service advisor should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A service advisor should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A service advisor should confirm cost and terms before any next step. | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |

### delta-generic-home-services-long-state-drift-delta-005

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-home-services-regression-001`
- Vertical: `home_services`
- Scenario: `long_state_drift_delta`
- Focus areas: long_state_drift, appointment_pressure_calibration
- Risk tags: hard_case, edge_case, state_drift
- Expected behavior: Long conversation should preserve clear, pain, contact/callback, support boundary, and terminal state.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you ha... | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short serv... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yes | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | scheduling is fine | Got it, scheduling urgency is clear. Should I check service need or estimate or property details, or stop here? | Got it, scheduling urgency is clear. Should I check service need or estimate or property details, or stop here? | Got it, scheduling urgency is clear. Should I check service need or estimate or property details, or stop here? | current_gap_clear | scheduling_urgency | scheduling_urgency |  | contextual_buyer_semantics | continue-call |
| 4 | estimate is unclear | Got it, estimate details and property context is the real gap. The next step would be a short service estimate review; what time works for that review? | Got it, estimate details and property context is the real gap. The next step would be a short service estimate review; what time works for that review? | Got it, estimate details and property context is the real gap. The next step would be a short service estimate review... | pain_confirmed | estimate_or_property_details | scheduling_urgency | estimate_or_property_details | contextual_buyer_semantics | continue-call |
| 5 | can you quote exact price now? | I cannot give an exact price without property details or inspection. A service advisor needs verified details before quoting. Is estimate details and property context what you want reviewed? | I cannot give an exact price without property details or inspection. A service advisor needs verified details before quoting. Is estimate details and propert... | I cannot give an exact price without property details or inspection. A service advisor needs verified details before... | campaign_claim_boundary_caution | estimate_or_property_details | scheduling_urgency | estimate_or_property_details | contextual_buyer_semantics | continue-call |
| 6 | send me details first | No problem. I can send a short summary focused on estimate details and property context. What email or callback time should I note? | No problem. I can send a short summary focused on estimate details and property context. What email or callback time should I note? | No problem. I can send a short summary focused on estimate details and property context. What email or callback time... | send_info_with_confirmed_pain | estimate_or_property_details | scheduling_urgency | estimate_or_property_details | contextual_buyer_semantics | continue-call |
| 7 | tomorrow at 3 works | Confirmed. I will record that callback time for a service advisor about the service estimate review. Goodbye. | Confirmed. I will record that callback time for a service advisor about the service estimate review. Goodbye. | Confirmed. I will record that callback time for a service advisor about the service estimate review. Goodbye. | callback_time_provided |  | scheduling_urgency | estimate_or_property_details | contextual_buyer_semantics | schedule-and-end |
| 8 | stop calling | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | stop_request |  | scheduling_urgency | estimate_or_property_details | terminal_call_control | end-call |

### delta-generic-healthcare-admin-or-medical-equipment-post-5a1-fix-replay-001

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-healthcare-admin-regression-001`
- Vertical: `healthcare_admin_or_medical_equipment`
- Scenario: `post_5a1_fix_replay`
- Focus areas: 5a1_replayed_fixes, regulated_caution
- Risk tags: hard_case, edge_case, post_patch_replay
- Expected behavior: Risky claims after confirmed pain should stay cautious and process-aware.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do yo... | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causin... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | specialist review is needed | Got it, specialist review need is the real gap. The next step would be a short specialist admin review; what time works for that review? | Got it, specialist review need is the real gap. The next step would be a short specialist admin review; what time works for that review? | Got it, specialist review need is the real gap. The next step would be a short specialist admin review; what time wor... | pain_confirmed | specialist_review_needed |  | specialist_review_needed | contextual_buyer_semantics | continue-call |
| 4 | what happens next? | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | no_contextual_semantic |  |  | specialist_review_needed | pre_speech_conversation_stability_guard | continue-call |
| 5 | can you guarantee this equipment solves the issue? | I cannot promise an equipment or service outcome here. A specialist review coordinator needs verified admin and specialist details first. Is specialist review need what you want reviewed? | I cannot promise an equipment or service outcome here. A specialist review coordinator needs verified admin and specialist details first. Is specialist revie... | I cannot promise an equipment or service outcome here. A specialist review coordinator needs verified admin and speci... | campaign_claim_boundary_caution | specialist_review_needed |  | specialist_review_needed | contextual_buyer_semantics | transfer-or-escalate |

### delta-generic-healthcare-admin-or-medical-equipment-appointment-pressure-calibration-002

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-healthcare-admin-regression-001`
- Vertical: `healthcare_admin_or_medical_equipment`
- Scenario: `appointment_pressure_calibration`
- Focus areas: appointment_pressure_calibration
- Risk tags: hard_case, edge_case, appointment_pressure
- Expected behavior: Agent should calibrate pressure across maybe, not sure, info-first, maybe-later, and callback timing.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do yo... | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causin... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | maybe | No problem. If you are not sure about admin workflow need, equipment or service fit, or specialist review needed, I can ask one simpler question or stop here. | No problem. If you are not sure about admin workflow need, equipment or service fit, or specialist review needed, I can ask one simpler question or stop here. | No problem. If you are not sure about admin workflow need, equipment or service fit, or specialist review needed, I c... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 4 | not sure | I am checking admin workflow need, equipment or service fit, or specialist review needed for a possible specialist admin review. Which part should I ask about first, if any? | I am checking admin workflow need, equipment or service fit, or specialist review needed for a possible specialist admin review. Which part should I ask abou... | I am checking admin workflow need, equipment or service fit, or specialist review needed for a possible specialist ad... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 5 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | contextual_buyer_semantics | continue-call |
| 6 | maybe later | No problem. What time should I call back? | No problem. What time should I call back? | No problem. What time should I call back? | callback_scheduling_request |  |  |  | contextual_buyer_semantics | continue-call |
| 7 | tomorrow at 3 works | Confirmed. I will record that callback time for a specialist review coordinator about the specialist admin review. Goodbye. | Confirmed. I will record that callback time for a specialist review coordinator about the specialist admin review. Goodbye. | Confirmed. I will record that callback time for a specialist review coordinator about the specialist admin review. Go... | callback_time_provided |  |  |  | contextual_buyer_semantics | schedule-and-end |

### delta-generic-healthcare-admin-or-medical-equipment-support-out-of-scope-boundary-003

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-healthcare-admin-regression-001`
- Vertical: `healthcare_admin_or_medical_equipment`
- Scenario: `support_out_of_scope_boundary`
- Focus areas: support_out_of_scope_boundaries
- Risk tags: hard_case, edge_case, support_boundary
- Expected behavior: Support, account, order, claim, warranty, or department turns should not become fake support actions.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do yo... | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causin... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | what is included? | For Admin Equipment Review, I should stick to approved details. I am only checking whether admin workflow need, equipment or service fit, or specialist review needed should go to a short... | For Admin Equipment Review, I should stick to approved details. I am only checking whether admin workflow need, equipment or service fit, or specialist revie... | For Admin Equipment Review, I should stick to approved details. I am only checking whether admin workflow need, equip... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 4 | can you guarantee this equipment solves the issue? | I cannot promise an equipment or service outcome here. A specialist review coordinator needs verified admin and specialist details first. Is specialist review need what you want reviewed? | I cannot promise an equipment or service outcome here. A specialist review coordinator needs verified admin and specialist details first. Is specialist revie... | I cannot promise an equipment or service outcome here. A specialist review coordinator needs verified admin and speci... | campaign_claim_boundary_caution | specialist_review_needed |  |  | contextual_buyer_semantics | transfer-or-escalate |
| 5 | wrong department | Understood. Who is the right person or team for specialist admin review, or should I stop here? | Understood. Who is the right person or team for specialist admin review, or should I stop here? | Understood. Who is the right person or team for specialist admin review, or should I stop here? | wrong_person_or_wrong_department |  |  |  | contextual_buyer_semantics | continue-call |
| 6 | talk to support | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | wrong_person_or_wrong_department |  |  |  | contextual_buyer_semantics | continue-call |

### delta-generic-healthcare-admin-or-medical-equipment-confusion-explanation-quality-004

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-healthcare-admin-regression-001`
- Vertical: `healthcare_admin_or_medical_equipment`
- Scenario: `confusion_explanation_quality`
- Focus areas: confusion_explanation_quality, appointment_pressure_calibration
- Risk tags: hard_case, edge_case, explanation_quality
- Expected behavior: Confusion and process questions should be answered in campaign terms without repeating the same diagnostic loop.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do yo... | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causin... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | I don't understand | Sorry, I meant the areas in this fit check: admin workflow need, equipment or service fit, or specialist review needed. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: admin workflow need, equipment or service fit, or specialist review needed. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: admin workflow need, equipment or service fit, or specialist review neede... | confusion_not_clear |  |  |  | contextual_buyer_semantics | continue-call |
| 4 | what do you mean? | I am checking admin workflow need, equipment or service fit, or specialist review needed for a possible specialist admin review. Which part should I ask about first, if any? | I am checking admin workflow need, equipment or service fit, or specialist review needed for a possible specialist admin review. Which part should I ask abou... | I am checking admin workflow need, equipment or service fit, or specialist review needed for a possible specialist ad... | previous_question_clarification |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 5 | what are you asking? | I am checking admin workflow need, equipment or service fit, or specialist review needed for a possible specialist admin review. Which part should I ask about first, if any? | I am checking admin workflow need, equipment or service fit, or specialist review needed for a possible specialist admin review. Which part should I ask abou... | I am checking admin workflow need, equipment or service fit, or specialist review needed for a possible specialist ad... | confusion_not_clear |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 6 | what happens next? | If admin workflow need, equipment or service fit, or specialist review needed are actually relevant, a specialist review coordinator can do a short specialist admin review. If not, I can... | If admin workflow need, equipment or service fit, or specialist review needed are actually relevant, a specialist review coordinator can do a short specialis... | If admin workflow need, equipment or service fit, or specialist review needed are actually relevant, a specialist rev... | no_contextual_semantic |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 7 | what is included? | For Admin Equipment Review, I should stick to approved details. I am only checking whether admin workflow need, equipment or service fit, or specialist review needed should go to a short... | For Admin Equipment Review, I should stick to approved details. I am only checking whether admin workflow need, equipment or service fit, or specialist revie... | For Admin Equipment Review, I should stick to approved details. I am only checking whether admin workflow need, equip... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 8 | is it expensive? | I do not have approved pricing to quote here. A specialist review coordinator should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A specialist review coordinator should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A specialist review coordinator should confirm cost and terms before an... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |

### delta-generic-healthcare-admin-or-medical-equipment-long-state-drift-delta-005

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-healthcare-admin-regression-001`
- Vertical: `healthcare_admin_or_medical_equipment`
- Scenario: `long_state_drift_delta`
- Focus areas: long_state_drift, appointment_pressure_calibration
- Risk tags: hard_case, edge_case, state_drift
- Expected behavior: Long conversation should preserve clear, pain, contact/callback, support boundary, and terminal state.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do yo... | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causin... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | equipment fit is handled | Got it, equipment or service fit is clear. Should I check admin workflow need or specialist review needed, or stop here? | Got it, equipment or service fit is clear. Should I check admin workflow need or specialist review needed, or stop here? | Got it, equipment or service fit is clear. Should I check admin workflow need or specialist review needed, or stop here? | current_gap_clear | equipment_or_service_fit | equipment_or_service_fit |  | contextual_buyer_semantics | continue-call |
| 4 | specialist review is needed | Got it, specialist review need is the real gap. The next step would be a short specialist admin review; what time works for that review? | Got it, specialist review need is the real gap. The next step would be a short specialist admin review; what time works for that review? | Got it, specialist review need is the real gap. The next step would be a short specialist admin review; what time wor... | pain_confirmed | specialist_review_needed | equipment_or_service_fit | specialist_review_needed | contextual_buyer_semantics | continue-call |
| 5 | can you guarantee this equipment solves the issue? | I cannot promise an equipment or service outcome here. A specialist review coordinator needs verified admin and specialist details first. Is specialist review need what you want reviewed? | I cannot promise an equipment or service outcome here. A specialist review coordinator needs verified admin and specialist details first. Is specialist revie... | I cannot promise an equipment or service outcome here. A specialist review coordinator needs verified admin and speci... | campaign_claim_boundary_caution | specialist_review_needed | equipment_or_service_fit | specialist_review_needed | contextual_buyer_semantics | transfer-or-escalate |
| 6 | what happens next? | For Admin Equipment Review, I should stick to approved details. I am only checking whether admin workflow need, equipment or service fit, or specialist review needed should go to a short... | For Admin Equipment Review, I should stick to approved details. I am only checking whether admin workflow need, equipment or service fit, or specialist revie... | For Admin Equipment Review, I should stick to approved details. I am only checking whether admin workflow need, equip... | no_contextual_semantic |  | equipment_or_service_fit | specialist_review_needed | pre_speech_conversation_stability_guard | continue-call |
| 7 | tomorrow at 3 works | Confirmed. I will note that time for the specialist admin review. Goodbye. | Confirmed. I will note that time for the specialist admin review. Goodbye. | Confirmed. I will note that time for the specialist admin review. Goodbye. | appointment_time_given | specialist_review_needed | equipment_or_service_fit | specialist_review_needed | contextual_buyer_semantics | schedule-and-end |

### delta-generic-automotive-service-post-5a1-fix-replay-001

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-automotive-service-regression-001`
- Vertical: `automotive_service`
- Scenario: `post_5a1_fix_replay`
- Focus areas: 5a1_replayed_fixes, appointment_pressure_calibration, confusion_explanation_quality
- Risk tags: hard_case, edge_case, post_patch_replay
- Expected behavior: Uncertainty after fallback repair should not become RouteSignal/B2B demo language or appointment pressure.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is n... | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a shor... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | I do not understand | Sorry, I meant the areas in this fit check: vehicle issue, repair timing, or warranty or estimate. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: vehicle issue, repair timing, or warranty or estimate. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: vehicle issue, repair timing, or warranty or estimate. Which part causes... | confusion_not_clear |  |  |  | contextual_buyer_semantics | continue-call |
| 4 | what is this about? | I am calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether vehicle issue, repair timing, or warranty or estimate should go to a short service advis... | I am calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether vehicle issue, repair timing, or warranty or estimate shou... | I am calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether vehicle issue, rep... | no_contextual_semantic |  |  |  | dialogue_pragmatics | continue-call |
| 5 | what happens next? | I am checking vehicle issue, repair timing, or warranty or estimate for a possible service advisor inspection review. Which part should I ask about first, if any? | I am checking vehicle issue, repair timing, or warranty or estimate for a possible service advisor inspection review. Which part should I ask about first, if... | I am checking vehicle issue, repair timing, or warranty or estimate for a possible service advisor inspection review.... | no_contextual_semantic |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 6 | maybe | No problem. If you are not sure about vehicle issue, repair timing, or warranty or estimate, I can ask one simpler question or stop here. | No problem. If you are not sure about vehicle issue, repair timing, or warranty or estimate, I can ask one simpler question or stop here. | No problem. If you are not sure about vehicle issue, repair timing, or warranty or estimate, I can ask one simpler qu... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 7 | not sure | No problem. If you are not sure, I can clarify whether vehicle issue, repair timing, or warranty or estimate matter here, or I can stop here. | No problem. If you are not sure, I can clarify whether vehicle issue, repair timing, or warranty or estimate matter here, or I can stop here. | No problem. If you are not sure, I can clarify whether vehicle issue, repair timing, or warranty or estimate matter h... | no_contextual_semantic |  |  |  | duplicate_response_repair | continue-call |

### delta-generic-automotive-service-appointment-pressure-calibration-002

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-automotive-service-regression-001`
- Vertical: `automotive_service`
- Scenario: `appointment_pressure_calibration`
- Focus areas: appointment_pressure_calibration
- Risk tags: hard_case, edge_case, appointment_pressure
- Expected behavior: Agent should calibrate pressure across maybe, not sure, info-first, maybe-later, and callback timing.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is n... | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a shor... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | maybe | No problem. If you are not sure about vehicle issue, repair timing, or warranty or estimate, I can ask one simpler question or stop here. | No problem. If you are not sure about vehicle issue, repair timing, or warranty or estimate, I can ask one simpler question or stop here. | No problem. If you are not sure about vehicle issue, repair timing, or warranty or estimate, I can ask one simpler qu... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 4 | not sure | I am checking vehicle issue, repair timing, or warranty or estimate for a possible service advisor inspection review. Which part should I ask about first, if any? | I am checking vehicle issue, repair timing, or warranty or estimate for a possible service advisor inspection review. Which part should I ask about first, if... | I am checking vehicle issue, repair timing, or warranty or estimate for a possible service advisor inspection review.... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 5 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | contextual_buyer_semantics | continue-call |
| 6 | maybe later | No problem. What time should I call back? | No problem. What time should I call back? | No problem. What time should I call back? | callback_scheduling_request |  |  |  | contextual_buyer_semantics | continue-call |
| 7 | tomorrow at 3 works | Confirmed. I will record that callback time for a service advisor about the service advisor inspection review. Goodbye. | Confirmed. I will record that callback time for a service advisor about the service advisor inspection review. Goodbye. | Confirmed. I will record that callback time for a service advisor about the service advisor inspection review. Goodbye. | callback_time_provided |  |  |  | contextual_buyer_semantics | schedule-and-end |

### delta-generic-automotive-service-support-out-of-scope-boundary-003

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-automotive-service-regression-001`
- Vertical: `automotive_service`
- Scenario: `support_out_of_scope_boundary`
- Focus areas: support_out_of_scope_boundaries
- Risk tags: hard_case, edge_case, support_boundary
- Expected behavior: Support, account, order, claim, warranty, or department turns should not become fake support actions.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is n... | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a shor... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | what is included? | For Service Advisor Review, I should stick to approved details. I am only checking whether vehicle issue, repair timing, or warranty or estimate should go to a short service advisor inspe... | For Service Advisor Review, I should stick to approved details. I am only checking whether vehicle issue, repair timing, or warranty or estimate should go to... | For Service Advisor Review, I should stick to approved details. I am only checking whether vehicle issue, repair timi... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 4 | can you check my warranty? | I cannot promise repair cost or warranty outcome here. A service advisor needs verified vehicle details or inspection first. Is warranty or estimate what you want reviewed? | I cannot promise repair cost or warranty outcome here. A service advisor needs verified vehicle details or inspection first. Is warranty or estimate what you... | I cannot promise repair cost or warranty outcome here. A service advisor needs verified vehicle details or inspection... | campaign_claim_boundary_caution | warranty_or_estimate |  |  | contextual_buyer_semantics | continue-call |
| 5 | wrong department | Understood. Who is the right person or team for service advisor inspection review, or should I stop here? | Understood. Who is the right person or team for service advisor inspection review, or should I stop here? | Understood. Who is the right person or team for service advisor inspection review, or should I stop here? | wrong_person_or_wrong_department |  |  |  | contextual_buyer_semantics | continue-call |
| 6 | talk to support | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | wrong_person_or_wrong_department |  |  |  | contextual_buyer_semantics | continue-call |

### delta-generic-automotive-service-confusion-explanation-quality-004

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-automotive-service-regression-001`
- Vertical: `automotive_service`
- Scenario: `confusion_explanation_quality`
- Focus areas: confusion_explanation_quality, appointment_pressure_calibration
- Risk tags: hard_case, edge_case, explanation_quality
- Expected behavior: Confusion and process questions should be answered in campaign terms without repeating the same diagnostic loop.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is n... | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a shor... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | I don't understand | Sorry, I meant the areas in this fit check: vehicle issue, repair timing, or warranty or estimate. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: vehicle issue, repair timing, or warranty or estimate. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: vehicle issue, repair timing, or warranty or estimate. Which part causes... | confusion_not_clear |  |  |  | contextual_buyer_semantics | continue-call |
| 4 | what do you mean? | I am checking vehicle issue, repair timing, or warranty or estimate for a possible service advisor inspection review. Which part should I ask about first, if any? | I am checking vehicle issue, repair timing, or warranty or estimate for a possible service advisor inspection review. Which part should I ask about first, if... | I am checking vehicle issue, repair timing, or warranty or estimate for a possible service advisor inspection review.... | previous_question_clarification |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 5 | what are you asking? | I am checking vehicle issue, repair timing, or warranty or estimate for a possible service advisor inspection review. Which part should I ask about first, if any? | I am checking vehicle issue, repair timing, or warranty or estimate for a possible service advisor inspection review. Which part should I ask about first, if... | I am checking vehicle issue, repair timing, or warranty or estimate for a possible service advisor inspection review.... | confusion_not_clear |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 6 | what happens next? | If vehicle issue, repair timing, or warranty or estimate are actually relevant, a service advisor can do a short service advisor inspection review. If not, I can stop here; should I ask o... | If vehicle issue, repair timing, or warranty or estimate are actually relevant, a service advisor can do a short service advisor inspection review. If not, I... | If vehicle issue, repair timing, or warranty or estimate are actually relevant, a service advisor can do a short serv... | no_contextual_semantic |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 7 | what is included? | For Service Advisor Review, I should stick to approved details. I am only checking whether vehicle issue, repair timing, or warranty or estimate should go to a short service advisor inspe... | For Service Advisor Review, I should stick to approved details. I am only checking whether vehicle issue, repair timing, or warranty or estimate should go to... | For Service Advisor Review, I should stick to approved details. I am only checking whether vehicle issue, repair timi... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 8 | is it expensive? | I do not have approved pricing to quote here. A service advisor should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A service advisor should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A service advisor should confirm cost and terms before any next step. | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |

### delta-generic-automotive-service-long-state-drift-delta-005

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-automotive-service-regression-001`
- Vertical: `automotive_service`
- Scenario: `long_state_drift_delta`
- Focus areas: long_state_drift, appointment_pressure_calibration
- Risk tags: hard_case, edge_case, state_drift
- Expected behavior: Long conversation should preserve clear, pain, contact/callback, support boundary, and terminal state.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is n... | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a shor... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | I do not understand | Sorry, I meant the areas in this fit check: vehicle issue, repair timing, or warranty or estimate. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: vehicle issue, repair timing, or warranty or estimate. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: vehicle issue, repair timing, or warranty or estimate. Which part causes... | confusion_not_clear |  |  |  | contextual_buyer_semantics | continue-call |
| 4 | what is this about? | I am calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether vehicle issue, repair timing, or warranty or estimate should go to a short service advis... | I am calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether vehicle issue, repair timing, or warranty or estimate shou... | I am calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether vehicle issue, rep... | no_contextual_semantic |  |  |  | dialogue_pragmatics | continue-call |
| 5 | what happens next? | I am checking vehicle issue, repair timing, or warranty or estimate for a possible service advisor inspection review. Which part should I ask about first, if any? | I am checking vehicle issue, repair timing, or warranty or estimate for a possible service advisor inspection review. Which part should I ask about first, if... | I am checking vehicle issue, repair timing, or warranty or estimate for a possible service advisor inspection review.... | no_contextual_semantic |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 6 | maybe | No problem. If you are not sure about vehicle issue, repair timing, or warranty or estimate, I can ask one simpler question or stop here. | No problem. If you are not sure about vehicle issue, repair timing, or warranty or estimate, I can ask one simpler question or stop here. | No problem. If you are not sure about vehicle issue, repair timing, or warranty or estimate, I can ask one simpler qu... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 7 | not sure | No problem. If you are not sure, I can clarify whether vehicle issue, repair timing, or warranty or estimate matter here, or I can stop here. | No problem. If you are not sure, I can clarify whether vehicle issue, repair timing, or warranty or estimate matter here, or I can stop here. | No problem. If you are not sure, I can clarify whether vehicle issue, repair timing, or warranty or estimate matter h... | no_contextual_semantic |  |  |  | duplicate_response_repair | continue-call |
| 8 | warranty estimate is the problem | Got it, warranty or estimate is the real gap. The next step would be a short service advisor inspection review; what time works for that review? | Got it, warranty or estimate is the real gap. The next step would be a short service advisor inspection review; what time works for that review? | Got it, warranty or estimate is the real gap. The next step would be a short service advisor inspection review; what... | pain_confirmed | warranty_or_estimate |  | warranty_or_estimate | contextual_buyer_semantics | continue-call |
| 9 | I already told you | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | no_contextual_semantic |  |  | warranty_or_estimate | pre_speech_conversation_stability_guard | continue-call |
| 10 | tomorrow at 3 works | Confirmed. I will note that time for the service advisor inspection review. Goodbye. | Confirmed. I will note that time for the service advisor inspection review. Goodbye. | Confirmed. I will note that time for the service advisor inspection review. Goodbye. | appointment_time_given | warranty_or_estimate |  | warranty_or_estimate | contextual_buyer_semantics | schedule-and-end |

### delta-generic-membership-or-subscription-post-5a1-fix-replay-001

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-membership-regression-001`
- Vertical: `membership_or_subscription`
- Scenario: `post_5a1_fix_replay`
- Focus areas: 5a1_replayed_fixes, support_out_of_scope_boundaries
- Risk tags: hard_case, edge_case, post_patch_replay
- Expected behavior: Cancellation request should be an account boundary, not a fake support or sales-review action.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed;... | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a sho... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | renewal is the issue | Got it, renewal or cancellation terms is the real gap. The next step would be a short membership account review; what time works for that review? | Got it, renewal or cancellation terms is the real gap. The next step would be a short membership account review; what time works for that review? | Got it, renewal or cancellation terms is the real gap. The next step would be a short membership account review; what... | pain_confirmed | renewal_or_cancellation |  | renewal_or_cancellation | contextual_buyer_semantics | continue-call |
| 4 | what happens next? | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | no_contextual_semantic |  |  | renewal_or_cancellation | pre_speech_conversation_stability_guard | continue-call |
| 5 | can you cancel my account? | I cannot cancel or change an account on this call. Please use authorized account support; I can stop here. | I cannot cancel or change an account on this call. Please use authorized account support; I can stop here. | I cannot cancel or change an account on this call. Please use authorized account support; I can stop here. | account_support_boundary |  |  | renewal_or_cancellation | pre_speech_conversation_stability_guard | continue-call |

### delta-generic-membership-or-subscription-appointment-pressure-calibration-002

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-membership-regression-001`
- Vertical: `membership_or_subscription`
- Scenario: `appointment_pressure_calibration`
- Focus areas: appointment_pressure_calibration
- Risk tags: hard_case, edge_case, appointment_pressure
- Expected behavior: Agent should calibrate pressure across maybe, not sure, info-first, maybe-later, and callback timing.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed;... | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a sho... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | maybe | No problem. If you are not sure about plan fit, renewal or cancellation, or usage or value, I can ask one simpler question or stop here. | No problem. If you are not sure about plan fit, renewal or cancellation, or usage or value, I can ask one simpler question or stop here. | No problem. If you are not sure about plan fit, renewal or cancellation, or usage or value, I can ask one simpler que... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 4 | not sure | I am checking plan fit, renewal or cancellation, or usage or value for a possible membership account review. Which part should I ask about first, if any? | I am checking plan fit, renewal or cancellation, or usage or value for a possible membership account review. Which part should I ask about first, if any? | I am checking plan fit, renewal or cancellation, or usage or value for a possible membership account review. Which pa... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 5 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | contextual_buyer_semantics | continue-call |
| 6 | maybe later | No problem. What time should I call back? | No problem. What time should I call back? | No problem. What time should I call back? | callback_scheduling_request |  |  |  | contextual_buyer_semantics | continue-call |
| 7 | tomorrow at 3 works | Confirmed. I will record that callback time for a membership specialist about the membership account review. Goodbye. | Confirmed. I will record that callback time for a membership specialist about the membership account review. Goodbye. | Confirmed. I will record that callback time for a membership specialist about the membership account review. Goodbye. | callback_time_provided |  |  |  | contextual_buyer_semantics | schedule-and-end |

### delta-generic-membership-or-subscription-support-out-of-scope-boundary-003

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-membership-regression-001`
- Vertical: `membership_or_subscription`
- Scenario: `support_out_of_scope_boundary`
- Focus areas: support_out_of_scope_boundaries
- Risk tags: hard_case, edge_case, support_boundary
- Expected behavior: Support, account, order, claim, warranty, or department turns should not become fake support actions.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed;... | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a sho... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | what is included? | For Membership Plan Review, I should stick to approved details. I am only checking whether plan fit, renewal or cancellation, or usage or value should go to a short membership account rev... | For Membership Plan Review, I should stick to approved details. I am only checking whether plan fit, renewal or cancellation, or usage or value should go to... | For Membership Plan Review, I should stick to approved details. I am only checking whether plan fit, renewal or cance... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 4 | can you cancel my account? | I cannot cancel or change an account on this call. Please use authorized account support; I can stop here. | I cannot cancel or change an account on this call. Please use authorized account support; I can stop here. | I cannot cancel or change an account on this call. Please use authorized account support; I can stop here. | account_support_boundary |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 5 | wrong department | Understood. Who is the right person or team for membership account review, or should I stop here? | Understood. Who is the right person or team for membership account review, or should I stop here? | Understood. Who is the right person or team for membership account review, or should I stop here? | wrong_person_or_wrong_department |  |  |  | contextual_buyer_semantics | continue-call |
| 6 | talk to support | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | wrong_person_or_wrong_department |  |  |  | contextual_buyer_semantics | continue-call |

### delta-generic-membership-or-subscription-confusion-explanation-quality-004

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-membership-regression-001`
- Vertical: `membership_or_subscription`
- Scenario: `confusion_explanation_quality`
- Focus areas: confusion_explanation_quality, appointment_pressure_calibration
- Risk tags: hard_case, edge_case, explanation_quality
- Expected behavior: Confusion and process questions should be answered in campaign terms without repeating the same diagnostic loop.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed;... | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a sho... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | I don't understand | Sorry, I meant the areas in this fit check: plan fit, renewal or cancellation, or usage or value. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: plan fit, renewal or cancellation, or usage or value. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: plan fit, renewal or cancellation, or usage or value. Which part causes t... | confusion_not_clear |  |  |  | contextual_buyer_semantics | continue-call |
| 4 | what do you mean? | I am checking plan fit, renewal or cancellation, or usage or value for a possible membership account review. Which part should I ask about first, if any? | I am checking plan fit, renewal or cancellation, or usage or value for a possible membership account review. Which part should I ask about first, if any? | I am checking plan fit, renewal or cancellation, or usage or value for a possible membership account review. Which pa... | previous_question_clarification |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 5 | what are you asking? | I am checking plan fit, renewal or cancellation, or usage or value for a possible membership account review. Which part should I ask about first, if any? | I am checking plan fit, renewal or cancellation, or usage or value for a possible membership account review. Which part should I ask about first, if any? | I am checking plan fit, renewal or cancellation, or usage or value for a possible membership account review. Which pa... | confusion_not_clear |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 6 | what happens next? | If plan fit, renewal or cancellation, or usage or value are actually relevant, a membership specialist can do a short membership account review. If not, I can stop here; should I ask one... | If plan fit, renewal or cancellation, or usage or value are actually relevant, a membership specialist can do a short membership account review. If not, I ca... | If plan fit, renewal or cancellation, or usage or value are actually relevant, a membership specialist can do a short... | no_contextual_semantic |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 7 | what is included? | For Membership Plan Review, I should stick to approved details. I am only checking whether plan fit, renewal or cancellation, or usage or value should go to a short membership account rev... | For Membership Plan Review, I should stick to approved details. I am only checking whether plan fit, renewal or cancellation, or usage or value should go to... | For Membership Plan Review, I should stick to approved details. I am only checking whether plan fit, renewal or cance... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 8 | is it expensive? | I do not have approved pricing to quote here. A membership specialist should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A membership specialist should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A membership specialist should confirm cost and terms before any next s... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |

### delta-generic-membership-or-subscription-long-state-drift-delta-005

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-membership-regression-001`
- Vertical: `membership_or_subscription`
- Scenario: `long_state_drift_delta`
- Focus areas: long_state_drift, appointment_pressure_calibration
- Risk tags: hard_case, edge_case, state_drift
- Expected behavior: Long conversation should preserve clear, pain, contact/callback, support boundary, and terminal state.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed;... | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a sho... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yes | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | plan fit is fine | Got it, plan fit is clear. Should I check renewal or cancellation or usage or value, or stop here? | Got it, plan fit is clear. Should I check renewal or cancellation or usage or value, or stop here? | Got it, plan fit is clear. Should I check renewal or cancellation or usage or value, or stop here? | current_gap_clear | plan_fit | plan_fit |  | contextual_buyer_semantics | continue-call |
| 4 | renewal is handled | Got it, those parts are clear. Should I check usage or value, or stop here? | Got it, those parts are clear. Should I check usage or value, or stop here? | Got it, those parts are clear. Should I check usage or value, or stop here? | current_gap_clear | renewal_or_cancellation | plan_fit, renewal_or_cancellation |  | contextual_buyer_semantics | continue-call |
| 5 | usage is fine | Understood. If plan fit, renewal or cancellation, and usage or value are clean, I should not push this further. Is there any other gap worth checking, or should I stop here? | Understood. If plan fit, renewal or cancellation, and usage or value are clean, I should not push this further. Is there any other gap worth checking, or sho... | Understood. If plan fit, renewal or cancellation, and usage or value are clean, I should not push this further. Is th... | current_gap_clear | usage_or_value | plan_fit, renewal_or_cancellation, usage_or_value |  | contextual_buyer_semantics | continue-call |
| 6 | can you cancel my account? | I cannot cancel or change an account on this call. Please use authorized account support; I can stop here. | I cannot cancel or change an account on this call. Please use authorized account support; I can stop here. | I cannot cancel or change an account on this call. Please use authorized account support; I can stop here. | account_support_boundary |  | plan_fit, renewal_or_cancellation, usage_or_value |  | pre_speech_conversation_stability_guard | continue-call |
| 7 | no need | Understood. If plan fit, renewal or cancellation, or usage or value are all clean, I should not push a review. I will stop here. Goodbye. | Understood. If plan fit, renewal or cancellation, or usage or value are all clean, I should not push a review. I will stop here. Goodbye. | Understood. If plan fit, renewal or cancellation, or usage or value are all clean, I should not push a review. I will... | all_clear_no_pain |  | plan_fit, renewal_or_cancellation, usage_or_value |  | contextual_buyer_semantics | end-call |
| 8 | stop calling | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | stop_request |  | plan_fit, renewal_or_cancellation, usage_or_value |  | terminal_call_control | end-call |
| 9 | actually one more thing | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | no_contextual_semantic |  | plan_fit, renewal_or_cancellation, usage_or_value |  | terminal_call_control | end-call |

### delta-generic-retail-or-ecommerce-support-sales-post-5a1-fix-replay-001

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-retail-ecommerce-regression-001`
- Vertical: `retail_or_ecommerce_support_sales`
- Scenario: `post_5a1_fix_replay`
- Focus areas: 5a1_replayed_fixes, support_out_of_scope_boundaries
- Risk tags: hard_case, edge_case, post_patch_replay
- Expected behavior: Order support request should remain a support boundary after a sales pain path.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you h... | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short pr... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | return policy is the concern | Got it, return or warranty policy is the real gap. The next step would be a short product support review; what time works for that review? | Got it, return or warranty policy is the real gap. The next step would be a short product support review; what time works for that review? | Got it, return or warranty policy is the real gap. The next step would be a short product support review; what time w... | pain_confirmed | return_or_warranty |  | return_or_warranty | contextual_buyer_semantics | continue-call |
| 4 | what happens next? | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | no_contextual_semantic |  |  | return_or_warranty | pre_speech_conversation_stability_guard | continue-call |
| 5 | can you help with my order? | I cannot handle order support on this call. Please use the support team for order details; I can stop here. | I cannot handle order support on this call. Please use the support team for order details; I can stop here. | I cannot handle order support on this call. Please use the support team for order details; I can stop here. | account_support_boundary |  |  | return_or_warranty | pre_speech_conversation_stability_guard | continue-call |

### delta-generic-retail-or-ecommerce-support-sales-appointment-pressure-calibration-002

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-retail-ecommerce-regression-001`
- Vertical: `retail_or_ecommerce_support_sales`
- Scenario: `appointment_pressure_calibration`
- Focus areas: appointment_pressure_calibration
- Risk tags: hard_case, edge_case, appointment_pressure
- Expected behavior: Agent should calibrate pressure across maybe, not sure, info-first, maybe-later, and callback timing.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you h... | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short pr... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | maybe | No problem. If you are not sure about product fit, availability or delivery, or return or warranty, I can ask one simpler question or stop here. | No problem. If you are not sure about product fit, availability or delivery, or return or warranty, I can ask one simpler question or stop here. | No problem. If you are not sure about product fit, availability or delivery, or return or warranty, I can ask one sim... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 4 | not sure | I am checking product fit, availability or delivery, or return or warranty for a possible product support review. Which part should I ask about first, if any? | I am checking product fit, availability or delivery, or return or warranty for a possible product support review. Which part should I ask about first, if any? | I am checking product fit, availability or delivery, or return or warranty for a possible product support review. Whi... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 5 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | contextual_buyer_semantics | continue-call |
| 6 | maybe later | No problem. What time should I call back? | No problem. What time should I call back? | No problem. What time should I call back? | callback_scheduling_request |  |  |  | contextual_buyer_semantics | continue-call |
| 7 | tomorrow at 3 works | Confirmed. I will record that callback time for a support sales specialist about the product support review. Goodbye. | Confirmed. I will record that callback time for a support sales specialist about the product support review. Goodbye. | Confirmed. I will record that callback time for a support sales specialist about the product support review. Goodbye. | callback_time_provided |  |  |  | contextual_buyer_semantics | schedule-and-end |

### delta-generic-retail-or-ecommerce-support-sales-support-out-of-scope-boundary-003

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-retail-ecommerce-regression-001`
- Vertical: `retail_or_ecommerce_support_sales`
- Scenario: `support_out_of_scope_boundary`
- Focus areas: support_out_of_scope_boundaries
- Risk tags: hard_case, edge_case, support_boundary
- Expected behavior: Support, account, order, claim, warranty, or department turns should not become fake support actions.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you h... | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short pr... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | what is included? | For Product Support Review, I should stick to approved details. I am only checking whether product fit, availability or delivery, or return or warranty should go to a short product suppor... | For Product Support Review, I should stick to approved details. I am only checking whether product fit, availability or delivery, or return or warranty shoul... | For Product Support Review, I should stick to approved details. I am only checking whether product fit, availability... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 4 | can you help with my order? | I cannot handle order support on this call. Please use the support team for order details; I can stop here. | I cannot handle order support on this call. Please use the support team for order details; I can stop here. | I cannot handle order support on this call. Please use the support team for order details; I can stop here. | account_support_boundary |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 5 | wrong department | Understood. Who is the right person or team for product support review, or should I stop here? | Understood. Who is the right person or team for product support review, or should I stop here? | Understood. Who is the right person or team for product support review, or should I stop here? | wrong_person_or_wrong_department |  |  |  | contextual_buyer_semantics | continue-call |
| 6 | talk to support | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, support handles that. Who is the right person there, or what contact, email, or callback path should I note? | wrong_person_or_wrong_department |  |  |  | contextual_buyer_semantics | continue-call |

### delta-generic-retail-or-ecommerce-support-sales-confusion-explanation-quality-004

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-retail-ecommerce-regression-001`
- Vertical: `retail_or_ecommerce_support_sales`
- Scenario: `confusion_explanation_quality`
- Focus areas: confusion_explanation_quality, appointment_pressure_calibration
- Risk tags: hard_case, edge_case, explanation_quality
- Expected behavior: Confusion and process questions should be answered in campaign terms without repeating the same diagnostic loop.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you h... | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short pr... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | I don't understand | Sorry, I meant the areas in this fit check: product fit, availability or delivery, or return or warranty. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: product fit, availability or delivery, or return or warranty. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: product fit, availability or delivery, or return or warranty. Which part... | confusion_not_clear |  |  |  | contextual_buyer_semantics | continue-call |
| 4 | what do you mean? | I am checking product fit, availability or delivery, or return or warranty for a possible product support review. Which part should I ask about first, if any? | I am checking product fit, availability or delivery, or return or warranty for a possible product support review. Which part should I ask about first, if any? | I am checking product fit, availability or delivery, or return or warranty for a possible product support review. Whi... | previous_question_clarification |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 5 | what are you asking? | I am checking product fit, availability or delivery, or return or warranty for a possible product support review. Which part should I ask about first, if any? | I am checking product fit, availability or delivery, or return or warranty for a possible product support review. Which part should I ask about first, if any? | I am checking product fit, availability or delivery, or return or warranty for a possible product support review. Whi... | confusion_not_clear |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 6 | what happens next? | If product fit, availability or delivery, or return or warranty are actually relevant, a support sales specialist can do a short product support review. If not, I can stop here; should I... | If product fit, availability or delivery, or return or warranty are actually relevant, a support sales specialist can do a short product support review. If n... | If product fit, availability or delivery, or return or warranty are actually relevant, a support sales specialist can... | no_contextual_semantic |  |  |  | pre_speech_conversation_stability_guard | continue-call |
| 7 | what is included? | For Product Support Review, I should stick to approved details. I am only checking whether product fit, availability or delivery, or return or warranty should go to a short product suppor... | For Product Support Review, I should stick to approved details. I am only checking whether product fit, availability or delivery, or return or warranty shoul... | For Product Support Review, I should stick to approved details. I am only checking whether product fit, availability... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 8 | is it expensive? | I do not have approved pricing to quote here. A support sales specialist should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A support sales specialist should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A support sales specialist should confirm cost and terms before any nex... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |

### delta-generic-retail-or-ecommerce-support-sales-long-state-drift-delta-005

- Source: `current_patched_runtime_delta_002`
- Campaign: `synthetic-retail-ecommerce-regression-001`
- Vertical: `retail_or_ecommerce_support_sales`
- Scenario: `long_state_drift_delta`
- Focus areas: long_state_drift, appointment_pressure_calibration
- Risk tags: hard_case, edge_case, state_drift
- Expected behavior: Long conversation should preserve clear, pain, contact/callback, support boundary, and terminal state.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you h... | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short pr... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | product fit is fine | Got it, product fit is clear. Should I check availability or delivery or return or warranty, or stop here? | Got it, product fit is clear. Should I check availability or delivery or return or warranty, or stop here? | Got it, product fit is clear. Should I check availability or delivery or return or warranty, or stop here? | current_gap_clear | product_fit | product_fit |  | contextual_buyer_semantics | continue-call |
| 4 | return policy is the concern | Got it, return or warranty policy is the real gap. The next step would be a short product support review; what time works for that review? | Got it, return or warranty policy is the real gap. The next step would be a short product support review; what time works for that review? | Got it, return or warranty policy is the real gap. The next step would be a short product support review; what time w... | pain_confirmed | return_or_warranty | product_fit | return_or_warranty | contextual_buyer_semantics | continue-call |
| 5 | send me details first | No problem. I can send a short summary focused on return or warranty policy. What email or callback time should I note? | No problem. I can send a short summary focused on return or warranty policy. What email or callback time should I note? | No problem. I can send a short summary focused on return or warranty policy. What email or callback time should I note? | send_info_with_confirmed_pain | return_or_warranty | product_fit | return_or_warranty | contextual_buyer_semantics | continue-call |
| 6 | send it to <email:sha256_12:6db61e6dcbcf> | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | email_provided |  | product_fit | return_or_warranty | contextual_buyer_semantics | continue-call |
| 7 | can you help with my order? | I cannot handle order support on this call. Please use the support team for order details; I can stop here. | I cannot handle order support on this call. Please use the support team for order details; I can stop here. | I cannot handle order support on this call. Please use the support team for order details; I can stop here. | account_support_boundary |  | product_fit | return_or_warranty | pre_speech_conversation_stability_guard | continue-call |
| 8 | can you guarantee refund? | I cannot promise a refund, warranty, stock, or delivery outcome here. A support sales specialist needs verified policy and order details first. Is return or warranty policy what you want... | I cannot promise a refund, warranty, stock, or delivery outcome here. A support sales specialist needs verified policy and order details first. Is return or... | I cannot promise a refund, warranty, stock, or delivery outcome here. A support sales specialist needs verified polic... | campaign_claim_boundary_caution | return_or_warranty | product_fit | return_or_warranty | contextual_buyer_semantics | transfer-or-escalate |
| 9 | tomorrow at 3 works | Confirmed. I will record that callback time for a support sales specialist about the product support review. Goodbye. | Confirmed. I will record that callback time for a support sales specialist about the product support review. Goodbye. | Confirmed. I will record that callback time for a support sales specialist about the product support review. Goodbye. | callback_time_provided |  | product_fit | return_or_warranty | contextual_buyer_semantics | schedule-and-end |

### delta-routesignal-routesignal-callbacks-clear-001

- Source: `current_patched_routesignal_live_demo_delta_002`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario: `routesignal_callbacks_clear`
- Focus areas: routesignal_preservation
- Risk tags: hard_case, edge_case, routesignal
- Expected behavior: Callbacks clear behavior remains stable in the live-demo path.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and mess... | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help s... | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person ha... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating iss... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | callbacks are fine | Got it, callbacks are clear. Should I check manual tracking or handoffs, or stop here? | Got it, callbacks are clear, well, should I check manual tracking or handoffs, or stop here? | Got it, callbacks are clear, well, should I check manual tracking or handoffs, or stop here? | current_gap_clear | callbacks | callbacks |  | contextual_buyer_semantics | continue-call |

### delta-routesignal-routesignal-handoffs-pain-next-step-002

- Source: `current_patched_routesignal_live_demo_delta_002`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario: `routesignal_handoffs_pain_next_step`
- Focus areas: routesignal_preservation
- Risk tags: hard_case, edge_case, routesignal
- Expected behavior: Handoffs pain can still move toward RouteSignal/Northstar next step in RouteSignal-only path.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and mess... | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help s... | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person ha... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating iss... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | handoffs get messy | Got it, handoff ownership is the real gap. RouteSignal helps each demo lead keep a clear owner and next reply. The next step is a short workflow review with someone from Northstar. They w... | Got it, handoff ownership is the real gap, well, RouteSignal helps each demo lead keep a clear owner and next reply. The next step is a short workflow review... | Got it, handoff ownership is the real gap, well, RouteSignal helps each demo lead keep a clear owner and next reply.... | pain_confirmed | handoffs |  | handoffs | contextual_buyer_semantics | continue-call |
| 4 | what happens next? | No problem. We can leave it here. | No problem. We can leave it here. | No problem. We can leave it here. | no_contextual_semantic |  |  | handoffs | pre_speech_conversation_stability_guard | continue-call |

### delta-routesignal-routesignal-send-info-yes-003

- Source: `current_patched_routesignal_live_demo_delta_002`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario: `routesignal_send_info_yes`
- Focus areas: routesignal_preservation
- Risk tags: hard_case, edge_case, routesignal
- Expected behavior: Send-info yes does not send email and remains compatible with RouteSignal wording.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and mess... | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help s... | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person ha... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating iss... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | send me details first | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. Um, I can keep it to a short written summary. <break time="0.24s" /> What email or callback time should I note? | No problem. Um, I can keep it to a short written summary. <break time="0.24s" /> What email or callback time should I... | send_info_request |  |  |  | contextual_buyer_semantics | continue-call |
| 4 | yes send it | Sure. What email should I note for the summary, or what callback time should I use? | Sure. Um, what email should I note for the summary, <break time="0.24s" /> or what callback time should I use? | Sure. Um, what email should I note for the summary, <break time="0.24s" /> or what callback time should I use? | send_info_affirmed_without_contact |  |  |  | contextual_buyer_semantics | continue-call |

### delta-routesignal-routesignal-callback-time-004

- Source: `current_patched_routesignal_live_demo_delta_002`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario: `routesignal_callback_time`
- Focus areas: routesignal_preservation, appointment_pressure_calibration
- Risk tags: hard_case, edge_case, routesignal
- Expected behavior: Callback time capture works through live-demo path without calendar or CRM side effects.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and mess... | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help s... | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person ha... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating iss... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | send me details first | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. Um, I can keep it to a short written summary. <break time="0.24s" /> What email or callback time should I note? | No problem. Um, I can keep it to a short written summary. <break time="0.24s" /> What email or callback time should I... | send_info_request |  |  |  | contextual_buyer_semantics | continue-call |
| 4 | yes send it | Sure. What email should I note for the summary, or what callback time should I use? | Sure. Um, what email should I note for the summary, <break time="0.24s" /> or what callback time should I use? | Sure. Um, what email should I note for the summary, <break time="0.24s" /> or what callback time should I use? | send_info_affirmed_without_contact |  |  |  | contextual_buyer_semantics | continue-call |
| 5 | tomorrow at 3 works | Confirmed. I will record that callback time for the specialist. Goodbye. | Confirmed. I will record that callback time for the specialist. Goodbye. | Confirmed. I will record that callback time for the specialist. Goodbye. | callback_time_provided |  |  |  | contextual_buyer_semantics | schedule-and-end |

### delta-routesignal-routesignal-password-boundary-005

- Source: `current_patched_routesignal_live_demo_delta_002`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario: `routesignal_password_boundary`
- Focus areas: routesignal_preservation, support_out_of_scope_boundaries
- Risk tags: hard_case, edge_case, routesignal
- Expected behavior: Out-of-scope support request should not break RouteSignal live-demo behavior.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and mess... | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help s... | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person ha... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating iss... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | can you help with my password? | If callback reminders for demo follow-up sit in a spreadsheet, they can slip. Which part is more familiar: manual tracking or missed callbacks? | If callback reminders for demo follow-up sit in a spreadsheet, they can slip, well, which part is more familiar: manual tracking or missed callbacks? | If callback reminders for demo follow-up sit in a spreadsheet, they can slip, well, which part is more familiar: manu... | no_contextual_semantic |  |  |  | pre_speech_conversation_stability_guard | continue-call |

### delta-routesignal-routesignal-already-told-you-006

- Source: `current_patched_routesignal_live_demo_delta_002`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario: `routesignal_already_told_you`
- Focus areas: routesignal_preservation, 5a1_replayed_fixes
- Risk tags: hard_case, edge_case, routesignal
- Expected behavior: After confirmed pain, repeated context should acknowledge rather than restart diagnostics.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and mess... | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help s... | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person ha... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating iss... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | handoffs get messy | Got it, handoff ownership is the real gap. RouteSignal helps each demo lead keep a clear owner and next reply. The next step is a short workflow review with someone from Northstar. They w... | Got it, handoff ownership is the real gap, well, RouteSignal helps each demo lead keep a clear owner and next reply. The next step is a short workflow review... | Got it, handoff ownership is the real gap, well, RouteSignal helps each demo lead keep a clear owner and next reply.... | pain_confirmed | handoffs |  | handoffs | contextual_buyer_semantics | continue-call |
| 4 | I already told you | No problem. We can leave it here. | No problem. We can leave it here. | No problem. We can leave it here. | no_contextual_semantic |  |  | handoffs | pre_speech_conversation_stability_guard | continue-call |

### delta-routesignal-routesignal-confusion-007

- Source: `current_patched_routesignal_live_demo_delta_002`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario: `routesignal_confusion`
- Focus areas: routesignal_preservation, confusion_explanation_quality
- Risk tags: hard_case, edge_case, routesignal
- Expected behavior: Confusion repair remains compatible with RouteSignal live-demo path.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and mess... | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help s... | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person ha... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating iss... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | I don't understand | Sorry, I meant the follow-up after an inbound demo request: callbacks, manual tracking, or handoffs. Which part causes trouble, if any? | Sorry, I meant the follow-up after an inbound demo request: callbacks, <break time="0.154s" /> manual tracking, or handoffs, so, which part causes trouble, i... | Sorry, I meant the follow-up after an inbound demo request: callbacks, <break time="0.154s" /> manual tracking, or ha... | confusion_not_clear |  |  |  | contextual_buyer_semantics | continue-call |
| 4 | what do you mean? | I meant: an inbound demo request needs one clear owner for the next reply. Can owner, callback, or handoff steps sit waiting? | I meant: an inbound demo request needs one clear owner for the next reply, so, can owner, callback, or handoff steps sit waiting? | I meant: an inbound demo request needs one clear owner for the next reply, so, can owner, callback, or handoff steps... | previous_question_clarification |  |  |  | pre_speech_conversation_stability_guard | continue-call |

### delta-routesignal-routesignal-refusal-terminal-008

- Source: `current_patched_routesignal_live_demo_delta_002`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario: `routesignal_refusal_terminal`
- Focus areas: routesignal_preservation, appointment_pressure_calibration
- Risk tags: hard_case, edge_case, routesignal
- Expected behavior: No-need and stop should avoid continued selling loops.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and mess... | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help s... | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person ha... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating iss... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | no need | Understood. If callbacks, manual tracking, and handoffs are all clean, I should not push a review. I will stop here. Goodbye. | Understood. If callbacks, manual tracking, and handoffs are all clean, I should not push a review. I will stop here. Goodbye. | Understood. If callbacks, manual tracking, and handoffs are all clean, I should not push a review. I will stop here.... | all_clear_no_pain |  |  |  | contextual_buyer_semantics | end-call |
| 4 | stop calling | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | stop_request |  |  |  | terminal_call_control | end-call |
| 5 | actually one more thing | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | no_contextual_semantic |  |  |  | terminal_call_control | end-call |

### delta-routesignal-routesignal-long-preservation-009

- Source: `current_patched_routesignal_live_demo_delta_002`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario: `routesignal_long_preservation`
- Focus areas: routesignal_preservation, long_state_drift
- Risk tags: hard_case, edge_case, routesignal, state_drift
- Expected behavior: Long RouteSignal path preserves callbacks clear, handoffs pain, send-info, and callback time.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and mess... | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help s... | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person ha... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating iss... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | callbacks are fine | Got it, callbacks are clear. Should I check manual tracking or handoffs, or stop here? | Got it, callbacks are clear, well, should I check manual tracking or handoffs, or stop here? | Got it, callbacks are clear, well, should I check manual tracking or handoffs, or stop here? | current_gap_clear | callbacks | callbacks |  | contextual_buyer_semantics | continue-call |
| 4 | handoffs get messy | Got it, handoff ownership is the real gap. RouteSignal helps each demo lead keep a clear owner and next reply. The next step is a short workflow review with someone from Northstar. They w... | Got it, handoff ownership is the real gap, well, RouteSignal helps each demo lead keep a clear owner and next reply. The next step is a short workflow review... | Got it, handoff ownership is the real gap, well, RouteSignal helps each demo lead keep a clear owner and next reply.... | pain_confirmed | handoffs | callbacks | handoffs | contextual_buyer_semantics | continue-call |
| 5 | send me details first | No problem. I can send a short summary focused on handoff ownership. What email or callback time should I note? | No problem, well, I can send a short summary focused on handoff ownership. <break time="0.184s" /> What email or callback time should I note? | No problem, well, I can send a short summary focused on handoff ownership. <break time="0.184s" /> What email or call... | send_info_with_confirmed_pain | handoffs | callbacks | handoffs | contextual_buyer_semantics | continue-call |
| 6 | yes send it | Sure. What email should I note for the summary, or what callback time should I use? | Sure. Um, what email should I note for the summary, <break time="0.24s" /> or what callback time should I use? | Sure. Um, what email should I note for the summary, <break time="0.24s" /> or what callback time should I use? | send_info_affirmed_without_contact |  | callbacks | handoffs | contextual_buyer_semantics | continue-call |
| 7 | tomorrow at 3 works | Confirmed. I will record that callback time for the specialist. Goodbye. | Confirmed. I will record that callback time for the specialist. Goodbye. | Confirmed. I will record that callback time for the specialist. Goodbye. | callback_time_provided |  | callbacks | handoffs | contextual_buyer_semantics | schedule-and-end |

### delta-routesignal-routesignal-pain-info-callback-010

- Source: `current_patched_routesignal_live_demo_delta_002`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario: `routesignal_pain_info_callback`
- Focus areas: routesignal_preservation, appointment_pressure_calibration
- Risk tags: hard_case, edge_case, routesignal
- Expected behavior: Pain, info-first, and callback timing remain stable in RouteSignal path.

| Turn | Buyer | Agent final response | TTS input | Provider text | Semantic | Target gap | Cleared | Confirmed | Action source | Call control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and mess... | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help s... | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person ha... | no_contextual_semantic |  |  |  | live_voice_session_policy | continue-call |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating iss... | permission_acknowledgement |  |  |  | contextual_buyer_semantics | continue-call |
| 3 | callbacks are a problem | Got it, missed callbacks is the real gap. RouteSignal helps demo leads stay assigned, reminded, and followed up before callback gaps turn into lost opportunities. The next step is a short... | Got it, missed callbacks is the real gap, so, RouteSignal helps demo leads stay assigned, reminded, and followed up before callback gaps turn into lost oppor... | Got it, missed callbacks is the real gap, so, RouteSignal helps demo leads stay assigned, reminded, and followed up b... | pain_confirmed | callbacks |  | callbacks | contextual_buyer_semantics | continue-call |
| 4 | send me details first | No problem. I can send a short summary focused on missed callback reminders. What email or callback time should I note? | No problem. Um, I can send a short summary focused on missed callback reminders. <break time="0.188s" /> What email or callback time should I note? | No problem. Um, I can send a short summary focused on missed callback reminders. <break time="0.188s" /> What email o... | send_info_with_confirmed_pain | callbacks |  | callbacks | contextual_buyer_semantics | continue-call |
| 5 | tomorrow at 3 works | Confirmed. I will record that callback time for the specialist. Goodbye. | Confirmed. I will record that callback time for the specialist. Goodbye. | Confirmed. I will record that callback time for the specialist. Goodbye. | callback_time_provided |  |  | callbacks | contextual_buyer_semantics | schedule-and-end |

## Redaction And Safety Summary

- Synthetic examples only.
- Raw email-like values are replaced by stable hash tokens.
- No private transcripts, secrets, audio, or customer data are included.
- Provider calls, local LLM calls, live TTS, email sends, calendar creation, CRM writes, and PROD-102 are false.
