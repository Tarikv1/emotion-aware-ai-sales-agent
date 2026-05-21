# DIALOGUE-MANAGER-001 Root Repair

`DIALOGUE-MANAGER-001-root-repair` is the first control-plane repair after `LIVE-DEMO-013-reasoner-route-guard`.

It does not open `PROD-102`, claim production readiness, enable payment collection, create a provider-hosted durable agent, use voice cloning, add provider ASR, install or wire a local LLM, make LLM calls required for live response, or let an LLM write final spoken responses.

## Problem

The live demo was failing systemically because the current turn path had no single owner for dialogue state, spoken response, and call control.

Before this checkpoint, one turn could be shaped by:

- deterministic dialogue reasoning
- live session continuity
- guarded response composition
- anti-loop repair
- duplicate-response repair
- conversation-stability repair
- late call-control overrides

That made narrow fixes pass locally while live calls still drifted into stale timing advice, internal labels, or reopened sales logic after terminal stops.

## Scope

This checkpoint adds `runtime/core/dialogue_manager.py` as the manager shell around the existing policy stack.

The first slice is intentionally narrow:

- create a manager state/action/trace contract for live-demo turns
- route existing continuity, anti-loop, duplicate, and stability repairs through one manager action
- derive terminal call control from manager action for stop and schedule confirmations
- preserve the accepted LIVE-DEMO-001 through LIVE-DEMO-013 behavior
- keep the deterministic reasoner and provider enrichment boundaries intact

It does not delete the older policy functions or broad-rewrite sales copy.

## Behavior

Each tested final response now carries a `dialogue_manager` packet with:

- `manager_id`
- `schema_version`
- `state_before`
- `selected_action.action_id`
- `selected_action.template_id`
- `state_after`
- `final_response`
- `call_control`
- `candidate_response_rewrite_count`
- `repair_chain`

Observed live failures are now covered as manager-owned routes:

- soft callback refusal after callback timing ends the call and remains terminal if another input arrives
- call-purpose questions recover the reason for the call instead of stale timing advice
- CRM replacement questions use public RouteSignal wording and continue qualification
- confirmed missed-lead pain routes to the Northstar workflow-review appointment ask
- ASR-shaped `who is harder` clarifies the previous question

## Commands

Validate the manager checkpoint without live microphone, provider ASR, provider TTS, provider LLM calls, or local LLM calls:

```powershell
python scripts\validate_dialogue_manager_001_root_repair.py
```

Run it with the focused live-demo regression stack before committing:

```powershell
python scripts\validate_runtime_manifest.py
python scripts\validate_live_demo_001_agent_voice_call.py
python scripts\validate_live_demo_002_conversation_stability.py
python scripts\validate_live_demo_009_appointment_lead_close.py
python scripts\validate_live_demo_010_live_feedback_route_polish.py
python scripts\validate_live_demo_011_live_followup_stop_and_pain_close.py
python scripts\validate_live_demo_012_soft_stop_and_context_recovery.py
python scripts\validate_live_demo_013_reasoner_route_guard.py
python scripts\validate_dialogue_manager_001_root_repair.py
```

## Evidence

Generated evidence:

- `research/experiments/generated/DIALOGUE-MANAGER-001-root-repair/result.json`
- `research/experiments/generated/DIALOGUE-MANAGER-001-root-repair/report.md`

Private browser transcript JSON files can continue to live under:

```text
data\private\live-demo-003\raw-turns\browser-transcript
```

Do not commit private transcript files from that folder.
