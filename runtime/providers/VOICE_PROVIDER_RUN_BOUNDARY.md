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

## Voice Design Boundary

Voice Design checkpoints such as `VOICE-020` may prepare synthetic prompts, synthetic preview text, settings candidates, and listening rubrics.

They must not:

- require an API key by default
- call a provider by default
- upload private call-center audio
- use customer voices as provider input
- clone any person's voice
- move private identifiers into generated artifacts

Private call-center audio may later inform local abstract tuning notes only after review.

Local voice IDs may be stored in ignored `config/local/voice_ids.json` to avoid repeated environment setup. API keys must remain environment-only.

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
- spoken-normalized and provider-rendered text may be used only for eligible freeform segments
- generated-audio asset metadata must be included in the result packet
- human listening review is required before making quality claims

## RESP-004 Boundary

For the `RESP-004` VOICE-044 listening check:

- RESP-003 remains the TTS bridge
- RESP-004 owns the separate listening-test artifact folder
- default mode is dry-run
- live provider calls require `--live`
- generated text must come from validated RESP-002/RESP-003 packets
- no quality claim is allowed until Tarik records the listening review
- generated audio, if any, stays under `research/experiments/generated/RESP-004-voice-044-listening-check/`

## LIVE-DEMO-001 Boundary

For the `LIVE-DEMO-001` supervised agent voice-call demo:

- the conversation brain must stay in this repository
- the default demo campaign should be the English B2B software campaign unless Tarik deliberately selects a German campaign
- ElevenLabs may be used only as TTS output, not as a hosted conversational agent
- browser speech recognition may create the transcript, but raw microphone audio must not be uploaded to the Python server
- the browser UI must require local microphone consent before recognition starts
- live ElevenLabs TTS requires `--live-tts`, `--consent-confirmed`, `ELEVENLABS_API_KEY`, a voice ID source, and a bounded timeout
- API key values and raw voice IDs must not be written to JSON, Markdown, logs, screenshots, or Git
- no real customer audio, voice cloning, durable provider agent, provider-owned sales logic, runtime behavior change, or `PROD-102` opening is allowed
- real Tarik demo turns and generated audio must stay under ignored `data/private/live-demo-001/`

## ULTRAVOX-001 Boundary

For the `ULTRAVOX-001` bounded realtime voice evaluation:

- default mode is dry-run
- no UltraVox API calls are made
- no audio is uploaded
- no API key is required
- no durable provider-side console agent is created
- no sales policy, protected text, campaign logic, or acceptance evidence moves out of this repository
- `PROD-102` remains closed
- hosted UltraVox API is evaluated only as a swappable realtime voice provider adapter
- the open-source UltraVox lane remains research-only until local serving, streaming, voice output, latency, and observability are separately proven
- any future live UltraVox test requires explicit approval, `ULTRAVOX_API_KEY` from the environment only, synthetic audio only, retention/deletion review, timeout guardrails, and generated JSON/Markdown evidence

## ULTRAVOX-002 Boundary

For the `ULTRAVOX-002` synthetic live smoke:

- exactly one synthetic live test is approved for this checkpoint
- the API key may be read only from `ULTRAVOX_API_KEY` in the process environment or ignored `runtime/config/local/ultravox.env`
- API key values, join URLs, and raw provider tokens must not be written to JSON, Markdown, logs, screenshots, or Git
- the test is agent-first and uploads no customer audio
- no voice cloning, durable UltraVox console agent, provider-owned sales logic, runtime behavior change, or `PROD-102` opening is allowed
- the script must close the WebSocket and attempt to delete the UltraVox call after the smoke test
- generated provider audio, if any, stays under ignored `research/experiments/generated/ULTRAVOX-002/audio/`
- this smoke proves only key/call/WebSocket/first-agent-audio plumbing; it is not a full speech-to-speech latency result

## ULTRAVOX-003 Boundary

For the `ULTRAVOX-003` synthetic customer-audio turn:

- exactly one synthetic customer-audio live test is approved for this checkpoint
- the API key may be read only from `ULTRAVOX_API_KEY` in the process environment or ignored `runtime/config/local/ultravox.env`
- API key values, raw voice values, full call IDs, join URLs, and provider tokens must not be written to JSON, Markdown, logs, screenshots, or Git
- customer input must be synthetic audio, either locally generated or the prior ignored `ULTRAVOX-002` synthetic fixture; it must not be real customer audio or private Tarik speech samples
- no voice cloning, durable UltraVox console agent, provider-owned sales logic, runtime behavior change, or `PROD-102` opening is allowed
- the script must stream signed 16-bit mono PCM through a server WebSocket, close the WebSocket, and attempt to delete the UltraVox call after the turn
- generated input/output audio, if any, stays under ignored `research/experiments/generated/ULTRAVOX-003/audio/`
- this test can measure one synthetic speech-to-speech turn, but it is not production evidence for latency, interruption handling, retention, cost, or quality

## Review Gate

Before a new provider integration becomes part of the active runtime path, the project must have:

- a dry-run mode
- a forced-missing-key fallback mode
- a validator
- generated JSON/Markdown evidence
- a secret scan
- a local generated-audio asset log shape
- thesis/product docs updated with limitations
