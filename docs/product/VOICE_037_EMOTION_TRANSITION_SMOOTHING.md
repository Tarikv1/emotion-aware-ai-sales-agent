# VOICE-037 Emotion Transition Smoothing

VOICE-037 applies Tarik's listening feedback that the agent's vocal emotion can change too sharply.

It is an offline, no-key runtime layer. It does not call a provider, generate audio, upload customer audio, use private audio, transcribe audio, or clone voices.

## Purpose

Human speech usually has emotional inertia. A speaker can become warmer, firmer, calmer, or more energetic, but the change usually happens gradually.

VOICE-037 prevents the voice runtime from creating abrupt jumps such as:

- warm acknowledgement directly into hard confidence
- upbeat delivery directly into low seriousness
- theatrical emotion directly after a calm phrase

The goal is not to remove emotion. The goal is to keep emotion believable.

## Behavior

VOICE-037 reads provider-facing delivery signals from the existing runtime packet:

- detected customer emotion from the guarded response decision
- interaction-prosody pitch intents
- provider-neutral pitch cues

It then creates an emotion transition plan:

- detect sharp transitions between adjacent emotional intents
- block over-emotional intents such as angry, hostile, theatrical, dramatic, or excited-high
- increase provider stability inside a bounded range when smoothing is needed
- cap provider style/exaggeration when smoothing is needed

For ElevenLabs, VOICE-037 adjusts request settings only:

```json
{
  "stability": "raised when sharp transitions are detected",
  "style": "capped when over-emotional delivery is detected",
  "speed": "preserved"
}
```

## Runtime Position

```text
RESP-001 guarded response
  -> VOICE-022 spoken text normalization
  -> VOICE-023 speech realism
  -> VOICE-026 interaction prosody
  -> VOICE-028 controlled imperfections
  -> VOICE-015 provider-neutral prosody
  -> VOICE-036 emphasis target guard
  -> VOICE-016 provider rendering
  -> VOICE-034 pacing calibration
  -> VOICE-035 connected speech phrase flow
  -> VOICE-036 German listening relaxation
  -> VOICE-037 emotion transition smoothing
  -> RESP-003 live TTS
```

## Guardrails

Allowed:

- Smooth provider-facing emotional intensity.
- Increase provider stability inside a bounded range.
- Cap provider style/exaggeration.
- Record detected and smoothed transition evidence.

Forbidden:

- Changing `final_response`.
- Changing rendered spoken words.
- Changing campaign questions, required disclosures, company scripts, human handoff text, hangup text, do-not-call text, appointment confirmations, or compliance text.
- Changing speed as part of emotion smoothing.
- Adding product claims, promises, fear pressure, legal advice, medical advice, coverage promises, payout promises, or savings promises.
- Uploading customer/private audio.
- Using voice cloning.
- Making audio-quality claims without human listening.

## Command

Run:

```powershell
python scripts\run_voice_037_emotion_smoothing.py
```

Validate:

```powershell
python scripts\validate_voice_037_emotion_smoothing.py
```

Default generated output:

```text
research\experiments\generated\VOICE-037-emotion-smoothing\
```

## Listening Interpretation

VOICE-037 should make emotional movement feel less jumpy. It is not expected to solve all remaining roboticness by itself.

If the next live listening check still sounds robotic, the next likely target is semantic emphasis and phrase-level intonation rather than raw pacing or emotional stability.
