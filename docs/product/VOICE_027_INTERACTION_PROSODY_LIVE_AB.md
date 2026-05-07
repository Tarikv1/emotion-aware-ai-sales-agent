# VOICE-027 Interaction Prosody Live A/B

## Purpose

VOICE-027 is the live-capable listening harness for `VOICE-026`.

It compares:

- `voice_025_baseline`: current boundary-aware speech realism without VOICE-026 interaction prosody
- `with_voice_026`: the same voice, script, and provider settings with lookup acknowledgements, neutral backchannels, and bounded sales-pace cues enabled

The goal is to isolate whether VOICE-026 makes the agent sound more responsive and human without making it over-emotional, falsely agreeable, or less trustworthy.

## Safety Boundary

Default mode is dry-run.

Live audio requires:

- `--live`
- `ELEVENLABS_API_KEY` in the current shell
- local ignored voice IDs in `config/local/voice_ids.json`
- timeout no higher than 10 seconds

The checkpoint does not:

- write API keys to files
- print API keys
- write raw voice IDs to JSON or Markdown
- upload customer audio
- use private call-center audio
- clone voices
- make audio-quality claims before human listening review

## What It Tests

The case set covers four scripts:

- English lookup-latency acknowledgement
- English unsafe-claim neutral backchannel
- German lookup-latency acknowledgement
- German unsafe-claim neutral backchannel with protected campaign question

Both variants keep:

- `VOICE-022` spoken text normalization
- `VOICE-023/025` speech realism and boundary-aware filler placement
- provider-neutral prosody rendering
- same improved English/German ElevenLabs voice candidates

Only VOICE-026 changes between variants.

## Commands

Dry-run:

```powershell
python scripts\run_voice_027_interaction_prosody_live_ab.py
```

Validate:

```powershell
python scripts\validate_voice_027_interaction_prosody_live_ab.py
```

Live limited English run:

```powershell
python scripts\run_voice_027_interaction_prosody_live_ab.py --live --language en --limit-scripts 1 --timeout-seconds 8
```

Live limited German run:

```powershell
python scripts\run_voice_027_interaction_prosody_live_ab.py --live --language de --limit-scripts 1 --timeout-seconds 8
```

Default output folder:

```text
research/experiments/generated/VOICE-027-interaction-prosody-live-ab/
```

Audio output folder in live mode:

```text
research/experiments/generated/VOICE-027-interaction-prosody-live-ab/audio/
```

## Listening Rubric

Listen to `voice_025_baseline` first and `with_voice_026` second for each script.

Use the rubric in the generated report:

- first-five-seconds robot sensor
- naturalness
- trust
- confidence
- warmth
- sales-call pacing
- pace variation
- thinking-time realism
- backchannel placement
- latency-acknowledgement usefulness
- unsafe-agreement safety
- pitch variation
- emotional responsiveness
- clarity
- language pronunciation
- low muffling or artifacts
- sales usefulness
- baseline vs VOICE-026 preference
- would use with real leads

## Current Status

The dry-run validator checks:

- four bilingual scripts
- two variants per script
- no provider call by default
- forced-missing-key live fallback
- no customer/private audio upload
- no voice cloning
- no raw local voice ID leakage
- no protected segment changes
- no unsafe agreement markers
- VOICE-026 marker count only in the `with_voice_026` variant

## Human Listening Review

Tarik ran limited live English/German audio and reported that the VOICE-027 outputs sound much better than before.

Interpretation:

- keep the VOICE-026 interaction-prosody direction
- do not broaden marker/filler changes yet
- tune pacing next

Remaining issue:

- pacing needs more tuning so the agent sounds energetic and sales-ready without becoming rushed

## Thesis Relevance

VOICE-027 turns the VOICE-026 runtime layer into a listening experiment.

It supports thesis evidence by keeping the comparison controlled:

- same provider
- same voice
- same script
- same speech-realism baseline
- one isolated interaction-prosody variable
- explicit no-claim rule until human listening review exists
