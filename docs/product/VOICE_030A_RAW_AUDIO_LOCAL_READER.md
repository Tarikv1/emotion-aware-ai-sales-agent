# VOICE-030A Raw Audio Local Reader

## Purpose

VOICE-030A starts raw-audio learning safely.

It reads local WAV audio and extracts acoustic delivery features such as pause ratio, pause count, speech-burst count, duration, and energy variation. It does not transcribe speech, infer meaning, call providers, clone voices, or apply runtime personalization.

## Boundary

VOICE-030A:

- supports WAV decoding with Python standard library tools
- uses synthetic WAV fixtures by default
- may read private raw audio only with `--allow-private-read`
- keeps private-input outputs inside `data/private/`
- does not transcribe audio
- does not upload audio
- does not call ASR, TTS, LLM, or cloud providers
- does not clone voices
- does not include raw audio paths in public generated reports
- does not auto-apply runtime settings

Current limitation: MP3, M4A, AAC, OGG, FLAC, and WebM are detected as unsupported for this checkpoint. A later checkpoint should add a reviewed local decoder or conversion path if Tarik's recordings are not WAV.

## What It Extracts

For each supported WAV file, the current reader extracts:

- duration
- sample rate
- pause ratio
- pause count
- longest pause
- average pause
- speech-burst count
- mean RMS
- mean speech RMS
- energy variation

These features are useful for learning rhythm and timing from speech without needing transcript text.

## Files

- `scripts/raw_audio_speech_features.py`
- `scripts/run_voice_030_raw_audio_reader.py`
- `scripts/validate_voice_030_raw_audio_reader.py`
- `research/experiments/cases/voice-030-raw-audio-local-reader.json`
- `research/experiments/generated/VOICE-030A-raw-audio-local-reader/results.json`
- `research/experiments/generated/VOICE-030A-raw-audio-local-reader/report.md`

## Commands

Run synthetic fixture:

```powershell
python scripts\run_voice_030_raw_audio_reader.py
```

Validate:

```powershell
python scripts\validate_voice_030_raw_audio_reader.py
```

Run on private WAV recordings:

```powershell
python scripts\run_voice_030_raw_audio_reader.py `
  --input-dir data\private\tarik-speech-samples\raw-audio `
  --allow-private-read
```

## Current Result

The synthetic fixture generated:

```text
audio files: 2
supported files: 2
unsupported files: 0
languages: English and German
total duration: 4.8 seconds
total pause count: 4
private input read: false
raw audio decoded: true
raw private audio decoded: false
provider calls made: false
transcription created: false
voice cloning used: false
runtime profile applied: false
```

## Product Meaning

VOICE-030A gives the project a real raw-audio feature path. It can measure how a speaker pauses, groups speech into bursts, and varies energy without depending on cloud transcription or exposing raw private data.

Later checkpoints can combine these audio features with `VOICE-029` transcript-pattern features to create a reviewed delivery profile.

## Thesis Value

This checkpoint documents the difference between acoustic speech-style learning and transcript/semantic learning.

That distinction matters because the agent can learn delivery timing from raw audio while avoiding identity learning, voice cloning, private facts, and provider upload.

Implementation note: the first parallel validation run exposed a Windows temp-file collision when two processes reused the same synthetic audio folder. The runner now writes process-scoped synthetic audio folders under `.tmp` so validation and generation can run concurrently without deleting a file held by another process.
