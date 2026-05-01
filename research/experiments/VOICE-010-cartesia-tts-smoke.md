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

The committed generated result now records the second live Cartesia bytes-endpoint smoke run using a German-suitable voice ID:

- cases: `2`
- German cases: `1`
- English cases: `1`
- API calls made: `2`
- audio files created: `2`
- fallback count: `0`
- response-language matches: `2 / 2`
- TTS text matches decision: `2 / 2`
- German time to first audio byte: `1035.629 ms`
- German total provider latency: `2411.314 ms`
- English time to first audio byte: `347.719 ms`
- English total provider latency: `1504.563 ms`

The first live run used an English-oriented voice ID for both languages:

- German time to first audio byte: `1083.043 ms`
- German total provider latency: `2532.073 ms`
- English time to first audio byte: `366.492 ms`
- English total provider latency: `1499.783 ms`

Initial listening impression:

- the generated audio sounded acceptable for a first smoke test
- the clips are short, so the quality judgment is weak evidence
- the German-suitable voice ID sounded better for German than the first voice
- the German-suitable voice still sounded a little muffled

## Interpretation

VOICE-010 proves the Cartesia adapter can be prepared safely before any secret is introduced, then used for a bounded live smoke test after local key setup.

It also avoids repeating the earlier long-running shell problem by requiring a bounded timeout for provider requests.

English met the `500 ms` TTS-start target in both bytes-endpoint tests. German did not.

The German voice-ID rerun improved German latency slightly and improved subjective German quality, but it did not solve the latency target or remove all quality concerns.

This should be interpreted carefully. The bytes endpoint is useful for first provider access and audio-file generation, but WebSocket streaming is the more relevant path for low-latency voice-agent speech.

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

This checkpoint used very short audio samples.

Further work is still required to answer:

- whether German pronunciation remains acceptable on longer sales responses
- whether English voice quality remains acceptable on longer sales responses
- whether WebSocket first-audio timing fits the call-center latency budget
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
