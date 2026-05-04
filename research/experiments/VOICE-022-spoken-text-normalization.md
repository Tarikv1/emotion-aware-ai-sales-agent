# VOICE-022 Spoken Text Normalization

## Question

Can the runtime make provider-facing TTS text sound more conversational in English and German without changing protected sales, campaign, compliance, or call-control text?

## Method

VOICE-022 adds a deterministic, local, segment-aware text-normalization layer.

The layer:

- rewrites only eligible freeform segments
- supports English contractions
- supports conservative German spoken equivalents
- preserves protected segment types and protected sources
- produces structured operations for review
- makes no provider calls
- uploads no customer audio
- uses no voice cloning

## Case Set

Case file:

```text
research/experiments/cases/voice-022-spoken-text-normalization.json
```

Coverage:

- 4 English cases
- 4 German cases
- freeform objection handling
- freeform empathy and transition wording
- protected campaign questions
- required disclosures
- strict German insurance boundary
- do-not-call and hangup lines
- disabled clean-script campaign
- appointment confirmation lock

## Result

Generated artifacts:

```text
research/experiments/generated/VOICE-022-spoken-text-normalization.json
research/experiments/generated/VOICE-022-spoken-text-normalization-report.md
```

Summary:

```text
cases: 8
English cases: 4
German cases: 4
normalizations: 11
eligible segments: 6
protected segments: 9
protected segment changes: 0
validation passed: 8 / 8
provider calls made: false
customer audio uploaded: false
voice cloning used: false
```

## Runtime Integration

VOICE-022 is now wired into RESP-002 before prosody planning.

```text
RESP-001 final_response
  -> VOICE-022 spoken text normalization
  -> VOICE-015 prosody cues
  -> VOICE-016 provider rendering
  -> RESP-003 optional live TTS
```

The invariant remains:

```text
final_response stays unchanged
```

Provider-facing TTS text may differ only when all segments are eligible freeform text and the RESP-002 validation passes.

## Interpretation

This is not a replacement for ElevenLabs voice design or remixing. It complements provider voice work by making the text itself less written and less robotic before TTS.

For thesis reporting, VOICE-022 records an implementation response to a concrete observed error: the agent sounded like it was reading written text too literally, especially phrases such as `I will` instead of `I'll`.
