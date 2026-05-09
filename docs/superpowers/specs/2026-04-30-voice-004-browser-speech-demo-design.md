# VOICE-004 Browser Speech Recognition Demo Design

Date: 2026-04-30

## Purpose

VOICE-004 adds the first no-key spoken transcript demo. The browser captures a user-initiated speech recognition result, sends only the transcript text to a local Python endpoint, and the existing realtime sales-agent core produces the response.

This preserves the core architecture:

```text
browser microphone permission
-> browser speech recognition transcript
-> local Python realtime agent endpoint
-> VOICE-001 response packet
-> browser speech playback
```

The browser does not become a second sales brain. It is only the speech input and playback interface.

## Scope

VOICE-004 includes:

- a local Python demo server
- a browser page using `SpeechRecognition` / `webkitSpeechRecognition`
- a local `/decide` endpoint that routes transcript text through the realtime agent
- generated demo HTML and metadata artifacts
- a validator that checks the browser demo contract without opening a browser

VOICE-004 does not include:

- cloud ASR API calls from Python
- API keys
- production telephony
- recording or storing microphone audio
- real customer audio
- barge-in handling
- production ASR quality benchmarking

## Safety And Consent

The demo must require an explicit consent checkbox before microphone recognition can start.

The browser may use implementation-specific speech recognition behavior. The page should disclose that this is a local prototype and should not be used with private customer audio.

The local Python server receives transcript text only. It does not receive microphone audio.

## Local Server Contract

The server should expose:

- `GET /` for the browser demo page
- `GET /metadata` for demo metadata
- `POST /decide` for transcript-to-agent decisions

The `/decide` endpoint should accept:

```json
{
  "transcript": "customer transcript",
  "campaign_id": "campaign-prod-005-b2c-telecom",
  "stage": "relevance-check",
  "input_type": "speech-final"
}
```

It should return a VOICE-004 packet containing the ASR adapter metadata and a VOICE-001-compatible response packet.

## Generated Artifacts

VOICE-004 should generate:

- `research/experiments/generated/VOICE-004/VOICE-004-browser-speech-demo.html`
- `research/experiments/generated/VOICE-004/VOICE-004-browser-speech-demo-metadata.json`
- `research/experiments/generated/VOICE-004/VOICE-004-browser-speech-demo-decision.json`

## Validation

The validator should assert:

- the script exists
- exported HTML contains Web Speech API usage
- exported HTML contains the consent gate
- metadata states no API key is required
- decision mode routes transcript through the realtime agent
- the returned response packet preserves claim-boundary escalation
- no secret-like API key patterns are written

