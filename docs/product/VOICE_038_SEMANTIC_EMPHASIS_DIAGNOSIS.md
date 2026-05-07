# VOICE-038 Semantic Emphasis Diagnosis

VOICE-038 is a listening checkpoint for the current preferred English ElevenLabs voice.

It does not change runtime behavior. It isolates a narrower issue from Tarik's listening feedback: the voice is now mostly non-robotic, but phrase rhythm and semantic emphasis broke around:

`whether reviewing options is worth your time`

## Purpose

- Keep the current preferred English voice candidate in testing.
- Compare controlled wording and rhythm variants with the same voice.
- Decide whether the remaining issue is wording, phrase chunking, provider emphasis behavior, or the voice itself.
- Avoid adding more filler, pacing randomness, or emotion smoothing before this diagnosis.

## Boundary

- Default mode is dry-run.
- Live provider calls require `--live`.
- API keys stay environment-only.
- Voice IDs stay in environment variables or ignored local config.
- Raw voice IDs and API key values are not written to artifacts.
- No customer audio is uploaded.
- No private call-center data is used.
- No voice cloning is used.
- No runtime behavior changes until Tarik selects a winning variant.

## Variants

VOICE-038 compares:

- Baseline original fragile clause.
- Clear opening with a simpler worth clause.
- Chunked decision phrase with one small break tag.
- Benefit-first wording.
- Semantic focus question.
- Opening alternative.

The goal is not to find "prettier text" in isolation. The goal is to find which phrasing the current voice can deliver naturally, with the right semantic emphasis.

## Run

Dry-run:

```powershell
python scripts\run_voice_038_semantic_emphasis_diagnosis.py
```

Live run after `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID_EN` are set in the current shell:

```powershell
python scripts\run_voice_038_semantic_emphasis_diagnosis.py --live --timeout-seconds 8
```

Forced missing-key fallback:

```powershell
python scripts\run_voice_038_semantic_emphasis_diagnosis.py --live --force-key-missing --timeout-seconds 2
```

Validate:

```powershell
python scripts\validate_voice_038_semantic_emphasis_diagnosis.py
```

## Output

Default output folder:

```text
research\experiments\generated\VOICE-038-semantic-emphasis-diagnosis\
```

Expected files:

- `results.json`
- `report.md`
- `audio\*.mp3` only when live mode succeeds

## Listening Rubric

Tarik should listen for:

- whether the opening sounds clear rather than garbled
- whether the important idea is emphasized naturally
- whether the phrase flows through the worth-your-time idea
- whether the sentence still sounds trustworthy and sales-appropriate
- whether the variant avoids over-scripted or over-emphasized delivery
- whether the wording is good enough to promote into runtime later

## Next Decision

If one variant clearly wins, the next checkpoint can promote the pattern into runtime as a semantic emphasis/rhythm rule.

If none of the variants work with the preferred voice, we should test one or two more English voice candidates before changing the runtime.

## Listening Outcome

Tarik's live listening review on 2026-05-06 found that all six variants sounded good and several steps above earlier English outputs.

Preferred variants:

- `clear_opening_simple_clause`
- `baseline_original_clause`

Interpretation:

- The current preferred English voice should stay in active testing.
- The clear/simple wording pattern is the safest runtime-promotion candidate.
- The baseline original clause remains an acceptable fallback/control because it also sounded good with the new voice.
- More voice hunting is not the default next step unless a later full-runtime check exposes a voice-specific problem.
