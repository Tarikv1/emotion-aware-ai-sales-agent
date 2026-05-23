# ADVERSARIAL-MATRIX-RED-FINDINGS-AUDIT-001

## Summary
- Source checkpoint: `LIVE-INSPIRED-ADVERSARIAL-DIALOGUE-MATRIX-001`
- Source red findings: `352`
- Audited red findings: `352`

## Count By Root Cause
- `appointment_too_early`: `12`
- `asr_near_miss_gap_not_recognized`: `9`
- `campaign_contamination`: `11`
- `direct_question_not_satisfied`: `5`
- `false_assumption_correction_missing`: `1`
- `hostile_challenge_not_deescalated`: `6`
- `internal_wording_source_live_policy`: `6`
- `needs_human_review`: `48`
- `out_of_campaign_relevance_bad_fallback`: `14`
- `repeated_response_without_progress`: `18`
- `stability_guard_menu_reset`: `222`

## Count By Source
- `contextual_buyer_semantics`: `16`
- `dialogue_pragmatics`: `6`
- `live_voice_session_policy`: `37`
- `pre_speech_conversation_stability_guard`: `223`
- `terminal_call_control`: `6`
- `universal_response_shape`: `64`

## Count By Scenario Family
- `agent_looping_complaints`: `5`
- `asr_near_miss_gap_phrases`: `10`
- `asr_near_miss_invented_transcript_stress`: `8`
- `buyer_correction_contradiction_stress`: `10`
- `buyer_says_agent_is_wrong`: `24`
- `callback_time_too_early_or_ambiguous`: `24`
- `campaign_selector_wrong_campaign_contamination`: `14`
- `commercial_pressure_close_strength_stress`: `16`
- `commercial_quality_stress`: `8`
- `direct_product_value_challenge_loops`: `6`
- `disallowed_persistence_after_stop`: `6`
- `early_callback_premature_scheduling`: `6`
- `false_assumption_correction`: `7`
- `hostile_challenging_buyer`: `21`
- `human_context_interruption_pressure`: `6`
- `impact_before_clean_pain`: `16`
- `long_conversation_state_drift`: `7`
- `mixed_intent_buyer_turns`: `6`
- `multi_campaign_contamination_stress`: `21`
- `permission_weak_acknowledgement_variants`: `15`
- `price_budget_affordability_stress`: `6`
- `repeated_answer_variation_anti_loop`: `23`
- `repeated_challenge_escalation`: `24`
- `repeated_product_detail_scope_questions`: `22`
- `sales_realism_score_heuristics`: `12`
- `scope_boundary_regulated_detail_stress`: `6`
- `vague_affirmative_after_context`: `12`
- `why_human_review_challenge`: `11`

## Count By Campaign
- `routesignal_live_demo`: `57`
- `synthetic-automotive-service-review`: `64`
- `synthetic-b2b-saas-operations`: `58`
- `synthetic-insurance-review`: `59`
- `synthetic-membership-plan-review`: `54`
- `synthetic-telecom-plan-review`: `60`

## Top Examples
### adv-multi-campaign-contamination-stress-routesignal_live_demo-02
- Root cause: `internal_wording_source_live_policy`
- Campaign: `routesignal_live_demo`
- Family: `multi_campaign_contamination_stress`
- Source: `live_voice_session_policy`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?

### adv-multi-campaign-contamination-stress-synthetic-automotive-service-review-02
- Root cause: `internal_wording_source_live_policy`
- Campaign: `synthetic-automotive-service-review`
- Family: `multi_campaign_contamination_stress`
- Source: `live_voice_session_policy`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?

### adv-multi-campaign-contamination-stress-synthetic-b2b-saas-operations-02
- Root cause: `internal_wording_source_live_policy`
- Campaign: `synthetic-b2b-saas-operations`
- Family: `multi_campaign_contamination_stress`
- Source: `live_voice_session_policy`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?

### adv-multi-campaign-contamination-stress-synthetic-insurance-review-02
- Root cause: `internal_wording_source_live_policy`
- Campaign: `synthetic-insurance-review`
- Family: `multi_campaign_contamination_stress`
- Source: `live_voice_session_policy`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?

### adv-multi-campaign-contamination-stress-synthetic-membership-plan-review-02
- Root cause: `internal_wording_source_live_policy`
- Campaign: `synthetic-membership-plan-review`
- Family: `multi_campaign_contamination_stress`
- Source: `live_voice_session_policy`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?

### adv-multi-campaign-contamination-stress-synthetic-telecom-plan-review-02
- Root cause: `internal_wording_source_live_policy`
- Campaign: `synthetic-telecom-plan-review`
- Family: `multi_campaign_contamination_stress`
- Source: `live_voice_session_policy`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?

### adv-direct-product-value-challenge-loops-routesignal_live_demo-02
- Root cause: `stability_guard_menu_reset`
- Campaign: `routesignal_live_demo`
- Family: `direct_product_value_challenge_loops`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `did_not_answer_direct_question, repeated_full_menu`
- Buyer script: `['__agent_open__', 'what are you selling', 'explain it plainly', 'say it in one sentence']`
- Final response: If callback reminders for demo follow-up sit in a spreadsheet, they can slip. Which part is more familiar: manual tracking or missed callbacks?

### adv-direct-product-value-challenge-loops-synthetic-automotive-service-review-02
- Root cause: `stability_guard_menu_reset`
- Campaign: `synthetic-automotive-service-review`
- Family: `direct_product_value_challenge_loops`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `did_not_answer_direct_question, repeated_full_menu`
- Buyer script: `['__agent_open__', 'what are you selling', 'explain it plainly', 'say it in one sentence']`
- Final response: I may not be the right contact for that question. Should I note a callback path, or stop here?

### adv-direct-product-value-challenge-loops-synthetic-b2b-saas-operations-02
- Root cause: `stability_guard_menu_reset`
- Campaign: `synthetic-b2b-saas-operations`
- Family: `direct_product_value_challenge_loops`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `did_not_answer_direct_question, repeated_full_menu`
- Buyer script: `['__agent_open__', 'what are you selling', 'explain it plainly', 'say it in one sentence']`
- Final response: I may not be the right contact for that question. Should I note a callback path, or stop here?

### adv-direct-product-value-challenge-loops-synthetic-insurance-review-02
- Root cause: `stability_guard_menu_reset`
- Campaign: `synthetic-insurance-review`
- Family: `direct_product_value_challenge_loops`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `did_not_answer_direct_question, repeated_full_menu`
- Buyer script: `['__agent_open__', 'what are you selling', 'explain it plainly', 'say it in one sentence']`
- Final response: I may not be the right contact for that question. Should I note a callback path, or stop here?

### adv-direct-product-value-challenge-loops-synthetic-membership-plan-review-02
- Root cause: `stability_guard_menu_reset`
- Campaign: `synthetic-membership-plan-review`
- Family: `direct_product_value_challenge_loops`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `did_not_answer_direct_question, repeated_full_menu`
- Buyer script: `['__agent_open__', 'what are you selling', 'explain it plainly', 'say it in one sentence']`
- Final response: I may not be the right contact for that question. Should I note a callback path, or stop here?

### adv-direct-product-value-challenge-loops-synthetic-telecom-plan-review-02
- Root cause: `stability_guard_menu_reset`
- Campaign: `synthetic-telecom-plan-review`
- Family: `direct_product_value_challenge_loops`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `did_not_answer_direct_question, repeated_full_menu`
- Buyer script: `['__agent_open__', 'what are you selling', 'explain it plainly', 'say it in one sentence']`
- Final response: I may not be the right contact for that question. Should I note a callback path, or stop here?

### adv-repeated-challenge-escalation-routesignal_live_demo-04
- Root cause: `stability_guard_menu_reset`
- Campaign: `routesignal_live_demo`
- Family: `repeated_challenge_escalation`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `did_not_answer_direct_question, repeated_full_menu`
- Buyer script: `['__agent_open__', 'why are you calling', "that still doesn't explain it"]`
- Final response: This is about inbound demo follow-up: one person should be responsible for the next reply. That prevents missed follow-up. Which part is least clear today?

### adv-why-human-review-challenge-routesignal_live_demo-04
- Root cause: `stability_guard_menu_reset`
- Campaign: `routesignal_live_demo`
- Family: `why_human_review_challenge`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `did_not_answer_direct_question, repeated_full_menu`
- Buyer script: `['__agent_open__', "what will they do that you can't"]`
- Final response: This is about inbound demo follow-up: one person should be responsible for the next reply. That prevents missed follow-up. Which part is least clear today?

### adv-why-human-review-challenge-synthetic-automotive-service-review-01
- Root cause: `direct_question_not_satisfied`
- Campaign: `synthetic-automotive-service-review`
- Family: `why_human_review_challenge`
- Source: `live_voice_session_policy`
- Flags: `did_not_answer_direct_question`
- Buyer script: `['__agent_open__', 'why do I need a human review']`
- Final response: Of course. I will route this to a specialist instead of continuing automatically.

### adv-why-human-review-challenge-synthetic-b2b-saas-operations-01
- Root cause: `direct_question_not_satisfied`
- Campaign: `synthetic-b2b-saas-operations`
- Family: `why_human_review_challenge`
- Source: `live_voice_session_policy`
- Flags: `did_not_answer_direct_question`
- Buyer script: `['__agent_open__', 'why do I need a human review']`
- Final response: Of course. I will route this to a specialist instead of continuing automatically.

### adv-why-human-review-challenge-synthetic-insurance-review-01
- Root cause: `direct_question_not_satisfied`
- Campaign: `synthetic-insurance-review`
- Family: `why_human_review_challenge`
- Source: `live_voice_session_policy`
- Flags: `did_not_answer_direct_question`
- Buyer script: `['__agent_open__', 'why do I need a human review']`
- Final response: Of course. I will route this to a specialist instead of continuing automatically.

### adv-why-human-review-challenge-synthetic-membership-plan-review-01
- Root cause: `direct_question_not_satisfied`
- Campaign: `synthetic-membership-plan-review`
- Family: `why_human_review_challenge`
- Source: `live_voice_session_policy`
- Flags: `did_not_answer_direct_question`
- Buyer script: `['__agent_open__', 'why do I need a human review']`
- Final response: Of course. I will route this to a specialist instead of continuing automatically.

### adv-why-human-review-challenge-synthetic-telecom-plan-review-01
- Root cause: `direct_question_not_satisfied`
- Campaign: `synthetic-telecom-plan-review`
- Family: `why_human_review_challenge`
- Source: `live_voice_session_policy`
- Flags: `did_not_answer_direct_question`
- Buyer script: `['__agent_open__', 'why do I need a human review']`
- Final response: Of course. I will route this to a specialist instead of continuing automatically.

### adv-asr-near-miss-gap-phrases-routesignal_live_demo-04
- Root cause: `stability_guard_menu_reset`
- Campaign: `routesignal_live_demo`
- Family: `asr_near_miss_gap_phrases`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `asr_near_miss_not_clarified, repeated_full_menu`
- Buyer script: `['__agent_open__', 'yeah', 'hand offs are messy', 'it wastes time']`
- Final response: If inbound demo requests land in one inbox, missed follow-up can happen because everyone assumes someone else replied. Which part is harder today: seeing it, assigning the reply, or remembering the callback?

## Recommended Patch Scope
- Patch stability_guard_menu_reset for near configured gaps before broad exploratory work.
- Patch internal_wording_source_live_policy where customer-facing boundary text leaks implementation wording.
- Patch direct question / why-human-review only after the menu reset slice is green.
- Leave callback ambiguity, repeated-response style, and broad hostile-challenge polish as follow-up unless focused validators reproduce a low-risk fix.

## Runtime Behavior Changed
- `false`
