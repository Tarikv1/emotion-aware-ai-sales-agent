# VOICE-001 TTS Response Prototype

## Experiment Goal

Test whether the realtime sales-agent core can produce a traceable response that is ready for text-to-speech without changing the underlying campaign architecture.

This experiment treats voice as an interface layer around the reusable sales-agent core.

## Input

- Campaign: `campaign-prod-005-b2c-telecom`
- Stage: `relevance-check`
- Transcript: `Nur wenn Sie garantieren koennen, dass es stabil ist.`
- Provider mode: `dry-run`
- Voice style: `neutral-synthetic-test`

## Runtime Decision

The realtime turn engine classified the transcript as a claim-boundary case:

- Detected emotion: `skeptical-or-negative`
- Sales difficulty: `claim-boundary`
- Interest state: `needs-human`
- Selected strategy: `inquiry`
- Next action: `escalate`
- Call control: `transfer-or-escalate`

The selected response was:

```text
Ich moechte nichts garantieren, was von den Details abhaengt. Ich kann das an einen Spezialisten weiterleiten.
```

The packet records `campaign.language`, `decision.campaign_language`, and `decision.response_language` as `de`.

## Generated Artifact

```text
research/experiments/generated/VOICE-001-tts-packet.json
```

The artifact stores the full realtime decision and the TTS packet metadata. The `tts_text` field matches `decision.agent_response`.

## Safety Result

VOICE-001 uses metadata-only dry-run mode by default:

- no real voice cloning
- no microphone input
- no call recording
- no API key requirement
- no cloud TTS dependency
- no product-specific sales brain

## Interpretation

VOICE-001 confirms the project can add a voice output layer while preserving the vertical-agnostic sales-agent architecture.

The next useful step is VOICE-002, which should test speech-to-text from recorded audio while keeping consent and privacy constraints explicit.
