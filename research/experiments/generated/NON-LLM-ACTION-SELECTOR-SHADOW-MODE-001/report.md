# NON-LLM-ACTION-SELECTOR-SHADOW-MODE-001

- Status: pass
- Replay cases: 147
- Selector valid actions: 147
- Agreement with expected: 141
- Runtime action available count: 0
- Agreement with runtime: 0
- Compatible with runtime: 0
- Possible improvement/regression: 0/1
- Unsafe selector count: 0
- Unknown count: 2
- Latency ms p50/p90/p99/max: 1.0265/1.4348/1.9931/2.0758
- Would change runtime: false for every case
- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama calls: false
- Live runtime wiring allowed: false
- Runtime behavior changed: false
- Response text changed: false

## Special Metrics

- Boundary: `{"accuracy": 1.0, "case_count": 23, "correct": 23}`
- Repair: `{"accuracy": 1.0, "case_count": 3, "correct": 3}`
- Terminal close: `{"accuracy": 1.0, "case_count": 3, "correct": 3}`
- No-fit: `{"accuracy": 0.9629629629629629, "case_count": 27, "correct": 26}`

## Proposal Counts

- answer_plan_change: 14
- answer_price: 11
- answer_privacy_boundary: 7
- answer_signup_path: 14
- answer_source_or_affiliation: 1
- ask_usage_intensity: 2
- ask_use_case_gap: 2
- avoid_repetition_rephrase: 1
- clarify_question_scope: 1
- compare_plus_vs_pro: 3
- compare_pro_tiers: 4
- disqualify_no_fit: 26
- handle_competitor_context: 15
- handle_price_objection: 8
- orient_plan_options: 1
- recommend_plus: 8
- recommend_pro: 7
- repair_already_told_you: 1
- repair_asr_uncertainty: 1
- repair_buyer_correction: 1
- respect_boundary: 16
- terminal_close: 3
