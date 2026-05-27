# LOCAL-QWEN-LORA-CONTRACT-FAILURE-AUDIT-001

- status: pass
- active_contract_version: `LOCAL-QWEN-COMPACT-PLANNER-CONTRACT-002`
- sft_target_contract_issue_count: 0
- provider_calls_made: false
- openai_api_calls_made: false
- live_tts_calls_made: false
- runtime_behavior_changed: false
- response_text_changed: false

## Prompt Alignment

{
  "dataset_prompt_has_allowed_values": true,
  "eval_prompt_has_allowed_values": true,
  "eval_prompt_uses_training_chat_builder": true,
  "active_contract_version": "LOCAL-QWEN-COMPACT-PLANNER-CONTRACT-002"
}

## adapter_v1_snapshot

- adapter_path: `local_artifacts/adapters/qwen2.5-sales-brain-lora-001`
- adapter_quality_status: not_ready
- adapter_live_ready: false
- quality_gate_passed: false
- validation_schema_valid: 10
- validation_verifier_pass: 10
- validation_strict_gold_semantic: 0
- validation_compact_contract_valid: 0
- test_schema_valid: 10
- test_verifier_pass: 9
- test_strict_gold_semantic: 0
- test_compact_contract_valid: 0
- model_output_appears_to_copy_old_labels: true

### Top Invalid Values

- action: `clarify` x15 (in_targets=false, allowed=false)
- act: `generalized_sales_move` x13 (in_targets=false, allowed=false)
- sub: `cloud_claude_007` x1 (in_targets=false, allowed=false)
- sub: `mid_cycle_upgrade` x1 (in_targets=false, allowed=false)
- sub: `cost_question_030` x1 (in_targets=false, allowed=false)
- sub: `use_case_and_team_size_awareness` x1 (in_targets=false, allowed=false)
- sub: `use_case_specific` x1 (in_targets=false, allowed=false)
- sub: `accept_017` x1 (in_targets=false, allowed=false)
- sub: `light_025` x1 (in_targets=false, allowed=false)
- sub: `side_effect_001` x1 (in_targets=false, allowed=false)

### Likely Causes

- training_duration_issue: true
- prompt_eval_mismatch: unknown_legacy_evidence_missing
- dataset_target_issue: false
- adapter_loading_issue: false
- contract_too_strict: false
- model_not_trained_enough: true
- prompt_allowed_value_evidence_missing: true
- eval_prompt_omitted_allowed_values: unknown_legacy_evidence_missing

### Diagnosis

- Adapter outputs use off-contract semantic synonyms rather than the exact cleaned label set.
- Invalid output labels were not present in rebuilt SFT targets.
- Some outputs copy deprecated, generic, or case-ID-like labels.
- Adapter evidence says the adapter loaded; base-model-only evaluation is unlikely.
- Legacy eval snapshot does not record prompt-contract alignment fields.

## adapter_v2_snapshot

- adapter_path: `local_artifacts/adapters/qwen2.5-sales-brain-lora-002`
- adapter_quality_status: not_ready
- adapter_live_ready: false
- quality_gate_passed: false
- validation_schema_valid: 9
- validation_verifier_pass: 9
- validation_strict_gold_semantic: 0
- validation_compact_contract_valid: 0
- test_schema_valid: 10
- test_verifier_pass: 9
- test_strict_gold_semantic: 0
- test_compact_contract_valid: 0
- model_output_appears_to_copy_old_labels: false

### Top Invalid Values

- sub: `plan_scope` x2 (in_targets=false, allowed=false)
- act: `adoption_scope` x2 (in_targets=false, allowed=false)
- action: `ask_usage_gap` x2 (in_targets=false, allowed=false)
- sub: `use_case_boundary` x2 (in_targets=false, allowed=false)
- act: `plan_fit` x2 (in_targets=false, allowed=false)
- sub: `coding_use_case` x1 (in_targets=false, allowed=false)
- act: `upgrade_question` x1 (in_targets=false, allowed=false)
- sub: `mid_cycle_upgrade` x1 (in_targets=false, allowed=false)
- action: `answer_plan_fit_before_upgrade` x1 (in_targets=false, allowed=false)
- act: `plan_cost_question` x1 (in_targets=false, allowed=false)

### Likely Causes

- training_duration_issue: true
- prompt_eval_mismatch: unknown_legacy_evidence_missing
- dataset_target_issue: false
- adapter_loading_issue: false
- contract_too_strict: false
- model_not_trained_enough: true
- prompt_allowed_value_evidence_missing: true
- eval_prompt_omitted_allowed_values: unknown_legacy_evidence_missing

### Diagnosis

- Adapter outputs use off-contract semantic synonyms rather than the exact cleaned label set.
- Invalid output labels were not present in rebuilt SFT targets.
- Outputs do not mainly copy old case-ID labels; they drift to new but unallowed aliases.
- Adapter evidence says the adapter loaded; base-model-only evaluation is unlikely.
- Legacy eval snapshot does not record prompt-contract alignment fields.

## current_eval_result

- adapter_path: `local_artifacts/adapters/qwen2.5-sales-brain-lora-002`
- adapter_quality_status: not_ready
- adapter_live_ready: false
- quality_gate_passed: false
- validation_schema_valid: 0
- validation_verifier_pass: 0
- validation_strict_gold_semantic: 0
- validation_compact_contract_valid: 0
- test_schema_valid: 0
- test_verifier_pass: 0
- test_strict_gold_semantic: 0
- test_compact_contract_valid: 0
- model_output_appears_to_copy_old_labels: false

### Top Invalid Values

- buyer: `individual` x4 (in_targets=false, allowed=false)
- act: `coding_voice_use_case` x1 (in_targets=false, allowed=false)
- sub: `sounds_right` x1 (in_targets=false, allowed=false)
- act: `side_effect_boundary_request` x1 (in_targets=false, allowed=false)
- sub: `use_case_gap` x1 (in_targets=false, allowed=false)
- act: `coding_or_voice_use_case` x1 (in_targets=false, allowed=false)
- sub: `compare_competitor_context` x1 (in_targets=false, allowed=false)
- sub: `data_sharing_boundary` x1 (in_targets=false, allowed=false)
- sub: `current_tool_context` x1 (in_targets=false, allowed=false)

### Likely Causes

- training_duration_issue: true
- prompt_eval_mismatch: false
- dataset_target_issue: false
- adapter_loading_issue: false
- contract_too_strict: false
- model_not_trained_enough: true
- prompt_allowed_value_evidence_missing: false
- eval_prompt_omitted_allowed_values: false

### Diagnosis

- Adapter outputs use off-contract semantic synonyms rather than the exact cleaned label set.
- Invalid output labels were not present in rebuilt SFT targets.
- Outputs do not mainly copy old case-ID labels; they drift to new but unallowed aliases.
- Adapter evidence says the adapter loaded; base-model-only evaluation is unlikely.
- Current eval evidence shows dataset/eval prompts expose the active allowed values.
