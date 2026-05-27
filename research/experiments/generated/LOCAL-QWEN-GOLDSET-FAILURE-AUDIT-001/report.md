# LOCAL-QWEN-GOLDSET-FAILURE-AUDIT-001

## Summary

- Source: `LOCAL-QWEN-GOLDSET-EVAL-001`
- Total failed cases: 28
- Local model calls made in this audit: false
- Provider/API/TTS calls made: false
- Runtime behavior changed: false
- Response text changed: false

## Failure Counts By Class

- `buyer_word_preservation_failure`: 2
- `compact_json_field_type_failure`: 22
- `compact_update_shape_failure`: 1
- `conjunction_relation_mismatch`: 5
- `current_utterance_fidelity_failure`: 28
- `gold_expected_output_maybe_too_strict`: 1
- `internal_policy_or_safety_failure`: 3
- `latency_risk`: 26
- `needs_human_review`: 1
- `negation_scope_mismatch`: 1
- `object_mentions_mismatch`: 5
- `recommendation_state_failure`: 0
- `response_plan_failure`: 6
- `sales_action_failure`: 28
- `schema_shape_failure`: 22
- `semantic_family_mismatch`: 6
- `speech_act_mismatch`: 6
- `state_update_failure`: 6
- `sub_intent_mismatch`: 6
- `team_state_failure`: 22
- `unsupported_claim_failure`: 0
- `verifier_blocked_correctly`: 6

## Cause Counts

- gold-label issue: 1
- model reasoning issue: 28
- prompt/schema issue: 22
- training-data issue: 22
- verifier issue: 1

## Top Repeated Failure Patterns

- 21x `compact.obj must be a list of strings | planner_output_missing`
- 1x `conjunction_relation_mismatch | conjunction_relation_mismatch:or->and | gold_response_plan_mismatch | gold_sales_mismatch | gold_semantic_mismatch | gold_state_mismatch | or_and_drift`
- 1x `gold_response_plan_mismatch | gold_sales_mismatch | gold_semantic_mismatch | gold_state_mismatch | must_not_include_present | must_not_include_present:model | must_not_include_present:subscription`
- 1x `buyer_word_not_preserved | buyer_word_not_preserved:by myself | gold_response_plan_mismatch | gold_sales_mismatch | gold_semantic_mismatch | gold_state_mismatch`
- 1x `compact.update has unsupported field(s): ['plan'] | compact.update missing required field(s): ['close', 'intensity', 'recommend', 'team', 'use'] | compact.update.close must be a string | compact.update.intensity must be a string | compact.u`
- 1x `buyer_word_not_preserved | buyer_word_not_preserved:me | gold_response_plan_mismatch | gold_sales_mismatch | gold_semantic_mismatch | gold_state_mismatch`
- 1x `gold_response_plan_mismatch | gold_sales_mismatch | gold_semantic_mismatch | gold_state_mismatch | must_not_include_present | must_not_include_present:team`
- 1x `gold_response_plan_mismatch | gold_sales_mismatch | gold_semantic_mismatch | gold_state_mismatch | must_not_include_present | must_not_include_present:CRM`

## Examples By Class

### schema_shape_failure
- `live_what_is_this_008` (model reasoning issue, prompt/schema issue, training-data issue): what is this [errors: compact.obj must be a list of strings]
- `live_midcycle_upgrade_015` (model reasoning issue, prompt/schema issue, training-data issue): can I upgrade in the middle of the month [errors: compact.obj must be a list of strings]
- `live_signup_question_019` (model reasoning issue, prompt/schema issue, training-data issue): where do I sign up [errors: compact.obj must be a list of strings]

### compact_json_field_type_failure
- `live_what_is_this_008` (model reasoning issue, prompt/schema issue, training-data issue): what is this [errors: compact.obj must be a list of strings]
- `live_midcycle_upgrade_015` (model reasoning issue, prompt/schema issue, training-data issue): can I upgrade in the middle of the month [errors: compact.obj must be a list of strings]
- `live_signup_question_019` (model reasoning issue, prompt/schema issue, training-data issue): where do I sign up [errors: compact.obj must be a list of strings]

### compact_update_shape_failure
- `paraphrase_chat_gbt_006` (model reasoning issue, prompt/schema issue, training-data issue): chat gbt is what I use [errors: compact.update missing required field(s): ['close', 'intensity', 'recommend', 'team', 'use'], compact.update has unsupported field(s): ['plan'], compact.update.intensity must be a string, compact.update.recommend must be a string]

### semantic_family_mismatch
- `live_current_tools_003` (model reasoning issue): I use ChatGPT or another AI tool [errors: conjunction_relation_mismatch:or->and, or_and_drift]
- `live_model_subscription_010` (model reasoning issue): is this about model or subscription [errors: must_not_include_present:model, must_not_include_present:subscription]
- `live_by_myself_012` (model reasoning issue): I use it by myself [errors: buyer_word_not_preserved:by myself]

### speech_act_mismatch
- `live_current_tools_003` (model reasoning issue): I use ChatGPT or another AI tool [errors: conjunction_relation_mismatch:or->and, or_and_drift]
- `live_model_subscription_010` (model reasoning issue): is this about model or subscription [errors: must_not_include_present:model, must_not_include_present:subscription]
- `live_by_myself_012` (model reasoning issue): I use it by myself [errors: buyer_word_not_preserved:by myself]

### sub_intent_mismatch
- `live_current_tools_003` (model reasoning issue): I use ChatGPT or another AI tool [errors: conjunction_relation_mismatch:or->and, or_and_drift]
- `live_model_subscription_010` (model reasoning issue): is this about model or subscription [errors: must_not_include_present:model, must_not_include_present:subscription]
- `live_by_myself_012` (model reasoning issue): I use it by myself [errors: buyer_word_not_preserved:by myself]

### object_mentions_mismatch
- `live_current_tools_003` (model reasoning issue): I use ChatGPT or another AI tool [errors: conjunction_relation_mismatch:or->and, or_and_drift]
- `live_model_subscription_010` (model reasoning issue): is this about model or subscription [errors: must_not_include_present:model, must_not_include_present:subscription]
- `paraphrase_self_use_012` (model reasoning issue): it is just me [errors: buyer_word_not_preserved:me]

### conjunction_relation_mismatch
- `live_current_tools_003` (model reasoning issue): I use ChatGPT or another AI tool [errors: conjunction_relation_mismatch:or->and, or_and_drift]
- `live_model_subscription_010` (model reasoning issue): is this about model or subscription [errors: must_not_include_present:model, must_not_include_present:subscription]
- `live_by_myself_012` (model reasoning issue): I use it by myself [errors: buyer_word_not_preserved:by myself]

### negation_scope_mismatch
- `negative_no_crm_001` (model reasoning issue): don't put me in CRM [errors: must_not_include_present:CRM]

### current_utterance_fidelity_failure
- `live_current_tools_003` (model reasoning issue): I use ChatGPT or another AI tool [errors: conjunction_relation_mismatch:or->and, or_and_drift]
- `live_what_is_this_008` (model reasoning issue, prompt/schema issue, training-data issue): what is this [errors: compact.obj must be a list of strings]
- `live_model_subscription_010` (model reasoning issue): is this about model or subscription [errors: must_not_include_present:model, must_not_include_present:subscription]

### state_update_failure
- `live_current_tools_003` (model reasoning issue): I use ChatGPT or another AI tool [errors: conjunction_relation_mismatch:or->and, or_and_drift]
- `live_model_subscription_010` (model reasoning issue): is this about model or subscription [errors: must_not_include_present:model, must_not_include_present:subscription]
- `live_by_myself_012` (model reasoning issue): I use it by myself [errors: buyer_word_not_preserved:by myself]

### team_state_failure
- `live_what_is_this_008` (model reasoning issue, prompt/schema issue, training-data issue): what is this [errors: compact.obj must be a list of strings]
- `live_by_myself_012` (model reasoning issue): I use it by myself [errors: buyer_word_not_preserved:by myself]
- `live_midcycle_upgrade_015` (model reasoning issue, prompt/schema issue, training-data issue): can I upgrade in the middle of the month [errors: compact.obj must be a list of strings]

### recommendation_state_failure

- none

### sales_action_failure
- `live_current_tools_003` (model reasoning issue): I use ChatGPT or another AI tool [errors: conjunction_relation_mismatch:or->and, or_and_drift]
- `live_what_is_this_008` (model reasoning issue, prompt/schema issue, training-data issue): what is this [errors: compact.obj must be a list of strings]
- `live_model_subscription_010` (model reasoning issue): is this about model or subscription [errors: must_not_include_present:model, must_not_include_present:subscription]

### response_plan_failure
- `live_current_tools_003` (model reasoning issue): I use ChatGPT or another AI tool [errors: conjunction_relation_mismatch:or->and, or_and_drift]
- `live_model_subscription_010` (model reasoning issue): is this about model or subscription [errors: must_not_include_present:model, must_not_include_present:subscription]
- `live_by_myself_012` (model reasoning issue): I use it by myself [errors: buyer_word_not_preserved:by myself]

### buyer_word_preservation_failure
- `live_by_myself_012` (model reasoning issue): I use it by myself [errors: buyer_word_not_preserved:by myself]
- `paraphrase_self_use_012` (model reasoning issue): it is just me [errors: buyer_word_not_preserved:me]

### internal_policy_or_safety_failure
- `live_model_subscription_010` (model reasoning issue): is this about model or subscription [errors: must_not_include_present:model, must_not_include_present:subscription]
- `paraphrase_no_team_013` (model reasoning issue): no team involved [errors: must_not_include_present:team]
- `negative_no_crm_001` (model reasoning issue): don't put me in CRM [errors: must_not_include_present:CRM]

### unsupported_claim_failure

- none

### latency_risk
- `live_current_tools_003` (model reasoning issue): I use ChatGPT or another AI tool [errors: conjunction_relation_mismatch:or->and, or_and_drift]
- `live_what_is_this_008` (model reasoning issue, prompt/schema issue, training-data issue): what is this [errors: compact.obj must be a list of strings]
- `live_model_subscription_010` (model reasoning issue): is this about model or subscription [errors: must_not_include_present:model, must_not_include_present:subscription]

### verifier_blocked_correctly
- `live_current_tools_003` (model reasoning issue): I use ChatGPT or another AI tool [errors: conjunction_relation_mismatch:or->and, or_and_drift]
- `live_model_subscription_010` (model reasoning issue): is this about model or subscription [errors: must_not_include_present:model, must_not_include_present:subscription]
- `live_by_myself_012` (model reasoning issue): I use it by myself [errors: buyer_word_not_preserved:by myself]

### gold_expected_output_maybe_too_strict
- `live_price_objection_017` (gold-label issue, model reasoning issue, prompt/schema issue, training-data issue, verifier issue): that seems too expensive [errors: compact.obj must be a list of strings]

### needs_human_review
- `live_price_objection_017` (gold-label issue, model reasoning issue, prompt/schema issue, training-data issue, verifier issue): that seems too expensive [errors: compact.obj must be a list of strings]

## Interpretation

Qwen is not ready for live dialogue replacement. The useful output of this phase is offline failure taxonomy and compact supervised data for a later fine-tuning review.
