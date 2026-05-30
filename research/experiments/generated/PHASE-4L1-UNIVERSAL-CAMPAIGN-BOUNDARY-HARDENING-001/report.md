# PHASE-4L1-UNIVERSAL-CAMPAIGN-BOUNDARY-HARDENING-001

- Status: needs_future_migration
- Architecture direction: universal sales adapter / selector / policy first
- Primary benchmark campaign: public OpenAI ChatGPT plans
- RouteSignal role: secondary regression fixture only
- Live selector control enabled: false
- Response replacement enabled: false
- Provider/model/TTS/CRM/email/calendar/payment/account side-effect path enabled: false
- Raw private transcript/audio added to public evidence: false

## Scope

4L1 inspected the suspicious shared-module hits left by 4L0 and fixed only low-risk leaks where the fix was neutral or adapter-mediated. It did not polish the OpenAI campaign, repair new RouteSignal scenarios, enable selector control, enable response replacement, call any provider/model/TTS path, or add CRM/email/calendar/payment/account side effects.

## Inspected Suspicious Modules

- `runtime/core/live_voice_session_policy.py`
- `runtime/core/contextual_buyer_semantics.py`
- `runtime/core/dialogue_manager.py`
- `runtime/core/dialogue_reasoner.py`
- `runtime/core/dialogue_pragmatics.py`
- `runtime/entrypoints/generate_guarded_response.py`
- `runtime/entrypoints/generic_campaign_turn.py`

## Classification Counts

| Classification | Count |
| --- | ---: |
| allowed_legacy_regression_fixture | 2 |
| allowed_campaign_adapter_access | 2 |
| universal_boundary_leak | 3 |
| needs_future_migration | 2 |

## Module Classifications

- `runtime/core/live_voice_session_policy.py`: allowed_legacy_regression_fixture. RouteSignal buyer-facing fallback responses remain for the existing live-demo fixture, while generic campaign config branches already avoid those defaults.
- `runtime/core/live_voice_session_policy.py`: needs_future_migration. The remaining legacy response paths should move behind campaign response capabilities in a dedicated live-demo fixture migration.
- `runtime/core/contextual_buyer_semantics.py`: universal_boundary_leak fixed. The RouteSignal-named scope semantic was neutralized to `campaign_scope_boundary`, and scope-boundary response text now comes from campaign response capabilities.
- `runtime/core/contextual_buyer_semantics.py`: allowed_campaign_adapter_access. RouteSignal playbook checks remain as adapter-mediated legacy fixture branches for gap ordering, confirmed/cleared gaps, and playbook traces.
- `runtime/core/dialogue_manager.py`: needs_future_migration. The RouteSignal-specific soft all-clear reopen gate is behaviorally narrow but should become a neutral campaign capability later.
- `runtime/core/dialogue_reasoner.py`: universal_boundary_leak fixed. Direct Northstar/RouteSignal identity requirements were replaced with campaign-derived identity terms.
- `runtime/core/dialogue_pragmatics.py`: universal_boundary_leak fixed. Direct RouteSignal Growth explanation was moved behind campaign response capabilities with a neutral generic fallback, and seller-agenda recovery now passes campaign context.
- `runtime/entrypoints/generate_guarded_response.py`: allowed_legacy_regression_fixture. The remaining RouteSignal phrase is a buyer-input classifier fixture phrase, not buyer-facing response copy or default generic campaign behavior.
- `runtime/entrypoints/generic_campaign_turn.py`: allowed_campaign_adapter_access. The RouteSignal playbook id is used to reject generic campaign configs that accidentally resolve to the legacy default playbook.

## Fixed Leaks

- Renamed `route_signal_scope_boundary` to `campaign_scope_boundary` in contextual semantics and universal buyer-move mapping.
- Added `scope_boundary_coverage_response` and `scope_boundary_specialist_response` to `campaign_playbook_adapter` response capabilities, so RouteSignal-specific scope response text is campaign-specific.
- Removed direct Northstar/RouteSignal copy from `dialogue_reasoner.py`.
- Moved direct RouteSignal Growth copy from `dialogue_pragmatics.py` into adapter response capabilities.
- Passed campaign context into seller-agenda recovery in `dialogue_pragmatics.py`.

## Future Migration Items

- Move remaining `live_voice_session_policy.py` legacy RouteSignal fixture responses behind neutral campaign response capability keys.
- Replace `dialogue_manager.py` `_is_routesignal_campaign` soft all-clear reopen gate with a neutral campaign capability.
- Split long-term RouteSignal regression fixture behavior from shared live/session policy modules once existing RouteSignal validators have an adapter-backed replacement.

## route_signal_scope_boundary Decision

Decision: renamed to neutral `campaign_scope_boundary`.

Compatibility: current runtime behavior is preserved because contextual semantics still maps the same scope-boundary buyer behavior to the same universal buyer move, `scope_limit_question`. Historical generated evidence was not rewritten. If an external consumer depended on the old exact semantic id, that is compatibility debt for a later migration, but no tracked validator references that id.

## Default Campaign Adapter Decision

Decision: keep RouteSignal as the legacy default adapter behavior for now.

Reason: existing RouteSignal and campaign-playbook validators still assert the legacy default. A broad default adapter change would be higher risk than this checkpoint justifies. The safer boundary is already present in `generic_campaign_turn.py`: generic campaign configs are invalid if they resolve to the default RouteSignal playbook.

## Boundary Contract

Universal modules may use only:

- neutral buyer moves
- neutral sales-stage states
- neutral campaign adapter fields
- neutral response capability keys
- neutral source/claim/side-effect boundaries

Campaign-specific modules may define:

- campaign product/company names
- campaign-specific diagnostic gaps
- campaign-specific close route
- campaign-specific human follow-up owner
- campaign-specific response capability text

## Roadmap Confirmation

- OpenAI remains the primary benchmark campaign.
- RouteSignal remains a secondary regression fixture only.
- No live selector control was enabled.
- No response replacement was enabled.
- No provider/model/TTS/CRM/email/calendar/payment/account path was enabled.
- No raw private transcript/audio was added to public evidence.
