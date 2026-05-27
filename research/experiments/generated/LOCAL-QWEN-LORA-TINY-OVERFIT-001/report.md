# LOCAL-QWEN-LORA-TINY-OVERFIT-001

## Training

- status: completed
- training_attempted: true
- training_completed: true
- exact_blocker: None
- blocker_classification: None
- adapter_path: `local_artifacts/adapters/qwen2.5-sales-brain-lora-tiny-overfit-001`
- adapter_saved: true
- adapter_files_committed: false
- train_rows: 8
- train_steps_completed: 100
- train_loss: 0.35515075276780406
- eval_loss: 0.0013545324327424169
- train_runtime_seconds: 177.39
- peak_gpu_memory_bytes: 10805037568
- provider_calls_made: false
- openai_api_calls_made: false
- live_tts_calls_made: false
- runtime_behavior_changed: false
- response_text_changed: false

## Tokenization

{
  "row_count": 8,
  "max_prompt_tokens": 700,
  "max_full_tokens": 844,
  "max_target_tokens": 146,
  "min_target_tokens": 111,
  "truncated_example_count": 0,
  "label_token_count": 1060,
  "labels_mask_prompt_tokens": true,
  "labels_train_only_assistant_tokens": true,
  "full_sequence_trained": false,
  "eos_token_appended_count": 8
}

## Evaluation

{
  "experiment_id": "LOCAL-QWEN-LORA-TINY-OVERFIT-001",
  "dataset_experiment_id": "LOCAL-QWEN-TINY-OVERFIT-DATASET-001",
  "status": "pass",
  "tiny_overfit_passed": true,
  "blocker_classification": null,
  "pass_condition": {
    "schema_valid_all_cases": true,
    "compact_contract_valid_all_cases": true,
    "verifier_pass_all_cases": true,
    "strict_gold_semantic_all_cases": true,
    "deprecated_case_id_generic_labels_zero": true,
    "malformed_compact_object_count_zero": true
  },
  "comparison": {
    "base_qwen": {
      "status": "completed",
      "adapter_loaded": false,
      "case_count": 8,
      "schema_valid_count": 0,
      "verifier_pass_count": 0,
      "compact_contract_valid_count": 0,
      "strict_gold_semantic_match_count": 0,
      "exact_target_match_count": 0,
      "malformed_compact_object_count": 8,
      "deprecated_case_id_generic_label_count": 0,
      "latency_metrics": {
        "model_load_time_ms": 9063.376,
        "total_generation_latency_ms": 46720.024,
        "average_generation_latency_ms": 5840.003,
        "p50_generation_latency_ms": 6180.026,
        "p90_generation_latency_ms": 6867.07,
        "average_first_output_latency_ms": 4978.782
      }
    },
    "lora_002": {
      "status": "completed",
      "adapter_loaded": true,
      "case_count": 8,
      "schema_valid_count": 0,
      "verifier_pass_count": 0,
      "compact_contract_valid_count": 0,
      "strict_gold_semantic_match_count": 0,
      "exact_target_match_count": 0,
      "malformed_compact_object_count": 8,
      "deprecated_case_id_generic_label_count": 0,
      "latency_metrics": {
        "model_load_time_ms": 8525.524,
        "total_generation_latency_ms": 171574.226,
        "average_generation_latency_ms": 21446.778,
        "p50_generation_latency_ms": 19935.606,
        "p90_generation_latency_ms": 28280.314,
        "average_first_output_latency_ms": 15185.753
      }
    },
    "tiny_adapter": {
      "status": "completed",
      "adapter_loaded": true,
      "case_count": 8,
      "schema_valid_count": 8,
      "verifier_pass_count": 8,
      "compact_contract_valid_count": 8,
      "strict_gold_semantic_match_count": 8,
      "exact_target_match_count": 8,
      "malformed_compact_object_count": 0,
      "deprecated_case_id_generic_label_count": 0,
      "latency_metrics": {
        "model_load_time_ms": 8568.852,
        "total_generation_latency_ms": 131160.207,
        "average_generation_latency_ms": 16395.026,
        "p50_generation_latency_ms": 17031.836,
        "p90_generation_latency_ms": 18700.586,
        "average_first_output_latency_ms": 6360.373
      }
    }
  },
  "models": {
    "base_qwen": {
      "model_label": "base_qwen",
      "adapter_path": null,
      "adapter_exists": true,
      "adapter_loaded": false,
      "model_loaded": true,
      "status": "completed",
      "case_count": 8,
      "cases": [
        {
          "case_id": "tiny_current_tool_and_001",
          "category": "current tool with AND",
          "model_label": "base_qwen",
          "status": "fail",
          "schema_valid": false,
          "verifier_pass": false,
          "semantic_match": false,
          "strict_gold_semantic_match": false,
          "gold_response_plan_match": true,
          "compact_contract_valid": false,
          "exact_target_match": false,
          "malformed_compact_object": true,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "compare_competitor_context",
            "sub": "current_chatgpt_and_other_ai_user",
            "obj": "LOCAL-QWEN-COMPACT-PLANNER-CONTRACT-002",
            "rel": "and",
            "neg": "none",
            "say": "I understand you use ChatGPT and other AI tools. How does Qwen compare in terms of features and cost?"
          },
          "compact_schema_errors": [
            "compact output missing required field(s): ['action', 'avoid', 'block', 'buyer', 'conf', 'facts', 'flags', 'intent', 'preserve', 'strategy', 'update']",
            "compact.buyer must be a string",
            "compact.intent must be a string",
            "compact.action must be a string",
            "compact.strategy must be a string",
            "compact.obj must be a list of strings",
            "compact.block must be a list of strings",
            "compact.facts must be a list of strings",
            "compact.preserve must be a list of strings",
            "compact.avoid must be a list of strings",
            "compact.flags must be a list of strings",
            "compact.update must be an object",
            "compact.conf must be a number"
          ],
          "compact_adapter_errors": [],
          "compact_contract_errors": [
            "compact.act value not allowed: 'compare_competitor_context'"
          ],
          "compact_label_quality_issues": [
            {
              "field": "act",
              "value": "compare_competitor_context",
              "issue": "not_allowed"
            }
          ],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [
            "planner_output_missing"
          ],
          "exact_mismatches": [
            "planner_output_missing"
          ],
          "failure_classes": [
            "schema",
            "compact_contract",
            "gold_semantic"
          ],
          "latency_metrics": {
            "prompt_token_count": 696,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 5473.04,
            "total_generation_latency_ms": 7609.969,
            "tokens_generated": 75,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 5955021824
          },
          "raw_output_excerpt": "{\"act\":\"compare_competitor_context\",\"sub\":\"current_chatgpt_and_other_ai_user\",\"obj\":\"LOCAL-QWEN-COMPACT-PLANNER-CONTRACT-002\",\"rel\":\"and\",\"neg\":\"none\",\"say\":\"I understand you use ChatGPT and other AI tools. How does Qwen compare in terms of features and cost?\"}"
        },
        {
          "case_id": "tiny_current_tool_or_002",
          "category": "current tool with OR",
          "model_label": "base_qwen",
          "status": "fail",
          "schema_valid": false,
          "verifier_pass": false,
          "semantic_match": false,
          "strict_gold_semantic_match": false,
          "gold_response_plan_match": true,
          "compact_contract_valid": false,
          "exact_target_match": false,
          "malformed_compact_object": true,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "compare_competitor_context",
            "sub": "current_chatgpt_or_other_ai_unknown",
            "intent": "evaluation",
            "rel": "and",
            "neg": "none",
            "action": "answer_affiliation_boundary",
            "strategy": "boundary_without_side_effects"
          },
          "compact_schema_errors": [
            "compact output missing required field(s): ['avoid', 'block', 'buyer', 'conf', 'facts', 'flags', 'obj', 'preserve', 'say', 'update']",
            "compact.buyer must be a string",
            "compact.say must be a string",
            "compact.obj must be a list of strings",
            "compact.block must be a list of strings",
            "compact.facts must be a list of strings",
            "compact.preserve must be a list of strings",
            "compact.avoid must be a list of strings",
            "compact.flags must be a list of strings",
            "compact.update must be an object",
            "compact.conf must be a number"
          ],
          "compact_adapter_errors": [],
          "compact_contract_errors": [
            "compact.act value not allowed: 'compare_competitor_context'"
          ],
          "compact_label_quality_issues": [
            {
              "field": "act",
              "value": "compare_competitor_context",
              "issue": "not_allowed"
            }
          ],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [
            "planner_output_missing"
          ],
          "exact_mismatches": [
            "planner_output_missing"
          ],
          "failure_classes": [
            "schema",
            "compact_contract",
            "gold_semantic"
          ],
          "latency_metrics": {
            "prompt_token_count": 695,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 4245.522,
            "total_generation_latency_ms": 4246.077,
            "tokens_generated": 46,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 5954867200
          },
          "raw_output_excerpt": "{\"act\":\"compare_competitor_context\",\"sub\":\"current_chatgpt_or_other_ai_unknown\",\"intent\":\"evaluation\",\"rel\":\"and\",\"neg\":\"none\",\"action\":\"answer_affiliation_boundary\",\"strategy\":\"boundary_without_side_effects\"}"
        },
        {
          "case_id": "tiny_negated_team_003",
          "category": "negated team",
          "model_label": "base_qwen",
          "status": "fail",
          "schema_valid": false,
          "verifier_pass": false,
          "semantic_match": false,
          "strict_gold_semantic_match": false,
          "gold_response_plan_match": true,
          "compact_contract_valid": false,
          "exact_target_match": false,
          "malformed_compact_object": true,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "answer_affiliation_boundary",
            "sub": "team_state",
            "obj": "individual_user",
            "rel": "unknown",
            "neg": "none",
            "buyer": "individual_user",
            "intent": "information",
            "update": "unknown",
            "block": "none",
            "action": "answer_affiliation_boundary",
            "strategy": "preserve_buyer_words",
            "facts": "public_plan_names"
          },
          "compact_schema_errors": [
            "compact output missing required field(s): ['avoid', 'conf', 'flags', 'preserve', 'say']",
            "compact.say must be a string",
            "compact.obj must be a list of strings",
            "compact.block must be a list of strings",
            "compact.facts must be a list of strings",
            "compact.preserve must be a list of strings",
            "compact.avoid must be a list of strings",
            "compact.flags must be a list of strings",
            "compact.update must be an object",
            "compact.conf must be a number"
          ],
          "compact_adapter_errors": [],
          "compact_contract_errors": [
            "compact.act value not allowed: 'answer_affiliation_boundary'",
            "compact.sub value not allowed: 'team_state'"
          ],
          "compact_label_quality_issues": [
            {
              "field": "act",
              "value": "answer_affiliation_boundary",
              "issue": "not_allowed"
            },
            {
              "field": "sub",
              "value": "team_state",
              "issue": "not_allowed"
            }
          ],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [
            "planner_output_missing"
          ],
          "exact_mismatches": [
            "planner_output_missing"
          ],
          "failure_classes": [
            "schema",
            "compact_contract",
            "gold_semantic"
          ],
          "latency_metrics": {
            "prompt_token_count": 695,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 6548.042,
            "total_generation_latency_ms": 6548.685,
            "tokens_generated": 63,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 5954867200
          },
          "raw_output_excerpt": "{\"act\":\"answer_affiliation_boundary\",\"sub\":\"team_state\",\"obj\":\"individual_user\",\"rel\":\"unknown\",\"neg\":\"none\",\"buyer\":\"individual_user\",\"intent\":\"information\",\"update\":\"unknown\",\"block\":\"none\",\"action\":\"answer_affiliation_boundary\",\"strategy\":\"preserve_buyer_words\",\"facts\":\"public_plan_names\"}"
        },
        {
          "case_id": "tiny_use_case_fidelity_004",
          "category": "use case fidelity",
          "model_label": "base_qwen",
          "status": "fail",
          "schema_valid": false,
          "verifier_pass": false,
          "semantic_match": false,
          "strict_gold_semantic_match": false,
          "gold_response_plan_match": true,
          "compact_contract_valid": false,
          "exact_target_match": false,
          "malformed_compact_object": true,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "coding_voice_use_case",
            "sub": "coding_voice_use_case",
            "obj": "plan_fit",
            "rel": "and",
            "neg": "none",
            "say": "coding workflow and voice",
            "intent": "evaluation",
            "action": "answer_plan_fit",
            "strategy": "diagnose_before_recommend"
          },
          "compact_schema_errors": [
            "compact output missing required field(s): ['avoid', 'block', 'buyer', 'conf', 'facts', 'flags', 'preserve', 'update']",
            "compact.buyer must be a string",
            "compact.obj must be a list of strings",
            "compact.block must be a list of strings",
            "compact.facts must be a list of strings",
            "compact.preserve must be a list of strings",
            "compact.avoid must be a list of strings",
            "compact.flags must be a list of strings",
            "compact.update must be an object",
            "compact.conf must be a number"
          ],
          "compact_adapter_errors": [],
          "compact_contract_errors": [
            "compact.act value not allowed: 'coding_voice_use_case'"
          ],
          "compact_label_quality_issues": [
            {
              "field": "act",
              "value": "coding_voice_use_case",
              "issue": "not_allowed"
            }
          ],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [
            "planner_output_missing"
          ],
          "exact_mismatches": [
            "planner_output_missing"
          ],
          "failure_classes": [
            "schema",
            "compact_contract",
            "gold_semantic"
          ],
          "latency_metrics": {
            "prompt_token_count": 696,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 3321.408,
            "total_generation_latency_ms": 5379.98,
            "tokens_generated": 53,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 5955021824
          },
          "raw_output_excerpt": "{\"act\":\"coding_voice_use_case\",\"sub\":\"coding_voice_use_case\",\"obj\":\"plan_fit\",\"rel\":\"and\",\"neg\":\"none\",\"say\":\"coding workflow and voice\",\"intent\":\"evaluation\",\"action\":\"answer_plan_fit\",\"strategy\":\"diagnose_before_recommend\"}"
        },
        {
          "case_id": "tiny_plan_category_005",
          "category": "plan category explanation",
          "model_label": "base_qwen",
          "status": "fail",
          "schema_valid": false,
          "verifier_pass": false,
          "semantic_match": false,
          "strict_gold_semantic_match": false,
          "gold_response_plan_match": true,
          "compact_contract_valid": false,
          "exact_target_match": false,
          "malformed_compact_object": true,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "answer_plan_category",
            "sub": "plan_category_explanation",
            "obj": "public_plan_names",
            "rel": "and",
            "neg": "none",
            "say": "Free, Plus, Pro, Business, and Enterprise plans offer different levels of features and support.",
            "flags": "value_before_plan_selection"
          },
          "compact_schema_errors": [
            "compact output missing required field(s): ['action', 'avoid', 'block', 'buyer', 'conf', 'facts', 'intent', 'preserve', 'strategy', 'update']",
            "compact.buyer must be a string",
            "compact.intent must be a string",
            "compact.action must be a string",
            "compact.strategy must be a string",
            "compact.obj must be a list of strings",
            "compact.block must be a list of strings",
            "compact.facts must be a list of strings",
            "compact.preserve must be a list of strings",
            "compact.avoid must be a list of strings",
            "compact.flags must be a list of strings",
            "compact.update must be an object",
            "compact.conf must be a number"
          ],
          "compact_adapter_errors": [],
          "compact_contract_errors": [
            "compact.act value not allowed: 'answer_plan_category'"
          ],
          "compact_label_quality_issues": [
            {
              "field": "act",
              "value": "answer_plan_category",
              "issue": "not_allowed"
            }
          ],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [
            "planner_output_missing"
          ],
          "exact_mismatches": [
            "planner_output_missing"
          ],
          "failure_classes": [
            "schema",
            "compact_contract",
            "gold_semantic"
          ],
          "latency_metrics": {
            "prompt_token_count": 700,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 3567.187,
            "total_generation_latency_ms": 6258.223,
            "tokens_generated": 56,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 5955671040
          },
          "raw_output_excerpt": "{\"act\":\"answer_plan_category\",\"sub\":\"plan_category_explanation\",\"obj\":\"public_plan_names\",\"rel\":\"and\",\"neg\":\"none\",\"say\":\"Free, Plus, Pro, Business, and Enterprise plans offer different levels of features and support.\",\"flags\":\"value_before_plan_selection\"}"
        },
        {
          "case_id": "tiny_midcycle_upgrade_006",
          "category": "midcycle upgrade",
          "model_label": "base_qwen",
          "status": "fail",
          "schema_valid": false,
          "verifier_pass": false,
          "semantic_match": false,
          "strict_gold_semantic_match": false,
          "gold_response_plan_match": true,
          "compact_contract_valid": false,
          "exact_target_match": false,
          "malformed_compact_object": true,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "ask_individual_usage_intensity",
            "sub": "pro_tier_question",
            "obj": "upgrade",
            "rel": "and",
            "neg": "none",
            "buy": "evaluating",
            "int": "unknown",
            "update": "unknown",
            "block": "none",
            "action": "ask_usage_intensity",
            "strategy": "value_before_plan_selection"
          },
          "compact_schema_errors": [
            "compact output missing required field(s): ['avoid', 'buyer', 'conf', 'facts', 'flags', 'intent', 'preserve', 'say']",
            "compact output has unsupported field(s): ['buy', 'int']",
            "compact.buyer must be a string",
            "compact.intent must be a string",
            "compact.say must be a string",
            "compact.obj must be a list of strings",
            "compact.block must be a list of strings",
            "compact.facts must be a list of strings",
            "compact.preserve must be a list of strings",
            "compact.avoid must be a list of strings",
            "compact.flags must be a list of strings",
            "compact.update must be an object",
            "compact.conf must be a number"
          ],
          "compact_adapter_errors": [],
          "compact_contract_errors": [
            "compact.act value not allowed: 'ask_individual_usage_intensity'",
            "compact.sub value not allowed: 'pro_tier_question'"
          ],
          "compact_label_quality_issues": [
            {
              "field": "act",
              "value": "ask_individual_usage_intensity",
              "issue": "not_allowed"
            },
            {
              "field": "sub",
              "value": "pro_tier_question",
              "issue": "not_allowed"
            }
          ],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [
            "planner_output_missing"
          ],
          "exact_mismatches": [
            "planner_output_missing"
          ],
          "failure_classes": [
            "schema",
            "compact_contract",
            "gold_semantic"
          ],
          "latency_metrics": {
            "prompt_token_count": 700,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 6177.663,
            "total_generation_latency_ms": 6178.502,
            "tokens_generated": 57,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 5955671040
          },
          "raw_output_excerpt": "{\"act\":\"ask_individual_usage_intensity\",\"sub\":\"pro_tier_question\",\"obj\":\"upgrade\",\"rel\":\"and\",\"neg\":\"none\",\"buy\":\"evaluating\",\"int\":\"unknown\",\"update\":\"unknown\",\"block\":\"none\",\"action\":\"ask_usage_intensity\",\"strategy\":\"value_before_plan_selection\"}"
        },
        {
          "case_id": "tiny_terminal_acceptance_007",
          "category": "terminal acceptance",
          "model_label": "base_qwen",
          "status": "fail",
          "schema_valid": false,
          "verifier_pass": false,
          "semantic_match": false,
          "strict_gold_semantic_match": false,
          "gold_response_plan_match": true,
          "compact_contract_valid": false,
          "exact_target_match": false,
          "malformed_compact_object": true,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "answer_without_inventing_facts",
            "sub": "unknown",
            "obj": "unknown",
            "rel": "unknown",
            "neg": "unknown",
            "buyer": "evaluating",
            "intent": "information",
            "update": "unknown",
            "block": "unknown",
            "action": "terminal_close",
            "strategy": "value_reframe",
            "facts": "public_plan_names"
          },
          "compact_schema_errors": [
            "compact output missing required field(s): ['avoid', 'conf', 'flags', 'preserve', 'say']",
            "compact.say must be a string",
            "compact.obj must be a list of strings",
            "compact.block must be a list of strings",
            "compact.facts must be a list of strings",
            "compact.preserve must be a list of strings",
            "compact.avoid must be a list of strings",
            "compact.flags must be a list of strings",
            "compact.update must be an object",
            "compact.conf must be a number"
          ],
          "compact_adapter_errors": [],
          "compact_contract_errors": [
            "compact.act value not allowed: 'answer_without_inventing_facts'",
            "compact.sub value not allowed: 'unknown'"
          ],
          "compact_label_quality_issues": [
            {
              "field": "act",
              "value": "answer_without_inventing_facts",
              "issue": "not_allowed"
            },
            {
              "field": "sub",
              "value": "unknown",
              "issue": "not_allowed"
            }
          ],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [
            "planner_output_missing"
          ],
          "exact_mismatches": [
            "planner_output_missing"
          ],
          "failure_classes": [
            "schema",
            "compact_contract",
            "gold_semantic"
          ],
          "latency_metrics": {
            "prompt_token_count": 695,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 6180.907,
            "total_generation_latency_ms": 6181.55,
            "tokens_generated": 60,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 5954867200
          },
          "raw_output_excerpt": "{\"act\":\"answer_without_inventing_facts\",\"sub\":\"unknown\",\"obj\":\"unknown\",\"rel\":\"unknown\",\"neg\":\"unknown\",\"buyer\":\"evaluating\",\"intent\":\"information\",\"update\":\"unknown\",\"block\":\"unknown\",\"action\":\"terminal_close\",\"strategy\":\"value_reframe\",\"facts\":\"public_plan_names\"}"
        },
        {
          "case_id": "tiny_safety_boundary_008",
          "category": "safety boundary",
          "model_label": "base_qwen",
          "status": "fail",
          "schema_valid": false,
          "verifier_pass": false,
          "semantic_match": false,
          "strict_gold_semantic_match": false,
          "gold_response_plan_match": true,
          "compact_contract_valid": false,
          "exact_target_match": false,
          "malformed_compact_object": true,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "respect_boundary",
            "sub": "no_calendar_request",
            "obj": "crm",
            "rel": "unknown",
            "neg": "team_state",
            "strategy": "boundary_without_side_effects",
            "action": "disqualify_no_fit"
          },
          "compact_schema_errors": [
            "compact output missing required field(s): ['avoid', 'block', 'buyer', 'conf', 'facts', 'flags', 'intent', 'preserve', 'say', 'update']",
            "compact.buyer must be a string",
            "compact.intent must be a string",
            "compact.say must be a string",
            "compact.obj must be a list of strings",
            "compact.block must be a list of strings",
            "compact.facts must be a list of strings",
            "compact.preserve must be a list of strings",
            "compact.avoid must be a list of strings",
            "compact.flags must be a list of strings",
            "compact.update must be an object",
            "compact.conf must be a number"
          ],
          "compact_adapter_errors": [],
          "compact_contract_errors": [
            "compact.act value not allowed: 'respect_boundary'"
          ],
          "compact_label_quality_issues": [
            {
              "field": "act",
              "value": "respect_boundary",
              "issue": "not_allowed"
            }
          ],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [
            "planner_output_missing"
          ],
          "exact_mismatches": [
            "planner_output_missing"
          ],
          "failure_classes": [
            "schema",
            "compact_contract",
            "gold_semantic"
          ],
          "latency_metrics": {
            "prompt_token_count": 693,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 4316.487,
            "total_generation_latency_ms": 4317.038,
            "tokens_generated": 40,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 5954556928
          },
          "raw_output_excerpt": "{\"act\":\"respect_boundary\",\"sub\":\"no_calendar_request\",\"obj\":\"crm\",\"rel\":\"unknown\",\"neg\":\"team_state\",\"strategy\":\"boundary_without_side_effects\",\"action\":\"disqualify_no_fit\"}"
        }
      ],
      "metrics": {
        "case_count": 8,
        "schema_valid_count": 0,
        "verifier_pass_count": 0,
        "semantic_match_count": 0,
        "gold_section_semantic_match_count": 0,
        "strict_gold_semantic_match_count": 0,
        "strict_gold_response_plan_match_count": 8,
        "compact_contract_valid_count": 0,
        "deprecated_label_count": 0,
        "case_id_label_leak_count": 0,
        "generic_action_count": 0,
        "generic_sub_intent_count": 0,
        "generic_act_count": 0,
        "exact_match_count": 0,
        "compact_adapter_error_count": 0,
        "failure_class_counts": {
          "schema": 8,
          "compact_contract": 8,
          "gold_semantic": 8
        },
        "exact_target_match_count": 0,
        "malformed_compact_object_count": 8,
        "deprecated_case_id_generic_label_count": 0
      },
      "latency_metrics": {
        "model_load_time_ms": 9063.376,
        "total_generation_latency_ms": 46720.024,
        "average_generation_latency_ms": 5840.003,
        "p50_generation_latency_ms": 6180.026,
        "p90_generation_latency_ms": 6867.07,
        "average_first_output_latency_ms": 4978.782
      },
      "exact_blocker": null,
      "generation_prompt_excludes_target": true
    },
    "lora_002": {
      "model_label": "lora_002",
      "adapter_path": "local_artifacts/adapters/qwen2.5-sales-brain-lora-002",
      "adapter_exists": true,
      "adapter_loaded": true,
      "model_loaded": true,
      "status": "completed",
      "case_count": 8,
      "cases": [
        {
          "case_id": "tiny_current_tool_and_001",
          "category": "current tool with AND",
          "model_label": "lora_002",
          "status": "fail",
          "schema_valid": false,
          "verifier_pass": false,
          "semantic_match": false,
          "strict_gold_semantic_match": false,
          "gold_response_plan_match": true,
          "compact_contract_valid": false,
          "exact_target_match": false,
          "malformed_compact_object": true,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "current_tool_context",
            "sub": "current_chatgpt_and_other_ai_user",
            "obj": [
              "ChatGPT and other AI tools"
            ],
            "rel": "and",
            "neg": "none",
            "buy": "evaluating",
            "int": "medium",
            "recommend": "",
            "action": "diagnose_before_recommend",
            "strategy": "value_before_plan_selection",
            "facts": [
              "public_plan_names"
            ],
            "preserve": [
              "ChatGPT and other AI tools"
            ],
            "avoid": [],
            "say": "Got it. I hear you use ChatGPT and other AI tools. That's a lot of context to cover. Let me ask about your usage before recommending anything.",
            "flags": [],
            "conf": 0.88
          },
          "compact_schema_errors": [
            "compact output missing required field(s): ['block', 'buyer', 'intent', 'update']",
            "compact output has unsupported field(s): ['buy', 'int', 'recommend']",
            "compact.buyer must be a string",
            "compact.intent must be a string",
            "compact.block must be a list of strings",
            "compact.update must be an object"
          ],
          "compact_adapter_errors": [],
          "compact_contract_errors": [
            "compact.action value not allowed: 'diagnose_before_recommend'"
          ],
          "compact_label_quality_issues": [
            {
              "field": "action",
              "value": "diagnose_before_recommend",
              "issue": "not_allowed"
            }
          ],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [
            "planner_output_missing"
          ],
          "exact_mismatches": [
            "planner_output_missing"
          ],
          "failure_classes": [
            "schema",
            "compact_contract",
            "gold_semantic"
          ],
          "latency_metrics": {
            "prompt_token_count": 696,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 4188.676,
            "total_generation_latency_ms": 22501.911,
            "tokens_generated": 127,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 6121065472
          },
          "raw_output_excerpt": "{\"act\":\"current_tool_context\",\"sub\":\"current_chatgpt_and_other_ai_user\",\"obj\":[\"ChatGPT and other AI tools\"],\"rel\":\"and\",\"neg\":\"none\",\"buy\":\"evaluating\",\"int\":\"medium\",\"recommend\":\"\",\"action\":\"diagnose_before_recommend\",\"strategy\":\"value_before_plan_selection\",\"facts\":[\"public_plan_names\"],\"preserve\":[\"ChatGPT and other AI tools\"],\"avoid\":[],\"say\":\"Got it. I hear you use ChatGPT and other AI tools"
        },
        {
          "case_id": "tiny_current_tool_or_002",
          "category": "current tool with OR",
          "model_label": "lora_002",
          "status": "fail",
          "schema_valid": false,
          "verifier_pass": false,
          "semantic_match": false,
          "strict_gold_semantic_match": false,
          "gold_response_plan_match": true,
          "compact_contract_valid": false,
          "exact_target_match": false,
          "malformed_compact_object": true,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "current_tool_context",
            "sub": "current_chatgpt_or_other_ai_unknown",
            "obj": [
              "ChatGPT or maybe Claude"
            ],
            "rel": "and",
            "neg": "none",
            "buy": "individual_user",
            "int": "evaluation",
            "eval": "medium",
            "boundary": false,
            "close": false,
            "action": "answer_without_inventing_facts",
            "strategy": "value_before_plan_selection",
            "facts": [
              "public_plan_names"
            ],
            "preserve": [
              "ChatGPT or maybe Claude"
            ],
            "avoid": [],
            "say": "I hear ChatGPT or maybe Claude. I'll compare the next step for those tools.",
            "flags": [],
            "conf": 0.88
          },
          "compact_schema_errors": [
            "compact output missing required field(s): ['block', 'buyer', 'intent', 'update']",
            "compact output has unsupported field(s): ['boundary', 'buy', 'close', 'eval', 'int']",
            "compact.buyer must be a string",
            "compact.intent must be a string",
            "compact.block must be a list of strings",
            "compact.update must be an object"
          ],
          "compact_adapter_errors": [],
          "compact_contract_errors": [],
          "compact_label_quality_issues": [],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [
            "planner_output_missing"
          ],
          "exact_mismatches": [
            "planner_output_missing"
          ],
          "failure_classes": [
            "schema",
            "compact_contract",
            "gold_semantic"
          ],
          "latency_metrics": {
            "prompt_token_count": 695,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 4876.811,
            "total_generation_latency_ms": 21128.833,
            "tokens_generated": 121,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 6120932352
          },
          "raw_output_excerpt": "{\"act\":\"current_tool_context\",\"sub\":\"current_chatgpt_or_other_ai_unknown\",\"obj\":[\"ChatGPT or maybe Claude\"],\"rel\":\"and\",\"neg\":\"none\",\"buy\":\"individual_user\",\"int\":\"evaluation\",\"eval\":\"medium\",\"boundary\":false,\"close\":false,\"action\":\"answer_without_inventing_facts\",\"strategy\":\"value_before_plan_selection\",\"facts\":[\"public_plan_names\"],\"preserve\":[\"ChatGPT or maybe Claude\"],\"avoid\":[],\"say\":\"I hear "
        },
        {
          "case_id": "tiny_negated_team_003",
          "category": "negated team",
          "model_label": "lora_002",
          "status": "fail",
          "schema_valid": false,
          "verifier_pass": false,
          "semantic_match": false,
          "strict_gold_semantic_match": false,
          "gold_response_plan_match": true,
          "compact_contract_valid": false,
          "exact_target_match": false,
          "malformed_compact_object": true,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "individual_usage_intensity",
            "sub": "individual_user",
            "obj": [
              "public_plan_names"
            ],
            "rel": "none",
            "neg": "team_state",
            "buyers": [
              "evaluating"
            ],
            "intent": "medium",
            "recommend": "",
            "close": false,
            "action": "ask_usage_intensity",
            "strategy": "value_before_plan_selection",
            "facts": [
              "public_plan_names"
            ],
            "preserve": [
              "individual_user"
            ],
            "avoid": [],
            "say": "Got it - individual user. I'll need to ask about usage before recommending anything.",
            "flags": [],
            "conf": 0.88
          },
          "compact_schema_errors": [
            "compact output missing required field(s): ['block', 'buyer', 'update']",
            "compact output has unsupported field(s): ['buyers', 'close', 'recommend']",
            "compact.buyer must be a string",
            "compact.block must be a list of strings",
            "compact.update must be an object"
          ],
          "compact_adapter_errors": [],
          "compact_contract_errors": [
            "compact.act value not allowed: 'individual_usage_intensity'",
            "compact.sub value not allowed: 'individual_user'"
          ],
          "compact_label_quality_issues": [
            {
              "field": "act",
              "value": "individual_usage_intensity",
              "issue": "not_allowed"
            },
            {
              "field": "sub",
              "value": "individual_user",
              "issue": "not_allowed"
            }
          ],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [
            "planner_output_missing"
          ],
          "exact_mismatches": [
            "planner_output_missing"
          ],
          "failure_classes": [
            "schema",
            "compact_contract",
            "gold_semantic"
          ],
          "latency_metrics": {
            "prompt_token_count": 695,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 12358.121,
            "total_generation_latency_ms": 16209.099,
            "tokens_generated": 99,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 6120932352
          },
          "raw_output_excerpt": "{\"act\":\"individual_usage_intensity\",\"sub\":\"individual_user\",\"obj\":[\"public_plan_names\"],\"rel\":\"none\",\"neg\":\"team_state\",\"buyers\":[\"evaluating\"],\"intent\":\"medium\",\"recommend\":\"\",\"close\":false,\"action\":\"ask_usage_intensity\",\"strategy\":\"value_before_plan_selection\",\"facts\":[\"public_plan_names\"],\"preserve\":[\"individual_user\"],\"avoid\":[],\"say\":\"Got it - individual user. I'll need to ask about usage bef"
        },
        {
          "case_id": "tiny_use_case_fidelity_004",
          "category": "use case fidelity",
          "model_label": "lora_002",
          "status": "fail",
          "schema_valid": false,
          "verifier_pass": false,
          "semantic_match": false,
          "strict_gold_semantic_match": false,
          "gold_response_plan_match": true,
          "compact_contract_valid": false,
          "exact_target_match": false,
          "malformed_compact_object": true,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "coding_voice_use_case",
            "sub": "coding_voice_use_case",
            "obj": [
              "coding_workflow",
              "voice"
            ],
            "rel": "and",
            "neg": "none",
            "buy": "individual_user",
            "int": "medium",
            "eval": "evaluation",
            "boundary": false,
            "close": false,
            "action": "recommend_plan",
            "strategy": "value_before_plan_selection",
            "facts": [
              "public_plan_names"
            ],
            "preserve": [
              "coding_workflow",
              "voice"
            ],
            "avoid": [],
            "say": "I hear coding workflow and voice. That's a great use case for Qwen. The next step is choosing the right plan fit."
          },
          "compact_schema_errors": [
            "compact output missing required field(s): ['block', 'buyer', 'conf', 'flags', 'intent', 'update']",
            "compact output has unsupported field(s): ['boundary', 'buy', 'close', 'eval', 'int']",
            "compact.buyer must be a string",
            "compact.intent must be a string",
            "compact.block must be a list of strings",
            "compact.flags must be a list of strings",
            "compact.update must be an object",
            "compact.conf must be a number"
          ],
          "compact_adapter_errors": [],
          "compact_contract_errors": [
            "compact.act value not allowed: 'coding_voice_use_case'"
          ],
          "compact_label_quality_issues": [
            {
              "field": "act",
              "value": "coding_voice_use_case",
              "issue": "not_allowed"
            }
          ],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [
            "planner_output_missing"
          ],
          "exact_mismatches": [
            "planner_output_missing"
          ],
          "failure_classes": [
            "schema",
            "compact_contract",
            "gold_semantic"
          ],
          "latency_metrics": {
            "prompt_token_count": 696,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 14236.507,
            "total_generation_latency_ms": 18742.379,
            "tokens_generated": 109,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 6121065472
          },
          "raw_output_excerpt": "{\"act\":\"coding_voice_use_case\",\"sub\":\"coding_voice_use_case\",\"obj\":[\"coding_workflow\",\"voice\"],\"rel\":\"and\",\"neg\":\"none\",\"buy\":\"individual_user\",\"int\":\"medium\",\"eval\":\"evaluation\",\"boundary\":false,\"close\":false,\"action\":\"recommend_plan\",\"strategy\":\"value_before_plan_selection\",\"facts\":[\"public_plan_names\"],\"preserve\":[\"coding_workflow\",\"voice\"],\"avoid\":[],\"say\":\"I hear coding workflow and voice. Th"
        },
        {
          "case_id": "tiny_plan_category_005",
          "category": "plan category explanation",
          "model_label": "lora_002",
          "status": "fail",
          "schema_valid": false,
          "verifier_pass": false,
          "semantic_match": false,
          "strict_gold_semantic_match": false,
          "gold_response_plan_match": true,
          "compact_contract_valid": false,
          "exact_target_match": false,
          "malformed_compact_object": true,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "answer_plan_category",
            "sub": "plan_category_explanation",
            "obj": [
              "public_plan_names"
            ],
            "rel": "and",
            "neg": "none",
            "buy": "evaluating",
            "int": "medium",
            "update": {
              "adoption": "unknown",
              "use": [],
              "intensity": "unknown",
              "team": false,
              "recommend": "",
              "close": ""
            },
            "block": [],
            "action": "answer_plan_category",
            "strategy": "value_before_plan_selection",
            "facts": [
              "public_plan_names"
            ]
          },
          "compact_schema_errors": [
            "compact output missing required field(s): ['avoid', 'buyer', 'conf', 'flags', 'intent', 'preserve', 'say']",
            "compact output has unsupported field(s): ['buy', 'int']",
            "compact.buyer must be a string",
            "compact.intent must be a string",
            "compact.say must be a string",
            "compact.preserve must be a list of strings",
            "compact.avoid must be a list of strings",
            "compact.flags must be a list of strings",
            "compact.conf must be a number"
          ],
          "compact_adapter_errors": [],
          "compact_contract_errors": [
            "compact.act value not allowed: 'answer_plan_category'"
          ],
          "compact_label_quality_issues": [
            {
              "field": "act",
              "value": "answer_plan_category",
              "issue": "not_allowed"
            }
          ],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [
            "planner_output_missing"
          ],
          "exact_mismatches": [
            "planner_output_missing"
          ],
          "failure_classes": [
            "schema",
            "compact_contract",
            "gold_semantic"
          ],
          "latency_metrics": {
            "prompt_token_count": 700,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 13055.722,
            "total_generation_latency_ms": 13056.34,
            "tokens_generated": 83,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 6121600000
          },
          "raw_output_excerpt": "{\"act\":\"answer_plan_category\",\"sub\":\"plan_category_explanation\",\"obj\":[\"public_plan_names\"],\"rel\":\"and\",\"neg\":\"none\",\"buy\":\"evaluating\",\"int\":\"medium\",\"update\":{\"adoption\":\"unknown\",\"use\":[],\"intensity\":\"unknown\",\"team\":false,\"recommend\":\"\",\"close\":\"\"},\"block\":[],\"action\":\"answer_plan_category\",\"strategy\":\"value_before_plan_selection\",\"facts\":[\"public_plan_names\"]}"
        },
        {
          "case_id": "tiny_midcycle_upgrade_006",
          "category": "midcycle upgrade",
          "model_label": "lora_002",
          "status": "fail",
          "schema_valid": false,
          "verifier_pass": false,
          "semantic_match": false,
          "strict_gold_semantic_match": false,
          "gold_response_plan_match": true,
          "compact_contract_valid": false,
          "exact_target_match": false,
          "malformed_compact_object": true,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": null,
          "compact_schema_errors": [],
          "compact_adapter_errors": [],
          "compact_contract_errors": [
            "compact output missing"
          ],
          "compact_label_quality_issues": [],
          "parse_errors": [
            "model output first JSON object is incomplete or invalid: Unterminated string starting at: line 1 column 1369 (char 1368)"
          ],
          "verifier_errors": [],
          "semantic_mismatches": [
            "planner_output_missing"
          ],
          "exact_mismatches": [
            "planner_output_missing"
          ],
          "failure_classes": [
            "schema",
            "compact_contract",
            "gold_semantic"
          ],
          "latency_metrics": {
            "prompt_token_count": 700,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 39922.994,
            "total_generation_latency_ms": 39923.611,
            "tokens_generated": 256,
            "completed_json_object": false,
            "stopped_after_first_json_object": false,
            "output_truncated": true,
            "timed_out": false,
            "peak_gpu_memory_bytes": 6121600000
          },
          "raw_output_excerpt": "{\"act\":\"plan_change_question\",\"sub\":\"plan_change_question\",\"obj\":[\"pro_tier_choice\"],\"rel\":\"none\",\"neg\":\"none\",\"buyer\":\"evaluating\",\"intent\":\"medium\",\"update\":{\"adoption\":\"\",\"use\":[],\"intensity\":\"\",\"team\":false,\"recommend\":\"\",\"close\":\"\",\"plan\":\"\",\"price\":\"\",\"side_effects\":false,\"boundary\":\"\",\"eval\":\"\",\"eval_boundary\":\"\",\"use_case_gap\":\"\",\"use_case\":\"\",\"recommend_reason\":\"\",\"use_case_boundary\":\"\",\""
        },
        {
          "case_id": "tiny_terminal_acceptance_007",
          "category": "terminal acceptance",
          "model_label": "lora_002",
          "status": "fail",
          "schema_valid": false,
          "verifier_pass": false,
          "semantic_match": false,
          "strict_gold_semantic_match": false,
          "gold_response_plan_match": true,
          "compact_contract_valid": false,
          "exact_target_match": false,
          "malformed_compact_object": true,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "answer_without_inventing_facts",
            "sub": "raw_url_request",
            "obj": [
              "public_plan_names"
            ],
            "rel": "none",
            "neg": "none",
            "buyer": "evaluating",
            "intent": "value_before_plan_selection",
            "update": {
              "adoption_state": "unknown",
              "use_case_scope": "none",
              "team_state": "none",
              "usage_intensity": "none",
              "plan_fit": "none",
              "recommend": "",
              "close": ""
            },
            "block": [],
            "action": "answer_without_inventing_facts",
            "strategy": "value_before_plan_selection",
            "facts": [
              "public_plan_names"
            ],
            "preserve": [
              "public_plan_names"
            ],
            "avoid": [],
            "say": "I'll need to hear more about your use case before recommending anything.",
            "flags": [],
            "conf": 0.88
          },
          "compact_schema_errors": [
            "compact.update missing required field(s): ['adoption', 'intensity', 'team', 'use']",
            "compact.update has unsupported field(s): ['adoption_state', 'plan_fit', 'team_state', 'usage_intensity', 'use_case_scope']",
            "compact.update.adoption must be a string",
            "compact.update.intensity must be a string",
            "compact.update.use must be a list of strings",
            "compact.update.team must be boolean"
          ],
          "compact_adapter_errors": [],
          "compact_contract_errors": [
            "compact.act value not allowed: 'answer_without_inventing_facts'",
            "compact.intent value not allowed: 'value_before_plan_selection'"
          ],
          "compact_label_quality_issues": [
            {
              "field": "act",
              "value": "answer_without_inventing_facts",
              "issue": "not_allowed"
            }
          ],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [
            "planner_output_missing"
          ],
          "exact_mismatches": [
            "planner_output_missing"
          ],
          "failure_classes": [
            "schema",
            "compact_contract",
            "gold_semantic"
          ],
          "latency_metrics": {
            "prompt_token_count": 695,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 19811.232,
            "total_generation_latency_ms": 23290.33,
            "tokens_generated": 136,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 6120932352
          },
          "raw_output_excerpt": "{\"act\":\"answer_without_inventing_facts\",\"sub\":\"raw_url_request\",\"obj\":[\"public_plan_names\"],\"rel\":\"none\",\"neg\":\"none\",\"buyer\":\"evaluating\",\"intent\":\"value_before_plan_selection\",\"update\":{\"adoption_state\":\"unknown\",\"use_case_scope\":\"none\",\"team_state\":\"none\",\"usage_intensity\":\"none\",\"plan_fit\":\"none\",\"recommend\":\"\",\"close\":\"\"},\"block\":[],\"action\":\"answer_without_inventing_facts\",\"strategy\":\"value_"
        },
        {
          "case_id": "tiny_safety_boundary_008",
          "category": "safety boundary",
          "model_label": "lora_002",
          "status": "fail",
          "schema_valid": false,
          "verifier_pass": false,
          "semantic_match": false,
          "strict_gold_semantic_match": false,
          "gold_response_plan_match": true,
          "compact_contract_valid": false,
          "exact_target_match": false,
          "malformed_compact_object": true,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "boundary_without_side_effects",
            "sub": "side_effect_boundary_request",
            "obj": [
              "public_plan_names"
            ],
            "rel": "none",
            "neg": "team_state",
            "buy": "individual_user",
            "int": "medium",
            "eval": "safety_boundary",
            "recommend": "",
            "action": "respect_boundary",
            "strategy": "boundary_without_side_effects",
            "facts": [
              "public_plan_names"
            ],
            "preserve": [
              "public_plan_names"
            ],
            "avoid": [],
            "say": "I hear side effects. I'll respect your boundary and not mention CRM.",
            "flags": [],
            "conf": 0.88
          },
          "compact_schema_errors": [
            "compact output missing required field(s): ['block', 'buyer', 'intent', 'update']",
            "compact output has unsupported field(s): ['buy', 'eval', 'int', 'recommend']",
            "compact.buyer must be a string",
            "compact.intent must be a string",
            "compact.block must be a list of strings",
            "compact.update must be an object"
          ],
          "compact_adapter_errors": [],
          "compact_contract_errors": [
            "compact.act value not allowed: 'boundary_without_side_effects'"
          ],
          "compact_label_quality_issues": [
            {
              "field": "act",
              "value": "boundary_without_side_effects",
              "issue": "not_allowed"
            }
          ],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [
            "planner_output_missing"
          ],
          "exact_mismatches": [
            "planner_output_missing"
          ],
          "failure_classes": [
            "schema",
            "compact_contract",
            "gold_semantic"
          ],
          "latency_metrics": {
            "prompt_token_count": 693,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 13035.962,
            "total_generation_latency_ms": 16721.723,
            "tokens_generated": 101,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 6119563264
          },
          "raw_output_excerpt": "{\"act\":\"boundary_without_side_effects\",\"sub\":\"side_effect_boundary_request\",\"obj\":[\"public_plan_names\"],\"rel\":\"none\",\"neg\":\"team_state\",\"buy\":\"individual_user\",\"int\":\"medium\",\"eval\":\"safety_boundary\",\"recommend\":\"\",\"action\":\"respect_boundary\",\"strategy\":\"boundary_without_side_effects\",\"facts\":[\"public_plan_names\"],\"preserve\":[\"public_plan_names\"],\"avoid\":[],\"say\":\"I hear side effects. I'll respect"
        }
      ],
      "metrics": {
        "case_count": 8,
        "schema_valid_count": 0,
        "verifier_pass_count": 0,
        "semantic_match_count": 0,
        "gold_section_semantic_match_count": 0,
        "strict_gold_semantic_match_count": 0,
        "strict_gold_response_plan_match_count": 8,
        "compact_contract_valid_count": 0,
        "deprecated_label_count": 0,
        "case_id_label_leak_count": 0,
        "generic_action_count": 0,
        "generic_sub_intent_count": 0,
        "generic_act_count": 0,
        "exact_match_count": 0,
        "compact_adapter_error_count": 0,
        "failure_class_counts": {
          "schema": 8,
          "compact_contract": 8,
          "gold_semantic": 8
        },
        "exact_target_match_count": 0,
        "malformed_compact_object_count": 8,
        "deprecated_case_id_generic_label_count": 0
      },
      "latency_metrics": {
        "model_load_time_ms": 8525.524,
        "total_generation_latency_ms": 171574.226,
        "average_generation_latency_ms": 21446.778,
        "p50_generation_latency_ms": 19935.606,
        "p90_generation_latency_ms": 28280.314,
        "average_first_output_latency_ms": 15185.753
      },
      "exact_blocker": null,
      "generation_prompt_excludes_target": true
    },
    "tiny_adapter": {
      "model_label": "tiny_adapter",
      "adapter_path": "local_artifacts/adapters/qwen2.5-sales-brain-lora-tiny-overfit-001",
      "adapter_exists": true,
      "adapter_loaded": true,
      "model_loaded": true,
      "status": "completed",
      "case_count": 8,
      "cases": [
        {
          "case_id": "tiny_current_tool_and_001",
          "category": "current tool with AND",
          "model_label": "tiny_adapter",
          "status": "pass",
          "schema_valid": true,
          "verifier_pass": true,
          "semantic_match": true,
          "strict_gold_semantic_match": true,
          "gold_response_plan_match": true,
          "compact_contract_valid": true,
          "exact_target_match": true,
          "malformed_compact_object": false,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "adoption_state",
            "sub": "current_chatgpt_and_other_ai_user",
            "obj": [
              "ChatGPT",
              "other AI tools"
            ],
            "rel": "and",
            "neg": "none",
            "buyer": "evaluating",
            "intent": "medium",
            "update": {
              "adoption": "current_chatgpt_and_other_ai_user",
              "use": [],
              "intensity": "",
              "team": false,
              "recommend": "",
              "close": ""
            },
            "block": [],
            "action": "ask_use_case_gap",
            "strategy": "preserve_buyer_words",
            "facts": [],
            "preserve": [
              "ChatGPT",
              "other AI tools"
            ],
            "avoid": [],
            "say": "Got it - you already use ChatGPT and other AI tools. The useful next detail is where the gap is.",
            "flags": [],
            "conf": 0.91
          },
          "compact_schema_errors": [],
          "compact_adapter_errors": [],
          "compact_contract_errors": [],
          "compact_label_quality_issues": [],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [],
          "exact_mismatches": [],
          "failure_classes": [],
          "latency_metrics": {
            "prompt_token_count": 696,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 3680.33,
            "total_generation_latency_ms": 18886.631,
            "tokens_generated": 143,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 9356366848
          },
          "raw_output_excerpt": "{\"act\":\"adoption_state\",\"sub\":\"current_chatgpt_and_other_ai_user\",\"obj\":[\"ChatGPT\",\"other AI tools\"],\"rel\":\"and\",\"neg\":\"none\",\"buyer\":\"evaluating\",\"intent\":\"medium\",\"update\":{\"adoption\":\"current_chatgpt_and_other_ai_user\",\"use\":[],\"intensity\":\"\",\"team\":false,\"recommend\":\"\",\"close\":\"\"},\"block\":[],\"action\":\"ask_use_case_gap\",\"strategy\":\"preserve_buyer_words\",\"facts\":[],\"preserve\":[\"ChatGPT\",\"other A"
        },
        {
          "case_id": "tiny_current_tool_or_002",
          "category": "current tool with OR",
          "model_label": "tiny_adapter",
          "status": "pass",
          "schema_valid": true,
          "verifier_pass": true,
          "semantic_match": true,
          "strict_gold_semantic_match": true,
          "gold_response_plan_match": true,
          "compact_contract_valid": true,
          "exact_target_match": true,
          "malformed_compact_object": false,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "current_tool_context",
            "sub": "current_chatgpt_or_other_ai_unknown",
            "obj": [
              "ChatGPT",
              "Claude"
            ],
            "rel": "or",
            "neg": "none",
            "buyer": "evaluating",
            "intent": "medium",
            "update": {
              "adoption": "current_chatgpt_or_other_ai_unknown",
              "use": [],
              "intensity": "",
              "team": false,
              "recommend": "",
              "close": ""
            },
            "block": [],
            "action": "ask_use_case_gap",
            "strategy": "preserve_buyer_words",
            "facts": [],
            "preserve": [
              "ChatGPT",
              "Claude"
            ],
            "avoid": [],
            "say": "Got it - ChatGPT or maybe Claude. The useful next detail is what you use it for.",
            "flags": [],
            "conf": 0.91
          },
          "compact_schema_errors": [],
          "compact_adapter_errors": [],
          "compact_contract_errors": [],
          "compact_label_quality_issues": [],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [],
          "exact_mismatches": [],
          "failure_classes": [],
          "latency_metrics": {
            "prompt_token_count": 695,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 14447.054,
            "total_generation_latency_ms": 18620.852,
            "tokens_generated": 138,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 9356240896
          },
          "raw_output_excerpt": "{\"act\":\"current_tool_context\",\"sub\":\"current_chatgpt_or_other_ai_unknown\",\"obj\":[\"ChatGPT\",\"Claude\"],\"rel\":\"or\",\"neg\":\"none\",\"buyer\":\"evaluating\",\"intent\":\"medium\",\"update\":{\"adoption\":\"current_chatgpt_or_other_ai_unknown\",\"use\":[],\"intensity\":\"\",\"team\":false,\"recommend\":\"\",\"close\":\"\"},\"block\":[],\"action\":\"ask_use_case_gap\",\"strategy\":\"preserve_buyer_words\",\"facts\":[],\"preserve\":[\"ChatGPT\",\"Claude"
        },
        {
          "case_id": "tiny_negated_team_003",
          "category": "negated team",
          "model_label": "tiny_adapter",
          "status": "pass",
          "schema_valid": true,
          "verifier_pass": true,
          "semantic_match": true,
          "strict_gold_semantic_match": true,
          "gold_response_plan_match": true,
          "compact_contract_valid": true,
          "exact_target_match": true,
          "malformed_compact_object": false,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "team_scope",
            "sub": "not_team_personal_use",
            "obj": [
              "by myself",
              "not a team"
            ],
            "rel": "and",
            "neg": "team_state",
            "buyer": "individual_user",
            "intent": "information",
            "update": {
              "adoption": "",
              "use": [],
              "intensity": "",
              "team": false,
              "recommend": "",
              "close": ""
            },
            "block": [
              "team_state"
            ],
            "action": "ask_individual_usage_intensity",
            "strategy": "preserve_buyer_words",
            "facts": [],
            "preserve": [
              "by myself",
              "not a team"
            ],
            "avoid": [
              "team plan",
              "business workspace"
            ],
            "say": "Understood - by myself, not a team. I would keep this on an individual-use path first.",
            "flags": [],
            "conf": 0.91
          },
          "compact_schema_errors": [],
          "compact_adapter_errors": [],
          "compact_contract_errors": [],
          "compact_label_quality_issues": [],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [],
          "exact_mismatches": [],
          "failure_classes": [],
          "latency_metrics": {
            "prompt_token_count": 695,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 2369.188,
            "total_generation_latency_ms": 17153.556,
            "tokens_generated": 132,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 9356240896
          },
          "raw_output_excerpt": "{\"act\":\"team_scope\",\"sub\":\"not_team_personal_use\",\"obj\":[\"by myself\",\"not a team\"],\"rel\":\"and\",\"neg\":\"team_state\",\"buyer\":\"individual_user\",\"intent\":\"information\",\"update\":{\"adoption\":\"\",\"use\":[],\"intensity\":\"\",\"team\":false,\"recommend\":\"\",\"close\":\"\"},\"block\":[\"team_state\"],\"action\":\"ask_individual_usage_intensity\",\"strategy\":\"preserve_buyer_words\",\"facts\":[],\"preserve\":[\"by myself\",\"not a team\"],\""
        },
        {
          "case_id": "tiny_use_case_fidelity_004",
          "category": "use case fidelity",
          "model_label": "tiny_adapter",
          "status": "pass",
          "schema_valid": true,
          "verifier_pass": true,
          "semantic_match": true,
          "strict_gold_semantic_match": true,
          "gold_response_plan_match": true,
          "compact_contract_valid": true,
          "exact_target_match": true,
          "malformed_compact_object": false,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "use_case_scope",
            "sub": "coding_voice_use_case",
            "obj": [
              "coding workflow",
              "voice"
            ],
            "rel": "and",
            "neg": "none",
            "buyer": "evaluating",
            "intent": "evaluation",
            "update": {
              "adoption": "",
              "use": [
                "coding workflow",
                "voice"
              ],
              "intensity": "",
              "team": false,
              "recommend": "",
              "close": ""
            },
            "block": [],
            "action": "ask_usage_intensity",
            "strategy": "preserve_buyer_words",
            "facts": [],
            "preserve": [
              "coding workflow",
              "voice"
            ],
            "avoid": [
              "writing"
            ],
            "say": "Got it - coding workflow and voice. Are you using it lightly, moderately, or heavily?",
            "flags": [],
            "conf": 0.91
          },
          "compact_schema_errors": [],
          "compact_adapter_errors": [],
          "compact_contract_errors": [],
          "compact_label_quality_issues": [],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [],
          "exact_mismatches": [],
          "failure_classes": [],
          "latency_metrics": {
            "prompt_token_count": 696,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 2429.825,
            "total_generation_latency_ms": 14840.555,
            "tokens_generated": 124,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 9356366848
          },
          "raw_output_excerpt": "{\"act\":\"use_case_scope\",\"sub\":\"coding_voice_use_case\",\"obj\":[\"coding workflow\",\"voice\"],\"rel\":\"and\",\"neg\":\"none\",\"buyer\":\"evaluating\",\"intent\":\"evaluation\",\"update\":{\"adoption\":\"\",\"use\":[\"coding workflow\",\"voice\"],\"intensity\":\"\",\"team\":false,\"recommend\":\"\",\"close\":\"\"},\"block\":[],\"action\":\"ask_usage_intensity\",\"strategy\":\"preserve_buyer_words\",\"facts\":[],\"preserve\":[\"coding workflow\",\"voice\"],\"avoi"
        },
        {
          "case_id": "tiny_plan_category_005",
          "category": "plan category explanation",
          "model_label": "tiny_adapter",
          "status": "pass",
          "schema_valid": true,
          "verifier_pass": true,
          "semantic_match": true,
          "strict_gold_semantic_match": true,
          "gold_response_plan_match": true,
          "compact_contract_valid": true,
          "exact_target_match": true,
          "malformed_compact_object": false,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "orientation_or_explanation",
            "sub": "plan_category_explanation",
            "obj": [
              "Free",
              "Plus",
              "Pro",
              "Business",
              "Enterprise"
            ],
            "rel": "and",
            "neg": "none",
            "buyer": "confused",
            "intent": "information",
            "update": {
              "adoption": "",
              "use": [],
              "intensity": "",
              "team": false,
              "recommend": "",
              "close": ""
            },
            "block": [],
            "action": "answer_plan_category",
            "strategy": "explain_without_overclaiming",
            "facts": [
              "public_plan_names"
            ],
            "preserve": [
              "Free",
              "Plus",
              "Pro",
              "Business",
              "Enterprise"
            ],
            "avoid": [],
            "say": "Free, Plus, Pro, Business, and Enterprise are ChatGPT public plan categories. The official source remains authoritative.",
            "flags": [
              "needs_fact_check"
            ],
            "conf": 0.91
          },
          "compact_schema_errors": [],
          "compact_adapter_errors": [],
          "compact_contract_errors": [],
          "compact_label_quality_issues": [],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [],
          "exact_mismatches": [],
          "failure_classes": [],
          "latency_metrics": {
            "prompt_token_count": 700,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 12542.535,
            "total_generation_latency_ms": 16910.115,
            "tokens_generated": 141,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 9356872704
          },
          "raw_output_excerpt": "{\"act\":\"orientation_or_explanation\",\"sub\":\"plan_category_explanation\",\"obj\":[\"Free\",\"Plus\",\"Pro\",\"Business\",\"Enterprise\"],\"rel\":\"and\",\"neg\":\"none\",\"buyer\":\"confused\",\"intent\":\"information\",\"update\":{\"adoption\":\"\",\"use\":[],\"intensity\":\"\",\"team\":false,\"recommend\":\"\",\"close\":\"\"},\"block\":[],\"action\":\"answer_plan_category\",\"strategy\":\"explain_without_overclaiming\",\"facts\":[\"public_plan_names\"],\"preserv"
        },
        {
          "case_id": "tiny_midcycle_upgrade_006",
          "category": "midcycle upgrade",
          "model_label": "tiny_adapter",
          "status": "pass",
          "schema_valid": true,
          "verifier_pass": true,
          "semantic_match": true,
          "strict_gold_semantic_match": true,
          "gold_response_plan_match": true,
          "compact_contract_valid": true,
          "exact_target_match": true,
          "malformed_compact_object": false,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "plan_change_question",
            "sub": "midcycle_upgrade_question",
            "obj": [
              "lower Pro tier",
              "upgrade later"
            ],
            "rel": "and",
            "neg": "none",
            "buyer": "price_sensitive",
            "intent": "evaluation",
            "update": {
              "adoption": "",
              "use": [],
              "intensity": "",
              "team": false,
              "recommend": "",
              "close": ""
            },
            "block": [],
            "action": "answer_plan_change",
            "strategy": "explain_without_overclaiming",
            "facts": [
              "public_plan_names"
            ],
            "preserve": [
              "lower Pro tier",
              "upgrade later"
            ],
            "avoid": [
              "automatically upgrades",
              "guaranteed"
            ],
            "say": "I would treat lower Pro tier and upgrade later as separate decisions, then verify the current rules before promising timing.",
            "flags": [
              "needs_fact_check"
            ],
            "conf": 0.91
          },
          "compact_schema_errors": [],
          "compact_adapter_errors": [],
          "compact_contract_errors": [],
          "compact_label_quality_issues": [],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [],
          "exact_mismatches": [],
          "failure_classes": [],
          "latency_metrics": {
            "prompt_token_count": 700,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 2548.601,
            "total_generation_latency_ms": 17456.684,
            "tokens_generated": 139,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 9356872704
          },
          "raw_output_excerpt": "{\"act\":\"plan_change_question\",\"sub\":\"midcycle_upgrade_question\",\"obj\":[\"lower Pro tier\",\"upgrade later\"],\"rel\":\"and\",\"neg\":\"none\",\"buyer\":\"price_sensitive\",\"intent\":\"evaluation\",\"update\":{\"adoption\":\"\",\"use\":[],\"intensity\":\"\",\"team\":false,\"recommend\":\"\",\"close\":\"\"},\"block\":[],\"action\":\"answer_plan_change\",\"strategy\":\"explain_without_overclaiming\",\"facts\":[\"public_plan_names\"],\"preserve\":[\"lower Pr"
        },
        {
          "case_id": "tiny_terminal_acceptance_007",
          "category": "terminal acceptance",
          "model_label": "tiny_adapter",
          "status": "pass",
          "schema_valid": true,
          "verifier_pass": true,
          "semantic_match": true,
          "strict_gold_semantic_match": true,
          "gold_response_plan_match": true,
          "compact_contract_valid": true,
          "exact_target_match": true,
          "malformed_compact_object": false,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "terminal_acceptance",
            "sub": "terminal_thanks_acceptance",
            "obj": [
              "thanks"
            ],
            "rel": "none",
            "neg": "none",
            "buyer": "evaluating",
            "intent": "none",
            "update": {
              "adoption": "",
              "use": [],
              "intensity": "",
              "team": false,
              "recommend": "",
              "close": "terminal_thanks_acceptance"
            },
            "block": [],
            "action": "terminal_close",
            "strategy": "terminal_close",
            "facts": [],
            "preserve": [
              "thanks"
            ],
            "avoid": [
              "new question"
            ],
            "say": "Thanks - check that, and come back when you are ready.",
            "flags": [],
            "conf": 0.91
          },
          "compact_schema_errors": [],
          "compact_adapter_errors": [],
          "compact_contract_errors": [],
          "compact_label_quality_issues": [],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [],
          "exact_mismatches": [],
          "failure_classes": [],
          "latency_metrics": {
            "prompt_token_count": 695,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 10655.264,
            "total_generation_latency_ms": 13789.069,
            "tokens_generated": 111,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 9356240896
          },
          "raw_output_excerpt": "{\"act\":\"terminal_acceptance\",\"sub\":\"terminal_thanks_acceptance\",\"obj\":[\"thanks\"],\"rel\":\"none\",\"neg\":\"none\",\"buyer\":\"evaluating\",\"intent\":\"none\",\"update\":{\"adoption\":\"\",\"use\":[],\"intensity\":\"\",\"team\":false,\"recommend\":\"\",\"close\":\"terminal_thanks_acceptance\"},\"block\":[],\"action\":\"terminal_close\",\"strategy\":\"terminal_close\",\"facts\":[],\"preserve\":[\"thanks\"],\"avoid\":[\"new question\"],\"say\":\"Thanks - che"
        },
        {
          "case_id": "tiny_safety_boundary_008",
          "category": "safety boundary",
          "model_label": "tiny_adapter",
          "status": "pass",
          "schema_valid": true,
          "verifier_pass": true,
          "semantic_match": true,
          "strict_gold_semantic_match": true,
          "gold_response_plan_match": true,
          "compact_contract_valid": true,
          "exact_target_match": true,
          "malformed_compact_object": false,
          "deprecated_or_case_id_or_generic_label_count": 0,
          "compact_planner_output": {
            "act": "safety_boundary",
            "sub": "no_crm_request",
            "obj": [
              "external action boundary"
            ],
            "rel": "none",
            "neg": "none",
            "buyer": "skeptical",
            "intent": "boundary",
            "update": {
              "adoption": "",
              "use": [],
              "intensity": "",
              "team": false,
              "recommend": "",
              "close": ""
            },
            "block": [
              "crm"
            ],
            "action": "respect_boundary",
            "strategy": "respect_boundary",
            "facts": [],
            "preserve": [],
            "avoid": [
              "CRM",
              "record"
            ],
            "say": "I will respect that boundary and not take any external action.",
            "flags": [],
            "conf": 0.91
          },
          "compact_schema_errors": [],
          "compact_adapter_errors": [],
          "compact_contract_errors": [],
          "compact_label_quality_issues": [],
          "parse_errors": [],
          "verifier_errors": [],
          "semantic_mismatches": [],
          "exact_mismatches": [],
          "failure_classes": [],
          "latency_metrics": {
            "prompt_token_count": 693,
            "prompt_truncated": false,
            "max_output_tokens": 256,
            "timeout_ms": 60000,
            "first_output_latency_ms": 2210.191,
            "total_generation_latency_ms": 13502.745,
            "tokens_generated": 108,
            "completed_json_object": true,
            "stopped_after_first_json_object": true,
            "output_truncated": false,
            "timed_out": false,
            "peak_gpu_memory_bytes": 9355987968
          },
          "raw_output_excerpt": "{\"act\":\"safety_boundary\",\"sub\":\"no_crm_request\",\"obj\":[\"external action boundary\"],\"rel\":\"none\",\"neg\":\"none\",\"buyer\":\"skeptical\",\"intent\":\"boundary\",\"update\":{\"adoption\":\"\",\"use\":[],\"intensity\":\"\",\"team\":false,\"recommend\":\"\",\"close\":\"\"},\"block\":[\"crm\"],\"action\":\"respect_boundary\",\"strategy\":\"respect_boundary\",\"facts\":[],\"preserve\":[],\"avoid\":[\"CRM\",\"record\"],\"say\":\"I will respect that boundary and"
        }
      ],
      "metrics": {
        "case_count": 8,
        "schema_valid_count": 8,
        "verifier_pass_count": 8,
        "semantic_match_count": 8,
        "gold_section_semantic_match_count": 8,
        "strict_gold_semantic_match_count": 8,
        "strict_gold_response_plan_match_count": 8,
        "compact_contract_valid_count": 8,
        "deprecated_label_count": 0,
        "case_id_label_leak_count": 0,
        "generic_action_count": 0,
        "generic_sub_intent_count": 0,
        "generic_act_count": 0,
        "exact_match_count": 8,
        "compact_adapter_error_count": 0,
        "failure_class_counts": {},
        "exact_target_match_count": 8,
        "malformed_compact_object_count": 0,
        "deprecated_case_id_generic_label_count": 0
      },
      "latency_metrics": {
        "model_load_time_ms": 8568.852,
        "total_generation_latency_ms": 131160.207,
        "average_generation_latency_ms": 16395.026,
        "p50_generation_latency_ms": 17031.836,
        "p90_generation_latency_ms": 18700.586,
        "average_first_output_latency_ms": 6360.373
      },
      "exact_blocker": null,
      "generation_prompt_excludes_target": true
    }
  },
  "tiny_exact_target_match_count": 8,
  "tiny_compact_contract_pass_count": 8,
  "tiny_strict_semantic_pass_count": 8,
  "tiny_allowed_label_learning": {
    "allowed_label_counts": {
      "act": 8,
      "sub": 8,
      "rel": 8,
      "neg": 8,
      "buyer": 8,
      "intent": 8,
      "action": 8,
      "strategy": 8
    },
    "target_label_match_counts": {
      "act": 8,
      "sub": 8,
      "rel": 8,
      "neg": 8,
      "buyer": 8,
      "intent": 8,
      "action": 8,
      "strategy": 8
    }
  },
  "tiny_learned_full_compact_shape": true,
  "provider_side_effect_result": {
    "provider_calls_made": false,
    "openai_api_calls_made": false,
    "live_tts_calls_made": false,
    "provider_side_effects_made": false
  }
}

## Notes

- Tiny adapter saved under ignored local_artifacts; no runtime wiring changed.

## Tiny Overfit Evaluation

- status: pass
- tiny_overfit_passed: true
- blocker_classification: None
- exact_target_match_count: 8
- compact_contract_pass_count: 8
- strict_semantic_pass_count: 8

## Base Vs Adapter

{
  "base_qwen": {
    "status": "completed",
    "adapter_loaded": false,
    "case_count": 8,
    "schema_valid_count": 0,
    "verifier_pass_count": 0,
    "compact_contract_valid_count": 0,
    "strict_gold_semantic_match_count": 0,
    "exact_target_match_count": 0,
    "malformed_compact_object_count": 8,
    "deprecated_case_id_generic_label_count": 0,
    "latency_metrics": {
      "model_load_time_ms": 9063.376,
      "total_generation_latency_ms": 46720.024,
      "average_generation_latency_ms": 5840.003,
      "p50_generation_latency_ms": 6180.026,
      "p90_generation_latency_ms": 6867.07,
      "average_first_output_latency_ms": 4978.782
    }
  },
  "lora_002": {
    "status": "completed",
    "adapter_loaded": true,
    "case_count": 8,
    "schema_valid_count": 0,
    "verifier_pass_count": 0,
    "compact_contract_valid_count": 0,
    "strict_gold_semantic_match_count": 0,
    "exact_target_match_count": 0,
    "malformed_compact_object_count": 8,
    "deprecated_case_id_generic_label_count": 0,
    "latency_metrics": {
      "model_load_time_ms": 8525.524,
      "total_generation_latency_ms": 171574.226,
      "average_generation_latency_ms": 21446.778,
      "p50_generation_latency_ms": 19935.606,
      "p90_generation_latency_ms": 28280.314,
      "average_first_output_latency_ms": 15185.753
    }
  },
  "tiny_adapter": {
    "status": "completed",
    "adapter_loaded": true,
    "case_count": 8,
    "schema_valid_count": 8,
    "verifier_pass_count": 8,
    "compact_contract_valid_count": 8,
    "strict_gold_semantic_match_count": 8,
    "exact_target_match_count": 8,
    "malformed_compact_object_count": 0,
    "deprecated_case_id_generic_label_count": 0,
    "latency_metrics": {
      "model_load_time_ms": 8568.852,
      "total_generation_latency_ms": 131160.207,
      "average_generation_latency_ms": 16395.026,
      "p50_generation_latency_ms": 17031.836,
      "p90_generation_latency_ms": 18700.586,
      "average_first_output_latency_ms": 6360.373
    }
  }
}
