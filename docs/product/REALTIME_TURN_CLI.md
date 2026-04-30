# Realtime Turn CLI

## Purpose

`scripts/realtime_turn_cli.py` is the first executable single-turn prototype for the real-time sales-agent core.

It accepts one customer transcript, campaign ID, and call stage, then returns the runtime decision that the live system would use before speaking.

This is still deterministic and text-based. It does not yet connect to speech-to-text, text-to-speech, telephony, CRM, or calendar systems.

## Example

```powershell
python scripts\realtime_turn_cli.py `
  --campaign campaign-prod-005-b2c-telecom `
  --stage relevance-check `
  --transcript "Nur wenn Sie garantieren koennen, dass es stabil ist."
```

Expected behavior:

```json
{
  "response_mode": "fast-response",
  "sales_difficulty": "claim-boundary",
  "interest_state": "needs-human",
  "next_action": "escalate",
  "call_control": "transfer-or-escalate"
}
```

## Supported Input Types

- `speech-final`: normal finalized customer transcript
- `voicemail-detected`: voicemail or answering machine detected
- `silence-timeout`: no customer response after retry handling

Silence example:

```powershell
python scripts\realtime_turn_cli.py `
  --campaign campaign-prod-005-b2c-energy `
  --stage opening-permission `
  --input-type silence-timeout `
  --silence-count 2
```

## Output Fields

The CLI returns:

- campaign metadata
- input stage and transcript
- `response_mode`
- `first_response_latency_budget_ms`
- observed local decision latency
- background modules
- detected emotion
- sales difficulty
- interest state
- selected strategy
- next action
- call control
- agent response

## Product Role

This CLI is the bridge between:

- `PROD-005` batch simulation
- future live speech input
- future voice/TTS response
- future CRM/calendar integrations

It proves the core runtime decision can be called turn-by-turn before building a UI or voice stack.
