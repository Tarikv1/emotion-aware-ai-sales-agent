# VOICE-005 Browser Latency Measurement

## Experiment Goal

Measure the local decision-loop latency for the browser speech demo after a final transcript is available.

VOICE-005 does not start a server. It uses the same one-shot VOICE-004 decision path that powers the browser demo and records local Python segment timings.

## Command

```powershell
python scripts\validate_voice_005_browser_latency.py
```

The validator calls:

```powershell
python scripts\measure_voice_005_latency.py
```

## Cases

VOICE-005 measures four transcript types:

- `VOICE-005-C01`: price objection fast path
- `VOICE-005-C02`: claim-boundary escalation fast path
- `VOICE-005-C03`: product-detail lookup bridge path
- `VOICE-005-C04`: unknown-signal follow-up path

## Measured Segments

- `campaign_load_ms`: local SalesCampaign load
- `realtime_decision_ms`: deterministic classification and call-control decision
- `guarded_response_ms`: RESP-001 guarded response generation and validation
- `voice_packet_build_ms`: response packet build for browser playback

## Safety And Scope

VOICE-005 remains no-key and local:

- no API key required
- no LLM provider call
- no production ASR call
- no production TTS call
- no server started during validation

Browser ASR and browser TTS playback are not measured in this checkpoint.

## Current Result

Generated artifacts:

```text
research/experiments/generated/VOICE-005-latency-results.json
research/experiments/generated/VOICE-005-latency-report.md
```

Current generated summary:

- cases: `4`
- maximum local decision-loop latency: under `1 ms`
- over-2s cases: `0`
- budget pass count: `4 / 4`

## Interpretation

The local deterministic decision loop is not the latency bottleneck in the current prototype.

The next important latency risks are outside this measurement scope:

- browser speech recognition finalization
- local HTTP round trip
- real TTS startup
- future LLM provider latency
- future production ASR/TTS provider latency

VOICE-005 gives us a baseline before those slower components are added.
