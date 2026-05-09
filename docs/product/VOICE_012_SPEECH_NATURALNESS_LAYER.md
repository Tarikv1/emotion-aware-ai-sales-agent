# VOICE-012 Speech Naturalness Layer

## Purpose

VOICE-012 adds a text-only speech naturalness layer before TTS.

The goal is to make the agent sound less machine-perfect without letting casual speech corrupt campaign scripts, qualification questions, compliance statements, or call-control wording.

This is not a provider feature and not an insurance-only feature. It belongs to the reusable voice/runtime layer and is configured per `SalesCampaign`.

## Runtime Position

```text
customer speech
  -> speech-to-text
  -> realtime sales-agent core
  -> guarded response generation
  -> speech naturalness layer
  -> text-to-speech adapter
```

VOICE-012 changes speech rhythm only. It does not decide customer state, sales strategy, next action, compliance, handoff, or call termination.

## Segment-Aware Model

The layer does not treat an agent response as one plain text blob.

It expects speech segments:

```text
segment_type
source
text
allow_fillers
```

Each segment is either protected or eligible.

## Protected Segments

VOICE-012 must not insert fillers inside:

- campaign qualification questions
- company-provided scripts
- approved openings
- required disclosures
- compliance statements
- legal, medical, coverage, or claim-boundary wording
- do-not-call confirmations
- hang-up lines
- appointment confirmations
- sensitive escalation wording

This matches real call-center behavior: a human agent may speak naturally in freeform parts, but reads company-required questions and disclosures cleanly.

## Eligible Segments

VOICE-012 may insert rare mid-utterance fillers only inside freeform speech such as:

- empathy
- objection handling
- soft transitions
- non-sensitive explanations
- clarifications
- bridge wording

Examples:

```text
I understand the concern. The important thing is, um, that I do not want to promise something we have not checked yet.
```

```text
Ich verstehe den Punkt. Wichtig ist, Ã¤hm, dass ich Ihnen nichts verspreche, was von Details abhaengt.
```

Bad examples that must stay blocked:

```text
Do you, um, handle inbound lead routing?
```

```text
Ich kann, Ã¤hm, keine Gesundheits-, Rechts-, Leistungs- oder Auszahlungszusage machen.
```

## Campaign Configuration

Campaigns can configure naturalness:

```json
"speech_naturalness": {
  "enabled": true,
  "style": "human-professional-with-rare-casual-fillers",
  "filler_frequency": "low",
  "max_fillers_per_response": 1,
  "allow_casual_fillers": true,
  "allow_hesitation_sounds": true,
  "pause_markers_allowed": true
}
```

Default behavior is conservative:

- deterministic output
- low filler frequency
- one filler per normal response
- protected segments unchanged
- no provider calls
- no API key
- no customer audio upload

## Bilingual Fillers

Current English filler pool:

- `um`
- `uh`
- `hm`
- `you know`
- `like`

Current German filler pool:

- `Ã¤hm`
- `Ã¤h`
- `hm`
- `also`

The layer can contextually replace a casual filler with a safer hesitation sound when the casual filler would change meaning. For example, before `that` or `dass`, it prefers `um` / `Ã¤hm`.

## Validation

Run:

```powershell
python scripts\validate_voice_012_speech_naturalness.py
```

The validator checks:

- English and German cases are present.
- Fillers appear only in eligible freeform segments.
- Protected questions, disclosures, appointment confirmations, and hang-up lines stay byte-for-byte unchanged.
- German cases do not receive English fillers.
- English cases do not receive German fillers.
- disabled campaign profiles produce clean speech.
- no API key, provider call, customer audio upload, or voice cloning is involved.

## Generated Artifacts

```text
research/experiments/generated/VOICE-012/VOICE-012-speech-naturalness.json
research/experiments/generated/VOICE-012/VOICE-012-speech-naturalness-report.md
```

## Product Meaning

VOICE-012 keeps the product architecture intact:

- reusable sales-agent core
- configurable `SalesCampaign` profiles
- deterministic safety and call-control ownership
- provider-independent voice rendering
- bilingual behavior without product forks

The important lesson is that human-like speech must be constrained by source-of-truth boundaries. The agent can sound more human in freeform speech, but it should sound exact when reading client-provided questions or compliance text.
