# VOICE-010: Cartesia TTS Smoke Test

## Objective

Add a guarded Cartesia Sonic 3 TTS smoke harness before requesting or using an API key.

## Method

The checkpoint adds:

- a Cartesia-specific case file
- a Cartesia bytes-endpoint smoke runner
- a validator that exercises dry-run and missing-key live fallback paths
- generated JSON and Markdown reports
- `.gitignore` protection for generated WAV files

The default command makes no provider call.

The live command requires:

- `--live`
- `CARTESIA_API_KEY`
- `CARTESIA_VOICE_ID`
- timeout no greater than `10` seconds

## Current Result

The committed generated result is dry-run:

- cases: `2`
- German cases: `1`
- English cases: `1`
- API calls made: `0`
- audio files created: `0`
- fallback count: `2`
- response-language matches: `2 / 2`
- TTS text matches decision: `2 / 2`

## Interpretation

VOICE-010 proves the Cartesia adapter can be prepared safely before any secret is introduced.

It also avoids repeating the earlier long-running shell problem by requiring a bounded timeout for provider requests.

## Safety Notes

The harness does not log:

- API key values
- voice ID values
- authorization headers

It does log:

- whether a live call was requested
- whether provider calls were made
- whether audio files were created
- fallback reason
- latency metadata when live calls occur

Generated audio files are machine-local artifacts and are ignored by Git.

## Known Limitation

This checkpoint has not yet measured Cartesia audio quality or latency because no API key has been used.

A live run is still required to answer:

- whether German pronunciation is good enough
- whether English voice quality is good enough
- whether the measured first-audio timing fits the call-center latency budget
- whether the selected voice is appropriate for both German and English

## Commands

Default dry run:

```powershell
python scripts\run_voice_010_cartesia_tts_smoke.py
```

Validation:

```powershell
python scripts\validate_voice_010_cartesia_tts_smoke.py
```

Live run after local key setup:

```powershell
python scripts\run_voice_010_cartesia_tts_smoke.py --live --timeout-seconds 8
```
