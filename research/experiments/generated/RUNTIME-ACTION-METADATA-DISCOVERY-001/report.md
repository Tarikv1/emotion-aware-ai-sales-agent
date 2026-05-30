# RUNTIME-ACTION-METADATA-DISCOVERY-001

- Status: pass
- Proposed extraction source: runtime_result passed into shadow_runtime_logger, with fallback discovery across runtime_decision, semantic_frame, and commercial_state dictionaries
- Recommended mapping approach: Map extracted runtime metadata to controlled action_selector action_id labels through runtime_to_action_label_map.json, then compare in read-only shadow mode.
- Runtime behavior changed: false
- Response text changed: false
- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama/TTS calls: false
- Raw private data: false

## Sources

- runtime/campaigns/public_openai_chatgpt_plans_dialogue.py: next_commercial_action, buyer_decision_stage, active_decision_frame, current_buyer_question_type, last_recommendation_given, recommendation_confidence, buyer_fit_level, commercial_stage
- runtime/core/contextual_buyer_semantics.py: semantic, action_id, dialogue_focus, response_strategy, response_variation_key, next_best_sales_action, should_recommend, should_close, should_disqualify, evidence
- runtime/core/realtime_turns.py: runtime_decision, response_mode, call_control, selected_strategy, next_action, sales_difficulty, interest_state
- runtime/core/live_voice_session_policy.py: boundary markers, terminal markers, repair markers
