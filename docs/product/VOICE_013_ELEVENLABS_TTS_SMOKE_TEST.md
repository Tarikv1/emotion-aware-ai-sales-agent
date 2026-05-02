# VOICE-013 ElevenLabs TTS Smoke Test

## Purpose

VOICE-013 adds a guarded ElevenLabs streaming TTS harness for longer German and English synthetic sales-agent samples.

It does not replace the reusable sales-agent core. It tests another provider adapter so Cartesia and ElevenLabs can later be compared using the same scripts, timing metrics, and human listening rubric.

The default command is safe:

- no provider connection is opened
- no API key is required
- no API key or voice ID is printed
- no customer audio is uploaded
- no generated text is sent to ElevenLabs unless `--live` is explicitly used
- no cloned or custom voice is used
- every provider path has a text-only fallback
- every live run has a bounded timeout
- audio quality is not scored without human listening review

## Why HTTP Streaming First

VOICE-013 uses ElevenLabs' HTTP streaming endpoint first.

The full test script is already available before the request, so HTTP streaming is simpler than WebSocket for this checkpoint. ElevenLabs documents WebSocket as useful when text arrives in chunks or word-to-audio alignment is needed, but notes that it is not always the best choice when the entire input text is available upfront.

Relevant ElevenLabs docs:

- [Stream speech](https://elevenlabs.io/docs/api-reference/text-to-speech/stream)
- [WebSocket](https://elevenlabs.io/docs/api-reference/websocket)
- [Understanding latency](https://elevenlabs.io/docs/eleven-api/concepts/latency)

## Cases

VOICE-013 uses four longer synthetic samples:

- two German samples
- two English samples
- the same plain quality scripts used for the Cartesia VOICE-011 comparison path
- no customer transcript or real call audio
- no insurance-specific promises or sensitive personal data

## Provider Defaults

Current defaults:

```text
endpoint: https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream
model: eleven_flash_v2_5
output_format: mp3_44100_128
enable_logging: false
```

`enable_logging=false` is requested to keep the smoke test privacy-oriented. ElevenLabs documents zero-retention behavior for that parameter, with account-plan limitations. If a live test fails because the account does not support that mode, the result should be recorded rather than silently weakening the privacy setting.

## Default Dry Run

Run without a key:

```powershell
python scripts\run_voice_013_elevenlabs_tts_smoke.py
```

Validate:

```powershell
python scripts\validate_voice_013_elevenlabs_tts_smoke.py
```

The validator checks:

- default dry-run mode
- simulated live mode with missing key
- two German and two English cases
- no provider API calls during validation
- no audio files during validation
- redacted request previews
- text-only fallback
- language-specific voice ID env gates
- human listening review remains required before quality claims

## Live Smoke Run

Only after obtaining an ElevenLabs key and selecting voices:

```powershell
$elevenKey = Read-Host "ElevenLabs API key"
$elevenVoiceIdDe = Read-Host "ElevenLabs German voice ID"
$elevenVoiceIdEn = Read-Host "ElevenLabs English voice ID"
Set-Item -Path Env:ELEVENLABS_API_KEY -Value $elevenKey
Set-Item -Path Env:ELEVENLABS_VOICE_ID_DE -Value $elevenVoiceIdDe
Set-Item -Path Env:ELEVENLABS_VOICE_ID_EN -Value $elevenVoiceIdEn

python scripts\run_voice_013_elevenlabs_tts_smoke.py --live --timeout-seconds 8

Remove-Item Env:ELEVENLABS_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:ELEVENLABS_VOICE_ID_DE -ErrorAction SilentlyContinue
Remove-Item Env:ELEVENLABS_VOICE_ID_EN -ErrorAction SilentlyContinue
$elevenKey = $null
$elevenVoiceIdDe = $null
$elevenVoiceIdEn = $null
```

If only one voice ID is available, use `ELEVENLABS_VOICE_ID` instead of the language-specific variables. Language-specific IDs are preferred for the quality comparison.

## Known Live Provider Constraint

The first live attempt reached ElevenLabs but returned HTTP `402` with provider error code `paid_plan_required` for all four cases.

Observed provider message:

```text
Free users cannot use library voices via the API. Please upgrade your subscription to use this voice.
```

Meaning:

- the harness reached the provider and made four API calls
- no audio files were created
- no customer audio was uploaded
- no API key or voice ID values were written to artifacts
- the selected library voices appear to require a paid-compatible ElevenLabs setup

The next live attempt should use either an account/plan that allows the selected voices through the API or voice IDs that are permitted on the current account.

## Current Live Result

A later live run succeeded with the selected ElevenLabs voices.

Summary:

- API calls made: `4`
- audio files created: `4`
- fallback count: `0`
- HTTP status: `200`
- max time to first audio byte: `507.54 ms`
- max total provider latency: `1112.927 ms`
- customer audio uploaded: `false`
- API key and voice ID values logged: `false`

Initial listening impression:

- there is room for improvement
- ElevenLabs sounds much better than the previous provider audio

This is still not a final provider decision. It is an informal listening result that should be followed by structured Cartesia-vs-ElevenLabs scoring.

## Live Output

A successful live run should create up to four local MP3 files:

```text
research/experiments/generated/VOICE-013-*.mp3
```

Those MP3 files are ignored by Git.

The JSON and Markdown report should record:

- API calls made
- time to first audio byte
- total provider latency
- audio byte count
- fallback reason, if any
- whether human listening review has been recorded

## Quality Review Boundary

VOICE-013 can measure timing automatically, but it cannot judge whether German sounds natural, whether English sounds more human than Cartesia, or whether the delivery fits a sales call.

Audio-quality comparison requires:

1. a live provider run,
2. generated MP3 files,
3. human listening review,
4. ratings on naturalness, clarity, pronunciation, pacing, muffling/artifacts, emotional appropriateness, and trustworthiness.

Until those ratings exist, the report must not claim that ElevenLabs is better or worse than Cartesia.

## Product Meaning

VOICE-013 keeps the architecture vertical-agnostic:

- same reusable sales-agent core
- same configurable `SalesCampaign` profiles
- same bilingual runtime checks
- ElevenLabs only as a guarded TTS adapter
- no customer audio upload
- no voice cloning

The next provider step should compare Cartesia and ElevenLabs using the same scripts, then add a controlled comparison between plain guarded text and VOICE-012 naturalized text.
