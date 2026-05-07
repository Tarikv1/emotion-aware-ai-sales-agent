# VOICE-040 Low-Pressure Focus

VOICE-040 converts one risky provider-facing phrase from the VOICE-039 runtime check into a calmer low-pressure wording.

It changes provider-facing TTS text only. It does not change the guarded `final_response`.

## Purpose

Tarik's VOICE-039 listening review found that the selected English voice is now strong enough to keep using, but the phrase:

```text
You don't need to change anything today
```

can invite wrong emphasis on `you`, `don't`, `anything`, or `today`.

VOICE-040 rewrites this only for eligible English freeform provider-facing speech:

```text
No changes needed today
```

This keeps the same low-pressure sales meaning while reducing the number of tempting emphasis targets.

## Runtime Position

```text
RESP-001 guarded response
  -> RESP-002 voice delivery
  -> VOICE-039 semantic emphasis candidate
  -> VOICE-040 low-pressure focus
  -> RESP-003 live-capable TTS
```

## Boundary

Allowed:

- English freeform provider-facing TTS wording
- the specific low-pressure phrase correction from the VOICE-039 listening review
- offline validation by default
- optional live listening check with explicit `--live`

Forbidden:

- changing `final_response`
- changing call control, strategy, appointment, or handoff decisions
- changing protected campaign, compliance, handoff, hangup, or do-not-call text
- rewriting German text
- adding product claims
- uploading customer/private audio
- voice cloning
- logging API keys or raw voice IDs

## Run

Dry-run:

```powershell
python scripts\run_voice_040_low_pressure_focus.py
```

Validate:

```powershell
python scripts\validate_voice_040_low_pressure_focus.py
```

Live listening check after `ELEVENLABS_API_KEY` and an English voice ID are available in the current shell or ignored local config:

```powershell
python scripts\run_voice_040_low_pressure_focus.py --live --provider elevenlabs --limit-cases 1 --timeout-seconds 8
```

## Output

Default output folder:

```text
research\experiments\generated\VOICE-040-low-pressure-focus\
```

Expected files:

- `result.json`
- `report.md`
- `audio\*.mp3` only when live mode succeeds

## Current Result

The dry-run validation checks three cases:

- longer English full-runtime candidate
- protected do-not-call lock
- German language lock

Expected result:

```text
low-pressure rewrites: 1
protected rewrites: 0
final response changes: 0
provider calls made by default: false
audio files created by default: 0
validation passed: true
```

## Human Listening Check

The next live review should use the preferred English voice and judge:

- whether `No changes needed today` avoids the wrong emphasis heard in VOICE-039
- whether the longer guarded response still sounds natural
- whether the phrase sounds professional instead of evasive or scripted
- whether the current voice candidate remains strong enough for the MVP voice track
