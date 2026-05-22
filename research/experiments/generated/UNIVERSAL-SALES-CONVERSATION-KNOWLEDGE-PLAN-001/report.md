# UNIVERSAL-SALES-CONVERSATION-KNOWLEDGE-PLAN-001

## 1. Summary

The current system has enough campaign facts. The weaker part is that buyer-move handling and response shape are still spread across `contextual_buyer_semantics.py`, `live_voice_session_policy.py`, `dialogue_pragmatics.py`, and post-generation repair guards. That is why live testing keeps producing campaign-by-campaign fixes for the same underlying moves: time pressure, tentative pain, product-detail questions, why-are-you-asking challenges, contradiction repair, and garbled ASR.

Recommendation: add a reusable universal conversation knowledge layer before further dialogue patching. The best first implementation phase is contract-only: create `runtime/core/universal_sales_conversation_knowledge.py`, validate its taxonomy and response-shape rules, and do not change runtime behavior yet.

## 2. Why Campaign-By-Campaign Patching Is Failing

The recent patches fixed real failures, but the fixes landed in the wrong architectural shape. Insurance product-detail limitation and automotive repair-timing contradiction repair are buyer-move patterns, not campaign-specific logic. The evidence shows the same pattern across verticals:

- `GENERIC-CAMPAIGN-RESPONSE-QUALITY-001` reported 152 response quality failures before patching across all eight generic vertical fixtures.
- `GENERIC-CAMPAIGN-SPOKEN-TEXT-QUALITY-001` reported 528 spoken-text failures before patching across the same vertical set.
- `LIVE-DEMO-MANUAL-FEEDBACK-002` passed after direct patches, but those patches added vertical/gap branches such as insurance product-detail handling and automotive `repair_timing` purpose/contradiction handling.
- Generic permission-to-diagnostic still commonly produces a full menu shape: "Thanks, I am checking X, Y, or Z. Which one is causing trouble, if any?" That is acceptable only in limited stages, but today it is the default fallback shape in too many situations.
- The local raw-turn path exists and the latest reference transcript files are present. The plan did not copy private transcript content; only file presence and known feedback-term matches were checked.

The assumption that each campaign needs its own dialogue repair is false. Campaigns need facts and boundaries. The runtime needs one shared policy for how to talk.

## 3. Current Architecture Findings

`runtime/core/universal_sales_knowledge.py` already defines universal sales stages and buyer move families. It is useful, but it is descriptive. It does not yet define executable response-shape contracts, repair rules, or ASR-garble behavior.

`runtime/core/vertical_sales_playbooks.py` contains vertical pain dimensions, qualification dimensions, safe value bridge principles, regulated cautions, blocked claim types, and handoff patterns. This should remain a vertical fact and safety source, not a place for turn-by-turn repair strategy.

`runtime/core/campaign_playbook_adapter.py` is the strongest existing boundary. It adapts RouteSignal and generic configs into a playbook with `campaign_context`, `diagnostic_gaps`, `core_diagnostic_gaps`, `gap_order`, allowed claims, blocked claims, and regulated cautions. Preserve this.

`runtime/core/contextual_buyer_semantics.py` currently owns too much. It contains:

- generic product-detail detection and responses,
- insurance-specific product-detail limitation wording,
- automotive-specific purpose and contradiction repair for `repair_timing`,
- time-constrained permission,
- tentative gap interest,
- diagnostic menu responses,
- current-gap clear and remaining-gap progression.

`runtime/core/live_voice_session_policy.py` also owns strategy selection through helpers such as `generic_campaign_review_question`, `generic_campaign_product_detail_text`, `generic_campaign_claim_boundary_text`, `continuity_text`, `duplicate_response_repair`, `anti_loop_response`, and `pre_speech_conversation_stability_guard`.

`runtime/core/dialogue_manager.py` is the right orchestrator. It already coordinates semantic frames, pragmatic moves, anti-loop repair, duplicate repair, stability guard, memory, call control, and safety flags. The missing input is a normalized universal buyer-move frame with response-shape constraints.

`runtime/speech/asr_quality_gate.py` only rejects empty transcripts and explicit low confidence below `0.45`. It does not detect high-confidence browser-ASR nonsense, domain near-misses, or mismatch with the previous agent question.

`scripts/run_live_demo_001_agent_voice_call.py` has the right provider boundary metadata: browser SpeechRecognition is client-side, customer audio is not uploaded to the Python server or TTS provider, generic live TTS is explicitly gated, and selected campaign mode is tracked. Do not mix voice ID consistency or ASR provider replacement into this refactor.

## 4. Proposed Universal Sales Conversation Knowledge Contract

Create:

`runtime/core/universal_sales_conversation_knowledge.py`

This should not become a second dialogue manager. It should be a declarative contract that the existing dialogue manager can consume.

Core sections:

- `buyer_move_taxonomy`
- `conversation_stage_policy`
- `response_shape_library`
- `universal_repair_rules`
- `call_control_policy`
- `asr_repair_boundary`
- `campaign_fact_slots`
- `forbidden_customer_facing_patterns`
- `validator_matrix`

Buyer move taxonomy:

- `permission_acknowledgement`
- `time_constrained_permission`
- `pain_confirmed`
- `tentative_gap_interest`
- `no_pain_clear`
- `not_relevant`
- `product_detail_question`
- `scope_limit_question`
- `regulated_claim_question`
- `why_are_you_asking`
- `contradiction_challenge`
- `already_answered_challenge`
- `confusion_not_clear`
- `repeat_or_rephrase_request`
- `send_info_request`
- `callback_request`
- `callback_time_provided`
- `appointment_interest`
- `right_person_redirect`
- `support_request`
- `stop_request`
- `asr_garbled_or_low_confidence`

Conversation stages:

- `opening`
- `permission`
- `diagnostic`
- `value_bridge`
- `scope_limit`
- `appointment_progression`
- `callback_capture`
- `send_info_capture`
- `handoff_right_person`
- `stop_close`

Response-shape rule:

Every response should:

1. Acknowledge buyer meaning.
2. Answer the direct question if one was asked.
3. Use campaign facts only from allowed slots.
4. Respect blocked claims and regulated cautions.
5. Choose one next action.

Every response should avoid:

- internal policy wording such as "I should",
- "approved qualified reviewer path",
- repeated full diagnostic menus after the buyer already gave an answer,
- invented product details, prices, guarantees, coverage, refunds, or integration/security claims,
- `transfer-or-escalate` for ordinary uncertainty,
- erasing confirmed or cleared gaps,
- guessing buyer meaning from garbled ASR,
- RouteSignal fallback for invalid or selected generic campaigns.

The contract should output a small policy frame, for example:

```json
{
  "buyer_move": "why_are_you_asking",
  "stage": "diagnostic",
  "response_shape": "acknowledge_explain_purpose_offer_one_next_step",
  "allowed_fact_slots": ["appointment_target", "human_followup_owner", "target_gap.review_focus"],
  "blocked_response_patterns": ["full_diagnostic_menu", "internal_policy_wording"],
  "call_control_allowed": ["continue-call"],
  "memory_policy": "preserve_confirmed_and_cleared_gaps"
}
```

## 5. Proposed ASR Repair Boundary

Add an ASR repair stage before contextual buyer semantics and before appointment or pain routing.

It should detect:

- explicit low ASR confidence,
- empty or fragment transcript,
- phonetic nonsense,
- malformed phrases such as `play a double be good`,
- known domain near-misses such as `repeal timings` near automotive repair timing,
- mismatch between previous agent question and buyer response,
- high-risk ambiguity around appointment times, email, names, prices, coverage, refunds, and regulated claims.

Expected behavior:

- ask for a repeat or short rephrase,
- do not infer pain,
- do not move to appointment,
- do not reopen a diagnostic menu,
- preserve previous confirmed and cleared memory,
- do not call providers,
- keep side-effect flags false.

This can start inside `runtime/core/universal_sales_conversation_knowledge.py` as an `asr_repair_boundary` section. If the implementation becomes too large, split it into `runtime/core/asr_repair_policy.py`.

## 6. Campaign Config Responsibility After Refactor

Campaign configs should own:

- `campaign_id`
- `client_name`
- `product_or_offer_name`
- `vertical_id`
- `objective`
- `human_followup_owner`
- `appointment_target`
- `allowed_claims`
- `blocked_claims`
- `regulated_cautions`
- `diagnostic_gaps`
- `core_diagnostic_gaps`
- `gap_order`
- `caller_identity`
- `language`
- examples of customer language

Campaign configs should not own:

- generic acknowledgement strategy,
- why-are-you-asking repair strategy,
- product-detail limitation response shape,
- loop repair strategy,
- ASR-garble handling,
- appointment progression policy,
- transfer/escalate policy except explicit configured escalation triggers.

The existing `campaign_playbook_adapter` should remain the adapter between campaign facts and runtime playbooks.

## 7. Runtime Integration Points

`runtime/entrypoints/generic_campaign_turn.py`

- Future 4E2 integration point.
- Run ASR repair after `evaluate_asr_quality(...)` and before `dialogue_manager.plan_dialogue_action(...)`.

`runtime/core/dialogue_manager.py`

- Future 4E2 integration point.
- Consume a normalized universal buyer-move frame with response-shape constraints, call-control constraints, and memory update policy.
- Keep it as the orchestrator.

`runtime/core/contextual_buyer_semantics.py`

- Future migration target.
- Reduce toward feature extraction and gap matching.
- Move universal repair decisions out.

`runtime/core/live_voice_session_policy.py`

- Future migration target.
- Keep text-rendering helpers where useful, but make them render from universal response shapes instead of selecting strategy.

`runtime/core/campaign_playbook_adapter.py`

- Preserve.
- It is already the correct campaign fact boundary.

`scripts/run_live_demo_001_agent_voice_call.py`

- Preserve current selector, provider boundary, generic live TTS gate, browser ASR metadata, and no-customer-audio-upload behavior.
- Do not use this phase to solve voice ID consistency or browser ASR provider replacement.

## 8. Validator Strategy

Add these validators:

- `scripts/validate_universal_sales_conversation_knowledge_001.py`
- `scripts/validate_universal_buyer_moves_cross_campaign_001.py`
- `scripts/validate_universal_asr_repair_boundary_001.py`
- `scripts/validate_universal_response_shape_quality_001.py`

Campaign matrix:

- RouteSignal
- `synthetic-insurance-review`
- `synthetic-b2b-saas-operations`
- `synthetic-automotive-service-review`
- `synthetic-home-services-estimate`

Buyer move cases:

- `make it quick`
- `maybe X`
- `X is usually a problem`
- `what does your product do?`
- `so you can't give me details?`
- `why are you asking?`
- `you didn't answer my question`
- `if you're not the right person, why ask?`
- `I already told you`
- `yeah that would be good`
- `play a double be good`
- `yadav would be good`
- `repeal timings are long`
- `send me details`
- `tomorrow at 3 works`
- `no thanks`
- `stop calling`

Assertions:

- buyer meaning acknowledged,
- direct question answered,
- no repeated full menu after answer,
- no internal policy wording,
- no transfer/escalate unless required,
- no campaign leakage,
- appointment ask only when appropriate,
- safe claim boundaries preserved,
- side-effect flags false,
- generic selected configs do not fall back to RouteSignal.

Do not overfit validators to exact full-sentence output except for safety-critical forbidden wording. The stronger target is semantic correctness plus response-shape compliance.

## 9. Migration Phases 4E1-4E5

Phase 4E1:

- Create `runtime/core/universal_sales_conversation_knowledge.py`.
- Add schema/contract validation.
- Define buyer moves, stages, response shapes, forbidden patterns, call-control constraints, ASR boundary, and campaign fact slots.
- No runtime behavior change except optional manifest registration.

Phase 4E2:

- Integrate universal buyer-move policy before campaign-specific routing.
- Replace repeated generic diagnostic fallback with universal explanation/repair.
- Add ASR-garble boundary.

Phase 4E3:

- Move product-detail and scope-limit handling into universal policy.
- Campaign config supplies allowed facts, blocked claims, follow-up owner, appointment target, and regulated cautions only.

Phase 4E4:

- Treat generic campaigns as fixtures.
- Validate the same universal buyer-move matrix across RouteSignal, a regulated generic campaign, a non-regulated generic campaign, and a service-style generic campaign.

Phase 4E5:

- Re-run browser typed and live TTS rehearsals.
- Only after the universal dialogue layer is stable, revisit generic voice ID consistency and ASR provider replacement.

## 10. Risks

Overabstracting into a second dialogue manager:

- Mitigation: keep the new module declarative. The existing dialogue manager remains the orchestrator.

Weakening regulated claim boundaries:

- Mitigation: separate `product_detail_question` from `regulated_claim_question`. Validators must assert blocked claims and regulated cautions.

Breaking RouteSignal while improving generic campaigns:

- Mitigation: include RouteSignal in every universal buyer-move validator and preserve the playbook adapter boundary.

Blocking valid short replies as ASR-garbled:

- Mitigation: use previous-question compatibility. `yeah`, `sure`, and `that would be good` can be valid in the right stage; nonsense should trigger repeat.

Existing validators codifying brittle wording:

- Mitigation: shift validators toward semantic and response-shape assertions, not exact prose snapshots.

Voice ID consistency distracting from architecture:

- Mitigation: track it separately after 4E5. It is a live TTS configuration issue, not a dialogue-policy issue.

## 11. Recommended Next Implementation Phase

Proceed with Phase 4E1.

Do not integrate behavior first. The next useful change is to create the contract module and validator so later runtime patches have one target architecture. If 4E1 jumps straight into rewriting `contextual_buyer_semantics.py`, it will likely create another scattered patch layer under a new name.

The 4E1 acceptance bar should be:

- `runtime/core/universal_sales_conversation_knowledge.py` exists.
- It validates buyer move taxonomy, stage policy, response shapes, forbidden wording, call-control constraints, ASR repair boundary, and campaign fact slots.
- It maps existing RouteSignal and generic campaign facts without reading secrets or calling providers.
- It proves generic campaigns are fixtures for the same universal buyer-move tests, not owners of dialogue strategy.
