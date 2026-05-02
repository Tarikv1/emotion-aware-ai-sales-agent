# RESP-002 Runtime Voice Delivery Design

## Goal

Add a runtime delivery layer after `RESP-001` so guarded sales-agent text can be prepared for voice output with segment-aware naturalness, bounded prosody cues, and provider-specific TTS input previews.

## Architecture

`RESP-001` remains the authority for guarded wording. `RESP-002` consumes the `RESP-001` packet, builds delivery segments from the final guarded response, applies the existing VOICE-015 prosody planner, and renders provider-specific text through the existing VOICE-016 adapter.

The layer must not change the customer-facing `final_response`, decision snapshot, call-control, strategy, or guardrail validation result. It adds a `voice_delivery` object for TTS preparation.

## Runtime Flow

```text
customer transcript
  -> realtime decision
  -> RESP-001 guarded response
  -> RESP-002 segment wrapper
  -> VOICE-015 prosody planner
  -> VOICE-016 provider rendering
  -> future live TTS provider
```

## Segment Policy

Freeform objection handling, bridge responses, empathy, clarification, and explanation are eligible for prosody.

Protected text stays exact:

- do-not-call and hang-up lines
- appointment confirmations
- human handoff exact scripts
- claim-boundary and legal/medical/coverage boundary responses
- campaign questions, disclosures, and company scripts if they appear in a later multi-segment response

## Provider Policy

Default provider rendering target is ElevenLabs because VOICE-017 produced the strongest current listening result there. Cartesia remains available through a CLI option.

`RESP-002` is offline by default. It does not call a provider, require an API key, upload customer audio, or create audio.

## Output Shape

The new packet keeps all `RESP-001` fields and adds:

```json
{
  "runtime_voice_delivery_id": "RESP-002-runtime-voice-delivery",
  "voice_delivery": {
    "enabled": true,
    "provider_key": "elevenlabs",
    "final_response_unchanged": true,
    "segments": [],
    "prosody": {},
    "provider_rendering": {},
    "validation": {}
  }
}
```

## Validation

The validator must prove:

- safe price-objection text receives voice delivery metadata
- `final_response` remains unchanged
- provider calls are not made
- customer audio is not uploaded
- eligible freeform responses can receive prosody cues
- do-not-call, scheduling, human request, and claim-boundary responses are protected
- provider tags are not inserted into protected segments
- generated artifacts contain no secret-like values
