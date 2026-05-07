# VOICE-031 Feature-To-Runtime Mapping Gate

VOICE-031 is the safety gate between reviewed private speech features and future runtime voice settings.

It does not make the agent speak differently yet. It creates a proposal packet that says which reviewed aggregate features could later influence campaign-level voice settings after human review.

## Why This Exists

VOICE-030B captures local owner speech samples.

VOICE-030C queues and analyzes private WAV samples.

VOICE-030D summarizes safe aggregate features for review.

VOICE-031 prevents the next step from becoming automatic personalization. It keeps the product voice professional, campaign-configurable, and vertical-agnostic.

## Allowed Inputs

Default mode uses a synthetic public fixture:

```powershell
python scripts\run_voice_031_feature_runtime_mapping.py
```

Private mode may read only a reviewed VOICE-030D summary, not raw audio or raw feature files:

```powershell
python scripts\run_voice_031_feature_runtime_mapping.py `
  --summary-json data\private\tarik-speech-samples\derived\review\voice-030d-feature-review-summary.json `
  --allow-private-review-read
```

If a private summary is read, output must stay under `data/private/`.

## Runtime Candidate Features

VOICE-031 allows only these reviewed candidates:

- `speech_burst_count`
- `energy_variation`
- `mean_speech_rms`

These become review-only hints:

- `rhythm_density_hint`
- `expressiveness_variation_hint`
- `presence_level_hint`

## Blocked Features

These features are diagnostic-only and must not become runtime pacing targets:

- `pause_ratio`
- `average_pause_ms`
- `longest_pause_ms`
- `silence_seconds`

Tarik may pause for a long time while formulating complex instructions. That is useful context for understanding private samples, but it should not make the sales agent slower.

## Guardrails

VOICE-031 enforces:

- no provider calls
- no transcription
- no raw audio reading
- no voice cloning
- no automatic runtime profile application
- no public artifact from private summaries
- campaign override required before future use
- protected campaign questions, disclosures, handoff, and hangup text remain locked
- reusable vertical-agnostic sales core is preserved

## WhatsApp Reminder

The optional WhatsApp voice-note import idea is deliberately deferred.

When Tarik decides to run VOICE-030D on enough local speech samples, Codex should remind him that selected WhatsApp voice notes can be imported if he wants more coverage.

Rules for that later import:

- keep files under `data/private/`
- label the source as `whatsapp_voice_note`
- convert non-WAV files locally before analysis
- do not upload private voice notes to providers

## Validation

```powershell
python scripts\validate_voice_031_feature_runtime_mapping.py
```
