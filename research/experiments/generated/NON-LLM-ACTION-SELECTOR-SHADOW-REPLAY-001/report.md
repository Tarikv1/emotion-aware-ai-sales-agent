# NON-LLM-ACTION-SELECTOR-SHADOW-REPLAY-001

- Status: pass
- Replay cases: 147
- Target met: true
- Runtime action available count: 0
- Sanitized only: true
- Raw private data/audio used: false
- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama calls: false
- Live runtime wiring allowed: false
- Runtime behavior changed: false
- Response text changed: false

## Category Counts

- already_told_you: 2
- asr_uncertainty: 1
- boundary: 16
- competitor_context: 16
- no_fit: 27
- other: 24
- plan_change: 14
- price: 11
- price_objection: 8
- privacy: 7
- signup: 14
- source_affiliation: 1
- team_vs_individual: 1
- terminal_close: 3
- usage_intensity: 1
- use_case: 1

## Expected Action Counts

- answer_plan_change: 14
- answer_price: 11
- answer_privacy_boundary: 7
- answer_signup_path: 14
- answer_source_or_affiliation: 1
- ask_usage_intensity: 1
- ask_use_case_gap: 1
- avoid_repetition_rephrase: 1
- clarify_question_scope: 1
- clarify_team_vs_individual: 1
- compare_pro_tiers: 7
- disqualify_no_fit: 27
- handle_competitor_context: 16
- handle_price_objection: 8
- orient_plan_options: 1
- recommend_plus: 8
- recommend_pro: 7
- repair_already_told_you: 1
- repair_asr_uncertainty: 1
- respect_boundary: 16
- terminal_close: 3
