# LOCAL-QWEN-BALANCED-SFT-DATASET-001

- Status: pass
- Total rows: 445
- In-distribution rows: 435
- OOD rows: 10
- Split counts: `{"ood_test": 10, "test": 66, "train": 304, "validation": 65}`
- Compact contract: `LOCAL-QWEN-COMPACT-PLANNER-CONTRACT-002`
- Local model calls made: false
- Provider/OpenAI/TTS calls made: false
- Runtime behavior changed: false
- Response text changed: false

## Semantic Group Counts

- adoption_current_tool_context: 45 (minimum 45)
- individual_not_team_and_team_scope: 45 (minimum 45)
- objections_and_competitor_context: 45 (minimum 45)
- orientation_or_explanation: 45 (minimum 45)
- plan_change_and_signup: 45 (minimum 35)
- plan_fit_and_recommendation: 45 (minimum 45)
- price_and_value: 45 (minimum 45)
- safety_and_boundary: 45 (minimum 45)
- usage_intensity: 30 (minimum 30)
- use_case_scope: 45 (minimum 45)

## Held-Out Coverage

- validation: covered_by_train=True, unseen_core=0, unseen_action_sub=0
- test: covered_by_train=True, unseen_core=0, unseen_action_sub=0

## Target Consistency

- target_cards_valid: true
- validation_test_labels_covered_by_train: true
- exact_text_heldout: true

## Source Types

- deterministic_paraphrase: 267
- live_sanitized: 51
- negative_control: 24
- ood_control: 10
- original_gold: 5
- synthetic_control: 88
