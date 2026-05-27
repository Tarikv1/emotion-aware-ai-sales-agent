# LOCAL-QWEN-LORA-CURRICULUM-TRAINING-001

- status: completed
- training_attempted: true
- training_completed: true
- completed_stages: tiny, 20, 60
- exact_blocker: None
- blocker_classification: None
- adapter_path: `local_artifacts/adapters/qwen2.5-sales-brain-lora-curriculum-001`
- adapter_saved: true
- adapter_files_committed: false
- train_runtime_seconds: 1041.37
- peak_gpu_memory_bytes: 10826617344
- provider_calls_made: false
- openai_api_calls_made: false
- live_tts_calls_made: false
- runtime_behavior_changed: false
- response_text_changed: false
- adapter_live_ready: false
- quality_gate_passed: false

## Stage Results

[
  {
    "stage": "tiny",
    "row_count": 8,
    "max_steps": 30,
    "global_step": 30,
    "train_loss": 0.9877387543519338,
    "eval_loss": 0.5309866070747375,
    "runtime_seconds": 108.885,
    "tokenization": {
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
    },
    "adapter_saved_after_stage": true,
    "peak_gpu_memory_bytes_after_stage": 10824809984
  },
  {
    "stage": "20",
    "row_count": 20,
    "max_steps": 75,
    "global_step": 75,
    "train_loss": 0.14688273772985364,
    "eval_loss": 0.0010504324454814196,
    "runtime_seconds": 253.287,
    "tokenization": {
      "row_count": 20,
      "max_prompt_tokens": 696,
      "max_full_tokens": 845,
      "max_target_tokens": 149,
      "min_target_tokens": 118,
      "truncated_example_count": 0,
      "label_token_count": 2573,
      "labels_mask_prompt_tokens": true,
      "labels_train_only_assistant_tokens": true,
      "full_sequence_trained": false,
      "eos_token_appended_count": 20
    },
    "adapter_saved_after_stage": true,
    "peak_gpu_memory_bytes_after_stage": 10826617344
  },
  {
    "stage": "60",
    "row_count": 60,
    "max_steps": 150,
    "global_step": 150,
    "train_loss": 0.12804181731926897,
    "eval_loss": 0.027555696666240692,
    "runtime_seconds": 669.779,
    "tokenization": {
      "row_count": 60,
      "max_prompt_tokens": 696,
      "max_full_tokens": 845,
      "max_target_tokens": 149,
      "min_target_tokens": 110,
      "truncated_example_count": 0,
      "label_token_count": 7434,
      "labels_mask_prompt_tokens": true,
      "labels_train_only_assistant_tokens": true,
      "full_sequence_trained": false,
      "eos_token_appended_count": 60
    },
    "adapter_saved_after_stage": true,
    "peak_gpu_memory_bytes_after_stage": 10826617344
  }
]

## Tokenization

{
  "tiny": {
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
  },
  "20": {
    "row_count": 20,
    "max_prompt_tokens": 696,
    "max_full_tokens": 845,
    "max_target_tokens": 149,
    "min_target_tokens": 118,
    "truncated_example_count": 0,
    "label_token_count": 2573,
    "labels_mask_prompt_tokens": true,
    "labels_train_only_assistant_tokens": true,
    "full_sequence_trained": false,
    "eos_token_appended_count": 20
  },
  "60": {
    "row_count": 60,
    "max_prompt_tokens": 696,
    "max_full_tokens": 845,
    "max_target_tokens": 149,
    "min_target_tokens": 110,
    "truncated_example_count": 0,
    "label_token_count": 7434,
    "labels_mask_prompt_tokens": true,
    "labels_train_only_assistant_tokens": true,
    "full_sequence_trained": false,
    "eos_token_appended_count": 60
  }
}
