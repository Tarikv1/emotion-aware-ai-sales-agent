# VOICE-029 Local Speech Profile Learning

## Purpose

VOICE-029 starts the local-only path for learning abstract delivery patterns from Tarik's speech style without training on raw audio, exporting private transcripts, cloning a voice, or calling a provider.

This is not runtime personalization yet. It creates a reviewable draft profile that can later inform campaign-level voice settings after human review.

## Boundary

VOICE-029:

- uses synthetic fixtures by default
- may read reviewed local redacted transcripts only with `--allow-private-read`
- keeps private-input outputs inside `data/private/`
- does not read raw audio
- does not transcribe audio yet
- does not call ASR, TTS, LLM, or cloud providers
- does not clone voices
- does not export raw transcript examples
- does not auto-apply the profile to runtime behavior

Private workspace:

```text
data/private/tarik-speech-samples/
  raw-audio/
  transcripts-redacted/
  derived/
  reviewed-patterns/
  quarantine/
```

The folder is ignored by Git through the existing `data/private/.gitignore` rule.

## What It Extracts

The current profile extracts abstract aggregate signals:

- filler/discourse marker frequency
- repair and rephrase marker frequency
- English contraction count
- pause marker count from text notation
- average words per sentence
- language-level summaries for English and German

It does not include raw examples. Common marker labels such as `so`, `okay`, `also`, or `ich meine` may appear as aggregate marker names, but source sentences and private details do not.

## Files

- `scripts/personal_speech_profile.py`
- `scripts/run_voice_029_local_speech_profile.py`
- `scripts/validate_voice_029_local_speech_profile.py`
- `scripts/init_personal_speech_learning_workspace.py`
- `research/experiments/cases/voice-029-local-speech-profile-learning.json`
- `research/experiments/generated/VOICE-029-local-speech-profile-learning/results.json`
- `research/experiments/generated/VOICE-029-local-speech-profile-learning/report.md`

## Commands

Run synthetic public fixture:

```powershell
python scripts\run_voice_029_local_speech_profile.py
```

Validate:

```powershell
python scripts\validate_voice_029_local_speech_profile.py
```

Preview private workspace folders:

```powershell
python scripts\init_personal_speech_learning_workspace.py --dry-run
```

Create private workspace folders:

```powershell
python scripts\init_personal_speech_learning_workspace.py
```

Run on local redacted transcripts:

```powershell
python scripts\run_voice_029_local_speech_profile.py `
  --input-dir data\private\tarik-speech-samples\transcripts-redacted `
  --allow-private-read
```

## Current Result

The synthetic fixture generated:

```text
samples: 4
languages: English and German
private input read: false
raw audio read: false
provider calls made: false
voice cloning used: false
raw transcript exported: false
apply to runtime by default: false
human review required before runtime use: true
```

## Product Meaning

This checkpoint creates the bridge between subjective owner speech feedback and safe runtime tuning.

It lets the project learn from how Tarik naturally explains ideas, but only as abstract style features. Later checkpoints may map reviewed profile outputs into `speech_realism`, `speech_interaction`, or `speech_imperfections` campaign settings.

## Thesis Value

VOICE-029 records the privacy-preserving difference between:

- raw speech data
- redacted local transcripts
- abstract speech-pattern profiles
- reviewed runtime configuration

That distinction matters for the thesis because it keeps the personalization path honest: the system can learn delivery tendencies without claiming to learn identity, private facts, or a cloned voice.
