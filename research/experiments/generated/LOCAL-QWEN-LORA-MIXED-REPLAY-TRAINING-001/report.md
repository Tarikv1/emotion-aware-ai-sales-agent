# LOCAL-QWEN-LORA-MIXED-REPLAY-TRAINING-001

- status: completed
- training_attempted: true
- training_completed: true
- exact_blocker: None
- max_steps_requested: 300
- train_steps_completed: 300
- train_loss: 0.3825461185413102
- eval_loss: 0.20553486049175262
- adapter_path: `local_artifacts/adapters/qwen2.5-sales-brain-lora-mixed-replay-001`
- adapter_saved: true
- adapter_files_committed: false
- peak_gpu_memory_bytes: 10847432704
- provider_calls_made: false
- openai_api_calls_made: false
- live_tts_calls_made: false
- runtime_behavior_changed: false
- response_text_changed: false

## Tokenization

{
  "train": {
    "row_count": 503,
    "max_prompt_tokens": 706,
    "max_full_tokens": 854,
    "max_target_tokens": 149,
    "min_target_tokens": 110,
    "truncated_example_count": 0,
    "label_token_count": 64341,
    "labels_mask_prompt_tokens": true,
    "labels_train_only_assistant_tokens": true,
    "full_sequence_trained": false,
    "eos_token_appended_count": 503
  },
  "validation_sample": {
    "row_count": 24,
    "max_prompt_tokens": 706,
    "max_full_tokens": 848,
    "max_target_tokens": 143,
    "min_target_tokens": 113,
    "truncated_example_count": 0,
    "label_token_count": 3058,
    "labels_mask_prompt_tokens": true,
    "labels_train_only_assistant_tokens": true,
    "full_sequence_trained": false,
    "eos_token_appended_count": 24
  }
}

## Notes

- Mixed-replay adapter saved under ignored local_artifacts; no runtime wiring changed.
