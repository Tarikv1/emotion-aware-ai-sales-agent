# VOICE-022 Spoken Text Normalization

## Purpose

VOICE-022 reduces robotic TTS wording before provider rendering.

It keeps the product architecture vertical-agnostic:

```text
reusable sales-agent core
  + SalesCampaign profile
  + guarded final_response
  + spoken TTS wording for eligible freeform segments
```

The layer supports English and German.

## What It Changes

For eligible freeform TTS text, VOICE-022 can convert written phrasing into spoken phrasing.

English examples:

- `I will` -> `I'll`
- `I am` -> `I'm`
- `you are` -> `you're`
- `that is` -> `that's`
- `it is` -> `it's`
- `there is` -> `there's`
- `do not` -> `don't`

German examples:

- `Ich habe` -> `Ich hab`
- `Wenn es` -> `Wenn's`
- `gibt es` -> `gibt's`
- `geht es` -> `geht's`

German normalization is intentionally conservative. It avoids heavy dialect, slang, and over-casual speech.

## What It Must Not Change

VOICE-022 must not rewrite:

- approved openings
- campaign qualification questions
- company-provided scripts
- required disclosures
- insurance, legal, medical, coverage, claim, payout, or savings boundaries
- do-not-call lines
- hangup lines
- human handoff exact scripts
- appointment confirmations

The official `final_response` remains unchanged. VOICE-022 only prepares provider-facing spoken TTS text.

## Runtime Position

```text
RESP-001 guarded response
  -> VOICE-022 spoken text normalization
  -> VOICE-015 prosody naturalness
  -> VOICE-016 provider rendering
  -> RESP-003 optional live TTS
```

In runtime packets, this appears under:

```text
voice_delivery.spoken_text_normalization
voice_delivery.spoken_segments
voice_delivery.prosody
voice_delivery.provider_rendering
```

## Campaign Controls

Campaigns can configure:

```json
{
  "spoken_text_normalization": {
    "enabled": true,
    "style": "professional-spoken",
    "english_contractions": true,
    "german_spoken_forms": true,
    "max_rewrites_per_response": 4
  }
}
```

If disabled, the layer passes text through unchanged.

## Commands

Run the offline VOICE-022 packet:

```powershell
python scripts\run_voice_022_spoken_text_normalization.py
```

Validate bilingual spoken normalization and protected-text locks:

```powershell
python scripts\validate_voice_022_spoken_text_normalization.py
```

Validate runtime integration:

```powershell
python scripts\validate_resp_002_runtime_voice_delivery.py
python scripts\validate_resp_003_runtime_live_tts.py
```

## Current Result

Current generated artifact:

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

## Product Meaning

VOICE-022 addresses a real listening issue: AI voices often read written text too literally.

This layer lets the product keep strict campaign and compliance text exact, while making freeform sales responses sound more like a human speaking in English or German.
