# VOICE-004 Browser Speech Recognition Demo

## Purpose

VOICE-004 is the first no-key spoken transcript demo for the sales agent.

It connects browser speech recognition to the existing realtime sales-agent core:

```text
browser microphone permission
-> browser speech recognition transcript
-> local Python /decide endpoint
-> realtime sales-agent decision
-> browser speech playback
```

The browser is not a second sales brain. It captures transcript text and plays back the selected response. The Python realtime core still owns classification, strategy, escalation, and call control.

## Script

```text
scripts/run_browser_speech_demo.py
```

Run local demo server:

```powershell
python scripts\run_browser_speech_demo.py
```

Then open:

```text
http://127.0.0.1:8765/
```

## Local Endpoints

- `GET /`: browser demo page
- `GET /metadata`: demo metadata
- `POST /decide`: transcript-to-agent decision

The `/decide` endpoint accepts transcript text and returns a VOICE-004 packet with a VOICE-001 response packet inside it.

## Safety Boundaries

VOICE-004:

- requires no API key
- makes no Python cloud ASR calls
- sends only transcript text to the local Python server
- does not upload microphone audio to the local Python server
- requires an explicit consent checkbox before browser microphone recognition
- should not be used with private customer audio

Browser speech recognition behavior depends on the user's browser. Some browsers may rely on browser-vendor speech services. That is why this remains a prototype, not a production privacy decision.

## Demo Behavior Notes

The page includes a recognition-language selector. Choose `English (en-US)` before speaking English, or `German (de-DE)` before speaking German. If the wrong language is selected, the browser can force the audio into the wrong language and produce strange transcripts.

The page also shows:

- last transcript sent to the local agent
- decision summary
- full decision packet

The agent response may stay the same across different spoken inputs if the transcripts map to the same sales-difficulty bucket. For example, multiple claim-boundary phrases should safely produce the same escalation-style response.

## Generated Artifacts

```text
research/experiments/generated/VOICE-004-browser-speech-demo.html
research/experiments/generated/VOICE-004-browser-speech-demo-metadata.json
research/experiments/generated/VOICE-004-browser-speech-demo-decision.json
```

## Validation

Run:

```powershell
python scripts\validate_voice_004_browser_speech_demo.py
```

The validator checks export mode, decision mode, browser speech API wiring, consent gating, local transcript routing, and secret-safe output.

## Next Milestones

- VOICE-005: latency measurement for browser spoken turns
- VOICE-006: interruption and barge-in behavior
- VOICE-007: production ASR integration behind explicit key/privacy gates
