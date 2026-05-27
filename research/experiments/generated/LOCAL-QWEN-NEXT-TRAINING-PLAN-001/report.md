# LOCAL-QWEN-NEXT-TRAINING-PLAN-001

- status: pass
- selected_option: option_1_data_expansion_needed
- adapter_live_ready: false
- more_training_recommended_now: false
- data_expansion_recommended: true
- curriculum_replay_fix_recommended: true
- label_simplification_recommended: false
- eval_strictness_adjustment_recommended: true

## Recommendation

{
  "primary": "Do not train more from the current 80-row curriculum. Expand to 300-500 balanced rows first, preserve held-out splits, and only then retrain with replay.",
  "minimum_dataset_work": [
    "Create balanced paraphrases per semantic neighborhood.",
    "Add rare safety, terminal, price, current-tool, personal-use, and use-case variants.",
    "Keep validation/test held out by case intent and paraphrase family, not only by case ID.",
    "Run the dataset consistency audit before any new QLoRA run."
  ],
  "required_curriculum_change_after_data_passes": [
    "Final training stage must mix tiny + stage2 + stage3 examples.",
    "Use replay weighting or balanced sampling for tiny and rare groups.",
    "Track tiny-overfit retention as a hard regression gate."
  ],
  "eval_change": [
    "Keep schema, verifier, safety, and side-effect checks strict.",
    "Add narrow semantic-equivalence rules for same action/strategy with acceptable response-plan wording."
  ]
}

## Option Scores

{
  "option_1_data_expansion_needed": 39,
  "option_2_curriculum_replay_fix": 16,
  "option_3_label_simplification": 4,
  "option_4_eval_strictness_adjustment": 21,
  "option_5_constrained_decoding_or_grammar": 1
}
