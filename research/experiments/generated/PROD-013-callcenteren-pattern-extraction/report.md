# PROD-013 CallCenterEN Pattern Extraction

This checkpoint extracts abstract sales-call patterns from local CallCenterEN files without storing exact scripts.

No exact scripts, company-specific wording, PII placeholders, agent names, customer names, long call summaries, provider calls, LLM calls, or dataset downloads are used.

## Source Boundary

- Dataset: https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english
- Paper: https://arxiv.org/abs/2507.02958
- License observed: `cc-by-nc-4.0`
- Reuse label: `abstract_pattern_extraction_only`
- Raw source folder: `data/external/callcenteren/raw`
- Word-level timing support: `True`
- Speaker role signal inference: `True`
- Speaker role inference is ground truth: `False`
- Source shape note: when speaker labels are absent, timed words are grouped into bounded pseudo-turns and speaker roles are inferred from role-specific sales/customer language for pattern mining only.

## Summary

- Source files scanned: `95946`
- Conversations parsed: `95934`
- Turns parsed: `4313595`
- Max conversations setting: `0`
- All conversations requested: `True`
- Pattern record limit per category: `5000`
- Record lists are samples: `True`
- Raw transcript text stored: `False`
- Leakage findings: `0`

## Pattern Categories

- Opening patterns: `494`
- Customer intent patterns: `13`
- Objection patterns: `5000`
- Emotion/tone transitions: `5000`
- Persuasion strategy patterns: `5000`
- Discovery question patterns: `9`
- Turn stage patterns: `18`
- Close attempt patterns: `5000`
- Safety/compliance boundaries: `4`
- Domain-specific scenario patterns: `8`
- Agent mistake patterns: `8`

## Timing And Speech Naturalness

- timestamps_available: `True`
- average_agent_turn_words: `19.51`
- average_customer_turn_words: `16.77`
- pause_before_agent_response_ms: `3960.39`
- interruption_count: `2`
- overlong_agent_monologue_count: `48070`
- rapid_fire_question_count: `114106`
- silence_after_offer_count: `24717`
- silence_after_price_count: `3481`

## Scenario Template Bank

- `scenario-buying_interest-002` persona `uncertain_buyer` intent `buying_interest` objection `too_expensive` tactic `ask one discovery question before closing` avoid `vague_claim, talks_too_much, premature_close` success `verbal_interested`
- `scenario-appointment_request-003` persona `scheduled_follow_up_buyer` intent `appointment_request` objection `too_expensive` tactic `confirm callback details` avoid `vague_claim, talks_too_much, premature_close` success `callback_agreed`
- `scenario-price_request-004` persona `price_sensitive_buyer` intent `price_request` objection `too_expensive` tactic `clarify price versus value blocker` avoid `vague_claim, talks_too_much, premature_close` success `next_useful_step_agreed`
- `scenario-callback_request-005` persona `uncertain_buyer` intent `callback_request` objection `too_expensive` tactic `ask one discovery question before closing` avoid `vague_claim, talks_too_much, premature_close` success `callback_agreed`
- `scenario-cancellation-006` persona `boundary_setting_customer` intent `cancellation` objection `too_expensive` tactic `respect boundary before any retention path` avoid `pushy, premature_close, ignores_customer_need` success `boundary_respected`
- `scenario-technical_problem-007` persona `support_first_customer` intent `technical_problem` objection `too_expensive` tactic `handoff instead of guessing` avoid `unsupported_claim, does_not_escalate_when_needed` success `handoff_or_issue_path_accepted`
- `scenario-billing_issue-008` persona `support_first_customer` intent `billing_issue` objection `too_expensive` tactic `confirm understanding then route to billing support` avoid `unsupported_claim, does_not_escalate_when_needed` success `handoff_or_issue_path_accepted`

## Leakage Tests

- exact_source_utterance_storage_check: `pass`
- long_transcript_summary_check: `pass`
- commercial_runtime_prompt_check: `pass`

## Runtime Use

Use this pattern bank to generate scenario templates, customer personas, objections, emotional states, safe tactics, and success/failure labels. Do not use it as copied call wording or as a commercial runtime prompt source.
