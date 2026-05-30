# PHASE-4L0-UNIVERSAL-SALES-ARCHITECTURE-RESET-001

- Status: needs_manual_review
- Architecture direction: universal sales adapter / selector / policy first
- Primary benchmark campaign: public OpenAI ChatGPT plans
- RouteSignal role: secondary regression fixture only
- Live selector control enabled: false
- Response replacement enabled: false
- Provider/model/TTS/CRM/email/calendar/payment/account side-effect path enabled: false
- Raw private transcript/audio added to public evidence: false

## Current Universal Modules Inspected

- `runtime/core/universal_conversation_policy_runtime.py`
- `runtime/core/contextual_buyer_semantics.py`
- `runtime/core/live_voice_session_policy.py`
- `runtime/core/dialogue_manager.py`
- `runtime/core/dialogue_pragmatics.py`
- `runtime/core/dialogue_reasoner.py`
- `runtime/entrypoints/generic_campaign_turn.py`
- `runtime/entrypoints/generate_guarded_response.py`
- `runtime/action_selector`
- `runtime/contracts`

## Campaign-Specific Modules Inspected

- `runtime/core/campaign_playbook_adapter.py`
- `runtime/core/sales_diagnostic_playbook.py`
- `runtime/campaigns/examples`
- `runtime/campaigns/public_openai_chatgpt_plans_dialogue.py`

## RouteSignal Leak Inventory

| Classification | Count | Scope |
| --- | ---: | --- |
| allowed_campaign_specific | 138 | RouteSignal adapter/playbook/examples and OpenAI contamination guard |
| allowed_fixture_or_evidence | 20238 | historical docs, generated evidence, and case fixtures |
| allowed_test_or_validator | 1640 | live-demo, universal, and OpenAI-primary validators |
| universal_adapter_leak | 57 | fixed in `runtime/core/universal_conversation_policy_runtime.py` |
| suspicious_needs_manual_review | 310 | legacy shared live/contextual/dialogue surfaces |

## Occurrence Classification

- `runtime/core/campaign_playbook_adapter.py`: allowed_campaign_specific. RouteSignal response facts now live in adapter `response_capabilities`.
- `runtime/core/sales_diagnostic_playbook.py`: allowed_campaign_specific. This remains the legacy RouteSignal diagnostic playbook fixture.
- `runtime/campaigns/examples`: allowed_campaign_specific. These are campaign profile examples and invalid/valid fixture records.
- `runtime/campaigns/public_openai_chatgpt_plans_dialogue.py`: allowed_campaign_specific. Mentions RouteSignal only as contamination/legacy-context guard material for the OpenAI campaign.
- `research/experiments/generated`, `research/experiments/cases`, `docs/product`, `docs/thesis`: allowed_fixture_or_evidence. Historical evidence was not rewritten.
- `scripts/validate_live_demo_*`, `scripts/validate_universal_*`, `scripts/validate_public_openai_*`: allowed_test_or_validator. RouteSignal remains a named regression fixture.
- `runtime/core/universal_conversation_policy_runtime.py`: universal_adapter_leak fixed. Direct RouteSignal campaign IDs, direct RouteSignal near-miss constants, direct RouteSignal offer renderer, and RouteSignal buyer-facing copy were moved out of the strict universal module.
- `runtime/core/live_voice_session_policy.py`: suspicious_needs_manual_review. It still contains many legacy RouteSignal response paths.
- `runtime/core/contextual_buyer_semantics.py`: suspicious_needs_manual_review. It still contains RouteSignal-specific semantic branches and wording.
- `runtime/core/dialogue_manager.py`, `runtime/core/dialogue_pragmatics.py`, `runtime/core/dialogue_reasoner.py`, `runtime/entrypoints/generate_guarded_response.py`, `runtime/entrypoints/generic_campaign_turn.py`: suspicious_needs_manual_review. These need a later bounded migration or explicit legacy-fixture boundary.

## Leaks Fixed

- Removed direct RouteSignal campaign-id branching from `runtime/core/universal_conversation_policy_runtime.py`.
- Removed direct RouteSignal callback near-miss constants from the strict universal policy module.
- Removed direct RouteSignal offer/value/review-process response rendering from the strict universal policy module.
- Added adapter-mediated `response_capabilities` in `runtime/core/campaign_playbook_adapter.py` for campaign-specific question phrases, callback near-miss phrases, offer/value sentences, worth-time condition, and review-process wording.

## Suspicious Items Left

- `runtime/core/live_voice_session_policy.py`: 159 inspected line hits.
- `runtime/core/contextual_buyer_semantics.py`: 115 inspected line hits.
- `runtime/core/dialogue_manager.py`: 18 inspected line hits.
- `runtime/core/dialogue_reasoner.py`: 8 inspected line hits.
- `runtime/core/dialogue_pragmatics.py`: 5 inspected line hits.
- `runtime/entrypoints/generate_guarded_response.py`: 3 inspected line hits.
- `runtime/entrypoints/generic_campaign_turn.py`: 2 inspected line hits.

These were not rewritten in 4L0 because the blast radius is high and RouteSignal validators are still expected to pass. The next step should be a dedicated legacy-live-demo boundary migration, not ad hoc edits.

## OpenAI-Primary Universal Evaluation Roadmap

- source/affiliation boundary: distinguish official OpenAI sources, public plan information, and non-affiliated helper language.
- plan category explanation: explain Free, Plus, Pro, Business, and Enterprise without inventing hidden tiers.
- subscription vs model/product explanation: keep plans, subscriptions, models, and product features separate.
- Free/Plus/Pro/Business/Enterprise plan fit: route by user need, team/admin/security requirements, and buying route.
- price/terms caveat: require current-price caveats and route final terms to official OpenAI pages.
- privacy/security/data boundary: answer conservatively and escalate security/admin needs to Enterprise/contact sales.
- competitor context: allow only source-bounded comparison; block invented superiority claims.
- current-tool context: handle current stack questions without assuming integrations or migrations.
- AND/OR fidelity: preserve combined and alternative buyer constraints.
- no-fit/disqualify: stop or disqualify unsupported, sensitive, non-commercial, or out-of-scope needs.
- self-serve close toward official plan page: close self-serve fits to the official ChatGPT plan page without account/payment side effects.
- Enterprise/contact-sales route: route enterprise/security/procurement needs to contact sales without pretending to schedule or submit anything.
- repeated-question / loop repair: answer repeated questions with shorter, different wording.
- spoken naturalness and active sales progression: stay concise, spoken, and progression-oriented.

## Confirmations

- RouteSignal remains a regression fixture only.
- No live selector control was enabled.
- No response replacement was enabled.
- No provider/model/TTS/CRM/email/calendar/payment/account side-effect path was enabled.
- No raw private transcript/audio was added to public evidence.
