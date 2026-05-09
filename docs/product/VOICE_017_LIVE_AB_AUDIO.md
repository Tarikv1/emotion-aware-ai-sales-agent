# VOICE-017 Live A/B Audio

## Purpose

VOICE-017 is a guarded live-capable A/B audio harness.

It compares:

- plain guarded text
- VOICE-016 provider-rendered prosody text

Default mode is dry-run. It makes no provider calls, requires no API key, uploads no customer audio, and creates no audio files.

## Source Artifact

```text
research/experiments/generated/VOICE-016/VOICE-016-provider-prosody-rendering.json
```

## A/B Scope

Selected cases:

- two English cases
- two German cases
- freeform objection handling
- mixed freeform plus protected campaign question/disclosure

Selected providers:

- ElevenLabs
- Cartesia

Selected variants:

- `plain`
- `prosody`

Dry-run produces `16` A/B entries:

```text
4 cases x 2 providers x 2 variants
```

## Safety Model

VOICE-017 keeps provider use behind explicit gates:

- dry-run is default
- live mode requires `--live`
- provider keys and voice IDs are read from environment variables only
- API key and voice ID values are never written to JSON or Markdown
- live `--provider both` is blocked unless `--allow-both-live` is also set
- all provider calls use a bounded timeout of at most `10` seconds
- generated audio files are ignored by Git
- no customer audio is uploaded
- no voice cloning is used
- no audio-quality claim is allowed without human listening review

## Default Dry Run

Run:

```powershell
python scripts\run_voice_017_live_ab_audio.py
```

Validate:

```powershell
python scripts\validate_voice_017_live_ab_audio.py
```

## Live ElevenLabs A/B

Use this when we want to test the likely stronger provider first:

```powershell
$elevenKey = Read-Host "ElevenLabs API key"
$elevenVoiceIdDe = Read-Host "ElevenLabs German voice ID"
$elevenVoiceIdEn = Read-Host "ElevenLabs English voice ID"
Set-Item -Path Env:ELEVENLABS_API_KEY -Value $elevenKey
Set-Item -Path Env:ELEVENLABS_VOICE_ID_DE -Value $elevenVoiceIdDe
Set-Item -Path Env:ELEVENLABS_VOICE_ID_EN -Value $elevenVoiceIdEn

python scripts\run_voice_017_live_ab_audio.py --provider elevenlabs --live --timeout-seconds 8

Remove-Item Env:ELEVENLABS_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:ELEVENLABS_VOICE_ID_DE -ErrorAction SilentlyContinue
Remove-Item Env:ELEVENLABS_VOICE_ID_EN -ErrorAction SilentlyContinue
$elevenKey = $null
$elevenVoiceIdDe = $null
$elevenVoiceIdEn = $null
```

If only one ElevenLabs voice ID is available, use `ELEVENLABS_VOICE_ID` instead of language-specific variables. Language-specific voice IDs are preferred.

## Live Cartesia A/B

Use this if we want to test the richer direct SSML-style rendering:

```powershell
$cartesiaKey = Read-Host "Cartesia API key"
$cartesiaVoiceIdDe = Read-Host "Cartesia German voice ID"
$cartesiaVoiceIdEn = Read-Host "Cartesia English voice ID"
Set-Item -Path Env:CARTESIA_API_KEY -Value $cartesiaKey
Set-Item -Path Env:CARTESIA_VOICE_ID_DE -Value $cartesiaVoiceIdDe
Set-Item -Path Env:CARTESIA_VOICE_ID_EN -Value $cartesiaVoiceIdEn

python scripts\run_voice_017_live_ab_audio.py --provider cartesia --live --timeout-seconds 8

Remove-Item Env:CARTESIA_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:CARTESIA_VOICE_ID_DE -ErrorAction SilentlyContinue
Remove-Item Env:CARTESIA_VOICE_ID_EN -ErrorAction SilentlyContinue
$cartesiaKey = $null
$cartesiaVoiceIdDe = $null
$cartesiaVoiceIdEn = $null
```

## Current Dry-Run Result

```text
cases: 4
German: 2
English: 2
providers: elevenlabs, cartesia
A/B variants: 16
API calls made: 0
audio files created: 0
fallback count: 16
customer audio uploaded: false
voice cloning used: false
human ratings recorded: false
quality claim allowed: false
```

## First Live Listening Result

The first live run used ElevenLabs only with `--limit 2`.

```text
cases: 2
German: 1
English: 1
providers: elevenlabs
A/B variants: 4
API calls made: 4
audio files created: 4
fallback count: 0
customer audio uploaded: false
voice cloning used: false
human ratings recorded: true
quality claim allowed: true, scoped to this two-case ElevenLabs run
```

The project owner listened to the generated plain/prosody pairs and strongly preferred the prosody variants.

Allowed claim:

```text
In the VOICE-017 two-case ElevenLabs live A/B run, prosody-shaped speech was strongly preferred over plain speech by the human listener.
```

Boundary:

- do not generalize this to all providers yet
- do not generalize this to all voices or scripts yet
- do not claim customer preference from one internal listening review

## Generated Artifacts

```text
research/experiments/generated/VOICE-017/VOICE-017-live-ab-audio.json
research/experiments/generated/VOICE-017/VOICE-017-live-ab-audio-report.md
research/experiments/generated/VOICE-017/VOICE-017-human-listening-review.md
```

Live audio files, if generated, are ignored by Git:

```text
research/experiments/generated/VOICE-017-*.mp3
research/experiments/generated/VOICE-017-*.wav
```

## Product Meaning

VOICE-017 is the bridge from safe provider preview to listening evidence.

It should answer the practical question: does prosody-shaped text actually sound more human than plain guarded text, or do the added controls make the voice sound more artificial?
