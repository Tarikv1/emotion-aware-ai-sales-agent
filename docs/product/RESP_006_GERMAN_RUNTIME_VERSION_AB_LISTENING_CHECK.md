# RESP-006 German Runtime Version A/B Listening Check

## Purpose

RESP-006 is the German counterpart to RESP-005.

It compares the old plain guarded runtime against the newer shaped runtime on the same longer German buyer objection before the project turns the accepted English variants into selectable voice-personality profiles.

German needs its own check because pacing, formality, filler, and "sales call" naturalness can shift when the same runtime style is spoken in Deutsch.

## Variants

- `old_plain_guarded`: the older `RESP-001` guarded German `final_response` sent directly to TTS.
- `new_shaped_runtime`: the current `RESP-002` / `VOICE-044` provider-ready German rendering, sent through the same `RESP-003` TTS boundary.

Both variants answer the same synthetic German customer question.

## Listening Outcome

Tarik did not accept either German variant yet. Both are close, but both need pacing revision.

- `old_plain_guarded`: starts a bit too fast, then becomes a bit too slow.
- `new_shaped_runtime`: starts strong, then becomes a bit too fast later in the answer.

The product implication is that German needs a narrow pacing-stability pass before these variants feed the voice-personality selector.

Decision artifact:

```text
research\experiments\generated\RESP-006-german-runtime-version-ab-listening-check\human-listening-decision.md
```

## Boundary

- Default mode is dry-run.
- Live provider calls require `--live`, provider key, selected German voice ID, and bounded timeout.
- No customer audio upload.
- No private raw audio read.
- No transcription.
- No voice cloning.
- API keys and raw voice IDs must not be written to artifacts.
- No German voice-personality claim is allowed until the pacing revision is reviewed.

## Commands

Run the dry-run packet:

```powershell
python scripts\run_resp_006_german_runtime_version_ab_listening_check.py
```

Validate artifact shape, German-only case coverage, redaction, and provider boundary:

```powershell
python scripts\validate_resp_006_german_runtime_version_ab_listening_check.py
```

Default output folder:

```text
research\experiments\generated\RESP-006-german-runtime-version-ab-listening-check\
```

Live provider execution remains explicit:

```powershell
python scripts\run_resp_006_german_runtime_version_ab_listening_check.py --provider elevenlabs --live --timeout-seconds 8
```
