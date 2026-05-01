# VOICE-006 Safe Interruption And Barge-In

## Experiment Goal

Test whether the voice agent can handle interruption without stopping for every sound.

The experiment focuses on conservative barge-in behavior:

```text
raw audio/noise -> keep speaking
likely echo -> keep speaking
no active agent speech -> do not trigger barge-in
short acknowledgement -> keep speaking
short ambiguous phrase -> pause and ask clarification
clear customer turn -> cancel and process
stop/refusal -> cancel and follow call-control policy
human request -> cancel and escalate
meaningful customer interruption -> cancel and process
```

The same policy is tested in English and German. This keeps the product architecture as one multilingual sales agent, not separate products per country.

When an interruption is sent into the sales core, the simulation now routes by campaign profile:

- English interruption turns use `campaign-prod-005-b2b-software`
- German interruption turns use `campaign-prod-005-b2c-telecom`

## Command

```powershell
python scripts\validate_voice_006_interruption_handling.py
```

The validator calls:

```powershell
python scripts\run_voice_006_interruption_simulation.py
```

## Cases

VOICE-006 now uses `36` bilingual interruption cases:

- English cases: `18`
- German cases: `18`
- Two examples per language for each interruption type

Covered interruption types:

- `noise_or_no_transcript`
- `likely_echo`
- `short_acknowledgement`
- `short_ambiguous_interruption`
- `clear_customer_question`
- `stop_or_refusal`
- `human_request`
- `meaningful_customer_interruption`
- `no_active_agent_speech`

## Current Result

Generated summary:

- cases: `36`
- English cases: `18`
- German cases: `18`
- confirmed interruptions: `20`
- false interruptions blocked: `12`
- clarification cases: `4`
- sent to agent core: `16`
- response-language matches: `16 / 16`

## Interpretation

VOICE-006 gives the prototype a safer rhythm:

- It does not panic-stop on noise.
- It does not stop for likely echo of the agent voice.
- It does pause for short meaningful customer signals.
- It asks a clarification question when the interruption is ambiguous.
- It still lets hard call-control cases reach the deterministic realtime core.
- It now protects every interruption category in German and English in the same policy.
- It now keeps the response language aligned with the active `SalesCampaign` when interruption turns reach the core.

## Safety Boundary

This is still a prototype policy. It uses transcript-level signals, not production acoustic diarization.

Future work should evaluate:

- streaming ASR partials
- confidence thresholds
- acoustic echo cancellation
- customer-vs-agent speaker detection
- interruption latency while TTS is actively playing
