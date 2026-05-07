# VOICE-039 Runtime Semantic Emphasis

VOICE-039 promotes the preferred `VOICE-038` clear/simple wording pattern into the full runtime voice path as a controlled candidate.

It changes provider-facing TTS text only. It does not change the guarded `final_response`.

## Purpose

Tarik's VOICE-038 listening review preferred two variants:

- `clear_opening_simple_clause`
- `baseline_original_clause`

VOICE-039 promotes the clear/simple pattern first because it is shorter, less abstract, and less likely to trigger awkward provider emphasis:

```text
The practical next step is to check whether reviewing options is worth your time
```

becomes provider-facing TTS wording like:

```text
We can quickly check if a review is worth your time
```

The original guarded response remains available as the baseline/control.

## Runtime Position

```text
RESP-001 guarded response
  -> RESP-002 voice delivery
  -> VOICE-037 emotion smoothing
  -> VOICE-039 semantic emphasis candidate
  -> RESP-003 live-capable TTS
```

## Boundary

Allowed:

- English freeform provider-facing TTS wording
- the specific VOICE-038 clear/simple worth-your-time pattern
- offline validation by default
- optional live RESP-003 check with explicit `--live`

Forbidden:

- changing `final_response`
- changing call control or strategy
- changing protected campaign, compliance, handoff, hangup, or do-not-call text
- rewriting German text
- adding product claims
- uploading customer/private audio
- voice cloning
- logging API keys or raw voice IDs

## Run

Dry-run:

```powershell
python scripts\run_voice_039_runtime_semantic_emphasis.py
```

Validate:

```powershell
python scripts\validate_voice_039_runtime_semantic_emphasis.py
```

Live listening check after `ELEVENLABS_API_KEY` and an English voice ID are available in the current shell or ignored local config:

```powershell
python scripts\run_voice_039_runtime_semantic_emphasis.py --live --provider elevenlabs --limit-cases 1 --timeout-seconds 8
```

## Output

Default output folder:

```text
research\experiments\generated\VOICE-039-runtime-semantic-emphasis\
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
semantic rewrites: 1
protected rewrites: 0
final response changes: 0
provider calls made by default: false
audio files created by default: 0
validation passed: true
```

A live-gated run in a shell without `ELEVENLABS_API_KEY` should safely produce:

```text
live_call_requested: true
provider_calls_made: false
audio_files_created: 0
fallback_reason: missing-elevenlabs-api-key
```

## Human Listening Check

Tarik's VOICE-039 live listening review found that the preferred English voice is now good enough to keep working with, and the main bottleneck is no longer the voice identity itself.

The remaining issue was phrase-level emphasis. In particular, the sentence `You don't need to change anything today` could put emphasis on the wrong word even when the rest of the longer script sounded good.

Follow-up: `VOICE-040` adds a narrower provider-facing low-pressure focus correction for that phrase while keeping this semantic-emphasis layer intact.

Future reviews should continue to judge:

- whether the promoted wording still sounds natural inside the full guarded response
- whether emphasis lands on the meaning, not on weak abstract words
- whether connected speech, pacing, and emotion smoothing still work together
- whether the baseline/control wording is still needed
