# LIVE-DEMO-002 Runtime Extraction Baseline

`LIVE-DEMO-002` records the accepted `LIVE-DEMO-001` behavior before treating the live-demo fixes as reusable runtime architecture. This is the runtime extraction baseline for the current supervised live demo.

The checkpoint is intentionally narrow: preserve the current user-heard demo behavior while extracting MVP-relevant behavior into runtime-owned modules.

## Scope

- Baseline source: `LIVE-DEMO-001`
- Behavior policy: `behavior_preserved`
- Runtime modules:
- `runtime/contracts/voice_turn_state_contract.py`
- `runtime/speech/asr_quality_gate.py`
- `runtime/core/live_voice_session_policy.py`
- Demo runner kept as orchestration/UI glue: `scripts/run_live_demo_001_agent_voice_call.py`
- Campaign-owned live-demo fields: `caller_identity`, `target_account_context`, `sales_delivery_guidance`, `sales_context_variety`, and `sales_emphasis_priority`

No provider call, hosted provider agent, voice cloning, private customer audio, production runtime promotion, or `PROD-102` work is part of this checkpoint.

## Baseline Coverage

The baseline runner records compact regression evidence for:

- repetition prevention
- follow-up continuity
- voice delivery propagation
- product-answer routing
- ASR quality handling
- callback scheduling boundary
- callback workflow disambiguation
- call-context recovery
- customer echo prevention
- seller-led next move
- seller-led close progression
- terminal call-control stop
- live TTS fallback voice guard
- stale-session greeting relevance
- voice consistency across turns
- agent_led_sales_opening
- qualification_steering
- sales_context_variety
- sales_emphasis_priority
- previous_question_clarification
- ambiguous_negative_clarification
- caller_identity_recall
- internal_repair_speech_blocked
- audible runtime-upgrade propagation

It also records the current private evidence packet shape by key only, including `quality_gate`, `voice_turn_state_received`, `tts_delivery`, and `dialogue_reasoner_async_enrichment`. The async enrichment evidence stores response fingerprints/counts, not new customer-facing response text, and the artifact does not store private audio or secrets.

## Intentional Improvement

`sales_opening_permission_check` is an `intentional_improvement` added after live feedback showed that the first greeting opened with a topic menu instead of behaving like a sales call. A greeting now asks whether the buyer has a minute for a quick question about missed lead follow-up.

`agent_led_sales_opening` is an `intentional_improvement` added after live feedback showed that the demo was still buyer-led by construction. `Start Conversation` now sends a runtime-owned `agent-open` turn before browser ASR starts. The agent speaks first, names `Northstar Workflow Labs` / `RouteSignal CRM`, states the missed-callback/handoff problem, and asks a qualifying question instead of waiting for Tarik to ask the first product question.

`qualification_steering` is compact regression coverage for the same sales-call correction. Weak acknowledgements after the agent-led opener now trigger `proactive_qualification_guidance_after_acknowledgement`, and a named gap such as handoffs routes to `seller_gap_selected_for_qualification` with a consented short workflow-review next step.

`previous_question_clarification` is an `intentional_improvement` added after live feedback showed that buyer requests such as `I did not understand what you asked before` could fall through to unrelated qualification wording. The runtime now explains the prior sales question in plain terms, preserves the current qualification focus, and asks one clearer version instead of advancing canned sentence-bank copy.

`caller_identity_recall` is an `intentional_improvement` added after live feedback showed that `where were you calling from again?` could fall through to the generic focus menu. The runtime now answers with the caller identity and product relationship directly: `Maya`, `Northstar Workflow Labs`, and `RouteSignal CRM`.

`ambiguous_negative_clarification` is an `intentional_improvement` added after live feedback showed that a bare `no` could feel oblivious or fall through to unrelated menus/copy. The runtime now treats short negative replies as ambiguous dialogue acts, asking whether the buyer is rejecting the timing or saying the missed-callback/handoff problem is not real.

`internal_repair_speech_blocked` is an `intentional_improvement` added after live feedback showed anti-loop repair text such as `avoid repeating the same question` could leak into customer-facing speech. Non-core focus follow-ups now use customer-safe boundary text and validators block internal repair/process wording.

`sales_context_variety_and_emphasis` is an `intentional_improvement` added after live feedback showed that the opener did not make the caller relationship clear enough and later qualification turns had too little context variety while emphasizing the wrong details. The campaign profile now exposes `caller_identity` with `Maya`, `Northstar Workflow Labs`, and `the team behind RouteSignal CRM`, plus `target_account_context` for the person handling inbound demo follow-up. The opener must include `calling from Northstar Workflow Labs, the team behind RouteSignal CRM`; follow-up qualification turns must cover a broader sales-context set; and voice prosody cues must prioritize problem/value targets such as missed callbacks, handoffs, owner routing, callback reminders, workflow review, and visibility instead of greeting text or small talk. The first `agent-open` turn keeps pacing/emphasis cues but suppresses filler insertion between the identity line and `Do you have a minute?`.

`proactive_price_guidance_after_acknowledgement` is an `intentional_improvement` added after live feedback showed that weak acknowledgements such as `hmm okay, that is interesting` replayed the same pricing sentence.

The corrected behavior keeps the resolved price focus but moves the agent into guided selling: it explains when Growth is worth reviewing, ties value to missed callbacks, reminders, and handoff review, and avoids reopening a focus menu or replaying the exact `$29/month` / `$59/month` answer.

`multi_topic_non_repeating_progression` is an `intentional_improvement` added after live feedback showed that topic follow-ups could still replay or fall back to menus. Price, fit, timing, and feature/detail sequences now progress through guided selling responses for turns such as `can you tell me more`, `what else should I know`, and `okay tell me more`.

`callback_scheduling_boundary` is an `intentional_improvement` added after live feedback showed that `I do not have time` followed by `call me 10 a.m. tomorrow` could fall back to product-topic menus. The runtime now treats the no-time turn as `callback_request_time_needed`, classifies it as `callback-request`, asks for a callback time, then treats the supplied time as `callback_time_confirmed` with `scheduling-confirmation`, `confirm-scheduling`, and `schedule-and-end`.

`callback_workflow_disambiguation` is an `intentional_improvement` added after live feedback showed that product callback language could be misread as scheduling. A buyer saying callbacks are the gap now routes through `seller_gap_selected_for_qualification`, while `what do you mean by callbacks` routes through `callback_workflow_clarified`. Both must explain callback reminders as a product workflow concept and must not ask for a callback time.

`call_context_recovery` is an `intentional_improvement` added after live feedback showed that agenda, next-step, confusion, time-waste, and frustration turns could fall through to generic topic menus or duplicate qualification copy. The runtime now routes these turns through explicit recovery reasons such as `time_constrained_agenda_answered`, `seller_agenda_recovered`, `workflow_review_next_step_explained`, `topic_confusion_repaired`, and related compact live-demo expectations.

`customer_echo_prevention` is regression coverage for the corrected customer-heard behavior that direct campaign answers should not open by repeating the buyer's stated topic, named plan, or stated price fact. The baseline covers manual tracking, Growth-plan value, small-team fit, workflow scope, integration boundary, and security boundary turns.

`seller_led_next_move` is regression coverage for the corrected sales-agent behavior that basic campaign answers should not stop at information delivery. Direct price, Product, Growth-plan, manual-tracking, small-team-fit, and workflow-scope turns now answer briefly and then ask one diagnostic buyer-led question, using the existing RAG-019/RAG-020/RAG-021 guidance without enabling broad runtime retrieval by default.

`seller_led_close_progression` is an `intentional_improvement` added after live feedback showed that the agent could ask diagnostic questions but still wait for the buyer to carry the sale. When the buyer names a gap such as handoffs after a price question, the runtime maps that gap to value and asks for a consented short workflow review instead of hard-closing.

`terminal_call_control_stop` is regression coverage for callback-confirmation turns that end with `schedule-and-end`. After goodbye, browser auto-listening stops instead of restarting the conversation.

`live_tts_fallback_voice_guard` is regression coverage for the ElevenLabs live path. If a live provider call was attempted but no audio file is returned, the browser does not auto-switch into default fallback voice mid-call; it pauses and exposes the fallback reason.

`stale_session_greeting_relevance` is an `intentional_improvement` added after live feedback showed that a greeting such as `hey what's up` could become unrelated when an old browser session already contained prior turns. Greetings now route to the sales opener unless an active resolved focus should continue.

`voice_consistency_across_turns` is an `intentional_improvement` added after live feedback showed that voice level, enthusiasm, and naturality could drift across answers. The live demo now pins ElevenLabs request voice settings to one stable profile across freeform and protected turns, while still keeping one configured voice ID.

`audible_runtime_upgrade_propagation` is an `intentional_improvement` added after live feedback showed that prior voice, RAG, and sales-delivery work could exist in packets without being heard in the browser demo. The demo now sends safe RESP-003 provider-shaped TTS input to browser fallback speech after stripping provider markup, validates bounded filler/naturalization on the spoken fallback text, enables local guarded retrieval for demo turns when the `RAG-017` registry exists, and requires one eligible price-worth turn where retrieval genuinely influences the guarded response.

`campaign_depth_before_duplicate_repair` is an `intentional_improvement` added after live feedback showed that product/detail questions after price could be swallowed by price duplicate repair. Explicit campaign-depth questions now route through the fictional campaign profile before same-topic duplicate repair.

`async_reasoning_enrichment_evidence` is regression coverage for attaching `DIALOGUE-REASONER-004` to the live-demo private trace without changing the spoken path. The packet proves the deterministic response exists before enrichment, records a response fingerprint, and keeps provider calls, text upload, route override, final-response mutation, and `PROD-102` blocked.

## Commands

Record the baseline artifact:

```powershell
python scripts\run_live_demo_002_runtime_extraction_baseline.py
```

Validate runtime extraction preservation:

```powershell
python scripts\validate_live_demo_002_runtime_extraction_baseline.py
```

Generated evidence:

```text
research\experiments\generated\LIVE-DEMO-002\runtime_extraction_baseline.json
research\experiments\generated\LIVE-DEMO-002\runtime_extraction_baseline.md
```

## Acceptance

The extraction is accepted only if:

- `scripts/validate_live_demo_001_agent_voice_call.py` still passes.
- `scripts/validate_live_demo_002_runtime_extraction_baseline.py` passes.
- The runtime manifest lists the extracted modules.
- Every baseline case remains `behavior_preserved`.
- The opener preserves unambiguous caller identity with `Maya`, `calling from Northstar Workflow Labs`, and `the team behind RouteSignal CRM`.
- The opener does not insert a filler between the seller/product identity and the permission check.
- Qualification follow-ups preserve `sales_context_variety` across repeated low-information buyer turns.
- Buyer requests to clarify the previous question route through `previous_question_clarification`.
- Caller identity recall routes through `caller_identity_recall`.
- Bare negative replies route through `ambiguous_negative_clarification`.
- Callback workflow language routes through `callback_workflow_disambiguation` instead of callback scheduling unless the buyer asks to be called back or supplies a time.
- Call-context and confusion turns route through `call_context_recovery` instead of generic focus menus or duplicate qualification copy.
- Customer-facing speech blocks internal repair wording through `internal_repair_speech_blocked`.
- Voice delivery preserves `sales_emphasis_priority` by targeting problem/value phrases, not greeting text.
- `DIALOGUE-REASONER-004` private evidence is attached without provider calls or customer-response mutation.
- `provider_calls_made`, `runtime_behavior_changed`, and `opens_prod_102` remain `false`.

Any intentional future user-heard change must be named as `intentional_improvement` and covered by validator expectations before implementation.
