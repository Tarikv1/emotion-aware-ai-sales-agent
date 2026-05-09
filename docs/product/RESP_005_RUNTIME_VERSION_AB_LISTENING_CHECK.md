# RESP-005 Runtime Version A/B Listening Check

## Purpose

RESP-005 creates one same-question A/B packet for judging the old runtime voice path against the newer shaped runtime path.

The case uses a longer answer so pacing, transitions, contractions, and AI-obviousness are easier to hear than in a short one-sentence sample.

## Variants

- `old_plain_guarded`: the older `RESP-001` guarded `final_response` sent directly to TTS.
- `new_shaped_runtime`: the current `RESP-002` / `VOICE-044` provider-ready rendering, sent through the same `RESP-003` TTS boundary.

Both variants answer the same synthetic customer question.

## Listening Outcome

Tarik accepted both variants as useful voice personality directions rather than choosing one universal winner.

- `old_plain_guarded`: natural, real, laid-back salesperson direction.
- `new_shaped_runtime`: more serious and lower-energy direction.

The product implication is that voice should become a bounded style/personality selector. Future tests should compare campaign fit and listener preference instead of treating every voice change as a single quality ladder.

Decision artifact:

```text
research\experiments\generated\RESP-005-runtime-version-ab-listening-check\human-listening-decision.md
```

## Boundary

- Default mode is dry-run.
- Live provider calls require `--live`, provider key, selected voice ID, and bounded timeout.
- No customer audio upload.
- No private raw audio read.
- No transcription.
- No voice cloning.
- API keys and raw voice IDs must not be written to artifacts.
- No production-wide quality claim is allowed from this single listening review.

## Commands

Run the dry-run packet:

```powershell
python scripts\run_resp_005_runtime_version_ab_listening_check.py
```

Validate artifact shape, same-question coverage, redaction, and provider boundary:

```powershell
python scripts\validate_resp_005_runtime_version_ab_listening_check.py
```

Default output folder:

```text
research\experiments\generated\RESP-005-runtime-version-ab-listening-check\
```

Live provider execution remains explicit:

```powershell
python scripts\run_resp_005_runtime_version_ab_listening_check.py --provider elevenlabs --live --timeout-seconds 8
```
