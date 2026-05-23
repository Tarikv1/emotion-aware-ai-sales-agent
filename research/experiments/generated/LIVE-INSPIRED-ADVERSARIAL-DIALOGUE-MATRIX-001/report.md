# LIVE-INSPIRED-ADVERSARIAL-DIALOGUE-MATRIX-001

## Summary
- Status: `red_findings`
- Scenario count: `729`
- Multi-turn conversations: `398`
- Core gate failures: `0`
- Exploratory red findings: `367`

## Scenario Count
- Total scenario runs: `729`
- Core gate: `9`
- Exploratory: `720`

## Campaign Coverage
- `routesignal_live_demo`: `125`
- `synthetic-automotive-service-review`: `120`
- `synthetic-b2b-saas-operations`: `120`
- `synthetic-insurance-review`: `122`
- `synthetic-membership-plan-review`: `120`
- `synthetic-telecom-plan-review`: `122`

## Scenario Family Coverage
- `agent_looping_complaints`: `24`
- `asr_near_miss_gap_phrases`: `26`
- `asr_near_miss_invented_transcript_stress`: `24`
- `buyer_correction_contradiction_stress`: `24`
- `buyer_says_agent_is_wrong`: `24`
- `callback_time_too_early_or_ambiguous`: `24`
- `campaign_selector_wrong_campaign_contamination`: `24`
- `commercial_pressure_close_strength_stress`: `25`
- `commercial_quality_stress`: `24`
- `direct_product_value_challenge_loops`: `25`
- `disallowed_persistence_after_stop`: `24`
- `early_callback_premature_scheduling`: `24`
- `false_assumption_correction`: `25`
- `hostile_challenging_buyer`: `24`
- `human_context_interruption_pressure`: `24`
- `human_context_sales_intent_hybrids`: `24`
- `impact_before_clean_pain`: `24`
- `long_conversation_state_drift`: `24`
- `mixed_intent_buyer_turns`: `24`
- `multi_campaign_contamination_stress`: `24`
- `permission_weak_acknowledgement_variants`: `25`
- `price_budget_affordability_stress`: `24`
- `repeated_answer_variation_anti_loop`: `24`
- `repeated_challenge_escalation`: `24`
- `repeated_product_detail_scope_questions`: `25`
- `sales_realism_score_heuristics`: `24`
- `scope_boundary_regulated_detail_stress`: `25`
- `stop_refusal_pressure_test`: `24`
- `vague_affirmative_after_context`: `25`
- `why_human_review_challenge`: `24`

## Pass/Fail Counts
- `passed`: `362`
- `failed_or_red`: `367`
- `core_gate_failures`: `0`
- `exploratory_red_findings`: `367`

## Top Failure Clusters
- `repeated_full_menu`: `277`
- `out_of_scope_reset_after_relevant_context`: `23`
- `repeated_response`: `18`
- `asr_near_miss_not_clarified`: `16`
- `did_not_answer_direct_question`: `13`
- `false_assumption_not_repaired`: `13`
- `appointment_too_early`: `12`
- `hostile_response_not_deescalated`: `12`
- `internal_wording_leak`: `10`
- `campaign_contamination`: `7`
- `too_long_for_live_voice`: `4`

## Failures By Scenario Family
- `agent_looping_complaints`: `5`
- `asr_near_miss_gap_phrases`: `21`
- `asr_near_miss_invented_transcript_stress`: `10`
- `buyer_correction_contradiction_stress`: `9`
- `buyer_says_agent_is_wrong`: `24`
- `callback_time_too_early_or_ambiguous`: `24`
- `campaign_selector_wrong_campaign_contamination`: `13`
- `commercial_pressure_close_strength_stress`: `16`
- `commercial_quality_stress`: `10`
- `direct_product_value_challenge_loops`: `6`
- `disallowed_persistence_after_stop`: `6`
- `early_callback_premature_scheduling`: `6`
- `false_assumption_correction`: `11`
- `hostile_challenging_buyer`: `21`
- `human_context_interruption_pressure`: `6`
- `impact_before_clean_pain`: `19`
- `long_conversation_state_drift`: `7`
- `mixed_intent_buyer_turns`: `6`
- `multi_campaign_contamination_stress`: `18`
- `permission_weak_acknowledgement_variants`: `15`
- `price_budget_affordability_stress`: `6`
- `repeated_answer_variation_anti_loop`: `23`
- `repeated_challenge_escalation`: `24`
- `repeated_product_detail_scope_questions`: `21`
- `sales_realism_score_heuristics`: `12`
- `scope_boundary_regulated_detail_stress`: `5`
- `vague_affirmative_after_context`: `12`
- `why_human_review_challenge`: `11`

## Failures By Campaign
- `routesignal_live_demo`: `59`
- `synthetic-automotive-service-review`: `62`
- `synthetic-b2b-saas-operations`: `61`
- `synthetic-insurance-review`: `61`
- `synthetic-membership-plan-review`: `58`
- `synthetic-telecom-plan-review`: `66`

## Failures By Selected Action Source
- `contextual_buyer_semantics`: `12`
- `dialogue_pragmatics`: `6`
- `live_voice_session_policy`: `36`
- `pre_speech_conversation_stability_guard`: `233`
- `terminal_call_control`: `6`
- `universal_response_shape`: `74`

## Examples Of Worst Conversations
### adv-asr-near-miss-gap-phrases-synthetic-insurance-review-04
- Family: `asr_near_miss_gap_phrases`
- Campaign: `synthetic-insurance-review`
- Priority: `critical`
- Flags: `asr_near_miss_not_clarified, internal_wording_leak, repeated_full_menu`
- Buyer script: `['__agent_open__', 'yeah', 'coverage thing is confusing', 'it wastes time']`
- Final response: The quick check is whether any of these areas is worth a short licensed coverage review: premium or budget, coverage fit, or renewal or timing. If not, I can stop here; which part should I check first?

### adv-asr-near-miss-gap-phrases-synthetic-b2b-saas-operations-03
- Family: `asr_near_miss_gap_phrases`
- Campaign: `synthetic-b2b-saas-operations`
- Priority: `critical`
- Flags: `asr_near_miss_not_clarified, internal_wording_leak`
- Buyer script: `['__agent_open__', 'yeah', 'integration thing is confusing']`
- Final response: I should not guess on technical details. I can send this to implementation specialist.

### adv-multi-campaign-contamination-stress-routesignal_live_demo-02
- Family: `multi_campaign_contamination_stress`
- Campaign: `routesignal_live_demo`
- Priority: `critical`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?

### adv-multi-campaign-contamination-stress-synthetic-automotive-service-review-02
- Family: `multi_campaign_contamination_stress`
- Campaign: `synthetic-automotive-service-review`
- Priority: `critical`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?

### adv-multi-campaign-contamination-stress-synthetic-b2b-saas-operations-02
- Family: `multi_campaign_contamination_stress`
- Campaign: `synthetic-b2b-saas-operations`
- Priority: `critical`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?

### adv-multi-campaign-contamination-stress-synthetic-insurance-review-02
- Family: `multi_campaign_contamination_stress`
- Campaign: `synthetic-insurance-review`
- Priority: `critical`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?

### adv-multi-campaign-contamination-stress-synthetic-membership-plan-review-02
- Family: `multi_campaign_contamination_stress`
- Campaign: `synthetic-membership-plan-review`
- Priority: `critical`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?

### adv-multi-campaign-contamination-stress-synthetic-telecom-plan-review-02
- Family: `multi_campaign_contamination_stress`
- Campaign: `synthetic-telecom-plan-review`
- Priority: `critical`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?

### adv-scope-boundary-regulated-detail-stress-routesignal_live_demo-01
- Family: `scope_boundary_regulated_detail_stress`
- Campaign: `routesignal_live_demo`
- Priority: `critical`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'can you tell me exactly what coverage I need']`
- Final response: I should not give coverage advice. I can route this to the approved qualified reviewer path.

### adv-scope-boundary-regulated-detail-stress-routesignal_live_demo-03
- Family: `scope_boundary_regulated_detail_stress`
- Campaign: `routesignal_live_demo`
- Priority: `critical`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'is coverage available at my address']`
- Final response: I should not give coverage advice. I can route this to the approved qualified reviewer path.

### adv-asr-near-miss-gap-phrases-synthetic-b2b-saas-operations-04
- Family: `asr_near_miss_gap_phrases`
- Campaign: `synthetic-b2b-saas-operations`
- Priority: `high`
- Flags: `asr_near_miss_not_clarified, out_of_scope_reset_after_relevant_context, repeated_full_menu`
- Buyer script: `['__agent_open__', 'yeah', 'visibility thing is unclear', 'it wastes time']`
- Final response: The quick check is whether any of these areas is worth a short operations fit review: manual work, integration risk, or visibility gap. If not, I can stop here; which part should I check first?

### adv-asr-near-miss-gap-phrases-synthetic-insurance-review-02
- Family: `asr_near_miss_gap_phrases`
- Campaign: `synthetic-insurance-review`
- Priority: `high`
- Flags: `asr_near_miss_not_clarified, out_of_scope_reset_after_relevant_context, repeated_full_menu`
- Buyer script: `['__agent_open__', 'yeah', 'payment pressure is a problem', 'it wastes time']`
- Final response: The quick check is whether any of these areas is worth a short licensed coverage review: premium or budget, coverage fit, or renewal or timing. If not, I can stop here; which part should I check first?

## Stability Guard Override Findings

## Direct Question/Challenge Findings
- `adv-direct-product-value-challenge-loops-routesignal_live_demo-02`
- `adv-direct-product-value-challenge-loops-synthetic-insurance-review-02`
- `adv-direct-product-value-challenge-loops-synthetic-telecom-plan-review-02`
- `adv-direct-product-value-challenge-loops-synthetic-automotive-service-review-02`
- `adv-direct-product-value-challenge-loops-synthetic-membership-plan-review-02`
- `adv-direct-product-value-challenge-loops-synthetic-b2b-saas-operations-02`
- `adv-repeated-challenge-escalation-routesignal_live_demo-04`
- `adv-why-human-review-challenge-routesignal_live_demo-04`
- `adv-why-human-review-challenge-synthetic-insurance-review-01`
- `adv-why-human-review-challenge-synthetic-telecom-plan-review-01`
- `adv-why-human-review-challenge-synthetic-automotive-service-review-01`
- `adv-why-human-review-challenge-synthetic-membership-plan-review-01`
- `adv-why-human-review-challenge-synthetic-b2b-saas-operations-01`

## ASR Near-Miss Findings
- `adv-asr-near-miss-gap-phrases-routesignal_live_demo-04`
- `adv-asr-near-miss-gap-phrases-synthetic-insurance-review-02`
- `adv-asr-near-miss-gap-phrases-synthetic-insurance-review-04`
- `adv-asr-near-miss-gap-phrases-synthetic-telecom-plan-review-03`
- `adv-asr-near-miss-gap-phrases-synthetic-telecom-plan-review-04`
- `adv-asr-near-miss-gap-phrases-synthetic-membership-plan-review-01`
- `adv-asr-near-miss-gap-phrases-synthetic-membership-plan-review-02`
- `adv-asr-near-miss-gap-phrases-synthetic-b2b-saas-operations-03`
- `adv-asr-near-miss-gap-phrases-synthetic-b2b-saas-operations-04`
- `adv-asr-near-miss-invented-transcript-stress-routesignal_live_demo-01`
- `adv-asr-near-miss-invented-transcript-stress-synthetic-insurance-review-01`
- `adv-asr-near-miss-invented-transcript-stress-synthetic-telecom-plan-review-01`
- `adv-asr-near-miss-invented-transcript-stress-synthetic-automotive-service-review-01`
- `adv-asr-near-miss-invented-transcript-stress-synthetic-membership-plan-review-01`
- `adv-asr-near-miss-invented-transcript-stress-synthetic-membership-plan-review-02`
- `adv-asr-near-miss-invented-transcript-stress-synthetic-b2b-saas-operations-01`

## Stop/Refusal Preservation
- Explicit-stop red findings: `0`

## Side-Effect Boundary Summary
- `provider_calls_made`: `false`
- `local_llm_calls_made`: `false`
- `live_tts_used`: `false`
- `tts_provider_calls_made`: `false`
- `audio_file_created`: `false`
- `sends_email`: `false`
- `creates_calendar_event`: `false`
- `writes_crm`: `false`
- `opens_prod_102`: `false`
- `customer_audio_uploaded_to_python_server`: `false`
- `customer_audio_uploaded_to_tts_provider`: `false`

## Recommendation
- `needs human review and ranked follow-up patches`
