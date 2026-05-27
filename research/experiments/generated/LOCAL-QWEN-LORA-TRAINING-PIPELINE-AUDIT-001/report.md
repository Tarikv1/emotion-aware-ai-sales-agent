# LOCAL-QWEN-LORA-TRAINING-PIPELINE-AUDIT-001

## Summary

- status: pass
- dataset: `research/experiments/generated/LOCAL-QWEN-TINY-OVERFIT-DATASET-001/train.jsonl`
- row_count: 8
- target_compact_json_is_assistant_message: true
- labels_train_only_assistant_tokens: true
- full_sequence_trained: false
- eos_token_appended_count: 8
- pad_eos_ids_sane: true
- adapter_path_evaluated_is_newly_trained_path: true
- base_model_and_adapter_loaded_together: true
- generation_prompt_excludes_target_answer: true
- targets_validate_before_training: true

## Prompt Hashes

{
  "dataset_prompt_sha256_sample": "cd5daaf0705f4136fb26ce177a6b7623b3b1a8104060219cf798f46a823adaf6",
  "train_prompt_sha256_sample": "452ddd2907b871aaab5c4637b22095da5f8dccba1d07ec395a9dfd1aa82d07a3",
  "eval_prompt_sha256_sample": "cd4acd35dc86d5b3ce56b453794820fe3589244507c4394402f2a29d6493b2bc",
  "chat_template_sha256": "cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f"
}

## Tokenization

{
  "tokenizer_class": "Qwen2Tokenizer",
  "chat_template_available": true,
  "chat_template_sha256": "cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f",
  "train_chat_template_used": "tokenizer.apply_chat_template",
  "eval_chat_template_used": "tokenizer.apply_chat_template",
  "generation_prompt_excludes_target_answer": true,
  "target_text_present_in_training_render": true,
  "target_text_present_in_unmasked_labels": true,
  "labels_mask_prompt_tokens": true,
  "labels_train_only_assistant_tokens": true,
  "full_sequence_trained": false,
  "tokenization_lengths": {
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
  "sample_prompt_token_count": 696,
  "sample_full_token_count": 842,
  "sample_unmasked_label_token_count": 146,
  "sample_eos_token_appended": true,
  "eos_token_appended_count": 8,
  "eos_token_id": 151645,
  "pad_token_id": 151643,
  "pad_eos_ids_sane": true,
  "pad_equals_eos": false
}
