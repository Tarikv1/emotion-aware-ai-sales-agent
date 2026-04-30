# VOICE-001 TTS Response Prototype Design

Date: 2026-04-30

## Purpose

VOICE-001 adds the first voice layer around the existing realtime sales-agent core. The goal is to prove that a campaign-agnostic realtime text decision can be converted into a spoken response without changing the underlying sales reasoning, compliance guardrails, call-control policy, or campaign profile model.

This is not an insurance-specific voice workflow and not a B2B-specific voice workflow. It should work for any future `SalesCampaign` profile where the core agent produces an approved `agent_response`.

## Scope

VOICE-001 covers text-to-speech output only:

```text
customer transcript
-> realtime turn decision
-> agent_response text
-> neutral synthetic voice output
```

VOICE-001 does not cover live microphone input, speech-to-text, phone/SIP integration, real-time interruption handling, voice cloning, or production call recording.

## Recommended Approach

Use a neutral synthetic test voice first.

This keeps the prototype safe, fast, and reusable. We can evaluate voice pacing, response length, latency envelope, and handoff behavior without introducing consent risk from cloning a real person's voice.

## Architecture

The voice layer should sit above the realtime turn engine:

```text
SalesCampaign config
        |
customer transcript
        |
realtime turn engine
        |
structured runtime decision
        |
agent_response text
        |
TTS adapter
        |
audio file or dry-run voice packet
```

The realtime engine remains responsible for:

- emotion classification
- sales difficulty classification
- interest-state classification
- response strategy
- next action
- call-control decision
- escalation or hang-up decision

The TTS layer remains responsible only for:

- selecting a neutral test voice
- converting approved `agent_response` text into audio when a provider is available
- writing traceable metadata for thesis/product evaluation
- failing safely when no voice provider is configured

## Consent And Safety

VOICE-001 must not clone a real person, public figure, client employee, or customer voice.

Every generated voice packet should be internally traceable as synthetic output. If future milestones use real recordings, the project must apply the workspace voice consent checklist before collecting or generating any audio.

## Implementation Components

Add a provider-safe script:

```text
scripts/generate_voice_response.py
```

The script should accept a campaign, stage, transcript, and output path. It should call the existing realtime turn decision path, extract `agent_response`, and create a voice packet.

The first implementation should support:

- `--dry-run` for deterministic validation without audio generation
- an optional local Windows SAPI provider if available
- no hardcoded API keys
- no required cloud provider
- JSON metadata output for reproducibility

## Evaluation

Add a validator that confirms:

- the script exists
- dry-run mode produces a voice packet
- the packet includes the realtime decision
- the packet includes the exact `agent_response` text used for TTS
- no voice provider is required for the test to pass
- no secrets or API keys are written to generated artifacts

## Out Of Scope For VOICE-001

- OpenAI Realtime API integration
- Twilio, SIP, or call-center telephony integration
- automatic speech recognition
- barge-in and interruption handling
- real call recording
- voice cloning
- production German voice selection

## Next Milestones

- VOICE-002: recorded audio input to speech-to-text transcript
- VOICE-003: full spoken turn loop with latency measurement
- VOICE-004: interruption and barge-in behavior
- VOICE-005: call-center integration assumptions and provider comparison

