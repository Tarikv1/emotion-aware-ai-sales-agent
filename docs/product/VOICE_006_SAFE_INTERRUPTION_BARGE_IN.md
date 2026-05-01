# VOICE-006 Safe Interruption And Barge-In

## Purpose

VOICE-006 defines how the voice agent handles customer interruption while the agent is speaking.

The goal is not to stop whenever the microphone hears sound. The goal is to stop only when there is likely customer speech that should interrupt the current agent response.

## Core Principle

```text
raw audio alone does not cancel agent speech
meaningful non-echo customer speech can pause or cancel agent speech
short ambiguous interruption asks clarification
call-control policy still wins
German and English use the same product policy with language-aware phrase packs
```

## Why This Matters

In a real call, the microphone may capture:

- background noise
- keyboard sounds
- someone else in the room
- speaker echo from the agent voice
- short acknowledgements such as "okay"
- actual customer interruptions

If the agent stops for every sound, it will feel broken. If the agent never stops, it will feel rude. VOICE-006 adds a conservative middle layer.

## Interruption Types

VOICE-006 uses these first labels:

- `noise_or_no_transcript`
- `likely_echo`
- `short_acknowledgement`
- `short_ambiguous_interruption`
- `clear_customer_question`
- `stop_or_refusal`
- `human_request`
- `meaningful_customer_interruption`

## Language Model

VOICE-006 is not two products.

It is one safe interruption policy with multilingual phrase packs. The current prototype explicitly covers:

- English: acknowledgements, ambiguous interruptions, refusals, human requests, and questions
- German: acknowledgements, ambiguous interruptions, refusals, human requests, and questions

The German pack includes patterns such as:

- "Rufen Sie mich bitte nicht mehr an"
- "kein Interesse"
- "Mitarbeiter"
- "echte Person"
- "Was bedeutet das?"
- "Wie bitte?"

The English pack includes equivalent patterns such as:

- "stop calling"
- "not interested"
- "real person"
- "what does that mean?"
- "huh?"

Future languages should be added as phrase packs inside this same policy, not as separate products.

## Actions

The interruption policy can choose:

- `continue-speaking`
- `pause-and-ask-clarification`
- `cancel-agent-speech-and-process-turn`

## Short Ambiguous Layer

Short phrases such as:

- "huh?"
- "wait"
- "sorry?"
- "what?"

should not automatically be sent to the sales core as a full customer turn.

The agent should pause and ask:

```text
I paused there. Was something unclear, or did you want to ask something?
```

For German, the current prototype uses:

```text
Ich habe kurz pausiert. War etwas unklar, oder wollten Sie etwas fragen?
```

This gives the customer room without inventing intent.

## Call-Control Priority

Some interruptions are not just clarification signals.

Examples:

- "stop calling me"
- "do not call"
- "I want a human"
- "please have a real person call me"

These should cancel current speech and go through the realtime policy core so call-control rules can end the call, suppress contact, or escalate.

## Browser Demo Behavior

VOICE-004 now exposes VOICE-006 state in the browser demo:

- interruption state panel
- conservative client-side interruption classifier
- echo guard
- short ambiguous clarification response
- cancellation only after confirmed interruption

The browser demo still remains a prototype. Production interruption handling will need stronger audio separation, echo cancellation, speaker diarization, and streaming ASR confidence signals.

## Validation

Run:

```powershell
python scripts\validate_voice_006_interruption_handling.py
```

The validator checks:

- background noise does not stop speech
- likely echo does not stop speech
- short ambiguous interruption pauses and asks clarification
- clear question cancels and becomes a new turn
- stop/refusal reaches call-control and ends the call
- human request reaches call-control and escalates
- browser HTML exposes the VOICE-006 interruption state

## Generated Artifacts

```text
research/experiments/generated/VOICE-006-interruption-results.json
research/experiments/generated/VOICE-006-interruption-report.md
research/experiments/generated/VOICE-006-browser-speech-demo.html
research/experiments/generated/VOICE-006-browser-speech-demo-metadata.json
```

## Next Work

VOICE-007 should move toward production ASR/TTS provider evaluation behind explicit privacy and key gates.

Later interruption work should add:

- streaming ASR confidence
- echo cancellation tests
- speaker separation
- barge-in timing thresholds
- interruption recovery after the clarification response
