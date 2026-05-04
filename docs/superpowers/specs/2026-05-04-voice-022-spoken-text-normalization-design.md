# VOICE-022 Spoken Text Normalization Design

## Context

Listening feedback showed that the voice could still sound robotic because the TTS provider read written phrasing too literally.

The most obvious example was English text such as `I will`, which a human sales agent would often say as `I'll`.

The same issue exists in German, but German spoken normalization must stay more conservative to avoid dialect, slang, or compliance risk.

## Design

Add a provider-neutral spoken-text normalization layer between RESP-001 guarded response generation and VOICE-015 prosody planning.

The layer accepts:

- `campaign`
- `segments`
- `language`

It returns:

- `output_segments`
- `normalizations`
- `tts_text`
- `validation`
- provider/privacy boundary metadata

## Safety Rules

The layer may rewrite only eligible freeform segments.

It must preserve:

- campaign questions
- required disclosures
- compliance statements
- claim and coverage boundaries
- do-not-call lines
- hangup lines
- appointment confirmations
- human handoff exact scripts
- source-owned company scripts

The guarded `final_response` remains policy-owned and unchanged.

## Bilingual Scope

English:

- contractions such as `I will` -> `I'll`, `you are` -> `you're`, `it is` -> `it's`

German:

- conservative spoken equivalents such as `Ich habe` -> `Ich hab`, `Wenn es` -> `Wenn's`, `gibt es` -> `gibt's`

German does not use heavy dialect or casual slang by default.

## Runtime Integration

RESP-002 stores both:

- original `segments`
- normalized `spoken_segments`

Prosody and provider rendering use `spoken_segments`.

RESP-003 may use provider-rendered text only after RESP-002 validates successfully and the content is eligible freeform text. Protected text continues to use `final_response`.

## Verification

Required validators:

- `python scripts\validate_voice_022_spoken_text_normalization.py`
- `python scripts\validate_resp_002_runtime_voice_delivery.py`
- `python scripts\validate_resp_003_runtime_live_tts.py`

No provider call, API key, private audio upload, or voice cloning is allowed in the default path.
