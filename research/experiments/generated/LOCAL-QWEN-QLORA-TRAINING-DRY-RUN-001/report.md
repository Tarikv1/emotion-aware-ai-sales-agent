# LOCAL-QWEN-QLORA-TRAINING-DRY-RUN-001

- status: completed
- dry_run_config_only: false
- dependency_ready: true
- training_attempted: true
- training_completed: true
- exact_blocker: None
- model_loaded: true
- adapter_saved: true
- adapter_path: `local_artifacts/adapters/qwen2.5-sales-brain-lora-002`
- adapter_files_committed: false
- train_rows: 60
- validation_rows: 10
- test_rows: 10
- train_steps_completed: 20
- train_loss: 1.0341696918010712
- eval_loss: 0.4279744029045105
- peak_gpu_memory_bytes: 10476538880
- provider_calls_made: false
- openai_api_calls_made: false
- live_tts_calls_made: false
- runtime_behavior_changed: false
- response_text_changed: false
- raw_private_transcript_included: false

## Tokenization

{
  "train": {
    "row_count": 60,
    "max_prompt_tokens": 419,
    "max_full_tokens": 557,
    "max_target_tokens": 148,
    "min_target_tokens": 109,
    "truncated_example_count": 0,
    "label_token_count": 7374
  },
  "validation": {
    "row_count": 10,
    "max_prompt_tokens": 411,
    "max_full_tokens": 537,
    "max_target_tokens": 130,
    "min_target_tokens": 114,
    "truncated_example_count": 0,
    "label_token_count": 1215
  },
  "max_seq_length": 1536
}

## Dependency Notes

{
  "modules": {
    "torch": true,
    "transformers": true,
    "accelerate": true,
    "bitsandbytes": true,
    "peft": true,
    "datasets": true,
    "trl": true,
    "evaluate": true,
    "sentencepiece": true,
    "protobuf": true
  },
  "versions": {
    "torch": "2.11.0+cu128",
    "transformers": "5.9.0",
    "accelerate": "1.13.0",
    "bitsandbytes": "0.49.2",
    "peft": "0.19.1",
    "datasets": "4.8.5",
    "trl": "1.5.0",
    "evaluate": "0.4.6",
    "sentencepiece": "0.2.1",
    "protobuf": "7.35.0"
  },
  "required": [
    "torch",
    "transformers",
    "accelerate",
    "bitsandbytes",
    "peft",
    "datasets"
  ],
  "optional": [
    "trl",
    "evaluate",
    "sentencepiece",
    "protobuf"
  ],
  "missing_required": [],
  "ready": true,
  "peft_import_ok": true,
  "peft_import_error": null,
  "transformers_trainer_import_ok": true,
  "transformers_trainer_import_error": null,
  "trl_sft_trainer_import_ok": false,
  "trl_sft_trainer_import_error": "RuntimeError: Failed to import trl.trainer.sft_trainer because of the following error (look up to see its traceback):\n'charmap' codec can't decode byte 0x81 in position 932: character maps to <undefined>",
  "training_backend": "transformers_trainer_peft_qlora"
}

## Notes

- Adapter saved under ignored local_artifacts; no runtime wiring changed.
