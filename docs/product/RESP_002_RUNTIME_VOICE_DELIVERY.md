# RESP-002 Runtime Voice Delivery

## Purpose

RESP-002 connects guarded response generation to the voice delivery stack.

It is still vertical-agnostic:

```text
SalesCampaign + realtime decision + guarded response
  -> runtime voice delivery
  -> future TTS provider
```

The first provider preview target is ElevenLabs because VOICE-017 showed a strong human preference for prosody-shaped speech in the first two-case live A/B run.

## Layer Position

```text
customer transcript
  -> realtime sales-agent policy core
  -> RESP-001 guarded response generation
  -> RESP-002 runtime voice delivery
  -> future live TTS provider
```

RESP-002 does not replace RESP-001. It consumes the guarded final response and adds delivery metadata.

## What RESP-002 Adds

The output keeps all RESP-001 fields and adds:

```text
runtime_voice_delivery_id
voice_delivery.segments
voice_delivery.prosody
voice_delivery.provider_rendering
voice_delivery.validation
```

The main safety invariant:

```text
final_response stays unchanged
```

## Segment Policy

Eligible for prosody:

- freeform objection handling
- freeform clarification
- freeform bridge responses
- freeform empathy
- freeform explanations

Protected from prosody:

- do-not-call and hang-up lines
- appointment confirmations
- human handoff exact scripts
- claim-boundary responses
- required disclosures
- campaign qualification questions
- company-provided scripts

## Provider Policy

RESP-002 is offline by default.

It does not:

- call ElevenLabs
- call Cartesia
- require API keys
- upload customer audio
- create audio files
- clone voices

It only produces provider-ready text/request previews.

## Default Command

```powershell
python scripts\generate_runtime_voice_delivery.py `
  --campaign campaign-prod-005-b2c-telecom `
  --stage relevance-check `
  --transcript "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt." `
  --out research\experiments\generated\RESP-002-runtime-voice-delivery-result.json `
  --report-out research\experiments\generated\RESP-002-runtime-voice-delivery-report.md
```

Validate:

```powershell
python scripts\validate_resp_002_runtime_voice_delivery.py
```

## Current Result

The current generated artifact uses a German B2C telecom price-objection turn.

Result:

```text
provider preview: elevenlabs
final_response_unchanged: true
provider_calls_made: false
requires_api_key: false
customer_audio_uploaded: false
voice_cloning_used: false
validation passed: true
prosody cues: 2
provider tags in protected segments: 0
```

## Product Meaning

RESP-002 is the bridge from safe text response to realistic voice output.

This keeps the architecture clean:

- policy decides what can be said
- RESP-001 decides guarded wording
- RESP-002 decides how the approved wording should be delivered by voice
- live TTS remains a separate explicit provider step
