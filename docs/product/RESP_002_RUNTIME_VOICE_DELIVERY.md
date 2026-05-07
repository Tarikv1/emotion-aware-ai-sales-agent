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
voice_delivery.core_delivery_pack
voice_delivery.segments
voice_delivery.spoken_segments
voice_delivery.realistic_segments
voice_delivery.interaction_segments
voice_delivery.imperfect_segments
voice_delivery.spoken_text_normalization
voice_delivery.speech_realism
voice_delivery.speech_interaction
voice_delivery.speech_imperfections
voice_delivery.prosody
voice_delivery.voice_pacing_calibration
voice_delivery.voice_connected_speech
voice_delivery.voice_listening_calibration
voice_delivery.voice_emotion_smoothing
voice_delivery.voice_semantic_emphasis
voice_delivery.voice_low_pressure_focus
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

Eligible freeform text may also receive spoken-text normalization, speech-realism/filler placement, interaction-prosody shaping, opt-in controlled imperfections, provider prosody, `VOICE-034` pacing calibration, `VOICE-035` connected speech, `VOICE-036` listening calibration, `VOICE-037` emotion-transition smoothing, `VOICE-039` semantic-emphasis wording candidates, and `VOICE-040` low-pressure focus correction before live TTS. This lets `I will` become `I'll` in English or `Ich habe` become `Ich hab` in German for provider-facing TTS text, while allowing bounded lookup acknowledgements, neutral backchannels, pace cues, professional sentence-boundary imperfections, tighter provider break/speed settings, connected phrase flow, weak-emphasis filtering, smoother emotional inertia, one controlled English clear/simple wording candidate, and one low-pressure phrase correction only where safe.

Protected from prosody:

- do-not-call and hang-up lines
- appointment confirmations
- human handoff exact scripts
- claim-boundary responses
- required disclosures
- campaign qualification questions
- company-provided scripts

## Core Delivery Pack

RESP-002 attaches the core delivery intelligence pack metadata. The pack improves provider-facing speech planning while keeping `final_response` unchanged.

The pack allows observable empathy and delivery shaping. It blocks hidden emotional certainty claims and protected text rewrites.

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

## Bilingual Voice Parity

English and German delivery quality should improve in parallel. RESP-002 therefore has a paired local parity check:

```powershell
python scripts\run_resp_002_bilingual_voice_parity.py
python scripts\validate_resp_002_bilingual_voice_parity.py
```

The parity check requires one English and one German freeform sales response to show concrete spoken-text normalization, prosody cues, pacing calibration, emotion smoothing, provider-rendering changes, and preserved protected-text boundaries. Counts do not need to match exactly because English and German speech mechanics differ.

## Current Result

The current generated artifact uses a German B2C telecom price-objection turn.

Result:

```text
provider preview: elevenlabs
final_response_unchanged: true
spoken_text_normalization validation: true
speech_interaction validation: true
speech_imperfections validation: true
voice pacing calibration validation: true
voice connected speech validation: true
voice listening calibration validation: true
voice emotion smoothing validation: true
voice semantic emphasis validation: true
voice low-pressure focus validation: true
provider_calls_made: false
requires_api_key: false
customer_audio_uploaded: false
voice_cloning_used: false
validation passed: true
prosody cues: 2
VOICE-034 pacing calibrated: true
VOICE-035 connected speech applied: true
VOICE-036 listening calibration applied: true
VOICE-037 emotion smoothing applied: true
VOICE-039 semantic emphasis rewrites: 0 for the default German turn
VOICE-040 low-pressure focus rewrites: 0 for the default German turn
provider tags in protected segments: 0
```

## Product Meaning

RESP-002 is the bridge from safe text response to realistic voice output.

This keeps the architecture clean:

- policy decides what can be said
- RESP-001 decides guarded wording
- RESP-002 decides how the approved wording should be spoken and delivered by voice, including spoken normalization, bounded speech realism, interaction prosody, opt-in controlled imperfections, provider preview rendering, pacing calibration, connected speech, listening calibration, emotion-transition smoothing, controlled semantic-emphasis candidates, and low-pressure focus corrections
- live TTS remains a separate explicit provider step
