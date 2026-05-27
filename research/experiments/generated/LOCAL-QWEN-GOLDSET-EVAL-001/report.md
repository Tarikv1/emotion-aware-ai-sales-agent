# LOCAL-QWEN-GOLDSET-EVAL-001

## Run Summary

- status: completed
- quality_status: fail
- model_id: Qwen/Qwen2.5-7B-Instruct
- planner_schema_mode: compact
- case_count_attempted: 80
- case_count_completed: 80
- schema_valid_count: 58
- verifier_pass_count: 52
- gold_match_count: 0
- exact_match_count: 0
- semantic_match_count: 52
- deterministic_exact_match_count: 80
- deterministic_semantic_match_count: 78
- failed_case_count: 28

## Qwen Versus Deterministic

- summary: {"both_fail": 1, "both_pass": 51, "deterministic_better": 27, "qwen_better": 1}
- failure_classes: {"buyer_word_not_preserved": 2, "conjunction_relation_mismatch": 1, "gold_response_plan_mismatch": 58, "gold_sales_mismatch": 58, "gold_semantic_mismatch": 58, "gold_state_mismatch": 58, "must_not_include_present": 3, "or_and_drift": 1, "planner_output_missing": 22}

## Fidelity And Safety

- current_utterance_fidelity_result: {"both_pass": 31, "deterministic_better": 49}
- and_or_fidelity_result: {"both_pass": 9, "deterministic_better": 1, "not_applicable": 70}
- negation_fidelity_result: {"both_pass": 6, "deterministic_better": 1, "not_applicable": 73}
- voice_not_writing_result: {"both_pass": 1, "not_applicable": 79}
- team_state_poisoning_result: {"both_pass": 21, "deterministic_better": 39, "not_applicable": 20}
- internal_policy_leak_result: {"both_pass": 80}
- fake_side_effect_result: {"both_pass": 80}
- unsupported_claim_result: {"both_pass": 78, "qwen_better": 2}
- sales_action_result: {"deterministic_better": 80}

## Latency

- model_load_time_ms: 46894.985
- total_generation_latency_ms: 943980.392
- average_generation_latency_ms: 11799.755
- p50_generation_latency_ms: 11791.447
- p90_generation_latency_ms: 13495.329
- slowest_cases: [{"case_id": "paraphrase_signup_020", "total_generation_latency_ms": 15270.254, "prompt_token_count": 1016, "tokens_generated": 123}, {"case_id": "live_terminal_acceptance_016", "total_generation_latency_ms": 14651.458, "prompt_token_count": 1013, "tokens_generated": 123}, {"case_id": "paraphrase_chatgpt_plus_claude_003", "total_generation_latency_ms": 14367.527, "prompt_token_count": 1017, "tokens_generated": 139}, {"case_id": "live_current_tools_002", "total_generation_latency_ms": 14003.543, "prompt_token_count": 1019, "tokens_generated": 133}, {"case_id": "negative_silence_001", "total_generation_latency_ms": 13986.525, "prompt_token_count": 981, "tokens_generated": 134}, {"case_id": "live_asr_chacha_005", "total_generation_latency_ms": 13825.038, "prompt_token_count": 1017, "tokens_generated": 135}, {"case_id": "negative_not_team_001", "total_generation_latency_ms": 13699.434, "prompt_token_count": 986, "tokens_generated": 133}, {"case_id": "live_current_tools_003", "total_generation_latency_ms": 13654.709, "prompt_token_count": 1019, "tokens_generated": 133}]
- tokens_generated: 9110
- prompt_tokens_total: 80786
- peak_gpu_memory_bytes: 6007781376
- correlation: {"prompt_tokens_vs_latency": 0.023, "generated_tokens_vs_latency": 0.8979}

## Side Effects

- local_model_calls_made: true
- local_model_call_count: 80
- provider_calls_made: false
- openai_api_calls_made: false
- live_tts_calls_made: false
- provider_side_effects_made: false
- model_download_attempted: false
- model_redownloaded: false
- model_weights_committed: false
- runtime_behavior_changed: false
- response_text_changed: false
- raw_private_transcript_copied_to_public_evidence: false

## Failed Cases

- {"case_id": "live_current_tools_003", "runner_status": "fail", "semantic_match": false, "failure_classes": ["conjunction_relation_mismatch", "gold_response_plan_mismatch", "gold_sales_mismatch", "gold_semantic_mismatch", "gold_state_mismatch", "or_and_drift"], "schema_errors": [], "verifier_errors": ["conjunction_relation_mismatch:or->and", "or_and_drift"], "semantic_mismatches": ["response_plan.buyer_words_to_preserve", "response_plan.campaign_facts_needed", "response_plan.must_include", "response_plan.must_not_include", "response_plan.response_tone", "sales_strategy.next_action", "sales_strategy.one_next_step", "sales_strategy.persuasion_strategy", "sales_strategy.should_ask_question", "sales_strategy.should_recommend", "semantic_frame.buyer_emotion_hint", "semantic_frame.buyer_state", "semantic_frame.commercial_intent", "semantic_frame.conjunction_relation", "semantic_frame.current_utterance_fidelity_notes", "semantic_frame.object_mentions", "semantic_frame.object_type", "semantic_frame.semantic_family", "semantic_frame.speech_act", "semantic_frame.sub_intent", "state_update.reason", "state_update.should_update_adoption_state", "state_update.should_update_use_case", "state_update.use_case_values"]}
- {"case_id": "live_what_is_this_008", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.obj must be a list of strings"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}
- {"case_id": "live_model_subscription_010", "runner_status": "fail", "semantic_match": false, "failure_classes": ["gold_response_plan_mismatch", "gold_sales_mismatch", "gold_semantic_mismatch", "gold_state_mismatch", "must_not_include_present"], "schema_errors": [], "verifier_errors": ["must_not_include_present:model", "must_not_include_present:subscription"], "semantic_mismatches": ["response_plan.buyer_words_to_preserve", "response_plan.max_sentence_count", "response_plan.must_include", "response_plan.must_not_include", "response_plan.response_tone", "sales_strategy.next_action", "sales_strategy.one_next_step", "sales_strategy.persuasion_strategy", "semantic_frame.buyer_emotion_hint", "semantic_frame.buyer_state", "semantic_frame.commercial_intent", "semantic_frame.conjunction_relation", "semantic_frame.current_utterance_fidelity_notes", "semantic_frame.object_mentions", "semantic_frame.object_type", "semantic_frame.semantic_family", "semantic_frame.speech_act", "semantic_frame.sub_intent", "state_update.reason"]}
- {"case_id": "live_by_myself_012", "runner_status": "fail", "semantic_match": false, "failure_classes": ["buyer_word_not_preserved", "gold_response_plan_mismatch", "gold_sales_mismatch", "gold_semantic_mismatch", "gold_state_mismatch"], "schema_errors": [], "verifier_errors": ["buyer_word_not_preserved:by myself"], "semantic_mismatches": ["response_plan.must_include", "response_plan.must_not_include", "response_plan.response_tone", "sales_strategy.next_action", "sales_strategy.one_next_step", "sales_strategy.persuasion_strategy", "sales_strategy.should_ask_question", "sales_strategy.should_recommend", "semantic_frame.buyer_emotion_hint", "semantic_frame.buyer_state", "semantic_frame.commercial_intent", "semantic_frame.conjunction_relation", "semantic_frame.current_utterance_fidelity_notes", "semantic_frame.object_type", "semantic_frame.semantic_family", "semantic_frame.speech_act", "semantic_frame.sub_intent", "state_update.blocked_updates", "state_update.reason", "state_update.should_update_use_case", "state_update.use_case_values"]}
- {"case_id": "live_midcycle_upgrade_015", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.obj must be a list of strings"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}
- {"case_id": "live_signup_question_019", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.obj must be a list of strings"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}
- {"case_id": "live_free_plan_question_029", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.obj must be a list of strings"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}
- {"case_id": "live_plus_cost_question_030", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.obj must be a list of strings"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}
- {"case_id": "live_price_objection_017", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.obj must be a list of strings"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}
- {"case_id": "live_occasional_use_028", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.obj must be a list of strings"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}
- {"case_id": "paraphrase_chat_gbt_006", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.update missing required field(s): ['close', 'intensity', 'recommend', 'team', 'use']", "compact.update has unsupported field(s): ['plan']", "compact.update.intensity must be a string", "compact.update.recommend must be a string", "compact.update.close must be a string", "compact.update.use must be a list of strings", "compact.update.team must be boolean"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}
- {"case_id": "paraphrase_cloud_007", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.obj must be a list of strings"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}
- {"case_id": "paraphrase_subscription_011", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.obj must be a list of strings"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}
- {"case_id": "paraphrase_self_use_012", "runner_status": "fail", "semantic_match": false, "failure_classes": ["buyer_word_not_preserved", "gold_response_plan_mismatch", "gold_sales_mismatch", "gold_semantic_mismatch", "gold_state_mismatch"], "schema_errors": [], "verifier_errors": ["buyer_word_not_preserved:me"], "semantic_mismatches": ["response_plan.buyer_words_to_preserve", "response_plan.must_include", "response_plan.must_not_include", "response_plan.response_tone", "sales_strategy.next_action", "sales_strategy.one_next_step", "sales_strategy.persuasion_strategy", "sales_strategy.should_ask_question", "sales_strategy.should_recommend", "semantic_frame.buyer_emotion_hint", "semantic_frame.buyer_state", "semantic_frame.commercial_intent", "semantic_frame.conjunction_relation", "semantic_frame.current_utterance_fidelity_notes", "semantic_frame.object_mentions", "semantic_frame.object_type", "semantic_frame.semantic_family", "semantic_frame.speech_act", "semantic_frame.sub_intent", "state_update.blocked_updates", "state_update.reason", "state_update.should_update_use_case", "state_update.use_case_values"]}
- {"case_id": "paraphrase_no_team_013", "runner_status": "fail", "semantic_match": false, "failure_classes": ["gold_response_plan_mismatch", "gold_sales_mismatch", "gold_semantic_mismatch", "gold_state_mismatch", "must_not_include_present"], "schema_errors": [], "verifier_errors": ["must_not_include_present:team"], "semantic_mismatches": ["response_plan.buyer_words_to_preserve", "response_plan.must_include", "response_plan.must_not_include", "response_plan.response_tone", "sales_strategy.next_action", "sales_strategy.one_next_step", "sales_strategy.persuasion_strategy", "sales_strategy.should_ask_question", "sales_strategy.should_recommend", "semantic_frame.buyer_emotion_hint", "semantic_frame.buyer_state", "semantic_frame.commercial_intent", "semantic_frame.conjunction_relation", "semantic_frame.current_utterance_fidelity_notes", "semantic_frame.object_mentions", "semantic_frame.object_type", "semantic_frame.semantic_family", "semantic_frame.speech_act", "semantic_frame.sub_intent", "state_update.blocked_updates", "state_update.reason", "state_update.should_update_use_case", "state_update.use_case_values"]}
- {"case_id": "paraphrase_individual_014", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.obj must be a list of strings"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}
- {"case_id": "paraphrase_upgrade_016", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.obj must be a list of strings"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}
- {"case_id": "paraphrase_affiliation_022", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.obj must be a list of strings"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}
- {"case_id": "paraphrase_terminal_023", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.obj must be a list of strings"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}
- {"case_id": "paraphrase_heavy_024", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.obj must be a list of strings"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}
- {"case_id": "paraphrase_research_027", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.obj must be a list of strings"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}
- {"case_id": "negative_side_effect_001", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.obj must be a list of strings"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}
- {"case_id": "negative_unsupported_fact_001", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.obj must be a list of strings"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}
- {"case_id": "negative_raw_url_001", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.obj must be a list of strings"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}
- {"case_id": "negative_wrong_product_001", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.obj must be a list of strings"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}
- {"case_id": "negative_no_calendar_001", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.obj must be a list of strings"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}
- {"case_id": "negative_no_crm_001", "runner_status": "fail", "semantic_match": false, "failure_classes": ["gold_response_plan_mismatch", "gold_sales_mismatch", "gold_semantic_mismatch", "gold_state_mismatch", "must_not_include_present"], "schema_errors": [], "verifier_errors": ["must_not_include_present:CRM"], "semantic_mismatches": ["response_plan.buyer_words_to_preserve", "response_plan.must_include", "response_plan.must_not_include", "response_plan.response_tone", "sales_strategy.next_action", "sales_strategy.one_next_step", "sales_strategy.persuasion_strategy", "sales_strategy.should_ask_question", "semantic_frame.buyer_emotion_hint", "semantic_frame.buyer_state", "semantic_frame.commercial_intent", "semantic_frame.current_utterance_fidelity_notes", "semantic_frame.negation_scope", "semantic_frame.object_mentions", "semantic_frame.object_type", "semantic_frame.semantic_family", "semantic_frame.speech_act", "semantic_frame.sub_intent", "state_update.blocked_updates", "state_update.reason"]}
- {"case_id": "negative_disallowed_action_001", "runner_status": "fail", "semantic_match": false, "failure_classes": ["planner_output_missing"], "schema_errors": ["compact.obj must be a list of strings"], "verifier_errors": [], "semantic_mismatches": ["planner_output_missing"]}

## Notes

- ENABLE_LOCAL_LLM_BRAIN_EXPERIMENT/LOCAL_LLM_ENABLED are recorded but not required by this explicit offline eval.
- Model download is always disabled in this runner.
- Evidence stores case IDs and model outputs, not raw private transcripts.
