# VOICE-002 Audio Input Prototype

## Experiment Goal

Test whether a recorded-audio artifact can enter the voice-agent pipeline, carry consent and transcript metadata, and route through the existing realtime sales-agent core.

This experiment validates the audio-input boundary, not production automatic speech recognition.

## Input

- Campaign: `campaign-prod-005-b2c-telecom`
- Stage: `relevance-check`
- Audio: `research/experiments/generated/VOICE-002/VOICE-002-customer-placeholder.wav`
- Audio type: synthetic placeholder WAV
- Transcript provider: `manual-transcript`
- Transcript: `Nur wenn Sie garantieren koennen, dass es stabil ist.`
- Consent confirmation: enabled for synthetic experiment audio

## Audio Metadata

The generated placeholder WAV is not a real customer recording.

- Format: `wav`
- Duration: `0.35` seconds
- Channels: `1`
- Sample rate: `8000` Hz
- Byte size: `5644`

## Runtime Decision

The transcript was routed through the realtime sales-agent core and classified as a claim-boundary case:

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

The audio-input path now passes the campaign profile into the realtime core, so the response language remains `de` for the German telecom campaign.

## Generated Artifacts

```text
research/experiments/generated/VOICE-002/VOICE-002-customer-placeholder.wav
research/experiments/generated/VOICE-002/VOICE-002-audio-input-packet.json
research/experiments/generated/VOICE-002/VOICE-002-listen.html
```

## Safety Result

VOICE-002 uses a safe `manual-transcript` adapter by default:

- no real customer recording required
- no cloud ASR dependency
- no API key requirement
- no voice cloning
- no production call storage
- explicit consent confirmation required

## Interpretation

VOICE-002 confirms that recorded-audio artifacts can be represented in the product architecture without changing the reusable sales-agent core.

The next useful step is a provider comparison milestone that evaluates automatic transcription options against the same adapter boundary.
