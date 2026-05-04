# RESP-003 Runtime Live TTS

## Purpose

RESP-003 connects the guarded runtime voice-delivery packet to optional live TTS audio generation.

It keeps the product architecture vertical-agnostic:

```text
SalesCampaign + realtime decision + guarded response
  -> RESP-002 runtime voice delivery
  -> RESP-003 runtime live-capable TTS
  -> playback or generated audio review
```

## Layer Position

```text
customer transcript
  -> realtime sales-agent policy core
  -> RESP-001 guarded response generation
  -> RESP-002 runtime voice delivery
  -> RESP-003 live-capable TTS delivery
```

RESP-003 does not decide what the agent is allowed to say. It only prepares or generates audio from text that has already passed the guarded response and runtime voice-delivery layers.

## Default Rule

RESP-003 is dry-run by default.

Default mode:

- does not call ElevenLabs
- does not call Cartesia
- does not require API keys
- does not upload customer audio
- does not clone voices
- does not create audio files
- still writes JSON/Markdown evidence

Live provider calls require:

- explicit `--live`
- provider-specific environment variables
- timeout no higher than 10 seconds
- local provider boundary review in `VOICE_PROVIDER_RUN_BOUNDARY.md`
- generated-audio asset logging in the result packet

## Text Selection

RESP-003 receives a RESP-002 packet and selects TTS input safely:

- freeform prosody-eligible text can use `voice_delivery.provider_rendering.rendered_text`
- provider-rendered text may include VOICE-022 spoken normalization, such as English contractions or conservative German spoken forms
- protected text uses `final_response`
- do-not-call, human handoff, claim-boundary, hang-up, appointment confirmation, campaign questions, and compliance statements do not get provider prosody tags

The invariant remains:

```text
final_response stays unchanged
```

## Provider Boundary

RESP-003 records:

- provider
- model
- endpoint type
- API key environment variable name
- selected voice ID environment variable name
- live-call flag
- timeout
- redacted request preview
- provider fallback reason
- audio output path when created
- generated-audio asset log

It does not record:

- raw API keys
- raw voice IDs
- customer audio
- private call audio
- voice-cloning material

## Default Command

```powershell
python scripts\generate_runtime_tts_delivery.py `
  --campaign campaign-prod-005-b2c-telecom `
  --stage relevance-check `
  --transcript "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt." `
  --out research\experiments\generated\RESP-003-runtime-live-tts-result.json `
  --report-out research\experiments\generated\RESP-003-runtime-live-tts-report.md
```

Validate:

```powershell
python scripts\validate_resp_003_runtime_live_tts.py
```

## Live Command Shape

ElevenLabs:

```powershell
python scripts\generate_runtime_tts_delivery.py `
  --campaign campaign-prod-005-b2c-telecom `
  --stage relevance-check `
  --transcript "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt." `
  --provider elevenlabs `
  --live `
  --timeout-seconds 8
```

Cartesia:

```powershell
python scripts\generate_runtime_tts_delivery.py `
  --campaign campaign-prod-005-b2c-telecom `
  --stage relevance-check `
  --transcript "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt." `
  --provider cartesia `
  --live `
  --timeout-seconds 8
```

## Current Result

The current generated artifact uses a German B2C telecom price-objection turn in dry-run mode.

Result:

```text
provider: elevenlabs
live_call_requested: false
provider_calls_made: false
generated_text_sent_to_provider: false
audio_file_created: false
fallback_reason: dry-run-mode
customer_audio_uploaded: false
voice_cloning_used: false
validation passed: true
```

## First Live Bilingual ElevenLabs Run

The first live RESP-003 ElevenLabs run created one German and one English audio file.

Technical result:

```text
German campaign: campaign-prod-005-b2c-telecom
German voice env var: ELEVENLABS_VOICE_ID_DE
German audio created: true
German time to first audio: 723.09 ms
German total provider latency: 901.017 ms

English campaign: campaign-prod-005-b2b-software
English voice env var: ELEVENLABS_VOICE_ID_EN
English audio created: true
English time to first audio: 488.206 ms
English total provider latency: 670.137 ms

customer audio uploaded: false
voice cloning used: false
API key value logged: false
voice ID value logged: false
validation passed: true
```

Audio quality is not claimed from this technical run. Human listening review is still required.

## First Human Listening Review

Tarik reviewed the German and English RESP-003 audio on 2026-05-03.

Review summary:

```text
The audio sounds okay and clarity/pronunciation are good.
The voices still sound obviously AI-generated.
The delivery is too slow for a sales-agent call.
Naturalness, pitch, and emotion need improvement.
Use with real leads right now: no.
```

Detailed review: `research/experiments/generated/RESP-003-bilingual-human-listening-review.md`

## Product Meaning

RESP-003 is the first runtime bridge where the safe agent response can become audio.

The separation is intentional:

- policy and campaign guardrails decide what can be said
- RESP-001 writes guarded text
- RESP-002 shapes delivery metadata and provider input
- RESP-003 optionally calls a TTS provider with explicit opt-in
- human listening review is still required before claiming voice quality
