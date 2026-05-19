# LIVE-DEMO-002 runtime extraction baseline

- Baseline source: `LIVE-DEMO-001`
- Behavior policy: `behavior_preserved`
- LIVE-DEMO-001 validator: `pass`
- Provider calls made: `false`
- Opens PROD-102: `false`

## Compact Regression Coverage
- `repetition_prevention`: `true`
- `followup_continuity`: `true`
- `voice_delivery_propagation`: `true`
- `product_answer_routing`: `true`
- `asr_quality_handling`: `true`
- `callback_scheduling_boundary`: `true`
- `callback_workflow_disambiguation`: `true`
- `call_context_recovery`: `true`
- `customer_echo_prevention`: `true`
- `seller_led_next_move`: `true`
- `seller_led_close_progression`: `true`
- `terminal_call_control_stop`: `true`
- `live_tts_fallback_voice_guard`: `true`
- `stale_session_greeting_relevance`: `true`
- `voice_consistency_across_turns`: `true`
- `agent_led_sales_opening`: `true`
- `qualification_steering`: `true`
- `sales_context_variety`: `true`
- `sales_emphasis_priority`: `true`
- `previous_question_clarification`: `true`
- `ambiguous_negative_clarification`: `true`
- `caller_identity_recall`: `true`
- `internal_repair_speech_blocked`: `true`
- `async_reasoning_enrichment_evidence`: `true`

## Baseline Cases
- `direct-price-seller-led` / `direct_price_answer_routing`: pass=`true`, reason=`no_session_continuity_match`
- `product-explanation` / `product_answer_routing`: pass=`true`, reason=`campaign_depth_product_explanation_answered`
- `manual-tracking` / `product_answer_routing`: pass=`true`, reason=`campaign_depth_manual_tracking_answered`
- `growth-plan` / `product_answer_routing`: pass=`true`, reason=`campaign_depth_growth_plan_answered`
- `small-team` / `product_answer_routing`: pass=`true`, reason=`campaign_depth_small_team_fit_answered`
- `unnecessary-specialist` / `product_answer_routing`: pass=`true`, reason=`campaign_depth_unnecessary_handoff_answered`
- `salesforce-boundary` / `product_answer_routing`: pass=`true`, reason=`campaign_depth_integration_boundary_answered`
- `security-boundary` / `product_answer_routing`: pass=`true`, reason=`campaign_depth_security_boundary_answered`
- `workflow-included` / `product_answer_routing`: pass=`true`, reason=`campaign_depth_workflow_scope_answered`
- `observed-greeting` / `followup_continuity`: pass=`true`, reason=`opening_greeting_answered`
- `observed-price` / `followup_continuity`: pass=`true`, reason=`focus_shift_to_price_from_qualification`
- `observed-effort-shift` / `followup_continuity`: pass=`true`, reason=`focus_shift_to_effort_from_price`
- `observed-effort-persisted` / `followup_continuity`: pass=`true`, reason=`duplicate_response_prevented_with_effort_progression`
- `fit-greeting` / `anti_loop`: pass=`true`, reason=`opening_greeting_answered`
- `fit-selected` / `anti_loop`: pass=`true`, reason=`focus_shift_to_fit_from_qualification`
- `fit-price-deferred` / `anti_loop`: pass=`true`, reason=`duplicate_response_prevented_with_fit_progression`
- `fit-repeat` / `anti_loop`: pass=`true`, reason=`duplicate_response_prevented_with_fit_progression`
- `fit-relevance` / `anti_loop`: pass=`true`, reason=`duplicate_response_prevented_with_fit_progression`
- `voice-dry-run` / `voice_delivery_propagation`: pass=`true`, reason=`campaign_depth_product_explanation_answered`
- `voice-forced-missing-key` / `voice_delivery_propagation`: pass=`true`, reason=`campaign_depth_product_explanation_answered`
- `asr-low-confidence` / `asr_quality_handling`: pass=`true`, reason=`asr_low_confidence_repair`
- `asr-clear-confidence` / `asr_quality_handling`: pass=`true`, reason=`campaign_depth_product_explanation_answered`
- `asr-fragment` / `asr_quality_handling`: pass=`true`, reason=`asr_fragment_repair`

## Intentional Improvements
- `agent-open-speaks-first` / `agent_led_sales_opening`: pass=`true`, policy=`intentional_improvement`, reason=`agent_opening_started`
- `agent-open-question-clarified` / `previous_question_clarification`: pass=`true`, policy=`intentional_improvement`, reason=`previous_question_clarified`
- `caller-identity-recalled` / `caller_identity_recall`: pass=`true`, policy=`intentional_improvement`, reason=`caller_identity_recalled`
- `agent-open-negative-clarified` / `ambiguous_negative_clarification`: pass=`true`, policy=`intentional_improvement`, reason=`ambiguous_negative_clarified`
- `agent-open-ack-steers-qualification` / `agent_led_sales_opening`: pass=`true`, policy=`intentional_improvement`, reason=`proactive_qualification_guidance_after_acknowledgement`
- `qualification-negative-clarified` / `ambiguous_negative_clarification`: pass=`true`, policy=`intentional_improvement`, reason=`ambiguous_negative_clarified`
- `security-followup-no-internal-repair-speech` / `internal_repair_speech_blocked`: pass=`true`, policy=`intentional_improvement`, reason=`resolved_security_focus_progressed`
- `agent-open-gap-to-workflow-review` / `agent_led_sales_opening`: pass=`true`, policy=`intentional_improvement`, reason=`seller_gap_selected_for_qualification`
- `callback-gap-maps-to-value-not-scheduling` / `callback_workflow_disambiguation`: pass=`true`, policy=`intentional_improvement`, reason=`seller_gap_selected_for_qualification`
- `callback-term-clarified-as-workflow` / `callback_workflow_disambiguation`: pass=`true`, policy=`intentional_improvement`, reason=`callback_workflow_clarified`
- `time-constrained-agenda` / `call_context_recovery`: pass=`true`, policy=`intentional_improvement`, reason=`time_constrained_agenda_answered`
- `buyer-expects-agent-lead` / `call_context_recovery`: pass=`true`, policy=`intentional_improvement`, reason=`seller_agenda_recovered`
- `workflow-review-next-step` / `call_context_recovery`: pass=`true`, policy=`intentional_improvement`, reason=`workflow_review_next_step_explained`
- `topic-confusion-repaired` / `call_context_recovery`: pass=`true`, policy=`intentional_improvement`, reason=`topic_confusion_repaired`
- `agent-open-followup-variety` / `sales_context_variety_and_emphasis`: pass=`true`, policy=`intentional_improvement`, reason=`resolved_qualification_focus_progressed`
- `sales-opening-greeting` / `sales_opening_permission_check`: pass=`true`, policy=`intentional_improvement`, reason=`opening_greeting_answered`
- `stale-session-greeting-opens-cleanly` / `stale_session_greeting_relevance`: pass=`true`, policy=`intentional_improvement`, reason=`opening_greeting_answered`
- `stable-elevenlabs-settings-across-mixed-turns` / `voice_consistency_across_turns`: pass=`true`, policy=`intentional_improvement`, reason=`callback_time_confirmed`
- `price-ack-proactive-guidance-1` / `proactive_guidance_after_acknowledgement`: pass=`true`, policy=`intentional_improvement`, reason=`proactive_price_guidance_after_acknowledgement`
- `price-ack-proactive-guidance-2` / `proactive_guidance_after_acknowledgement`: pass=`true`, policy=`intentional_improvement`, reason=`proactive_price_guidance_after_acknowledgement`
- `price-gap-to-workflow-review` / `seller_led_close_progression`: pass=`true`, policy=`intentional_improvement`, reason=`seller_gap_selected_for_price`
- `guided-price-progression` / `multi_topic_non_repeating_progression`: pass=`true`, policy=`intentional_improvement`, reason=`resolved_price_focus_progressed`
- `guided-fit-progression` / `multi_topic_non_repeating_progression`: pass=`true`, policy=`intentional_improvement`, reason=`resolved_fit_focus_progressed`
- `guided-timing-progression` / `multi_topic_non_repeating_progression`: pass=`true`, policy=`intentional_improvement`, reason=`resolved_timing_focus_progressed`
- `guided-features-progression` / `multi_topic_non_repeating_progression`: pass=`true`, policy=`intentional_improvement`, reason=`resolved_details_focus_progressed`
- `no-time-asks-for-callback-time` / `callback_scheduling_boundary`: pass=`true`, policy=`intentional_improvement`, reason=`callback_request_time_needed`
- `callback-time-confirms-and-ends` / `callback_scheduling_boundary`: pass=`true`, policy=`intentional_improvement`, reason=`callback_time_confirmed`

## Private Evidence Packet Shape

The baseline records packet keys only, not private turn audio or secret values.

- Top-level keys: `asr, audio_url, campaign_id, demo_conversation_memory, demo_conversation_stability_guard, demo_session_continuity, dialogue_reasoner_async_enrichment, durable_provider_agent_created, input_type, latency, live_demo_id, mode, opens_prod_102, packet, provider_agent_used, runtime_behavior_changed, session_id, session_turn_index, stage, summary, transcript, turn_taking, voice_cloning_used`
- ASR keys include: `audio_uploaded_to_python_server, browser_vendor_may_process_audio, confidence, provider, quality_gate, transcript_sent_to_python_server`
- Turn-taking keys include: `listen_while_agent_speaks, restart_after_agent_output_ms, server_policy, voice_turn_state_received`
- Packet keys include: `api_calls_made, campaign, candidate_response, composer_hooks, core_pack, decision_snapshot, final_response, generation_mode, guardrails, input_type, latency, llm_used, policy_response, provider, requires_api_key, response_constraints, response_generation_id, retrieval, runtime_tts_delivery_id, runtime_voice_delivery_id, stage, transcript, tts_delivery, validation, voice_delivery`
- Async enrichment keys include: `api_key_value_logged, blocked_reason, customer_response_blocked_on_provider, customer_response_snapshot, deterministic_reasoning_fingerprint, final_response_changed_by_provider, hybrid_schema_fields, ignored_by_live_turn, locked_deterministic_route, mutates_final_response, opens_prod_102, prompt_char_count, prompt_stored, provider_call_allowed, provider_call_made, provider_result_applied_after_response, provider_result_received_after_response, queued_before_provider, raw_response_stored, reasoner_id, response_packet_id, runtime_route_override_allowed, schema_version, status, text_sent_to_provider, upstream_hybrid_reasoner_id`
- Async response snapshot keys include: `available_before_provider, char_count, immutable_by_provider, text_fingerprint, text_logged`
