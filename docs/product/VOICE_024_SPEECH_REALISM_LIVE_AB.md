# VOICE-024 Speech Realism Live A/B Harness

## Purpose

VOICE-024 isolates the audible effect of VOICE-023.

It compares the same improved English or German ElevenLabs custom voice in two variants:

- `without_voice_023`: spoken-text normalization plus prosody/provider rendering
- `with_voice_023`: spoken-text normalization plus VOICE-023 speech realism plus prosody/provider rendering

The goal is to hear whether bounded thinking fillers, protected-text locks, and prosody bundles make the agent feel more live without making it casual, overacted, or unsafe.

## Safety Boundary

Default mode is dry-run.

Live audio requires:

- explicit `--live`
- `ELEVENLABS_API_KEY` in the current shell
- local voice IDs in ignored `config/local/voice_ids.json`
- timeout of no more than 10 seconds

Forbidden:

- API keys in tracked files
- raw voice IDs in generated JSON or Markdown
- private customer audio
- voice cloning
- audio-quality claims before human listening review

## Active Voice IDs

The tracked case file stores only local config keys:

- `elevenlabs.candidates.english_v2_improved`
- `elevenlabs.candidates.german_v2_improved`

Actual IDs stay in `config/local/voice_ids.json`, which is ignored by Git.

## Dry-Run Command

```powershell
python scripts\run_voice_024_speech_realism_live_ab.py
```

Validate dry-run and forced missing-key behavior:

```powershell
python scripts\validate_voice_024_speech_realism_live_ab.py
```

## Live Listening Command

Run this only in the terminal where `ELEVENLABS_API_KEY` is set:

```powershell
python scripts\run_voice_024_speech_realism_live_ab.py --live --timeout-seconds 8
```

Generated MP3 files are local machine artifacts under `research/experiments/generated/VOICE-024-speech-realism-live-ab/audio/` and are ignored by Git.

## Listening Rubric

Rate each A/B pair on:

- first-five-seconds robot sensor
- naturalness
- sales-call pacing
- pace variation
- thinking-time realism
- filler usefulness
- pitch variation
- emotional responsiveness
- clarity
- language pronunciation
- low muffling or artifacts
- trustworthiness
- sales usefulness
- without VOICE-023 vs with VOICE-023 preference
- would use with real leads

## Thesis Meaning

VOICE-024 turns subjective listening feedback into an ablation test:

```text
same custom voice
same synthetic script
same provider
same timeout and safety boundary
only VOICE-023 changes
```

This supports the thesis by separating provider voice quality from the local speech-realism layer.

## Artifacts

Implementation:

- `scripts/run_voice_024_speech_realism_live_ab.py`
- `scripts/validate_voice_024_speech_realism_live_ab.py`
- `research/experiments/cases/voice-024-speech-realism-live-ab.json`

Generated artifacts:

- `research/experiments/generated/VOICE-024-speech-realism-live-ab/results.json`
- `research/experiments/generated/VOICE-024-speech-realism-live-ab/report.md`
- `research/experiments/generated/VOICE-024-speech-realism-live-ab/audio/`
