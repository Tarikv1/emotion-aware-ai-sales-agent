# LIVE-DEMO-004 Realtime Turn-Taking ASR/VAD

`LIVE-DEMO-004-realtime-turn-taking-asr-vad` is a narrow follow-up to the failed supervised listening pass from `LIVE-DEMO-003`.

It does not open `PROD-102`, claim production readiness, add provider ASR, enable payment collection, create a provider-hosted durable agent, use voice cloning, make LLM calls required for live response, or let an LLM write final spoken responses.

## Goal

Reduce live demo talk-over and premature agent responses caused by browser ASR timing.

The checkpoint makes the current browser SpeechRecognition policy explicit and testable:

- browser SpeechRecognition is browser ASR, not true production VAD
- raw microphone audio is not uploaded to the Python server
- interim ASR results do not auto-submit
- auto-submit requires at least one final ASR result
- pending auto-submit is cancelled when interim speech continues
- final transcript submission waits through a longer pause window
- manual send remains available when browser ASR is unreliable

## Runtime Policy

Runtime-owned policy lives in:

```text
runtime/speech/realtime_turn_taking_policy.py
```

The live browser runner exposes the policy in metadata:

```text
metadata.browser_asr.turn_taking_policy
metadata.browser_asr.acceptance_policy
```

This keeps the current browser demo and future WebRTC/telephony adapters aligned on the same boundary: do not respond while the user is still speaking, and do not pretend browser final events are reliable production VAD.

## Commands

Validate the checkpoint without live microphone or provider calls:

```powershell
python scripts\validate_live_demo_004_realtime_turn_taking_asr_vad.py
```

Run the live demo after validation:

```powershell
python scripts\run_live_demo_001_agent_voice_call.py --live-tts --consent-confirmed --timeout-seconds 8 --port 8796 --private-out data\private\live-demo-003\raw-turns
```

## Acceptance Criteria

Hard gates:

- no provider ASR is introduced
- no raw audio upload to the Python server
- no provider-hosted durable agent
- no voice cloning
- no LLM blocking or mutating the live spoken response
- no `PROD-102`
- browser ASR is documented as not true VAD
- interim ASR results cannot auto-submit
- final ASR result is required for auto-submit
- pending submit is cancelled if interim speech continues
- final submit delay is at least `1800 ms`
- the minimum listening window is at least `1200 ms`
- existing `LIVE-DEMO-001`, `LIVE-DEMO-002`, and `LIVE-DEMO-003` validators still pass

Human live check:

- the agent should not start answering while Tarik is mid-sentence
- thinking pauses should be tolerated better than in `LIVE-DEMO-003`
- terminal call controls should still stop listening restart
- ElevenLabs remains TTS only

## Evidence

Generated evidence:

- `research/experiments/generated/LIVE-DEMO-004-realtime-turn-taking-asr-vad/result.json`
- `research/experiments/generated/LIVE-DEMO-004-realtime-turn-taking-asr-vad/report.md`

This checkpoint is still not a production realtime voice stack. If browser ASR remains too weak after this, the next checkpoint should evaluate a real streaming ASR/VAD layer behind the same no-provider-agent and no-LLM-final-response boundaries.
