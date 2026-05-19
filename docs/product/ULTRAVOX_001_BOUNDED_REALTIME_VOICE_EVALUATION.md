# ULTRAVOX-001 Bounded Realtime Voice Evaluation

## Purpose

ULTRAVOX-001 evaluates UltraVox as a realtime voice candidate for this sales-agent architecture without changing runtime behavior.

This is not `PROD-102`, not a production promotion, and not live provider approval.

## Scope

This evaluation answers one question:

```text
Can UltraVox reduce the live voice latency stack while preserving our guarded sales-agent runtime as the source of truth?
```

It compares four architecture choices:

- `ultravox-hosted-api-provider-adapter`
- `ultravox-hosted-console-agent`
- `ultravox-open-source-self-host-lane`
- `current-resp003-tts-bridge-baseline`

## Current Recommendation

First bounded evaluation:

```text
ultravox-hosted-api-provider-adapter
```

Reason:

- it can test the hosted realtime voice stack quickly
- it keeps this repository as the source of truth for policy, protected text, campaign logic, and evidence
- it avoids making an UltraVox console agent the durable product runtime

Self-hosting remains a research lane:

```text
ultravox-open-source-self-host-lane
```

That lane offers stronger long-term control, but it is not the smallest first experiment because it needs local serving, streaming, voice output or TTS, latency measurement, and observability work before it can replace the hosted realtime stack.

Do not productize first:

```text
ultravox-hosted-console-agent
```

That path is the fastest demo shape, but it moves prompt and dialogue ownership into the provider surface. It is a weak fit for protected-text exactness, deterministic policy evidence, and checkpoint-driven product control.

Baseline control:

```text
current-resp003-tts-bridge-baseline
```

RESP-003 remains the baseline until UltraVox proves a measurable latency and quality gain against the same guarded response contract.

## Hard Gates

ULTRAVOX-001:

- makes no UltraVox API calls
- uploads no audio
- requires no API key
- stores no provider secret
- uses no customer audio
- uses no voice cloning
- creates no durable UltraVox console agent
- moves no sales policy, protected text, campaign logic, or acceptance evidence out of this repository
- does not open `PROD-102`

## Live Next Gate

A future live UltraVox test needs a separate explicit approval.

Minimum live-test boundary:

- `ULTRAVOX_API_KEY` only from environment
- one synthetic call only
- no customer audio
- no voice cloning
- no durable provider-side agent as product runtime
- no uploaded corpus or private campaign data
- timeout guardrails
- provider retention/deletion review
- generated JSON/Markdown evidence
- clear comparison against the RESP-003 baseline

## Commands

Generate the dry-run evaluation:

```powershell
python scripts\evaluate_ultravox_001_bounded_realtime_voice.py `
  --cases research\experiments\cases\ultravox-001-bounded-realtime-voice-evaluation.json `
  --out research\experiments\generated\ULTRAVOX-001\ULTRAVOX-001-bounded-realtime-voice-evaluation.json `
  --report-out research\experiments\generated\ULTRAVOX-001\ULTRAVOX-001-bounded-realtime-voice-evaluation-report.md
```

Validate the dry-run evaluation boundary:

```powershell
python scripts\validate_ultravox_001_bounded_realtime_voice.py
```

## Generated Artifacts

```text
research/experiments/generated/ULTRAVOX-001/ULTRAVOX-001-bounded-realtime-voice-evaluation.json
research/experiments/generated/ULTRAVOX-001/ULTRAVOX-001-bounded-realtime-voice-evaluation-report.md
```

## Product Meaning

UltraVox is not treated as the sales-agent brain.

The safe evaluation shape is:

```text
customer audio
  -> UltraVox realtime voice session
  -> constrained tool call / adapter boundary
  -> local guarded sales-agent runtime
  -> approved response/action
  -> UltraVox speech output
```

The unsafe first path is:

```text
customer audio
  -> UltraVox provider prompt owns sales dialogue
  -> provider speaks directly
```

The unsafe path may demo faster, but it discards the core project asset: deterministic sales-policy behavior with inspectable checkpoint evidence.
