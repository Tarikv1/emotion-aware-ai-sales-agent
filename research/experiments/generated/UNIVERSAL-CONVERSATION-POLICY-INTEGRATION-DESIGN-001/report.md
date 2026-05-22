# UNIVERSAL-CONVERSATION-POLICY-INTEGRATION-DESIGN-001

## 1. Summary

This phase is design-only. Runtime behavior should not change yet.

The right integration pattern is not to make `universal_sales_conversation_knowledge.py` another dialogue manager. It should produce a small policy frame that constrains the existing route: ASR gate, contextual semantics, pragmatics, dialogue manager, live voice session policy, and existing stability guards.

The smallest safe first behavior slice is generic-campaign ASR garble repair, with universal policy frames traced for all relevant turns and enforcement initially limited to generic campaigns. This addresses the live issue where accepted but nonsensical browser ASR text can be treated as meaningful buyer intent.

## 2. Proposed Policy Frame

`UniversalConversationPolicyFrame`

```json
{
  "schema_version": 1,
  "knowledge_id": "UNIVERSAL-SALES-CONVERSATION-KNOWLEDGE-001",
  "buyer_move_id": "asr_garbled_or_low_confidence",
  "response_shape_id": "ask_repeat_for_asr_garble",
  "conversation_stage": "diagnostic",
  "allowed_fact_slots": ["language"],
  "forbidden_patterns": ["infer pain", "capture appointment", "repeat diagnostic menu"],
  "allowed_call_controls": ["continue-call"],
  "memory_policy": "preserve_memory_do_not_advance_state",
  "appointment_pressure_level": "none",
  "direct_question_required": false,
  "asr_repair_required": true,
  "should_preserve_confirmed_gaps": true,
  "should_preserve_cleared_gaps": true,
  "one_next_action_only": true,
  "provider_calls_made": false,
  "local_llm_calls_made": false,
  "opens_prod_102": false
}
```

The frame should be attached into the runtime trace, for example under `dialogue_manager.universal_policy_frame` and optionally copied to the top-level generic/browser packet. It should not replace `contextual_buyer_semantics`; it should constrain how that semantic result may be used.

## 3. Integration Sequence

1. Browser/server receives transcript and selected campaign mode.
2. Existing `evaluate_asr_quality(...)` runs.
3. New universal ASR repair check runs before buyer-move routing.
4. Existing contextual buyer semantics extracts buyer meaning and campaign gap evidence.
5. Universal policy maps buyer move plus stage to response-shape constraints.
6. Dialogue manager chooses an action while obeying universal call-control and response-shape constraints.
7. Existing live voice session policy renders text, but must obey the universal response shape.
8. Existing anti-loop, duplicate, and stability guards remain safety nets, not primary strategy owners.

Current observed order in [dialogue_manager.py](D:/Codex/active/emotion-aware-ai-sales-agent/runtime/core/dialogue_manager.py): `plan_dialogue_action(...)` evaluates contextual semantics and pragmatics, builds `state_before`, handles terminal control, handles rejected ASR gate, then applies semantic, pragmatic, or live voice session policy continuity.

For 4E2B, put the universal ASR check after `evaluate_asr_quality(...)` and before contextual semantic continuity can infer pain or appointment state.

## 4. What The Universal Layer Owns

- Buyer move taxonomy.
- Response-shape constraints.
- ASR repair boundary decisions.
- Allowed campaign fact slots.
- Forbidden customer-facing patterns.
- Call-control constraints.
- Memory preservation rules such as preserving confirmed and cleared gaps during repair.
- Trace metadata showing why a universal policy constraint applied.

## 5. What It Must Not Own

- Campaign config validation.
- Campaign gap definitions or evidence phrase ownership.
- Final customer prose generation.
- Dialogue routing as a second action planner.
- TTS, ASR provider, browser selector, or live TTS gate behavior.
- Provider calls, local LLM calls, email, calendar, CRM, or PROD-102.
- RouteSignal product facts, pricing, or demo-specific wording.

The failure mode to avoid is obvious: if the universal layer starts returning full spoken responses, it becomes the new dialogue manager and the current system just gains another patch surface.

## 6. First Integration Slice Recommendation

Recommendation: **4E2B should add policy-frame tracing and enforce only generic-campaign ASR garble repair.**

This is the best first slice because:

- It handles `play a double be good` and `yadav would be good` before semantic routing.
- It prevents false pain confirmation and false appointment capture.
- It does not require rewriting product-detail, challenge, or diagnostic rendering.
- It can preserve RouteSignal by leaving RouteSignal enforcement off.
- It gives future validators a visible `universal_policy_frame` without forcing broad behavior changes.

Do not start with product-detail/scope-limit handling. That path is useful but touches regulated wording and existing product-boundary repairs. Do not start with full repeated-diagnostic prevention either; it crosses semantic routing, response rendering, and stability guards.

## 7. Validator Plan

Create:

`scripts/validate_universal_conversation_policy_integration_001.py`

Scenarios:

- RouteSignal default: `__agent_open__ -> yeah sure -> callbacks are fine`
  - Expect RouteSignal playbook, `current_gap_clear` / callbacks, no policy enforcement regression.
- Generic insurance ASR garble: `__agent_open__ -> yeah sure -> play a double be good`
  - Expect repeat/rephrase, no pain inference, no appointment ask, no full diagnostic menu.
- Generic automotive near-miss: `__agent_open__ -> yes -> repeal timings are usually pretty long`
  - Expect confirmation/rephrase unless the implementation has an explicit safe near-miss mapping rule; no full menu.
- Generic automotive clean pain: `__agent_open__ -> yes -> repair timings are usually pretty long`
  - Expect `pain_confirmed`, `target_gap=repair_timing`, no full menu.
- Generic challenge: `__agent_open__ -> yes -> repair timings are usually pretty long -> why are you asking for this information again`
  - Expect direct why-answer, preserve `repair_timing`, no full menu.
- Generic product-detail: `__agent_open__ -> yes -> what does your product do?`
  - Expect scope answer via universal policy constraints, no internal wording, no `transfer-or-escalate`.
- Generic appointment confirmation garble after callback-time ask: buyer says `yadav would be good`
  - Expect repeat/rephrase and no `schedule-and-end`.

Common assertions:

- `provider_calls_made=false`
- `local_llm_calls_made=false`
- `sends_email=false`
- `creates_calendar_event=false`
- `writes_crm=false`
- `opens_prod_102=false`
- `customer_audio_uploaded_to_python_server=false`
- `customer_audio_uploaded_to_tts_provider=false`

## 8. Feature-Gating / Rollback Plan

Use two separate controls:

- `universal_policy_trace_enabled`: default true. Adds the frame to traces without changing behavior.
- `universal_policy_enforcement_enabled`: default false for RouteSignal, true only for the generic ASR-garble first slice once its validator passes.

Rollback should disable enforcement while preserving trace. That keeps diagnosis visible without changing dialogue behavior.

Do not use environment secrets or provider settings for this gate. This is a deterministic runtime policy gate.

## 9. Risks

- The universal layer becomes a second dialogue manager if it emits final prose or picks actions directly.
- Near-miss ASR rules can overcorrect valid buyer language. Start with repeat/confirm, not automatic mapping.
- RouteSignal can regress if universal enforcement is enabled before generic behavior is stable.
- Existing stability guards can conflict with universal constraints unless the policy frame is attached before guards run.
- A too-broad first slice will recreate campaign-by-campaign patching inside a universal-looking wrapper.

## 10. Recommended Next Implementation Phase

Phase 4E2B:

1. Add a small runtime helper that builds `UniversalConversationPolicyFrame` from:
   - ASR quality gate
   - transcript
   - current stage
   - contextual semantic frame if available
   - campaign type
2. Attach the frame to runtime trace with no provider calls.
3. Enforce only generic-campaign ASR garble repair before contextual semantics can infer pain or appointment state.
4. Keep RouteSignal enforcement disabled.
5. Add `scripts/validate_universal_conversation_policy_integration_001.py`.

Runtime behavior changed in this design phase: **false**.
