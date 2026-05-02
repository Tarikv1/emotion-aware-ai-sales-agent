# Voice Provider Run Boundary

## Purpose

This is the local Emotion Aware checklist for any command that can contact a voice or media provider.

Use it before live TTS, ASR, voice generation, audio upload, lip-sync, or any provider call that sends text, audio, or identity-related data outside the project.

## Default Rule

Default project commands must stay offline.

Provider calls require explicit opt-in:

```text
--live
```

or a similarly clear live-provider flag documented by the script.

## Required Boundary Fields

Every live voice-provider run should record:

- provider
- capability: TTS / ASR / voice generation / audio analysis
- network used
- upload used
- text sent to provider
- customer audio uploaded
- synthetic prompt only
- voice cloning used
- API key location
- environment-only key handling
- required environment variables
- bounded timeout
- explicit opt-in flag
- generated output path
- provider fallback behavior
- human listening review status

## Safety Requirements

- API keys must be environment-only.
- API keys must not be written to JSON, Markdown, logs, reports, screenshots, or Git.
- Voice IDs may be logged only as environment variable names, not raw values.
- No customer audio may be uploaded without a separate consent and retention review.
- No voice cloning is allowed unless explicit written permission exists for that exact voice and use.
- Generated audio must be labeled internally as synthetic.
- Live calls must use a bounded timeout.
- Cost-bearing commands must be explicitly approved before use.
- Provider terms, data retention, and logging behavior must be reviewed before production use.

## Consent Checklist

Before using any real person's voice or customer audio:

- Do we have explicit permission?
- Is the permitted use written down?
- Does the permission cover this product, audience, and duration?
- Can the person revoke permission?
- Where did the source audio come from?
- Who owns the recording?
- Are source voice samples stored outside Git?
- Are generated outputs traceable to provider, voice, prompt, and script settings?

## Live TTS Boundary

For ElevenLabs or Cartesia live TTS:

- input should be synthetic or approved campaign text
- no customer audio is uploaded
- no voice cloning is used
- API key is read from an environment variable
- voice ID is read from an environment variable
- timeout is capped by the script
- generated audio goes under `research/experiments/generated`
- generated audio files are ignored by Git unless a future explicit artifact policy says otherwise

## RESP-003 Boundary

For `RESP-003` runtime live-capable TTS:

- default mode is dry-run
- live provider calls require `--live`
- generated text must come from a validated `RESP-002` packet
- protected text should use the exact guarded `final_response`
- provider-rendered prosody text may be used only for eligible freeform segments
- generated-audio asset metadata must be included in the result packet
- human listening review is required before making quality claims

## Review Gate

Before a new provider integration becomes part of the active runtime path, the project must have:

- a dry-run mode
- a forced-missing-key fallback mode
- a validator
- generated JSON/Markdown evidence
- a secret scan
- a local generated-audio asset log shape
- thesis/product docs updated with limitations
