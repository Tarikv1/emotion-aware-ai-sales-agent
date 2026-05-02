# Voice Generated Audio Asset Log

## Purpose

This is the local Emotion Aware template for tracking generated audio artifacts.

Use this shape for live TTS outputs, listening experiments, provider comparisons, and future runtime voice tests.

## Asset Fields

- experiment id:
- asset id:
- output path:
- audio format:
- provider:
- provider model:
- provider voice environment variable:
- language:
- campaign id:
- date:
- status: accepted / rejected / needs review

## Input Fields

- source text:
- source text path:
- provider-rendered text:
- synthetic prompt:
- customer audio uploaded:
- source audio used:
- source audio rights:
- person or voice likeness involved:
- voice cloning used:
- consent note:

## Run Boundary

- network used:
- upload used:
- cost:
- API key location:
- environment variables used:
- command:
- timeout seconds:
- fallback used:
- provider error:

## Review Fields

- human listening review:
- naturalness:
- clarity:
- language pronunciation:
- pacing:
- muffling or artifacts:
- emotional appropriateness:
- trustworthiness:
- sales usefulness:
- compliance concern:
- decision:
- follow-up:

## JSON Shape

```json
{
  "asset_log_id": "VOICE-generated-audio-asset-log",
  "experiment_id": "",
  "asset_id": "",
  "output_path": "",
  "audio_format": "",
  "provider": "",
  "provider_model": "",
  "provider_voice_env_var": "",
  "language": "",
  "campaign_id": "",
  "status": "needs review",
  "inputs": {
    "source_text": "",
    "source_text_path": "",
    "provider_rendered_text": "",
    "synthetic_prompt": true,
    "customer_audio_uploaded": false,
    "source_audio_used": false,
    "source_audio_rights": "",
    "person_or_voice_likeness_involved": false,
    "voice_cloning_used": false,
    "consent_note": ""
  },
  "run_boundary": {
    "network_used": true,
    "upload_used": false,
    "cost": "provider API call",
    "api_key_location": "environment-only",
    "environment_variables_used": [],
    "command": "",
    "timeout_seconds": 0,
    "fallback_used": false,
    "provider_error": null
  },
  "review": {
    "human_listening_review": false,
    "naturalness": null,
    "clarity": null,
    "language_pronunciation": null,
    "pacing": null,
    "muffling_or_artifacts": null,
    "emotional_appropriateness": null,
    "trustworthiness": null,
    "sales_usefulness": null,
    "compliance_concern": false,
    "decision": "needs review",
    "follow_up": ""
  }
}
```

## Git Policy

Generated audio files should stay local and ignored by Git unless there is a deliberate release or review package.

The asset log can be committed because it should not contain API keys, raw private customer data, raw customer audio, or provider secret values.
