# VOICE-018 Sales Voice Tuning

## Question

Can the project turn listening feedback into a safer provider-input improvement before spending more live TTS calls?

The feedback was:

- audio is clear
- pronunciation is acceptable
- pacing is too slow for sales
- pitch and emotion are too flat
- the voice still sounds obviously AI-generated

## Method

VOICE-018 starts from the validated VOICE-016 provider previews.

It applies a `professional-sales-v1` tuning profile:

- faster eligible freeform segments
- compressed existing pause/break tags
- emotion intent metadata
- pitch intent metadata
- no provider calls
- no customer audio upload
- no voice cloning
- no quality claim without live listening

Protected segments remain exact and neutral.

## Result

```text
cases: 8
German cases: 4
English cases: 4
providers: cartesia, elevenlabs
sales-tuned variants: 16
tuned segments: 12
protected segments: 14
pause compressions: 10
average eligible speed ratio: 1.11
max speed ratio: 1.142
protected text changes: 0
validation passed: 16 / 16
provider calls made: false
customer audio uploaded: false
voice cloning used: false
quality claim allowed: false
```

## Interpretation

VOICE-018 improves the text/request preparation side of the voice stack. It does not prove audio quality yet.

The next evidence step is live audio A/B testing:

```text
VOICE-017 style prosody input
versus
VOICE-018 professional-sales tuned input
```

Human listening should score:

- naturalness
- sales-call speed
- pitch variation
- emotional appropriateness
- clarity
- AI-obviousness
- trust
- provider artifacts

## Risk

ElevenLabs request-level speed can affect an entire text input. If protected campaign questions and disclosures need neutral delivery while freeform speech is faster, the runtime may need segment-split TTS requests.
