# NON-LLM-ACTION-SELECTOR-DATASET-001

- Status: pass
- Total rows: 451
- Split counts: `{"test": 82, "train": 304, "validation": 65}`
- Label count: 23
- Sanitized only: true
- Raw private data: false
- Audio data used: false
- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama calls: false
- Live runtime wiring allowed: false
- Runtime behavior changed: false
- Response text changed: false

## Label Distribution

### train
- answer_plan_change: 1
- answer_price: 19
- answer_privacy_boundary: 4
- answer_signup_path: 1
- answer_source_or_affiliation: 22
- ask_usage_intensity: 45
- ask_use_case_gap: 75
- clarify_team_vs_individual: 23
- compare_pro_tiers: 4
- disqualify_no_fit: 8
- explain_subscription_vs_model: 11
- handle_competitor_context: 8
- handle_price_objection: 19
- orient_plan_options: 12
- recommend_business_or_enterprise: 22
- recommend_plus: 4
- recommend_pro: 4
- respect_boundary: 9
- terminal_close: 13

### validation
- answer_plan_change: 13
- answer_price: 5
- answer_privacy_boundary: 3
- answer_signup_path: 1
- compare_pro_tiers: 2
- disqualify_no_fit: 14
- handle_competitor_context: 7
- handle_price_objection: 4
- recommend_plus: 5
- recommend_pro: 5
- respect_boundary: 5
- terminal_close: 1

### test
- answer_plan_change: 1
- answer_price: 6
- answer_privacy_boundary: 4
- answer_signup_path: 13
- answer_source_or_affiliation: 1
- ask_usage_intensity: 1
- ask_use_case_gap: 1
- avoid_repetition_rephrase: 1
- clarify_question_scope: 1
- clarify_team_vs_individual: 1
- compare_pro_tiers: 5
- disqualify_no_fit: 13
- handle_competitor_context: 9
- handle_price_objection: 4
- orient_plan_options: 1
- recommend_plus: 3
- recommend_pro: 2
- repair_already_told_you: 1
- repair_asr_uncertainty: 1
- respect_boundary: 11
- terminal_close: 2

## Rare Labels

- avoid_repetition_rephrase: 1
- clarify_question_scope: 1
- repair_already_told_you: 1
- repair_asr_uncertainty: 1

## Held-Out Overlap

- Exact buyer text: `{"train_test": [], "train_validation": [], "validation_test": []}`
- Case IDs: `{"train_test": [], "train_validation": [], "validation_test": []}`
