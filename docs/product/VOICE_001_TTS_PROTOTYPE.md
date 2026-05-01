# VOICE-001 TTS Response Prototype

## Purpose

VOICE-001 is the first voice-layer checkpoint for the vertical-agnostic sales agent.

It does not create a new sales brain. It wraps the existing realtime turn engine:

```text
customer transcript
-> realtime sales-agent decision
-> approved agent_response text
-> neutral synthetic voice packet
```

The reusable sales-agent core still owns emotion detection, sales difficulty classification, strategy selection, escalation, hang-up decisions, and campaign guardrails.

## Why Start With Text-To-Speech

Text-to-speech is the lowest-risk voice milestone because it uses an already-approved `agent_response` and does not require recording, storing, or transcribing customer audio.

VOICE-001 intentionally uses a neutral synthetic test voice. It does not clone a real person, client employee, customer, or public figure.

## Script

```text
scripts/generate_voice_response.py
```

Example dry-run:

```powershell
python scripts\generate_voice_response.py `
  --campaign campaign-prod-005-b2c-telecom `
  --stage relevance-check `
  --transcript "Nur wenn Sie garantieren koennen, dass es stabil ist." `
  --dry-run `
  --out-json research\experiments\generated\VOICE-001-tts-packet.json
```

Dry-run mode writes a deterministic JSON packet and requires no audio provider.

## Packet Contract

The VOICE-001 packet includes:

- `campaign_id`
- campaign metadata
- call stage and transcript
- full realtime decision
- `tts_text`
- neutral synthetic voice metadata
- latency contract
- optional audio output path
- trace metadata

The `tts_text` must equal `decision.agent_response`. This ensures the voice layer speaks the same response that the realtime agent selected.

For active bilingual runtime paths, the packet also carries:

- `campaign.language`
- `decision.campaign_language`
- `decision.response_language`

The voice layer must not translate or switch languages by itself. It speaks the response language selected by the reusable realtime core from the configured `SalesCampaign`.

## Optional Local Audio Output

On Windows, a local test WAV can be generated with the `windows-sapi` provider:

```powershell
python scripts\generate_voice_response.py `
  --campaign campaign-prod-005-b2c-telecom `
  --stage relevance-check `
  --transcript "Nur wenn Sie garantieren koennen, dass es stabil ist." `
  --provider windows-sapi `
  --out-audio research\experiments\generated\VOICE-001-sample.wav `
  --out-json research\experiments\generated\VOICE-001-windows-sapi-packet.json
```

This provider uses the local Windows speech engine and does not require an API key.

## Safety Boundaries

VOICE-001 must not:

- clone a real person's voice
- require an API key
- send customer audio to a cloud provider
- collect microphone input
- record calls
- bypass campaign guardrails
- speak text that is different from the approved `agent_response`

## Validation

Run:

```powershell
python scripts\validate_voice_001_tts.py
```

The validator confirms that dry-run mode produces a voice packet, preserves the realtime decision, uses neutral synthetic voice metadata, and does not write secret-like API key patterns.

## Next Milestones

- VOICE-002: recorded audio input to speech-to-text transcript
- VOICE-003: full spoken turn loop with latency measurement
- VOICE-004: interruption and barge-in behavior
- VOICE-005: telephony/call-center integration assumptions
