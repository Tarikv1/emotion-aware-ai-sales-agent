# ADVERSARIAL-MATRIX-RED-FINDINGS-AUDIT-001

## Summary
- Source checkpoint: `LIVE-INSPIRED-ADVERSARIAL-DIALOGUE-MATRIX-001`
- Source red findings: `64`
- Audited red findings: `64`

## Count By Root Cause
- `appointment_too_early`: `6`
- `campaign_contamination`: `4`
- `hostile_challenge_not_deescalated`: `18`
- `needs_human_review`: `1`
- `out_of_campaign_relevance_bad_fallback`: `12`
- `repeated_response_without_progress`: `23`

## Count By Source
- `contextual_buyer_semantics`: `3`
- `live_voice_session_policy`: `5`
- `pre_speech_conversation_stability_guard`: `5`
- `universal_response_shape`: `51`

## Count By Scenario Family
- `buyer_correction_contradiction_stress`: `1`
- `buyer_says_agent_is_wrong`: `18`
- `callback_time_too_early_or_ambiguous`: `6`
- `campaign_selector_wrong_campaign_contamination`: `5`
- `commercial_quality_stress`: `5`
- `multi_campaign_contamination_stress`: `9`
- `repeated_answer_variation_anti_loop`: `18`
- `scope_boundary_regulated_detail_stress`: `2`

## Count By Campaign
- `routesignal_live_demo`: `12`
- `synthetic-automotive-service-review`: `11`
- `synthetic-b2b-saas-operations`: `11`
- `synthetic-insurance-review`: `11`
- `synthetic-membership-plan-review`: `8`
- `synthetic-telecom-plan-review`: `11`

## Top Examples
### adv-buyer-correction-contradiction-stress-routesignal_live_demo-02
- Root cause: `needs_human_review`
- Campaign: `routesignal_live_demo`
- Family: `buyer_correction_contradiction_stress`
- Source: `contextual_buyer_semantics`
- Flags: `too_long_for_live_voice`
- Buyer script: `['__agent_open__', 'yeah', 'callbacks are a problem', 'I said inbound demo follow-up, not callbacks']`
- Final response: Got it, you already said that is the problem: missed callbacks. RouteSignal helps demo leads stay assigned, reminded, and followed up before callback gaps turn into lost opportunities. The next step is a short workflow review with someone from Northstar. They would check missed callback reminders against your actual follow-up flow. What time works for a quick call?

### adv-buyer-says-agent-is-wrong-routesignal_live_demo-01
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `routesignal_live_demo`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that's wrong"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a non-binding workflow review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-routesignal_live_demo-02
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `routesignal_live_demo`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that doesn't make sense"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a non-binding workflow review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-routesignal_live_demo-03
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `routesignal_live_demo`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "you're making assumptions"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a non-binding workflow review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-automotive-service-review-01
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-automotive-service-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that's wrong"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a service advisor inspection review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-automotive-service-review-02
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-automotive-service-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that doesn't make sense"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a service advisor inspection review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-automotive-service-review-03
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-automotive-service-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "you're making assumptions"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a service advisor inspection review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-b2b-saas-operations-01
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-b2b-saas-operations`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that's wrong"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether an operations fit review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-b2b-saas-operations-02
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-b2b-saas-operations`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that doesn't make sense"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether an operations fit review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-b2b-saas-operations-03
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-b2b-saas-operations`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "you're making assumptions"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether an operations fit review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-insurance-review-01
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-insurance-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that's wrong"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a licensed coverage review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-insurance-review-02
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-insurance-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that doesn't make sense"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a licensed coverage review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-insurance-review-03
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-insurance-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "you're making assumptions"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a licensed coverage review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-membership-plan-review-01
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-membership-plan-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that's wrong"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether an account support or plan-fit review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-membership-plan-review-02
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-membership-plan-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that doesn't make sense"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether an account support or plan-fit review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-membership-plan-review-03
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-membership-plan-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "you're making assumptions"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether an account support or plan-fit review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-telecom-plan-review-01
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-telecom-plan-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that's wrong"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a human plan and availability review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-telecom-plan-review-02
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-telecom-plan-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that doesn't make sense"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a human plan and availability review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-telecom-plan-review-03
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-telecom-plan-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "you're making assumptions"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a human plan and availability review is useful. Is there any issue here you actually want reviewed?

### adv-callback-time-too-early-or-ambiguous-routesignal_live_demo-02
- Root cause: `appointment_too_early`
- Campaign: `routesignal_live_demo`
- Family: `callback_time_too_early_or_ambiguous`
- Source: `universal_response_shape`
- Flags: `appointment_too_early`
- Buyer script: `['__agent_open__', 'tomorrow works']`
- Final response: Got it. I'll note that time for the verified implementation reviewer to follow up.

## Recommended Patch Scope
- Patch stability_guard_menu_reset for near configured gaps before broad exploratory work.
- Patch internal_wording_source_live_policy where customer-facing boundary text leaks implementation wording.
- Patch direct question / why-human-review only after the menu reset slice is green.
- Leave callback ambiguity, repeated-response style, and broad hostile-challenge polish as follow-up unless focused validators reproduce a low-risk fix.

## Runtime Behavior Changed
- `false`
