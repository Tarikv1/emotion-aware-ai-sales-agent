# VOICE-021 ElevenLabs Custom Voice Comparison

## Purpose

VOICE-021 compares owner-created ElevenLabs voices for the sales-agent voice layer.

It compares:

- English v1 original
- English v2 improved
- German v1 original
- German v2 improved

The improved voices are expected to reflect the ElevenLabs remix/naturalness prompts created in `VOICE-020`.

## Privacy And Config Boundary

Raw voice IDs do not belong in tracked files.

They live in:

```text
config/local/voice_ids.json
```

That file is ignored by Git.

Tracked VOICE-021 files reference only safe candidate IDs:

```text
english_v1
english_v2_improved
german_v1
german_v2_improved
```

API keys remain environment-only through `ELEVENLABS_API_KEY`.

## What It Tests

VOICE-021 uses synthetic, spoken-normalized sales scripts.

The scripts are designed to reveal:

- whether the first few seconds trigger a "robot voice" feeling
- whether the improved version has better naturalness
- whether pacing is still too stable
- whether pitch and emotional responsiveness improved
- whether the German voice sounds less muffled or telephone-like
- whether the English and German voices are sales-useful

## Default Dry Run

```powershell
python scripts\run_voice_021_custom_voice_comparison.py
```

This writes:

```text
research/experiments/generated/VOICE-021/VOICE-021-custom-voice-comparison.json
research/experiments/generated/VOICE-021/VOICE-021-custom-voice-comparison-report.md
```

Dry run makes no provider calls and creates no audio.

## Live Run

Set the API key in the current PowerShell session:

```powershell
$elevenKey = Read-Host -AsSecureString "ElevenLabs API key"
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($elevenKey)
$plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
Set-Item -Path Env:ELEVENLABS_API_KEY -Value $plain
[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
Remove-Variable plain
```

Then run:

```powershell
python scripts\run_voice_021_custom_voice_comparison.py --live --timeout-seconds 8
```

To start smaller:

```powershell
python scripts\run_voice_021_custom_voice_comparison.py --live --language en --limit-scripts 1 --timeout-seconds 8
python scripts\run_voice_021_custom_voice_comparison.py --live --language de --limit-scripts 1 --timeout-seconds 8
```

## Validation

```powershell
python scripts\validate_voice_021_custom_voice_comparison.py
```

The validator checks:

- 4 voice candidates
- 4 listening scripts
- 8 planned comparison outputs
- no provider calls in default mode
- no raw voice IDs in generated artifacts
- no API keys in generated artifacts
- no customer audio upload
- no voice cloning

## Current Dry-Run Result

```text
candidates: 4
scripts: 4
results: 8
German results: 4
English results: 4
provider calls made: 0
audio files created: 0
raw voice IDs logged: false
customer audio uploaded: false
voice cloning used: false
quality claim allowed: false
```

## First Live Listening Result

The full VOICE-021 live comparison created all 8 audio samples successfully.

```text
provider calls: 8 / 8
audio files created: 8 / 8
fallbacks: 0
raw voice IDs logged: false
customer audio uploaded: false
voice cloning used: false
max total provider latency: 605.661 ms
```

Human review:

- improved English and German voices are clearly better than the first versions
- pace is acceptable
- pitch variation is acceptable but not fully natural yet
- emotional responsiveness may be slightly too high
- muffling was not detected
- pronunciation is good
- next gap: thinking-time realism and hesitation behavior

The next voice target is controlled thinking fillers inside pauses, not random filler injection.

## Product Meaning

VOICE-021 lets us compare the actual created voices before committing to one default English voice and one default German voice.

It also keeps the voice-agent workflow clean:

- ElevenLabs creates/remixes the base voice
- VOICE-022 improves provider-facing spoken text
- VOICE-015/016 shape rhythm and provider rendering
- VOICE-021 tests whether the chosen voice is good enough for real sales use
