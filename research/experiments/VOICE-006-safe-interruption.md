# VOICE-006 Safe Interruption And Barge-In

## Experiment Goal

Test whether the voice agent can handle interruption without stopping for every sound.

The experiment focuses on conservative barge-in behavior:

```text
raw audio/noise -> keep speaking
likely echo -> keep speaking
short ambiguous phrase -> pause and ask clarification
clear customer turn -> cancel and process
stop/refusal -> cancel and follow call-control policy
human request -> cancel and escalate
```

## Command

```powershell
python scripts\validate_voice_006_interruption_handling.py
```

The validator calls:

```powershell
python scripts\run_voice_006_interruption_simulation.py
```

## Cases

- `VOICE-006-C01`: background noise must not stop the agent
- `VOICE-006-C02`: likely echo must not stop the agent
- `VOICE-006-C03`: short ambiguous interruption asks clarification
- `VOICE-006-C04`: clear customer question becomes a new turn
- `VOICE-006-C05`: stop request interrupts and ends call
- `VOICE-006-C06`: human request interrupts and escalates

## Current Result

Generated summary:

- cases: `6`
- confirmed interruptions: `4`
- false interruptions blocked: `2`
- clarification cases: `1`
- sent to agent core: `3`

## Interpretation

VOICE-006 gives the prototype a safer rhythm:

- It does not panic-stop on noise.
- It does not stop for likely echo of the agent voice.
- It does pause for short meaningful customer signals.
- It asks a clarification question when the interruption is ambiguous.
- It still lets hard call-control cases reach the deterministic realtime core.

## Safety Boundary

This is still a prototype policy. It uses transcript-level signals, not production acoustic diarization.

Future work should evaluate:

- streaming ASR partials
- confidence thresholds
- acoustic echo cancellation
- customer-vs-agent speaker detection
- interruption latency while TTS is actively playing
