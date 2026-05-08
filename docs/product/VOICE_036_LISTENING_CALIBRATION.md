# VOICE-036 Listening Calibration

VOICE-036 applies Tarik's first listening feedback after `VOICE-035`.

It is an offline, no-key runtime layer. It does not call a provider, generate audio, upload customer audio, use private audio, transcribe audio, or clone voices.

## Purpose

The `VOICE-035` live listening check showed two different problems:

- German connected speech became too compressed and too fast to judge clearly.
- English sounded better than before, but some emphasis felt unnatural because the wrong words were being made salient.

VOICE-036 keeps these problems separate.

## Behavior

German connected-speech relaxation:

- Keeps the connected phrase from VOICE-035.
- Adds a tiny provider-facing breath cue after the short acknowledgement.
- Reduces the German ElevenLabs speed from the VOICE-034/035 fast setting into a clearer sales-call range.
- After the RESP-003 matched A/B review, the German relaxation target is slower than the original VOICE-036 fast setting. A later German voice-ID check allowed only a tiny speed lift while staying inside the slower bounded range.

Example:

```text
Das verstehe ich, <break time="0.08s" /> also geht's Ihnen ...
```

Emphasis target guard:

- Runs after `VOICE-015` prosody planning and before provider rendering.
- Blocks weak single-word emphasis targets such as `practical` when they are not clearly campaign-relevant.
- Uses a conservative default: no emphasis is better than wrong emphasis.

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

- Filter unsafe or weak emphasis cues before provider rendering.
- Add a tiny German breath cue for eligible freeform connected speech.
- Reduce German voice speed only inside the bounded listening-feedback range.
- Keep English speed behavior unchanged except for separately reviewed narrow caps such as the English trust-repair transition cap in VOICE-034.

Forbidden:

- Changing `final_response`.
- Changing campaign questions, required disclosures, company scripts, human handoff text, hangup text, do-not-call text, appointment confirmations, or compliance text.
- Adding product claims, promises, fear pressure, legal advice, medical advice, coverage promises, payout promises, or savings promises.
- Uploading customer/private audio.
- Using voice cloning.
- Making audio-quality claims without human listening.

## Command

Run:

```powershell
python scripts\run_voice_036_listening_calibration.py
```

Validate:

```powershell
python scripts\validate_voice_036_listening_calibration.py
```

Default generated output:

```text
research\experiments\generated\VOICE-036-listening-calibration\
```

## Listening Interpretation

VOICE-036 should make the German sample easier to understand than VOICE-035 and the first RESP-003 matched A/B run, while preserving the more natural connected phrase shape.

For English, VOICE-036 does not try to solve all remaining roboticness. It only prevents weak emphasis targets from being sent to providers that can render emphasis. Future work can add a richer emphasis model that chooses semantically important campaign words, but the current safe default is conservative.
