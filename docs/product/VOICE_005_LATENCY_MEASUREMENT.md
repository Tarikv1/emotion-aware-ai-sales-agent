# VOICE-005 Latency Measurement

## Purpose

VOICE-005 adds the first latency measurement checkpoint for the browser speech demo path.

The goal is to keep the product honest about the speed requirement:

```text
customer finishes speaking
-> transcript is available
-> realtime decision
-> RESP-001 guarded response generation
-> browser can speak the final response
```

## Current Scope

VOICE-005 measures local Python latency after a final transcript already exists.

Measured:

- campaign load
- realtime sales-agent decision
- RESP-001 guarded response generation
- VOICE-001-style response packet build
- response-language routing for active German and English campaigns

Not measured yet:

- browser speech endpointing
- browser speech recognition latency
- browser-to-local-server HTTP overhead
- browser speech synthesis startup
- actual audio playback duration
- production ASR or TTS provider latency

This means VOICE-005 is not the full live-call latency number. It is the first internal decision-loop latency baseline.

## Why This Comes Now

The project already has:

- VOICE-004 browser transcript demo
- RESP-001 guarded response generation
- guarded local server auto-start workflow

VOICE-005 checks whether the local decision path itself is fast before adding heavier components such as production ASR, production TTS, streaming transport, interruption handling, or LLM provider calls.

## Output Contract

VOICE-004 decision packets now include:

```text
latency_measurement
  voice_milestone
  measurement_scope
  server_started
  requires_api_key
  browser_asr_measured
  browser_tts_playback_measured
  target_first_response_ms
  target_tts_start_ms
  total_decision_loop_ms
  observed_bucket
  budget_pass
  segments
```

Segments:

- `campaign_load_ms`
- `realtime_decision_ms`
- `guarded_response_ms`
- `voice_packet_build_ms`

Each latency case also records `expected_response_language` and `response_language`, so latency checks do not accidentally drift back to a single-language runtime path.

## Commands

Validate:

```powershell
python scripts\validate_voice_005_browser_latency.py
```

Generate report:

```powershell
python scripts\measure_voice_005_latency.py
```

## Generated Artifacts

```text
research/experiments/generated/VOICE-005-latency-results.json
research/experiments/generated/VOICE-005-latency-report.md
```

## Current Interpretation

The synthetic local decision-loop cases are well under the 2-second live-response budget.

That is expected because the prototype currently uses deterministic local logic and no provider calls. The important result is not that production latency is solved. The important result is that the core decision path now has a measurable latency contract before more expensive components are added.

VOICE-005 now measures paired German and English active runtime cases:

- German cases: `4`
- English cases: `4`
- Response-language matches: `8 / 8`

## Next Latency Work

Future latency checkpoints should measure:

- browser `/decide` HTTP round trip
- browser ASR finalization time
- browser speech synthesis start delay
- production ASR provider latency
- production TTS provider latency
- LLM candidate wording latency
- timeout and fallback behavior when an external provider is slow
