# LIVE-DEMO-OPERATOR-REHEARSAL-001

Status: pass
Failure count: 0

## Dry-Run Start

- `python scripts\run_live_demo_001_agent_voice_call.py --force-key-missing`

## Rehearsal Sequences

- RouteSignal: `__agent_open__`, `yeah sure`, `callbacks are fine`.
- Insurance generic: `__agent_open__`, `yeah sure`, `premium is a problem`, `tomorrow at 3 works`.
- B2B generic: `__agent_open__`, `yeah sure`, `manual work is a problem`, `tomorrow at 3 works`.

## Invalid Config

- Result: HTTP 400

## Transcript Capture

- Required fields: `live_demo_id`, `session_id`, `campaign_id` or `campaign_config_path`, `turns`, per-turn `campaign_selector`, per-turn `provider_boundary`.

## Safety Boundary

- Provider calls made: `false`
- Local LLM calls made: `false`
- Live TTS used: `false`
- Email/calendar/CRM writes: `false`
- PROD-102 opened: `false`

## Manual Checklist

- `docs\demo\LIVE_DEMO_OPERATOR_REHEARSAL.md`

## Failures

- None
