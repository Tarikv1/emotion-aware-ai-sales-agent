# VOICE-011 Cartesia WebSocket Smoke Test

## Purpose

VOICE-011 adds a guarded Cartesia WebSocket TTS harness for longer German and English synthetic sales-agent samples.

It does not replace the reusable sales-agent core. It tests the audio adapter layer that may later speak an approved agent response.

The default command is safe:

- no provider connection is opened
- no API key is required
- no API key or voice ID is printed
- no customer audio is uploaded
- no generated text is sent to Cartesia unless `--live` is explicitly used
- no cloned or custom voice is used
- every provider path has a text-only fallback
- every live run has a bounded timeout
- audio quality is not scored without human listening review

## Why WebSocket

VOICE-010 proved the basic Cartesia bytes endpoint. VOICE-011 moves to WebSocket because it is closer to the live voice-agent path:

- the socket can stay open across turns
- text can be sent in chunks as an LLM or response generator emits it
- one context can represent one agent utterance
- audio chunks can be measured as they arrive
- timestamps can be requested
- connection setup can be separated from first-audio timing in future runs

Relevant Cartesia docs:

- [Text to Speech WebSocket](https://docs.cartesia.ai/api-reference/tts/websocket)
- [Realtime Text to Speech Quickstart](https://docs.cartesia.ai/get-started/realtime-text-to-speech-quickstart)
- [Compare TTS Endpoints](https://docs.cartesia.ai/use-the-api/compare-tts-endpoints)
- [Sonic 3](https://docs.cartesia.ai/build-with-cartesia/tts-models/sonic-3)

## Cases

VOICE-011 uses four longer synthetic samples:

- two German samples
- two English samples
- objection-handling and bridge/handoff language
- no customer transcript or real call audio
- no insurance-specific promises or sensitive personal data

The German scripts intentionally include normal German characters such as umlauts because pronunciation quality cannot be tested honestly with only ASCII transliteration.

## Default Dry Run

Run without a key:

```powershell
python scripts\run_voice_011_cartesia_websocket_smoke.py
```

Validate:

```powershell
python scripts\validate_voice_011_cartesia_websocket_smoke.py
```

The validator checks:

- default dry-run mode
- simulated live mode with missing key
- two German and two English cases
- no provider WebSocket connections during validation
- no audio files during validation
- redacted request previews
- text-only fallback
- human listening review remains required before quality claims

## Live Smoke Run

Only after obtaining a Cartesia key and selecting voices:

```powershell
$cartesiaKey = Read-Host "Cartesia API key"
$cartesiaVoiceIdDe = Read-Host "Cartesia German voice ID"
$cartesiaVoiceIdEn = Read-Host "Cartesia English voice ID"
Set-Item -Path Env:CARTESIA_API_KEY -Value $cartesiaKey
Set-Item -Path Env:CARTESIA_VOICE_ID_DE -Value $cartesiaVoiceIdDe
Set-Item -Path Env:CARTESIA_VOICE_ID_EN -Value $cartesiaVoiceIdEn

python scripts\run_voice_011_cartesia_websocket_smoke.py --live --timeout-seconds 8

Remove-Item Env:CARTESIA_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:CARTESIA_VOICE_ID_DE -ErrorAction SilentlyContinue
Remove-Item Env:CARTESIA_VOICE_ID_EN -ErrorAction SilentlyContinue
$cartesiaKey = $null
$cartesiaVoiceIdDe = $null
$cartesiaVoiceIdEn = $null
```

If only one voice ID is available, use `CARTESIA_VOICE_ID` instead of the language-specific variables. Language-specific IDs are preferred for the quality comparison.

## Live Output

A successful live run should create up to four local WAV files:

```text
research/experiments/generated/VOICE-011-*.wav
```

Those WAV files are ignored by Git.

The JSON and Markdown report should record:

- WebSocket connection attempts
- time to first audio chunk
- total stream latency
- audio chunk count
- timestamp event count
- fallback reason, if any
- whether human listening review has been recorded

## Quality Review Boundary

VOICE-011 can measure timing automatically, but it cannot judge whether German sounds muffled, whether English pacing feels natural, or whether the emotional delivery fits a sales call.

Audio-quality comparison requires:

1. a live provider run,
2. generated WAV files,
3. human listening review,
4. ratings on naturalness, clarity, pronunciation, pacing, muffling/artifacts, and emotional appropriateness.

Until those ratings exist, the report must not claim that one voice or provider is better.

## Product Meaning

VOICE-011 keeps the architecture vertical-agnostic:

- same reusable sales-agent core
- same configurable SalesCampaign profiles
- same bilingual runtime checks
- Cartesia only as a guarded TTS adapter
- no customer audio upload
- no voice cloning

The longer scripts are synthetic quality samples. They are useful for provider evaluation, not a replacement for runtime response generation.

## Next Work

After the live run:

- listen to all four generated WAV files
- record German and English ratings
- compare plain guarded text against VOICE-012 naturalized text
- compare WebSocket first-audio timing with the `500 ms` target
- decide whether Cartesia remains the first TTS candidate
- test ElevenLabs only if Cartesia quality or latency is not convincing
