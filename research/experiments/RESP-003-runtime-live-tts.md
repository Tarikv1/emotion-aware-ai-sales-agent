# RESP-003 Runtime Live TTS

## Question

Can the runtime voice-delivery packet be converted into a live-capable TTS packet without weakening guarded response safety?

## Hypothesis

A separate RESP-003 layer can safely prepare or generate provider audio if it:

- consumes only validated RESP-002 packets
- keeps `final_response` unchanged
- defaults to dry-run mode
- requires explicit `--live` before provider calls
- logs provider boundaries and generated-audio asset metadata
- never uploads customer audio
- never stores API keys or raw voice IDs
- never uses voice cloning

## Method

The checkpoint uses the German B2C telecom runtime campaign from `PROD-005`.

Default command:

```powershell
python scripts\generate_runtime_tts_delivery.py `
  --campaign campaign-prod-005-b2c-telecom `
  --stage relevance-check `
  --transcript "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt." `
  --out research/experiments/generated/RESP-003/RESP-003-runtime-live-tts-result.json `
  --report-out research/experiments/generated/RESP-003/RESP-003-runtime-live-tts-report.md
```

Validator:

```powershell
python scripts\validate_resp_003_runtime_live_tts.py
```

## Current Evidence

The validator covers:

- default dry-run mode
- live mode with forced missing-key fallback
- freeform prosody-eligible response using provider-rendered text
- protected do-not-call response using exact `final_response`
- redacted request preview
- environment-only key handling
- generated-audio asset log shape
- no customer audio upload
- no voice cloning
- no secret-like values in generated artifacts

## Result

Current generated result:

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

## First Live Bilingual Result

Two live ElevenLabs calls were run after setting environment-only keys and voice IDs outside Git.

German runtime TTS:

```text
campaign: campaign-prod-005-b2c-telecom
language: de
selected voice env var: ELEVENLABS_VOICE_ID_DE
provider calls made: true
audio file created: true
audio byte size: 119581
HTTP status: 200
time to first audio: 723.09 ms
total provider latency: 901.017 ms
customer audio uploaded: false
voice cloning used: false
API key value logged: false
voice ID value logged: false
validation passed: true
```

English runtime TTS:

```text
campaign: campaign-prod-005-b2b-software
language: en
selected voice env var: ELEVENLABS_VOICE_ID_EN
provider calls made: true
audio file created: true
audio byte size: 112894
HTTP status: 200
time to first audio: 488.206 ms
total provider latency: 670.137 ms
customer audio uploaded: false
voice cloning used: false
API key value logged: false
voice ID value logged: false
validation passed: true
```

Generated MP3 files remain local and ignored by Git. The JSON/Markdown evidence can be committed after secret scanning.

## Human Listening Review

Tarik reviewed the German and English RESP-003 audio on 2026-05-03.

Summary:

```text
The audio is clear and pronunciation is good, but it still sounds obviously AI-generated.
It is too slow for a sales-agent call.
Use with real leads right now: no.
```

Detailed review: `research/experiments/generated/RESP-003/RESP-003-bilingual-human-listening-review.md`

## Interpretation

RESP-003 makes the runtime path live-TTS capable without making provider calls part of the default setup.

This is important because the sales agent now has a clean sequence:

```text
guarded response -> voice delivery -> optional TTS provider call
```

## Limitations

- Dry-run validation does not prove live provider quality.
- Live provider calls still depend on current provider behavior, keys, selected voice IDs, and network latency.
- Human listening review is required before making voice-quality claims.
- The current runtime packet still handles one response segment at a time.

## Next

- Run a live RESP-003 test only when a provider key and voice ID are intentionally set.
- Add playback integration after RESP-003 audio generation is stable.
- Expand from one response segment to multi-segment turns for campaign questions and disclosures.
