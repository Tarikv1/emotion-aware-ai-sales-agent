# VOICE-013 ElevenLabs TTS Smoke

## Objective

Prepare a safe ElevenLabs TTS provider harness so the project can compare ElevenLabs against Cartesia without leaking secrets, uploading customer audio, or confusing provider quality with product architecture.

## Method

The experiment uses the ElevenLabs streaming TTS endpoint in dry-run mode by default:

```text
synthetic quality script
  -> redacted ElevenLabs request preview
  -> text-only fallback unless --live and env gates are present
```

Live mode requires:

- `--live`
- `ELEVENLABS_API_KEY`
- `ELEVENLABS_VOICE_ID_DE` and `ELEVENLABS_VOICE_ID_EN`, or fallback `ELEVENLABS_VOICE_ID`
- bounded timeout

## Case File

```text
research/experiments/cases/voice-013-elevenlabs-tts-smoke.json
```

The cases mirror the longer VOICE-011 Cartesia scripts:

- German objection handling
- German bridge and handoff
- English B2B objection handling
- English scheduling and close

## Current Dry-Run Result

Generated artifacts:

```text
research/experiments/generated/VOICE-013/VOICE-013-elevenlabs-tts-smoke.json
research/experiments/generated/VOICE-013/VOICE-013-elevenlabs-tts-smoke-report.md
```

Current summary:

- cases: `4`
- German cases: `2`
- English cases: `2`
- live call requested: `false`
- API calls made: `0`
- audio files created: `0`
- fallback count: `4`
- response-language matches: `4 / 4`
- quality script language matches: `4 / 4`
- customer audio uploaded: `false`
- generated text sent to provider: `false`

## First Live Attempt

The first live attempt reached ElevenLabs but did not create audio files.

Live summary:

- live call requested: `true`
- API calls made: `4`
- audio files created: `0`
- fallback count: `4`
- HTTP status: `402`
- provider error code: `paid_plan_required`
- provider message: `Free users cannot use library voices via the API. Please upgrade your subscription to use this voice.`
- customer audio uploaded: `false`
- API key and voice ID values logged: `false`

Interpretation:

- the ElevenLabs key was accepted far enough to reach provider authorization/business-rule handling
- the selected voice IDs appear to be library voices that require a paid plan for API use
- no audio-quality or latency comparison can be made from this run because no audio was returned
- the next live attempt needs either a paid-compatible voice/account setup or a voice ID allowed by the current account

## Second Live Attempt

The second live attempt produced audio files.

Live summary:

- live call requested: `true`
- API calls made: `4`
- audio files created: `4`
- fallback count: `0`
- HTTP status: `200`
- max time to first audio byte: `507.54 ms`
- max total provider latency: `1112.927 ms`
- customer audio uploaded: `false`
- API key and voice ID values logged: `false`

Generated local MP3 files:

- `research/experiments/generated/VOICE-013/VOICE-013-C01-de-elevenlabs-stream.mp3`
- `research/experiments/generated/VOICE-013/VOICE-013-C02-de-elevenlabs-stream.mp3`
- `research/experiments/generated/VOICE-013/VOICE-013-C03-en-elevenlabs-stream.mp3`
- `research/experiments/generated/VOICE-013/VOICE-013-C04-en-elevenlabs-stream.mp3`

User listening impression:

- there is still room for improvement
- ElevenLabs sounded much better than the previous provider audio

Interpretation:

- ElevenLabs should remain a serious provider candidate
- one German case slightly exceeded the `500 ms` first-audio target by `7.54 ms`
- total provider latency was substantially shorter than the Cartesia WebSocket total stream timings from `VOICE-011`
- provider quality needs a structured listening rubric before making a final recommendation

## Interpretation

VOICE-013 is ready for structured comparison against Cartesia and for a follow-up naturalized-text test using VOICE-012.

The default path proves:

- the provider adapter can be prepared without a key
- request previews redact API keys and voice IDs
- the live run must be explicit
- language-specific voice selection is first-class
- human listening remains required before any provider quality claim

## Limitation

The current listening result is an informal first impression, not a formal evaluation.

The next experiment should record:

- side-by-side Cartesia vs ElevenLabs ratings
- plain text vs VOICE-012 naturalized text ratings
- German and English quality differences
- whether rare fillers improve human-likeness without reducing trust
