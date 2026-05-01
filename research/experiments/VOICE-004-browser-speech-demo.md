# VOICE-004 Browser Speech Recognition Demo

## Experiment Goal

Test the first no-key spoken transcript path for the emotion-aware sales agent.

VOICE-004 lets the browser capture a speech-recognition transcript, sends transcript text to the local Python agent endpoint, and receives a realtime sales-agent response packet.

## Input

- Provider: `browser-speech-recognition-demo`
- Default campaign: `campaign-prod-005-b2c-telecom`
- Default stage: `relevance-check`
- Sample transcript: `Nur wenn Sie garantieren koennen, dass es stabil ist.`
- Local server URL: `http://127.0.0.1:8765/`

## Runtime Decision

The deterministic sample decision routes through the existing realtime sales-agent core:

- Sales difficulty: `claim-boundary`
- Interest state: `needs-human`
- Next action: `escalate`
- Call control: `transfer-or-escalate`

The selected response is:

```text
I hear the certainty concern. I do not want to make a claim that depends on details we have not checked, so the safest next step is to route this to a telecom specialist.
```

## Generated Artifacts

```text
research/experiments/generated/VOICE-004-browser-speech-demo.html
research/experiments/generated/VOICE-004-browser-speech-demo-metadata.json
research/experiments/generated/VOICE-004-browser-speech-demo-decision.json
```

## Safety Result

VOICE-004 keeps the prototype no-key and local:

- no API key required
- no Python cloud ASR call
- no microphone audio upload to the local server
- transcript text only is sent to `/decide`
- explicit consent checkbox before microphone recognition
- no real customer audio required

Browser speech recognition may depend on browser implementation details, so it remains a demo path rather than a production privacy answer.

## Debugging Observation

During manual browser testing, English speech could be transcribed as German because the initial prototype hardcoded browser recognition to `de-DE`.

The demo now exposes a recognition-language selector with `de-DE`, `en-US`, and `tr-TR`. It also shows the last transcript sent and a decision summary so repeated agent responses are easier to interpret.

The deterministic agent may intentionally produce the same response for different transcripts when they map to the same sales-difficulty bucket. The validator now checks a price-objection transcript separately so the demo proves that responses can change when the classification changes.

The demo now uses RESP-001 guarded response generation. The realtime policy still selects classification, next action, and call control. RESP-001 proposes guarded wording, validates it, stores the original fixed policy response as `response_generation.policy_response`, and copies `response_generation.final_response` into the spoken `tts_text`.

This is a bridge toward a real guarded LLM response layer, not the final natural sales agent. A future LLM should plug in as a candidate wording provider behind the same validation and fallback contract.

## Interpretation

VOICE-004 proves the next useful product loop:

```text
speak
-> browser transcript
-> reusable realtime sales-agent core
-> RESP-001 guarded response generation
-> compliant response
-> browser speech playback
```

The next milestone should measure latency in this browser spoken-turn loop before moving to interruption and barge-in behavior.
