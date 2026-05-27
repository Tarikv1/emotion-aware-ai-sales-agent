# LOCAL-QWEN-CURRICULUM-FORGETTING-AUDIT-001

- status: pass
- forgotten_tiny_case_count: 8
- sequential_overwrite_without_mixed_replay: true
- tiny_replay_examples_in_later_stages: false
- learning_rate_steps_likely_caused_forgetting: true
- local_model_calls_made: false
- provider_calls_made: false

## Forgetting

{
  "forgotten_tiny_case_count": 8,
  "forgotten_case_ids": [
    "tiny_current_tool_and_001",
    "tiny_current_tool_or_002",
    "tiny_midcycle_upgrade_006",
    "tiny_negated_team_003",
    "tiny_plan_category_005",
    "tiny_safety_boundary_008",
    "tiny_terminal_acceptance_007",
    "tiny_use_case_fidelity_004"
  ],
  "failure_class_counts": {
    "strict_gold_response_plan": 6,
    "strict_gold_semantic": 8,
    "verifier": 1
  },
  "adapter_live_ready": false,
  "quality_gate_passed": false
}

## Replay Diagnostics

{
  "completed_stages": [
    "tiny",
    "20",
    "60"
  ],
  "train_steps_by_stage": {
    "tiny": 30,
    "20": 75,
    "60": 150
  },
  "train_row_counts_by_stage": {
    "tiny": 8,
    "20": 20,
    "60": 60
  },
  "sequential_stage_training_detected": true,
  "sequential_overwrite_without_mixed_replay": true,
  "final_stage": "60",
  "final_stage_used_only_stage3_rows": true,
  "tiny_replay_examples_in_later_stages": false,
  "learning_rate": 0.0002,
  "learning_rate_steps_likely_caused_forgetting": true,
  "recommended_curriculum_shape": "mixed tiny+stage2+stage3 replay with balanced sampling before any retrain",
  "replay_weighting_or_balanced_sampling_recommended": true
}

## Similar Later-Stage Conflicts

{
  "conflict_count": 8,
  "case_classifications": {
    "conflicting_similar_targets": 8
  }
}
