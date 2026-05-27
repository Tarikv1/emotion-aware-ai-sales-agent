# LOCAL-QWEN-TINY-OVERFIT-DATASET-001

## Summary

- status: pass
- rows: 8
- target_schema_issue_count: 0
- target_contract_issue_count: 0
- target_verifier_issue_count: 0
- target_label_quality_issue_count: 0
- raw_private_transcript_included: false
- provider_side_effects_made: false
- runtime_behavior_changed: false
- response_text_changed: false

## Cases

- `tiny_current_tool_and_001`: current tool with AND -> act=adoption_state, sub=current_chatgpt_and_other_ai_user, action=ask_use_case_gap, strategy=preserve_buyer_words
- `tiny_current_tool_or_002`: current tool with OR -> act=current_tool_context, sub=current_chatgpt_or_other_ai_unknown, action=ask_use_case_gap, strategy=preserve_buyer_words
- `tiny_negated_team_003`: negated team -> act=team_scope, sub=not_team_personal_use, action=ask_individual_usage_intensity, strategy=preserve_buyer_words
- `tiny_use_case_fidelity_004`: use case fidelity -> act=use_case_scope, sub=coding_voice_use_case, action=ask_usage_intensity, strategy=preserve_buyer_words
- `tiny_plan_category_005`: plan category explanation -> act=orientation_or_explanation, sub=plan_category_explanation, action=answer_plan_category, strategy=explain_without_overclaiming
- `tiny_midcycle_upgrade_006`: midcycle upgrade -> act=plan_change_question, sub=midcycle_upgrade_question, action=answer_plan_change, strategy=explain_without_overclaiming
- `tiny_terminal_acceptance_007`: terminal acceptance -> act=terminal_acceptance, sub=terminal_thanks_acceptance, action=terminal_close, strategy=terminal_close
- `tiny_safety_boundary_008`: safety boundary -> act=safety_boundary, sub=no_crm_request, action=respect_boundary, strategy=respect_boundary

## Notes

- All rows are synthetic sanitized tiny-overfit cases.
- Targets use compact planner contract values only.
- No model, provider, OpenAI, CRM, email, calendar, or TTS calls are made.
