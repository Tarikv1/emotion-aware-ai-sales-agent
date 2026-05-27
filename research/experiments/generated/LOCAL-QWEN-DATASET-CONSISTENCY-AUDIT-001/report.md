# LOCAL-QWEN-DATASET-CONSISTENCY-AUDIT-001

- status: pass
- source_eval: `research/experiments/generated/LOCAL-QWEN-LORA-CURRICULUM-EVAL-001/result.json`
- local_model_calls_made: false
- provider_calls_made: false
- runtime_behavior_changed: false
- response_text_changed: false

## Held-Out Coverage

- validation unseen act/sub/action/strategy combos: 6
- test unseen act/sub/action/strategy combos: 2
- validation unseen action/sub pairs: 5
- test unseen action/sub pairs: 2

## Similar-Input Consistency

### current_tool_ai

- cases: 21
- action_strategy_consistent: false
- preserve_consistent: false
- facts_consistent: false
- warnings: multiple action/strategy targets in same semantic neighborhood, preserve fields vary inside same semantic neighborhood, facts fields vary inside same semantic neighborhood, say style varies inside same semantic neighborhood

### personal_not_team

- cases: 8
- action_strategy_consistent: false
- preserve_consistent: false
- facts_consistent: true
- warnings: multiple action/strategy targets in same semantic neighborhood, preserve fields vary inside same semantic neighborhood, say style varies inside same semantic neighborhood

### plan_explanation

- cases: 9
- action_strategy_consistent: false
- preserve_consistent: false
- facts_consistent: true
- warnings: multiple action/strategy targets in same semantic neighborhood, preserve fields vary inside same semantic neighborhood, say style varies inside same semantic neighborhood

### price_or_price_objection

- cases: 4
- action_strategy_consistent: false
- preserve_consistent: false
- facts_consistent: false
- warnings: multiple action/strategy targets in same semantic neighborhood, preserve fields vary inside same semantic neighborhood, facts fields vary inside same semantic neighborhood, say style varies inside same semantic neighborhood

### upgrade_midcycle

- cases: 3
- action_strategy_consistent: false
- preserve_consistent: false
- facts_consistent: true
- warnings: multiple action/strategy targets in same semantic neighborhood, preserve fields vary inside same semantic neighborhood, say style varies inside same semantic neighborhood

### terminal_acceptance

- cases: 5
- action_strategy_consistent: false
- preserve_consistent: false
- facts_consistent: false
- warnings: multiple action/strategy targets in same semantic neighborhood, preserve fields vary inside same semantic neighborhood, facts fields vary inside same semantic neighborhood, say style varies inside same semantic neighborhood

### safety_boundary

- cases: 20
- action_strategy_consistent: false
- preserve_consistent: false
- facts_consistent: false
- warnings: multiple action/strategy targets in same semantic neighborhood, preserve fields vary inside same semantic neighborhood, facts fields vary inside same semantic neighborhood, say style varies inside same semantic neighborhood

### use_case_coding_voice_writing_research

- cases: 13
- action_strategy_consistent: false
- preserve_consistent: false
- facts_consistent: false
- warnings: multiple action/strategy targets in same semantic neighborhood, preserve fields vary inside same semantic neighborhood, facts fields vary inside same semantic neighborhood, say style varies inside same semantic neighborhood

## Gold Strictness Review

{
  "classification_counts": {
    "gold_label_too_strict": 7,
    "insufficient_training_examples": 25,
    "split_distribution_issue": 9,
    "target_inconsistency": 25,
    "true_model_failure": 24
  },
  "strictness_signal_counts": {
    "response_plan_mismatch_only": 1,
    "same_action_strategy_different_say": 12,
    "same_core_semantics_verifier_passed": 7,
    "semantic_fields_match_exact_text_differs": 1
  }
}

## Side Effects

{
  "local_model_calls_made": false,
  "provider_calls_made": false,
  "openai_api_calls_made": false,
  "live_tts_calls_made": false,
  "provider_side_effects_made": false,
  "model_download_attempted": false,
  "model_redownloaded": false,
  "model_weights_committed": false,
  "adapter_files_committed": false,
  "runtime_behavior_changed": false,
  "response_text_changed": false,
  "raw_private_transcript_included": false,
  "raw_private_transcript_copied_to_public_evidence": false,
  "case_text_stored_in_evidence": false
}
