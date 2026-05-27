# Balanced Qwen Dataset Training Approval Summary

- approved_for_training: true
- blockers: 0
- warnings: 357
- adapter_live_ready: false
- live_wiring_allowed: false
- mixed_replay_training_recommended_next: true

## What Improved From 4H17

- Balanced dataset increased coverage to 445 rows with 435 in-distribution rows and 10 isolated OOD rows.
- Validation/test label combinations and action/sub pairs are covered by train.
- Exact held-out text overlap and near-duplicate held-out overlap remain false.
- Target-card consistency, compact targets, and expanded verifier checks are preserved.

## Blockers

- none

## Warnings

- [warning] expanded_ask_flag_not_set: Expanded target action starts with ask_ but should_ask_question is not true.
- [warning] expanded_ask_flag_not_set: Expanded target action starts with ask_ but should_ask_question is not true.
- [warning] expanded_ask_flag_not_set: Expanded target action starts with ask_ but should_ask_question is not true.
- [warning] expanded_ask_flag_not_set: Expanded target action starts with ask_ but should_ask_question is not true.
- [warning] expanded_ask_flag_not_set: Expanded target action starts with ask_ but should_ask_question is not true.
- [warning] expanded_ask_flag_not_set: Expanded target action starts with ask_ but should_ask_question is not true.
- [warning] expanded_ask_flag_not_set: Expanded target action starts with ask_ but should_ask_question is not true.
- [warning] expanded_ask_flag_not_set: Expanded target action starts with ask_ but should_ask_question is not true.
- [warning] expanded_ask_flag_not_set: Expanded target action starts with ask_ but should_ask_question is not true.
- [warning] expanded_ask_flag_not_set: Expanded target action starts with ask_ but should_ask_question is not true.
- [warning] templated_context_suffix: Buyer text uses a repeated control suffix.
- [warning] expanded_ask_flag_not_set: Expanded target action starts with ask_ but should_ask_question is not true.
- [warning] templated_context_suffix: Buyer text uses a repeated control suffix.
- [warning] expanded_ask_flag_not_set: Expanded target action starts with ask_ but should_ask_question is not true.
- [warning] templated_context_suffix: Buyer text uses a repeated control suffix.
- [warning] expanded_ask_flag_not_set: Expanded target action starts with ask_ but should_ask_question is not true.
- [warning] templated_context_suffix: Buyer text uses a repeated control suffix.
- [warning] expanded_ask_flag_not_set: Expanded target action starts with ask_ but should_ask_question is not true.
- [warning] templated_context_suffix: Buyer text uses a repeated control suffix.
- [warning] expanded_ask_flag_not_set: Expanded target action starts with ask_ but should_ask_question is not true.
- [warning] templated_context_suffix: Buyer text uses a repeated control suffix.
- [warning] expanded_ask_flag_not_set: Expanded target action starts with ask_ but should_ask_question is not true.
- [warning] templated_context_suffix: Buyer text uses a repeated control suffix.
- [warning] expanded_ask_flag_not_set: Expanded target action starts with ask_ but should_ask_question is not true.
- [warning] templated_context_suffix: Buyer text uses a repeated control suffix.

## Remaining Data Risks

- Synthetic and deterministic rows still carry over-template risk; warnings are review items, not live-readiness proof.
- Some planner-style wording remains useful for compact target supervision but should not be treated as final spoken copy.
- Approval only unlocks mixed-replay training; it does not prove adapter quality or live replacement safety.

## Recommended Next Phase

- Run mixed-replay training only if approved_for_training is true.
- Keep live wiring disabled until a separately trained adapter passes schema, verifier, safety, latency, and shadow-mode gates.
