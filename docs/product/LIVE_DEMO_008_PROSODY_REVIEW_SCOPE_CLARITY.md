# LIVE-DEMO-008 Prosody Review Scope Clarity

`LIVE-DEMO-008-prosody-review-scope-clarity` is a narrow follow-up to Tarik's supervised `LIVE-DEMO-007` listening feedback.

It does not open `PROD-102`, claim production readiness, add provider ASR, enable payment collection, create a provider-hosted durable agent, use voice cloning, add spoken backchannels, make LLM calls required for live response, or let an LLM write final spoken responses.

## Scope

This checkpoint fixes two live-demo defects:

- ElevenLabs provider text must not insert a break inside tight product phrases such as `callback reminders` or `owner and reminder`
- callback-gap follow-up responses must not ask the buyer to decide internal workflow-review mechanics
- the agent should state the review scope itself, then ask whether that buyer gap is worth checking or, after `LIVE-DEMO-009`, move to an appointment-setting next step when the buyer has already confirmed the gap

The fix keeps provider calls disabled by default in validation. It changes deterministic runtime wording and provider-rendered TTS metadata only.

## Behavior

Before this checkpoint, the provider-rendered TTS could contain text like:

```text
callback <break ... /> reminders
```

That made the voice pause between words that should be spoken together. `LIVE-DEMO-008` keeps sales-target pause metadata only when the target lands on a punctuation or sentence boundary. If the target is followed by another word, the runtime falls back to sentence or clause pauses instead of splitting the phrase.

Before this checkpoint, callback follow-up text could ask:

```text
Would a short workflow review focus only on that gap?
```

That puts internal review-scope responsibility on the buyer. The runtime now states the scope, for example that the review would focus on missed callback reminders, and then asks whether that buyer gap is the right one to check.

## Commands

Validate the checkpoint without live microphone, provider ASR, provider TTS, or provider LLM calls:

```powershell
python scripts\validate_live_demo_008_prosody_review_scope_clarity.py
```

Run it with the existing LIVE-DEMO regression stack before committing:

```powershell
python scripts\validate_live_demo_001_agent_voice_call.py
python scripts\validate_live_demo_007_human_transcript_plain_qualification.py
python scripts\validate_live_demo_008_prosody_review_scope_clarity.py
```

## Acceptance

Synthetic gate:

- provider calls made: `false`
- no `callback <break ... /> reminders`
- no `callback reminders <break ... /> are`
- no `owner <break ... /> and reminder`
- no "would a short workflow review focus only on that gap"
- no "should I keep the review..." as a buyer-facing internal-scope question
- the agent states what the review would do before asking a buyer-relevant confirmation or appointment-setting next step

Human live check:

- `callback reminders` is spoken as one phrase
- the agent explains what a workflow review would focus on instead of asking the customer to know it
- follow-up questions feel buyer-relevant, not like internal product configuration; after a confirmed gap, an appointment-setting ask is acceptable

## Evidence

Generated evidence:

- `research/experiments/generated/LIVE-DEMO-008-prosody-review-scope-clarity/result.json`
- `research/experiments/generated/LIVE-DEMO-008-prosody-review-scope-clarity/report.md`

Private browser transcript JSON files can continue to live under:

```text
data\private\live-demo-003\raw-turns\browser-transcript
```

Do not commit private transcript files from that folder.
