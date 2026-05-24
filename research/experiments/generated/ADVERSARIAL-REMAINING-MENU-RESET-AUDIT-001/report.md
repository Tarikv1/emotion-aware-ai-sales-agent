# ADVERSARIAL-REMAINING-MENU-RESET-AUDIT-001

## Summary
- Source checkpoint: `LIVE-INSPIRED-ADVERSARIAL-DIALOGUE-MATRIX-001`
- Source red findings: `217`
- Audited red findings: `217`

## Classification Counts
- `needs_human_review`: `7`
- `terminal_preservation_artifact`: `6`
- `true_appointment_too_early`: `6`
- `true_campaign_contamination`: `4`
- `true_hostile_challenge_not_deescalated`: `18`
- `true_out_of_scope_reset_after_relevant_context`: `12`
- `true_repeated_response_without_progress`: `24`
- `true_stability_menu_reset`: `140`

## Counts By Selected Action Source
- `contextual_buyer_semantics`: `6`
- `dialogue_pragmatics`: `6`
- `live_voice_session_policy`: `6`
- `pre_speech_conversation_stability_guard`: `109`
- `terminal_call_control`: `6`
- `universal_response_shape`: `84`

## Counts By Scenario Family
- `asr_near_miss_gap_phrases`: `1`
- `asr_near_miss_invented_transcript_stress`: `6`
- `buyer_correction_contradiction_stress`: `1`
- `buyer_says_agent_is_wrong`: `18`
- `callback_time_too_early_or_ambiguous`: `18`
- `campaign_selector_wrong_campaign_contamination`: `8`
- `commercial_pressure_close_strength_stress`: `16`
- `commercial_quality_stress`: `8`
- `direct_product_value_challenge_loops`: `6`
- `disallowed_persistence_after_stop`: `6`
- `human_context_interruption_pressure`: `6`
- `impact_before_clean_pain`: `16`
- `long_conversation_state_drift`: `5`
- `multi_campaign_contamination_stress`: `14`
- `permission_weak_acknowledgement_variants`: `15`
- `price_budget_affordability_stress`: `6`
- `repeated_answer_variation_anti_loop`: `18`
- `repeated_challenge_escalation`: `3`
- `repeated_product_detail_scope_questions`: `21`
- `sales_realism_score_heuristics`: `12`
- `scope_boundary_regulated_detail_stress`: `6`
- `vague_affirmative_after_context`: `7`

## Counts By Campaign
- `routesignal_live_demo`: `34`
- `synthetic-automotive-service-review`: `42`
- `synthetic-b2b-saas-operations`: `34`
- `synthetic-insurance-review`: `37`
- `synthetic-membership-plan-review`: `31`
- `synthetic-telecom-plan-review`: `39`

## Top True Defects
### adv-permission-weak-acknowledgement-variants-routesignal_live_demo-02
- Classification: `true_stability_menu_reset`
- Campaign: `routesignal_live_demo`
- Family: `permission_weak_acknowledgement_variants`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'okay fine']`
- Final response: This is about inbound demo follow-up: one person should be responsible for the next reply. That prevents missed follow-up. Which part is least clear today?

### adv-permission-weak-acknowledgement-variants-routesignal_live_demo-04
- Classification: `true_stability_menu_reset`
- Campaign: `routesignal_live_demo`
- Family: `permission_weak_acknowledgement_variants`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'fine but be fast']`
- Final response: This is about inbound demo follow-up: one person should be responsible for the next reply. That prevents missed follow-up. Which part is least clear today?

### adv-permission-weak-acknowledgement-variants-synthetic-insurance-review-02
- Classification: `true_stability_menu_reset`
- Campaign: `synthetic-insurance-review`
- Family: `permission_weak_acknowledgement_variants`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'okay fine']`
- Final response: The quick check is whether any of these areas is worth a short licensed coverage review: premium or budget, coverage fit, or renewal or timing. If not, I can stop here; which part should I check first?

### adv-permission-weak-acknowledgement-variants-synthetic-insurance-review-03
- Classification: `true_stability_menu_reset`
- Campaign: `synthetic-insurance-review`
- Family: `permission_weak_acknowledgement_variants`
- Source: `contextual_buyer_semantics`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'go ahead']`
- Final response: Thanks, I am checking premium or budget, coverage fit, or renewal or timing. Which one is causing trouble, if any?

### adv-permission-weak-acknowledgement-variants-synthetic-insurance-review-04
- Classification: `true_stability_menu_reset`
- Campaign: `synthetic-insurance-review`
- Family: `permission_weak_acknowledgement_variants`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'fine but be fast']`
- Final response: The quick check is whether any of these areas is worth a short licensed coverage review: premium or budget, coverage fit, or renewal or timing. If not, I can stop here; which part should I check first?

### adv-permission-weak-acknowledgement-variants-synthetic-telecom-plan-review-02
- Classification: `true_stability_menu_reset`
- Campaign: `synthetic-telecom-plan-review`
- Family: `permission_weak_acknowledgement_variants`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'okay fine']`
- Final response: The quick check is whether any of these areas is worth a short human plan and availability review: plan fit, coverage or availability, or contract or switching. If not, I can stop here; which part should I check first?

### adv-permission-weak-acknowledgement-variants-synthetic-telecom-plan-review-03
- Classification: `true_stability_menu_reset`
- Campaign: `synthetic-telecom-plan-review`
- Family: `permission_weak_acknowledgement_variants`
- Source: `contextual_buyer_semantics`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'go ahead']`
- Final response: Thanks, I am checking plan fit, coverage or availability, or contract or switching. Which one is causing trouble, if any?

### adv-permission-weak-acknowledgement-variants-synthetic-telecom-plan-review-04
- Classification: `true_stability_menu_reset`
- Campaign: `synthetic-telecom-plan-review`
- Family: `permission_weak_acknowledgement_variants`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'fine but be fast']`
- Final response: The quick check is whether any of these areas is worth a short human plan and availability review: plan fit, coverage or availability, or contract or switching. If not, I can stop here; which part should I check first?

### adv-permission-weak-acknowledgement-variants-synthetic-automotive-service-review-02
- Classification: `true_stability_menu_reset`
- Campaign: `synthetic-automotive-service-review`
- Family: `permission_weak_acknowledgement_variants`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'okay fine']`
- Final response: The quick check is whether any of these areas is worth a short service advisor inspection review: vehicle issue, repair timing, or warranty or estimate. If not, I can stop here; which part should I check first?

### adv-permission-weak-acknowledgement-variants-synthetic-automotive-service-review-03
- Classification: `true_stability_menu_reset`
- Campaign: `synthetic-automotive-service-review`
- Family: `permission_weak_acknowledgement_variants`
- Source: `contextual_buyer_semantics`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'go ahead']`
- Final response: Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any?

### adv-permission-weak-acknowledgement-variants-synthetic-automotive-service-review-04
- Classification: `true_stability_menu_reset`
- Campaign: `synthetic-automotive-service-review`
- Family: `permission_weak_acknowledgement_variants`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'fine but be fast']`
- Final response: The quick check is whether any of these areas is worth a short service advisor inspection review: vehicle issue, repair timing, or warranty or estimate. If not, I can stop here; which part should I check first?

### adv-permission-weak-acknowledgement-variants-synthetic-membership-plan-review-02
- Classification: `true_stability_menu_reset`
- Campaign: `synthetic-membership-plan-review`
- Family: `permission_weak_acknowledgement_variants`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'okay fine']`
- Final response: The quick check is whether any of these areas is worth a short account support or plan-fit review: plan fit, renewal or cancellation, or usage or value. If not, I can stop here; which part should I check first?

### adv-permission-weak-acknowledgement-variants-synthetic-membership-plan-review-04
- Classification: `true_stability_menu_reset`
- Campaign: `synthetic-membership-plan-review`
- Family: `permission_weak_acknowledgement_variants`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'fine but be fast']`
- Final response: The quick check is whether any of these areas is worth a short account support or plan-fit review: plan fit, renewal or cancellation, or usage or value. If not, I can stop here; which part should I check first?

### adv-permission-weak-acknowledgement-variants-synthetic-b2b-saas-operations-02
- Classification: `true_stability_menu_reset`
- Campaign: `synthetic-b2b-saas-operations`
- Family: `permission_weak_acknowledgement_variants`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'okay fine']`
- Final response: The quick check is whether any of these areas is worth a short operations fit review: manual work, integration risk, or visibility gap. If not, I can stop here; which part should I check first?

### adv-permission-weak-acknowledgement-variants-synthetic-b2b-saas-operations-04
- Classification: `true_stability_menu_reset`
- Campaign: `synthetic-b2b-saas-operations`
- Family: `permission_weak_acknowledgement_variants`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'fine but be fast']`
- Final response: The quick check is whether any of these areas is worth a short operations fit review: manual work, integration risk, or visibility gap. If not, I can stop here; which part should I check first?

### adv-direct-product-value-challenge-loops-routesignal_live_demo-02
- Classification: `true_repeated_response_without_progress`
- Campaign: `routesignal_live_demo`
- Family: `direct_product_value_challenge_loops`
- Source: `universal_response_shape`
- Flags: `repeated_response`
- Buyer script: `['__agent_open__', 'what are you selling', 'explain it plainly', 'say it in one sentence']`
- Final response: In one sentence: this call checks whether inbound demo follow-up is slipping now and is worth a short review.

### adv-direct-product-value-challenge-loops-synthetic-insurance-review-02
- Classification: `true_repeated_response_without_progress`
- Campaign: `synthetic-insurance-review`
- Family: `direct_product_value_challenge_loops`
- Source: `universal_response_shape`
- Flags: `repeated_response`
- Buyer script: `['__agent_open__', 'what are you selling', 'explain it plainly', 'say it in one sentence']`
- Final response: In one sentence: this call checks whether premium pressure is still a problem and is worth a short review.

### adv-direct-product-value-challenge-loops-synthetic-telecom-plan-review-02
- Classification: `true_repeated_response_without_progress`
- Campaign: `synthetic-telecom-plan-review`
- Family: `direct_product_value_challenge_loops`
- Source: `universal_response_shape`
- Flags: `repeated_response`
- Buyer script: `['__agent_open__', 'what are you selling', 'explain it plainly', 'say it in one sentence']`
- Final response: In one sentence: this call checks whether plan fit is still a problem and is worth a short review.

### adv-direct-product-value-challenge-loops-synthetic-automotive-service-review-02
- Classification: `true_repeated_response_without_progress`
- Campaign: `synthetic-automotive-service-review`
- Family: `direct_product_value_challenge_loops`
- Source: `universal_response_shape`
- Flags: `repeated_response`
- Buyer script: `['__agent_open__', 'what are you selling', 'explain it plainly', 'say it in one sentence']`
- Final response: In one sentence: this call checks whether repair timing is still a problem and is worth a short review.

### adv-direct-product-value-challenge-loops-synthetic-membership-plan-review-02
- Classification: `true_repeated_response_without_progress`
- Campaign: `synthetic-membership-plan-review`
- Family: `direct_product_value_challenge_loops`
- Source: `universal_response_shape`
- Flags: `repeated_response`
- Buyer script: `['__agent_open__', 'what are you selling', 'explain it plainly', 'say it in one sentence']`
- Final response: In one sentence: this call checks whether plan fit is still a problem and is worth a short review.

### adv-direct-product-value-challenge-loops-synthetic-b2b-saas-operations-02
- Classification: `true_repeated_response_without_progress`
- Campaign: `synthetic-b2b-saas-operations`
- Family: `direct_product_value_challenge_loops`
- Source: `universal_response_shape`
- Flags: `repeated_response`
- Buyer script: `['__agent_open__', 'what are you selling', 'explain it plainly', 'say it in one sentence']`
- Final response: In one sentence: this call checks whether manual work is still a problem and is worth a short review.

### adv-repeated-product-detail-scope-questions-routesignal_live_demo-02
- Classification: `true_stability_menu_reset`
- Campaign: `routesignal_live_demo`
- Family: `repeated_product_detail_scope_questions`
- Source: `dialogue_pragmatics`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'what exactly can you tell me', 'why are you calling if you cannot explain it']`
- Final response: I am calling because RouteSignal helps with inbound demo follow-up: demo leads getting assigned, reminded, and followed up. Northstar is asking for a short workflow review if leads are slipping today.

### adv-repeated-product-detail-scope-questions-routesignal_live_demo-03
- Classification: `true_stability_menu_reset`
- Campaign: `routesignal_live_demo`
- Family: `repeated_product_detail_scope_questions`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'can you give me any information', 'what can you say in plain English']`
- Final response: If inbound demo requests land in one inbox, missed follow-up can happen because everyone assumes someone else replied. Which part is harder today: seeing it, assigning the reply, or remembering the callback?

### adv-repeated-product-detail-scope-questions-routesignal_live_demo-04
- Classification: `true_stability_menu_reset`
- Campaign: `routesignal_live_demo`
- Family: `repeated_product_detail_scope_questions`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'what does this do', 'can you explain the scope']`
- Final response: If inbound demo requests land in one inbox, missed follow-up can happen because everyone assumes someone else replied. Which part is harder today: seeing it, assigning the reply, or remembering the callback?

### adv-repeated-product-detail-scope-questions-synthetic-insurance-review-01
- Classification: `true_stability_menu_reset`
- Campaign: `synthetic-insurance-review`
- Family: `repeated_product_detail_scope_questions`
- Source: `universal_response_shape`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'what does your product do', 'can you give me details', 'so you cannot give me details']`
- Final response: Correct. I can explain the high-level purpose, but detailed advice belongs with the licensed insurance specialist. This call only checks whether a licensed coverage review is worth it. Do you want me to check whether a review is useful?

### adv-repeated-product-detail-scope-questions-synthetic-insurance-review-02
- Classification: `true_stability_menu_reset`
- Campaign: `synthetic-insurance-review`
- Family: `repeated_product_detail_scope_questions`
- Source: `dialogue_pragmatics`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'what exactly can you tell me', 'why are you calling if you cannot explain it']`
- Final response: I am calling from Synthetic Insurance Agency about Policy Review Call, and asking whether premium or budget, coverage fit, or renewal or timing are worth a short licensed coverage review. If none of those apply, I can stop here.

### adv-repeated-product-detail-scope-questions-synthetic-insurance-review-03
- Classification: `true_stability_menu_reset`
- Campaign: `synthetic-insurance-review`
- Family: `repeated_product_detail_scope_questions`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'can you give me any information', 'what can you say in plain English']`
- Final response: If premium or budget, coverage fit, or renewal or timing are actually relevant, a licensed insurance specialist can do a short licensed coverage review. If not, I can stop here; should I ask one quick fit question?

### adv-repeated-product-detail-scope-questions-synthetic-insurance-review-04
- Classification: `true_stability_menu_reset`
- Campaign: `synthetic-insurance-review`
- Family: `repeated_product_detail_scope_questions`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'what does this do', 'can you explain the scope']`
- Final response: If premium or budget, coverage fit, or renewal or timing are actually relevant, a licensed insurance specialist can do a short licensed coverage review. If not, I can stop here; should I ask one quick fit question?

### adv-repeated-product-detail-scope-questions-synthetic-telecom-plan-review-01
- Classification: `true_stability_menu_reset`
- Campaign: `synthetic-telecom-plan-review`
- Family: `repeated_product_detail_scope_questions`
- Source: `universal_response_shape`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'what does your product do', 'can you give me details', 'so you cannot give me details']`
- Final response: Correct. I can explain the high-level purpose, but detailed advice belongs with the telecom account specialist. This call only checks whether a human plan and availability review is worth it. Do you want me to check whether a review is useful?

### adv-repeated-product-detail-scope-questions-synthetic-telecom-plan-review-02
- Classification: `true_stability_menu_reset`
- Campaign: `synthetic-telecom-plan-review`
- Family: `repeated_product_detail_scope_questions`
- Source: `dialogue_pragmatics`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'what exactly can you tell me', 'why are you calling if you cannot explain it']`
- Final response: I am calling from Synthetic Telecom Provider about Plan Review Call, and asking whether plan fit, coverage or availability, or contract or switching are worth a short human plan and availability review. If none of those apply, I can stop here.

## False Positives / Expectation Too Strict
### adv-disallowed-persistence-after-stop-routesignal_live_demo-03
- Classification: `terminal_preservation_artifact`
- Campaign: `routesignal_live_demo`
- Family: `disallowed_persistence_after_stop`
- Flags: `repeated_full_menu`
- Final response: Understood. I will stop here. Goodbye.

### adv-disallowed-persistence-after-stop-synthetic-insurance-review-03
- Classification: `terminal_preservation_artifact`
- Campaign: `synthetic-insurance-review`
- Family: `disallowed_persistence_after_stop`
- Flags: `repeated_full_menu`
- Final response: Understood. I will stop here. Goodbye.

### adv-disallowed-persistence-after-stop-synthetic-telecom-plan-review-03
- Classification: `terminal_preservation_artifact`
- Campaign: `synthetic-telecom-plan-review`
- Family: `disallowed_persistence_after_stop`
- Flags: `repeated_full_menu`
- Final response: Understood. I will stop here. Goodbye.

### adv-disallowed-persistence-after-stop-synthetic-automotive-service-review-03
- Classification: `terminal_preservation_artifact`
- Campaign: `synthetic-automotive-service-review`
- Family: `disallowed_persistence_after_stop`
- Flags: `repeated_full_menu`
- Final response: Understood. I will stop here. Goodbye.

### adv-disallowed-persistence-after-stop-synthetic-membership-plan-review-03
- Classification: `terminal_preservation_artifact`
- Campaign: `synthetic-membership-plan-review`
- Family: `disallowed_persistence_after_stop`
- Flags: `repeated_full_menu`
- Final response: Understood. I will stop here. Goodbye.

### adv-disallowed-persistence-after-stop-synthetic-b2b-saas-operations-03
- Classification: `terminal_preservation_artifact`
- Campaign: `synthetic-b2b-saas-operations`
- Family: `disallowed_persistence_after_stop`
- Flags: `repeated_full_menu`
- Final response: Understood. I will stop here. Goodbye.

## Recommended Patch Scope
- Patch true_stability_menu_reset after corrections, hostile challenges, mismatch, and configured-gap clarity requests.
- Patch true_hostile_challenge_not_deescalated with direct one-move de-escalation.
- Patch true_repeated_response_without_progress only where the buyer explicitly complains about repetition.
- Patch true_appointment_too_early separately only if callback/time requests still schedule instead of noting a preference.
- Do not patch acceptable ASR clarifications into pain confirmations.

## Runtime Behavior Changed
- `false`
