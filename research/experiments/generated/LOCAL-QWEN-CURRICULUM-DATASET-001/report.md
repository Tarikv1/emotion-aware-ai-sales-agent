# LOCAL-QWEN-CURRICULUM-DATASET-001

- status: pass
- source_sft_experiment_id: LOCAL-QWEN-SFT-DATASET-001
- source_tiny_experiment_id: LOCAL-QWEN-TINY-OVERFIT-DATASET-001
- compact_value_contract_version: LOCAL-QWEN-COMPACT-PLANNER-CONTRACT-002
- raw_private_transcript_included: false
- provider_calls_made: false
- openai_api_calls_made: false
- live_tts_calls_made: false

## Counts

{
  "stage1_tiny": 8,
  "stage2_20": 20,
  "stage3_60": 60,
  "validation": 10,
  "test": 10
}

## Held-Out Contamination

{
  "validation": {
    "case_id_overlap_count": 0,
    "case_id_overlap": [],
    "exact_buyer_text_overlap_count": 0,
    "exact_buyer_text_overlap": [],
    "held_out_clean": true
  },
  "test": {
    "case_id_overlap_count": 0,
    "case_id_overlap": [],
    "exact_buyer_text_overlap_count": 0,
    "exact_buyer_text_overlap": [],
    "held_out_clean": true
  }
}

## Validation

{
  "invalid_count": 0,
  "invalid_cases": [],
  "target_validation_totals": {
    "tiny": 8,
    "20": 20,
    "60": 60,
    "validation": 10,
    "test": 10
  },
  "target_validation_pass_counts": {
    "tiny": 8,
    "20": 20,
    "60": 60,
    "validation": 10,
    "test": 10
  }
}
