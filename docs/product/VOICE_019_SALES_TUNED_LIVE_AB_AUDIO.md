# VOICE-019 Sales-Tuned Live A/B Audio

## Purpose

VOICE-019 prepares the next listening test:

```text
VOICE-017-style prosody-shaped input
versus
VOICE-018 professional-sales tuned input
```

The goal is to test whether the sales-tuned input sounds faster, less flat, and more human without losing clarity or trust.

Default mode is dry-run. Live provider calls require explicit opt-in.

## Source Artifacts

VOICE-019 reads:

```text
research/experiments/generated/VOICE-018/VOICE-018-sales-voice-tuning.json
research/experiments/cases/voice-017-live-ab-audio.json
```

The first file provides the prosody and sales-tuned text variants. The second file provides the already-reviewed provider configuration, endpoint rules, environment variable names, and provider safety boundaries.

## A/B Variants

Variant A:

```text
prosody
```

This is the VOICE-017-style provider-rendered prosody input.

Variant B:

```text
sales_tuned
```

This is the VOICE-018 professional-sales tuned provider input.

The default case set uses the same four bilingual cases as VOICE-017:

- 2 German cases
- 2 English cases
- ElevenLabs and Cartesia provider variants

## Safety Model

VOICE-019 inherits the VOICE-017 live-provider discipline:

- dry-run is default
- live mode requires `--live`
- provider keys and voice IDs are read from environment variables only
- API key and voice ID values are never written to JSON or Markdown
- live `--provider both` is blocked unless `--allow-both-live` is also set
- all provider calls use a bounded timeout of at most `10` seconds
- generated VOICE-019 audio files are ignored by Git
- no customer audio is uploaded
- no voice cloning is used
- no audio-quality claim is allowed without human listening review

## Current Dry-Run Result

```text
cases: 4
German cases: 2
English cases: 2
providers: elevenlabs, cartesia
A/B variants: 16
prosody variants: 8
sales-tuned variants: 8
API calls made: 0
audio files created: 0
fallback count: 16
customer audio uploaded: false
voice cloning used: false
human ratings recorded: false
quality claim allowed: false
```

## Commands

Dry run:

```powershell
python scripts\run_voice_019_sales_tuned_live_ab_audio.py
```

Validate dry-run and forced-missing-key fallback:

```powershell
python scripts\validate_voice_019_sales_tuned_live_ab_audio.py
```

Live ElevenLabs A/B:

```powershell
$elevenKey = Read-Host "ElevenLabs API key"
$elevenVoiceIdDe = Read-Host "ElevenLabs German voice ID"
$elevenVoiceIdEn = Read-Host "ElevenLabs English voice ID"
Set-Item -Path Env:ELEVENLABS_API_KEY -Value $elevenKey
Set-Item -Path Env:ELEVENLABS_VOICE_ID_DE -Value $elevenVoiceIdDe
Set-Item -Path Env:ELEVENLABS_VOICE_ID_EN -Value $elevenVoiceIdEn

python scripts\run_voice_019_sales_tuned_live_ab_audio.py --provider elevenlabs --live --timeout-seconds 8 --limit 2

Remove-Item Env:ELEVENLABS_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:ELEVENLABS_VOICE_ID_DE -ErrorAction SilentlyContinue
Remove-Item Env:ELEVENLABS_VOICE_ID_EN -ErrorAction SilentlyContinue
$elevenKey = $null
$elevenVoiceIdDe = $null
$elevenVoiceIdEn = $null
```

If only one ElevenLabs voice ID is available, use `ELEVENLABS_VOICE_ID` instead of language-specific variables. Language-specific voice IDs are preferred.

Live Cartesia A/B:

```powershell
$cartesiaKey = Read-Host "Cartesia API key"
$cartesiaVoiceIdDe = Read-Host "Cartesia German voice ID"
$cartesiaVoiceIdEn = Read-Host "Cartesia English voice ID"
Set-Item -Path Env:CARTESIA_API_KEY -Value $cartesiaKey
Set-Item -Path Env:CARTESIA_VOICE_ID_DE -Value $cartesiaVoiceIdDe
Set-Item -Path Env:CARTESIA_VOICE_ID_EN -Value $cartesiaVoiceIdEn

python scripts\run_voice_019_sales_tuned_live_ab_audio.py --provider cartesia --live --timeout-seconds 8 --limit 2

Remove-Item Env:CARTESIA_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:CARTESIA_VOICE_ID_DE -ErrorAction SilentlyContinue
Remove-Item Env:CARTESIA_VOICE_ID_EN -ErrorAction SilentlyContinue
$cartesiaKey = $null
$cartesiaVoiceIdDe = $null
$cartesiaVoiceIdEn = $null
```

## Generated Artifacts

- `research/experiments/cases/voice-019-sales-tuned-live-ab-audio.json`
- `research/experiments/generated/VOICE-019/VOICE-019-sales-tuned-live-ab-audio.json`
- `research/experiments/generated/VOICE-019/VOICE-019-sales-tuned-live-ab-audio-report.md`

Live audio outputs use the ignored pattern:

```text
research/experiments/generated/VOICE-019-*.mp3
research/experiments/generated/VOICE-019-*.wav
```

## Product Meaning

VOICE-019 is the bridge from offline sales-voice tuning to human listening evidence. It lets us test whether the new professional-sales pacing actually sounds better in provider audio instead of assuming it from text metadata.
