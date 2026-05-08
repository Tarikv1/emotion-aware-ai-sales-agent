# VOICE-035 Connected Speech Phrase Flow

VOICE-035 is a bilingual runtime voice-delivery checkpoint for making provider-facing TTS text sound less like isolated written words.

It runs after `VOICE-034` pacing calibration and before live TTS. It does not call a provider, require an API key, upload customer audio, clone voices, or generate audio.

## Purpose

Human speech usually connects short phrases, filler words, and bridge clauses. Written punctuation can make a TTS model over-separate the words, especially when the text contains a short sentence, a break tag, and then a filler such as `well` or `also`.

VOICE-035 turns a small number of safe freeform patterns into connected provider-facing phrasing.

Examples:

- English before: `I'll keep this simple. <break ... /> Well, you're right to ask. It's only useful...`
- English after: `I'll keep this simple, well, you're right to ask, and it's only useful...`
- English trust before: `I'm not asking you to decide now. <break ... /> That's why I'll keep it brief.`
- English trust after: `I'm not asking you to decide now, so I'll keep it brief.`
- German before: `Das verstehe ich. <break ... /> Also, Geht's Ihnen...`
- German after: `Das verstehe ich, also geht's Ihnen...`

## Runtime Position

```text
RESP-001 guarded response
  -> VOICE-022 spoken text normalization
  -> VOICE-023 speech realism
  -> VOICE-026 interaction prosody
  -> VOICE-028 controlled imperfections
  -> VOICE-015 provider-neutral prosody
  -> VOICE-016 provider rendering
  -> VOICE-034 pacing calibration
  -> VOICE-035 connected speech phrase flow
  -> RESP-003 live TTS
```

## Scope

VOICE-035 may change only provider-facing TTS rendering for eligible freeform segments.

Allowed:

- Join obvious sentence-boundary filler transitions.
- Remove a break tag when it causes robotic isolation before a filler.
- Lowercase a filler after a comma when it becomes part of the same spoken phrase.
- Add a tiny bridge conjunction only for a short already-approved bridge sentence, such as `and it's`.

Forbidden:

- Changing `final_response`.
- Changing call control, next action, strategy, or qualification state.
- Changing protected campaign questions, company scripts, disclosures, do-not-call text, hangup text, human handoff text, or appointment confirmations.
- Adding product claims, guarantees, savings promises, legal advice, medical advice, coverage promises, payout promises, or fear pressure.

## Bilingual Behavior

English currently targets:

- `Well,` or `So,` after a short sentence and provider break.
- Trust-repair transitions such as `That's why I'll...` after a short reassurance.
- Short bridge clauses such as `It's...` or `That's...` after a reassurance sentence.

German currently targets:

- `Also, Geht's...` after a short acknowledgement and provider break.
- Generic `Also,` after a short sentence when the segment is eligible freeform.
- Short `Das...` bridge clauses after a sentence boundary.

This is not accent imitation or cultural stereotyping. It is punctuation and phrase-flow tuning for the configured response language.

## Validation

Run:

```powershell
python scripts\validate_voice_035_connected_speech.py
```

The validator checks:

- English and German eligible freeform text gets connected phrase flow.
- Protected German do-not-call text stays exact.
- VOICE-034 speed bounds remain active.
- Provider calls stay disabled.
- Customer audio upload and voice cloning stay disabled.
- Runtime validation exposes `voice_connected_speech_passed`.

## Listening Interpretation

VOICE-035 should reduce the "word by word" feeling Tarik heard in the VOICE-034 live samples. It is not expected to solve every voice-naturalness issue by itself.

If future live listening still sounds robotic, the next likely tuning area is not more filler words; it is provider voice settings, phrase rhythm, and possibly a better ElevenLabs voice/remix prompt.

## Live Listening Follow-Up

The first `RESP-003` live check with VOICE-035 active showed:

- English phrase flow improved compared with the previous checkpoint.
- German became too compressed and fast to judge pauses/fillers clearly.
- English still had some roboticness, likely from weak or wrong-word emphasis.

Follow-up:

- `VOICE-036` now handles this by restoring a tiny German breath cue, relaxing German speed, and blocking weak emphasis targets before provider rendering.

The later RESP-003 bilingual listening pass showed that lowering the English trust-repair speed too far made English more robotic. VOICE-035 now handles the trust case by removing the brittle sentence break and converting `That's why I'll...` into `so I'll...`, while VOICE-034 keeps the trust speed in a livelier bounded range.
