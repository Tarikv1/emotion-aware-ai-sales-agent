# VOICE-021 ElevenLabs Custom Voice Comparison

## Question

Do the owner-created improved English and German ElevenLabs voices sound better than the first versions when reading sales-agent scripts?

## Method

VOICE-021 compares four local voice candidates:

- `english_v1`
- `english_v2_improved`
- `german_v1`
- `german_v2_improved`

The tracked case file stores candidate labels only. Raw ElevenLabs voice IDs stay in ignored local config.

Case file:

```text
research/experiments/cases/voice-021-elevenlabs-custom-voice-comparison.json
```

Runner:

```text
scripts/run_voice_021_custom_voice_comparison.py
```

Validator:

```text
scripts/validate_voice_021_custom_voice_comparison.py
```

## Scripts

The comparison uses four synthetic spoken-normalized sales scripts:

- English opening plus objection handling
- English empathy plus bridge response
- German opening plus objection handling
- German empathy plus bridge response

Each script is paired only with same-language voice candidates.

## Dry-Run Result

Generated artifacts:

```text
research/experiments/generated/VOICE-021/VOICE-021-custom-voice-comparison.json
research/experiments/generated/VOICE-021/VOICE-021-custom-voice-comparison-report.md
```

Summary:

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

## Live Result

Tarik ran the full live comparison after setting `ELEVENLABS_API_KEY` locally.

Result:

```text
provider calls: 8 / 8
audio files created: 8 / 8
fallbacks: 0
raw voice IDs logged: false
customer audio uploaded: false
voice cloning used: false
max time to first audio: 251.186 ms
max total provider latency: 605.661 ms
```

## Human Listening Review

Tarik's review:

- improved English and German voices are definitely better than the first versions
- pace seems okay
- pitch variation seems okay, but not fully natural yet
- emotional responsiveness may be slightly too high, but still acceptable
- no muffling
- pronunciation seems good
- remaining issue: thinking behavior is not natural enough
- current thinking time is too short
- humans often fill thinking breaks with short fillers such as `um`, `hm`, or language-appropriate equivalents

Interpretation:

- The improved voices should be preferred for the next live tests.
- The next quality target is not simply "more emotion"; it is believable cognitive hesitation.
- A follow-up layer should add controlled thinking fillers inside pauses and slightly longer bounded thinking time for eligible freeform segments.

## Live Test Rule

A live run requires:

- `--live`
- `ELEVENLABS_API_KEY` in the environment
- local voice IDs in `config/local/voice_ids.json`
- `--timeout-seconds` no greater than 10

Quality claims remain blocked until Tarik listens to the generated audio and records ratings.

## Listening Rubric

Rate each sample on:

- first-five-seconds robot sensor
- naturalness
- sales-call pacing
- pace variation
- pitch variation
- emotional responsiveness
- clarity
- language pronunciation
- low muffling or artifacts
- trustworthiness
- sales usefulness
- original vs improved preference
- would use with real leads

## Interpretation

VOICE-021 separates voice identity quality from response-generation quality.

If v2 is clearly better, it can become the default local voice ID for that language. If both versions still sound too robotic, the next step is either another ElevenLabs remix pass or provider/settings experimentation before claiming the voice layer is real-lead ready.
