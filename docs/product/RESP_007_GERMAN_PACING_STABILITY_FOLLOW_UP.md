# RESP-007 German Pacing Stability Follow-Up

RESP-007 is the narrow follow-up to the RESP-006 German listening decision.

It keeps the same German customer question and the same German answer content. The only editable surface is provider-facing pacing delivery: break tags and bounded voice speed settings.

## Purpose

Tarik's RESP-006 listening result found:

- `old_plain_guarded`: starts a bit too fast and then becomes a bit too slow.
- `new_shaped_runtime`: starts strong but becomes a bit too fast later.

RESP-007 tests whether both can be stabilized without changing voice identity, sales strategy, campaign facts, or answer content.

## Variants

- `old_plain_pacing_stabilized`: starts less rushed with an opening pause guard and uses a slight late-drag prevention speed setting.
- `new_shaped_pacing_stabilized`: keeps the stronger shaped-runtime direction but caps the late speed risk and spaces the later answer.

Both variants use the same synthetic German question from RESP-006 and preserve the same answer content after delivery tags are stripped.

## Boundary

- Default mode is dry-run.
- Live provider calls require `--live`, provider key, selected German voice ID, and bounded timeout.
- No customer audio upload.
- No private raw audio read.
- No transcription.
- No voice cloning.
- API keys and raw voice IDs must not be written to artifacts.
- No quality claim is allowed until Tarik records a human listening review.
- The voice-personality selector remains blocked until RESP-007 is reviewed.

## Commands

Run the dry-run packet:

```powershell
python scripts\run_resp_007_german_pacing_stability_follow_up.py
```

Validate artifact shape, same-answer-content preservation, redaction, and provider boundary:

```powershell
python scripts\validate_resp_007_german_pacing_stability_follow_up.py
```

Default output folder:

```text
research\experiments\generated\RESP-007-german-pacing-stability-follow-up\
```

Live provider execution remains explicit:

```powershell
python scripts\run_resp_007_german_pacing_stability_follow_up.py --provider elevenlabs --live --timeout-seconds 8
```
