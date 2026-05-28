# LOCAL-QWEN-MIXED-REPLAY-TRAINING-DATASET-001

- status: pass
- mixed_train_row_count: 503
- source_train_row_count: 304
- held_out_contamination_passed: true
- validation_untouched: true
- test_untouched: true
- ood_test_untouched: true
- raw_private_transcript_included: false

## Semantic Groups

{
  "adoption_current_tool_context": 49,
  "individual_not_team_and_team_scope": 50,
  "objections_and_competitor_context": 50,
  "orientation_or_explanation": 50,
  "plan_change_and_signup": 52,
  "plan_fit_and_recommendation": 48,
  "price_and_value": 48,
  "safety_and_boundary": 54,
  "usage_intensity": 54,
  "use_case_scope": 48
}

## Source Types

{
  "deterministic_paraphrase": 279,
  "live_sanitized": 58,
  "negative_control": 34,
  "original_gold": 12,
  "synthetic_control": 120
}

## Replay Weighting

{
  "seed": 42020,
  "group_targets": {
    "adoption_current_tool_context": 45,
    "orientation_or_explanation": 45,
    "individual_not_team_and_team_scope": 50,
    "use_case_scope": 45,
    "usage_intensity": 54,
    "price_and_value": 48,
    "plan_fit_and_recommendation": 48,
    "plan_change_and_signup": 52,
    "safety_and_boundary": 54,
    "objections_and_competitor_context": 50
  },
  "tiny_anchor_rows_available": 8,
  "tiny_core_equivalent_train_rows": 3,
  "tiny_core_missing_from_train": [
    "tiny_current_tool_and_001",
    "tiny_current_tool_or_002",
    "tiny_use_case_fidelity_004",
    "tiny_midcycle_upgrade_006",
    "tiny_safety_boundary_008"
  ],
  "original_anchor_rows_available": 60,
  "original_gold_equivalent_train_rows": 23,
  "original_gold_missing_from_train": [
    "live_current_tools_002",
    "live_current_tools_003",
    "live_asr_chachu_004",
    "live_asr_chacha_005",
    "live_asr_check_gpt_006",
    "live_not_team_011",
    "live_by_myself_012",
    "live_signup_question_019",
    "live_team_controls_question_026",
    "paraphrase_no_team_013",
    "paraphrase_upgrade_016",
    "paraphrase_signup_020",
    "paraphrase_team_admin_029",
    "paraphrase_security_030",
    "negative_not_team_001",
    "negative_internal_policy_001",
    "negative_affiliation_001",
    "negative_campaign_leakage_001",
    "negative_silence_001",
    "negative_no_tts_001",
    "negative_hallucination_pressure_001",
    "negative_price_trap_001",
    "negative_disallowed_action_001"
  ],
  "replay_role_counts": {
    "balanced_expanded": 304,
    "original_gold_equivalent": 23,
    "semantic_balance_oversample": 173,
    "tiny_core_equivalent": 3
  }
}

## Held-Out Contamination

{
  "held_out_case_id_leak_count": 0,
  "held_out_text_overlap_count": 0,
  "held_out_exact_row_hash_overlap_count": 0,
  "held_out_case_ids_in_mixed_train": [],
  "held_out_text_overlap_case_ids": [],
  "held_out_exact_row_hash_overlap_case_ids": [],
  "passed": true
}
