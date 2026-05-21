# DIALOGUE-MANAGER-002 Pragmatic Dialogue Repair

`DIALOGUE-MANAGER-002-pragmatic-dialogue-repair` is the second control-plane repair after `DIALOGUE-MANAGER-001-root-repair`.

It does not open `PROD-102`, claim production readiness, enable payment collection, create a provider-hosted durable agent, use voice cloning, add provider ASR, install or wire a local LLM, make LLM calls required for live response, or let an LLM write final spoken responses.

## Problem

`DIALOGUE-MANAGER-001` gave the live path one manager action and call-control owner, but small human dialogue moves were still scattered across policy branches.

That left the system vulnerable to the same root pattern Tarik heard live:

- buyer asks what the call is about
- buyer asks what a term means
- buyer asks why the question matters
- buyer says the agent should lead because the agent called
- buyer states real missed-lead pain and should be moved to appointment-setting

Some individual responses were already acceptable, but they were not first-class manager moves. That made debugging look like another one-off route patch instead of a dialogue-control repair.

## Scope

This checkpoint adds `runtime/core/dialogue_pragmatics.py` behind the dialogue manager.

The slice is intentionally narrow:

- classify common pragmatic buyer moves before generic sales route selection
- attach a `dialogue_pragmatics` packet to live-demo turn output and browser diagnostics
- prevent term-meaning questions such as `what do you mean by handoff` from being stored as confirmed workflow pain
- keep terminal call control, ASR quality repair, anti-loop repair, duplicate repair, and stability repair under the manager
- reuse existing live-session policy wording where it is already safe
- add one direct handoff term explanation that stays customer-facing and avoids internal labels

It does not replace the deterministic runtime with a local LLM.

## Behavior

Covered pragmatic moves:

- `call_purpose_question`
- `previous_question_clarification`
- `term_or_context_unfamiliarity`
- `term_meaning_question`
- `relevance_challenge`
- `agent_should_lead`
- `crm_replacement_question`
- `pain_statement`

Each applied move records:

- `pragmatics_id`
- `schema_version`
- `move_id`
- `target_action`
- `continuity_reason`
- `confidence`
- `dialogue_focus`
- `selected_gap`
- `previous_question_type`
- provider and local-LLM boundary flags

The manager now records the pragmatic move in `state_before`, `selected_action`, `dialogue_manager.pragmatic_move`, and top-level `dialogue_pragmatics`.

## Commands

Validate the pragmatic dialogue checkpoint without live microphone, provider ASR, provider TTS, provider LLM calls, or local LLM calls:

```powershell
python scripts\validate_dialogue_manager_002_pragmatic_dialogue_repair.py
```

Run it with the focused live-demo regression stack before committing:

```powershell
python scripts\validate_dialogue_manager_002_pragmatic_dialogue_repair.py
python scripts\validate_dialogue_manager_001_root_repair.py
python scripts\validate_live_demo_001_agent_voice_call.py
python scripts\validate_live_demo_002_conversation_stability.py
python scripts\validate_live_demo_009_appointment_lead_close.py
python scripts\validate_live_demo_010_live_feedback_route_polish.py
python scripts\validate_live_demo_011_live_followup_stop_and_pain_close.py
python scripts\validate_live_demo_012_soft_stop_and_context_recovery.py
python scripts\validate_live_demo_013_reasoner_route_guard.py
python scripts\validate_runtime_manifest.py
```

## Evidence

Generated evidence:

- `research/experiments/generated/DIALOGUE-MANAGER-002-pragmatic-dialogue-repair/result.json`
- `research/experiments/generated/DIALOGUE-MANAGER-002-pragmatic-dialogue-repair/report.md`

Private browser transcript JSON files can continue to live under:

```text
data\private\live-demo-003\raw-turns\browser-transcript
```

Do not commit private transcript files from that folder.
