# LOCAL-QWEN-LORA-EVAL-001

- status: completed
- adapter_quality_status: not_ready
- adapter_live_ready: false
- quality_gate_passed: false
- evidence_integrity_passed: true
- exact_blocker: None
- model_loaded: true
- adapter_loaded: true
- adapter_saved: true
- adapter_path: `local_artifacts/adapters/qwen2.5-sales-brain-lora-002`
- adapter_evaluated_path: `local_artifacts/adapters/qwen2.5-sales-brain-lora-002`
- adapter_version_label: `lora-002`
- training_contract_version: `LOCAL-QWEN-COMPACT-PLANNER-CONTRACT-002`
- eval_contract_version: `LOCAL-QWEN-COMPACT-PLANNER-CONTRACT-002`
- adapter_files_committed: false
- validation_rows: 10
- test_rows: 10

## Adapter Metrics

- validation_schema_valid: 0
- validation_verifier_pass: 0
- validation_semantic_match: 0
- validation_strict_gold_semantic_match: 0
- validation_strict_gold_response_plan_match: 10
- validation_compact_contract_valid: 0
- validation_deprecated_label_count: 0
- validation_case_id_label_leak_count: 0
- validation_generic_action_count: 0
- validation_generic_sub_intent_count: 0
- test_schema_valid: 0
- test_verifier_pass: 0
- test_semantic_match: 0
- test_strict_gold_semantic_match: 0
- test_strict_gold_response_plan_match: 10
- test_compact_contract_valid: 0
- test_deprecated_label_count: 0
- test_case_id_label_leak_count: 0
- test_generic_action_count: 0
- test_generic_sub_intent_count: 0
- compact_contract_failure_count: 20
- strict_gold_semantic_failure_count: 20

## Quality Gate Failures

[
  "validation.schema_valid_count 0 != case_count 10",
  "validation.verifier_pass_count 0 != case_count 10",
  "validation.compact_contract_valid_count 0 != case_count 10",
  "validation.strict_gold_semantic_match_count 0 != case_count 10",
  "test.schema_valid_count 0 != case_count 10",
  "test.verifier_pass_count 0 != case_count 10",
  "test.compact_contract_valid_count 0 != case_count 10",
  "test.strict_gold_semantic_match_count 0 != case_count 10"
]

## Prompt Alignment

{
  "dataset_prompt_has_allowed_values": true,
  "eval_prompt_has_allowed_values": true,
  "eval_prompt_uses_training_chat_builder": true,
  "eval_prompt_builder": "scripts.train_local_qwen_planner_lora_001.chat_messages",
  "dataset_contract_version": "LOCAL-QWEN-COMPACT-PLANNER-CONTRACT-002",
  "active_contract_version": "LOCAL-QWEN-COMPACT-PLANNER-CONTRACT-002",
  "training_eval_contract_versions_match": true
}

## Contract Error Examples

[
  {
    "case_id": "live_cloud_claude_007",
    "split": "validation",
    "labels": {
      "act": "coding_voice_use_case",
      "sub": "coding_voice_use_case",
      "action": "answer_without_inventing_facts",
      "strategy": "value_before_plan_selection"
    },
    "compact_schema_errors": [
      "compact output missing required field(s): ['avoid', 'block', 'buyer', 'intent', 'neg', 'obj', 'rel', 'update']",
      "compact.rel must be a string",
      "compact.neg must be a string",
      "compact.buyer must be a string",
      "compact.intent must be a string",
      "compact.obj must be a list of strings",
      "compact.block must be a list of strings",
      "compact.avoid must be a list of strings",
      "compact.update must be an object"
    ],
    "compact_adapter_errors": [],
    "compact_contract_errors": [
      "compact.act value not allowed: 'coding_voice_use_case'"
    ]
  },
  {
    "case_id": "live_midcycle_upgrade_015",
    "split": "validation",
    "labels": {
      "act": "plan_change_question",
      "sub": "plan_category_explanation",
      "action": "answer_plan_change",
      "strategy": "diagnose_before_recommend"
    },
    "compact_schema_errors": [
      "compact.update missing required field(s): ['use']",
      "compact.update has unsupported field(s): ['plan', 'use_case']",
      "compact.update.use must be a list of strings"
    ],
    "compact_adapter_errors": [],
    "compact_contract_errors": [
      "compact.buyer value not allowed: 'individual'"
    ]
  },
  {
    "case_id": "live_plus_cost_question_030",
    "split": "validation",
    "labels": {
      "act": "price_question",
      "sub": "price_objection",
      "action": "answer_price",
      "strategy": "value_before_plan_selection"
    },
    "compact_schema_errors": [
      "compact.update missing required field(s): ['use']",
      "compact.update has unsupported field(s): ['plan', 'use_case']",
      "compact.update.use must be a list of strings"
    ],
    "compact_adapter_errors": [],
    "compact_contract_errors": []
  },
  {
    "case_id": "paraphrase_and_relation_001",
    "split": "validation",
    "labels": {
      "act": "use_case_scope",
      "sub": "coding_voice_use_case",
      "action": "ask_use_case_gap",
      "strategy": "diagnose_before_recommend"
    },
    "compact_schema_errors": [
      "compact.update missing required field(s): ['use']",
      "compact.update has unsupported field(s): ['plan', 'use_case']",
      "compact.update.use must be a list of strings"
    ],
    "compact_adapter_errors": [],
    "compact_contract_errors": []
  },
  {
    "case_id": "paraphrase_what_call_009",
    "split": "validation",
    "labels": {
      "act": "current_tool_context",
      "sub": "current_chatgpt_user",
      "action": "answer_without_inventing_facts",
      "strategy": "answer_without_inventing_facts"
    },
    "compact_schema_errors": [
      "compact.update missing required field(s): ['use']",
      "compact.update has unsupported field(s): ['plan', 'use_case']",
      "compact.update.use must be a list of strings"
    ],
    "compact_adapter_errors": [],
    "compact_contract_errors": [
      "compact.buyer value not allowed: 'individual'"
    ]
  },
  {
    "case_id": "paraphrase_accept_017",
    "split": "validation",
    "labels": {
      "act": "use_case_scope",
      "sub": "sounds_right",
      "action": "answer_without_inventing_facts",
      "strategy": "value_before_plan_selection"
    },
    "compact_schema_errors": [
      "compact output missing required field(s): ['block', 'buyer', 'intent', 'neg', 'obj', 'rel', 'update']",
      "compact.rel must be a string",
      "compact.neg must be a string",
      "compact.buyer must be a string",
      "compact.intent must be a string",
      "compact.obj must be a list of strings",
      "compact.block must be a list of strings",
      "compact.update must be an object"
    ],
    "compact_adapter_errors": [],
    "compact_contract_errors": [
      "compact.sub value not allowed: 'sounds_right'"
    ]
  },
  {
    "case_id": "paraphrase_light_025",
    "split": "validation",
    "labels": {
      "act": "use_case_scope",
      "sub": "light_occasional_use",
      "action": "ask_usage_intensity",
      "strategy": "value_before_plan_selection"
    },
    "compact_schema_errors": [
      "compact.obj must be a list of strings",
      "compact.update missing required field(s): ['use']",
      "compact.update has unsupported field(s): ['plan', 'use_case']",
      "compact.update.use must be a list of strings"
    ],
    "compact_adapter_errors": [],
    "compact_contract_errors": []
  },
  {
    "case_id": "negative_side_effect_001",
    "split": "validation",
    "labels": {
      "act": "side_effect_boundary_request",
      "sub": "side_effect_boundary_request",
      "action": "respect_boundary",
      "strategy": "boundary_without_side_effects"
    },
    "compact_schema_errors": [
      "compact output missing required field(s): ['block', 'buyer', 'intent', 'neg', 'obj', 'rel', 'update']",
      "compact.rel must be a string",
      "compact.neg must be a string",
      "compact.buyer must be a string",
      "compact.intent must be a string",
      "compact.obj must be a list of strings",
      "compact.block must be a list of strings",
      "compact.update must be an object"
    ],
    "compact_adapter_errors": [],
    "compact_contract_errors": [
      "compact.act value not allowed: 'side_effect_boundary_request'"
    ]
  }
]

## Invalid Label Examples

[
  {
    "case_id": "live_cloud_claude_007",
    "split": "validation",
    "field": "act",
    "value": "coding_voice_use_case",
    "allowed_by_active_contract": false
  },
  {
    "case_id": "live_midcycle_upgrade_015",
    "split": "validation",
    "field": "buyer",
    "value": "individual",
    "allowed_by_active_contract": false
  },
  {
    "case_id": "paraphrase_what_call_009",
    "split": "validation",
    "field": "buyer",
    "value": "individual",
    "allowed_by_active_contract": false
  },
  {
    "case_id": "paraphrase_accept_017",
    "split": "validation",
    "field": "sub",
    "value": "sounds_right",
    "allowed_by_active_contract": false
  },
  {
    "case_id": "negative_side_effect_001",
    "split": "validation",
    "field": "act",
    "value": "side_effect_boundary_request",
    "allowed_by_active_contract": false
  },
  {
    "case_id": "live_what_is_this_008",
    "split": "test",
    "field": "sub",
    "value": "use_case_gap",
    "allowed_by_active_contract": false
  },
  {
    "case_id": "live_terminal_acceptance_016",
    "split": "test",
    "field": "buyer",
    "value": "individual",
    "allowed_by_active_contract": false
  },
  {
    "case_id": "paraphrase_or_relation_002",
    "split": "test",
    "field": "act",
    "value": "coding_or_voice_use_case",
    "allowed_by_active_contract": false
  },
  {
    "case_id": "paraphrase_plan_list_010",
    "split": "test",
    "field": "sub",
    "value": "compare_competitor_context",
    "allowed_by_active_contract": false
  },
  {
    "case_id": "negative_privacy_001",
    "split": "test",
    "field": "sub",
    "value": "data_sharing_boundary",
    "allowed_by_active_contract": false
  },
  {
    "case_id": "negative_privacy_001",
    "split": "test",
    "field": "buyer",
    "value": "individual",
    "allowed_by_active_contract": false
  },
  {
    "case_id": "negative_policy_request_001",
    "split": "test",
    "field": "sub",
    "value": "current_tool_context",
    "allowed_by_active_contract": false
  }
]

## Base Versus Adapter Delta

{
  "validation": {
    "schema_valid_delta": -7,
    "verifier_pass_delta": -7,
    "semantic_match_delta": -7
  },
  "test": {
    "schema_valid_delta": -7,
    "verifier_pass_delta": -7,
    "semantic_match_delta": -7
  }
}

## Latency

{
  "model_load_time_ms": 9352.53,
  "total_generation_latency_ms": 302076.373,
  "average_generation_latency_ms": 15103.819,
  "p50_generation_latency_ms": 14645.001,
  "p90_generation_latency_ms": 19578.748,
  "average_first_output_latency_ms": 9054.949,
  "peak_gpu_memory_bytes": 6147833856
}

## Side Effects

- provider_calls_made: false
- openai_api_calls_made: false
- live_tts_calls_made: false
- runtime_behavior_changed: false
- response_text_changed: false
- raw_private_transcript_included: false
