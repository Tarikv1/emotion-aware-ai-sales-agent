# LIVE-DEMO-013 Reasoner Route Guard

`LIVE-DEMO-013-reasoner-route-guard` is a narrow follow-up to Tarik's supervised `LIVE-DEMO-012` ElevenLabs listening feedback.

It does not open `PROD-102`, claim production readiness, enable payment collection, create a provider-hosted durable agent, use voice cloning, add provider ASR, install a local LLM, make LLM calls required for live response, or let an LLM write final spoken responses.

## Scope

This checkpoint fixes two live failures without broad-rewriting the runtime:

- a CRM replacement question leaked the internal phrase `fictional profile`
- an ASR-shaped clarification, `who is harder`, was treated as a fresh qualification path instead of a request to explain the previous question

## Behavior

CRM replacement questions now use public product wording and keep the call open:

```text
No. RouteSignal CRM is not meant to replace a CRM that already works. It is worth reviewing only if owner routing, callback reminders, or handoffs still get missed around the CRM. Is that the gap you are checking?
```

Generic CRM integration questions now stay customer-safe without exposing fixture labels:

```text
For Salesforce, someone from Northstar would need to verify exact setup and permissions before I claim fit. The useful check here is simpler: are owner routing, callback reminders, or handoffs still getting missed?
```

ASR-shaped previous-question clarification now explains the prior qualification question:

```text
I meant: an inbound demo request needs one clear owner for the next reply. Can owner, callback, or handoff steps sit waiting?
```

## Architecture Note

`DIALOGUE-REASONER-001` already produced deterministic dialogue-act packets, but `LIVE-DEMO-012` still used them only after final speech for private async enrichment evidence.

`LIVE-DEMO-013` moves deterministic reasoning earlier in the local live-demo turn packet and lets the runtime policy use it only for narrow, high-confidence routes:

- CRM/integration boundary answers
- previous-question clarification when no more specific repair route should win

Specific existing repairs, such as new-trial-request clarification, callback-workflow clarification, value-relevance explanation, buyer-no-question repair, and topic-confusion repair, still take precedence.

## Commands

Validate the checkpoint without live microphone, provider ASR, provider TTS, provider LLM calls, or local LLM calls:

```powershell
python scripts\validate_live_demo_013_reasoner_route_guard.py
```

Run it with the current LIVE-DEMO regression stack before committing:

```powershell
python scripts\validate_live_demo_001_agent_voice_call.py
python scripts\validate_live_demo_002_conversation_stability.py
python scripts\validate_live_demo_008_prosody_review_scope_clarity.py
python scripts\validate_live_demo_009_appointment_lead_close.py
python scripts\validate_live_demo_010_live_feedback_route_polish.py
python scripts\validate_live_demo_011_live_followup_stop_and_pain_close.py
python scripts\validate_live_demo_012_soft_stop_and_context_recovery.py
python scripts\validate_live_demo_013_reasoner_route_guard.py
```

## Acceptance

Synthetic gate:

- provider calls made: `false`
- local LLM calls made: `false`
- CRM replacement answer uses `RouteSignal CRM`, not internal fixture wording
- CRM replacement answer keeps the call open for qualification
- generic integration answers require verified setup review without claiming exact compatibility
- `who is harder` is reasoned as previous-question clarification
- previous-question clarification does not rotate into another scripted qualification line
- `not familiar` after clarification simplifies the workflow check instead of reopening another menu

Human live check:

- asking whether this replaces the current CRM gets a direct, public, customer-safe answer
- no customer-facing speech contains `fictional profile`
- ASR/clarification turns explain the previous question instead of jumping to a different qualification script
- the call continues toward the workflow-gap/appointment-setting path, not full sale or payment closure

## Evidence

Generated evidence:

- `research/experiments/generated/LIVE-DEMO-013-reasoner-route-guard/result.json`
- `research/experiments/generated/LIVE-DEMO-013-reasoner-route-guard/report.md`

Private browser transcript JSON files can continue to live under:

```text
data\private\live-demo-003\raw-turns\browser-transcript
```

Do not commit private transcript files from that folder.
