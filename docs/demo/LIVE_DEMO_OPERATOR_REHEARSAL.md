# LIVE-DEMO Operator Rehearsal

This checklist is for a local dry-run browser rehearsal before any provider-audio testing. It uses synthetic demo inputs only. It does not require a real microphone, live TTS, provider calls, email, calendar, CRM, or PROD-102.

## Start Dry-Run Demo

From `D:\Codex\active\emotion-aware-ai-sales-agent`:

```powershell
python scripts\run_live_demo_001_agent_voice_call.py --force-key-missing
```

Open the printed local URL, normally `http://127.0.0.1:8781/`.

Do not pass `--live-tts`. The operator rehearsal is dry-run only.

## Select RouteSignal

RouteSignal is the default when no generic campaign config is selected.

1. Open the campaign selector.
2. Choose the RouteSignal live demo option, or leave the default selected.
3. Confirm the selected campaign metadata panel shows:
   - `campaign_id`
   - `vertical_id`
   - `product_or_offer_name`
   - `appointment_target`
   - `human_followup_owner`
   - `config_path: (none)`
   - `mode: RouteSignal live-demo`

RouteSignal-specific wording is allowed only on this default path.

## Select Generic Campaign Config

1. Open the campaign selector.
2. Choose one option under generic campaign config / generic dry-run campaigns.
3. Confirm the selected campaign metadata panel updates:
   - `campaign_id`
   - `vertical_id`
   - `product_or_offer_name`
   - `appointment_target`
   - `human_followup_owner`
   - `config_path`
   - `mode: generic config dry-run`
4. Confirm the visible warning appears:

`Generic campaign configs run dry-run TTS by default. No provider calls are made.`

## Manual Typed-Turn Rehearsal

Use this typed-turn rehearsal when you want deterministic operator practice without microphone or browser ASR.

This path avoids microphone use.

1. Do not start live TTS.
2. Do not check microphone consent unless you intentionally want browser ASR.
3. Type `__agent_open__` into the transcript box.
4. Click `Send To Agent`.
5. Continue with typed turns.

RouteSignal rehearsal:

```text
__agent_open__
yeah sure
callbacks are fine
```

Insurance generic rehearsal:

```text
__agent_open__
yeah sure
premium is a problem
tomorrow at 3 works
```

B2B generic rehearsal:

```text
__agent_open__
yeah sure
manual work is a problem
tomorrow at 3 works
```

## Browser Fallback Voice Only

Browser fallback voice is manual and browser-local.

1. Run the demo without `--live-tts`.
2. Submit a typed turn.
3. After the response appears, click `Browser Fallback Voice`.
4. Confirm no audio file is required and the provider boundary remains false.

Do not treat browser fallback voice as provider TTS. It is only a local browser playback aid for rehearsal.

## Diagnostics To Check

In `Decision`, `Provider Boundary`, and the transcript diagnostics, check:

- `campaign_selector_mode`
- `campaign_config_path`
- `selected_campaign_config`
- `campaign_id`
- `campaign_playbook_id`
- `vertical_id`
- `provider_calls_made`
- `local_llm_calls_made`
- `live_tts_used`
- `sends_email`
- `creates_calendar_event`
- `writes_crm`
- `opens_prod_102`

Expected dry-run safety values:

```json
{
  "provider_calls_made": false,
  "local_llm_calls_made": false,
  "live_tts_used": false,
  "sends_email": false,
  "creates_calendar_event": false,
  "writes_crm": false,
  "opens_prod_102": false
}
```

## Transcript Export

Use:

- `Download JSON`
- `Download TXT`

The JSON export should include:

- `live_demo_id`
- `session_id`
- `campaign_id` or `campaign_config_path`
- `turns`
- per-turn `campaign_selector`
- per-turn `provider_boundary`

Keep exported rehearsal transcripts local unless they contain only synthetic demo content.

## Invalid Config Rehearsal

If a selected generic config is invalid, the UI should:

- show a clear operator-facing error
- keep listening paused/stopped
- not speak fallback text
- not restart listening automatically
- not fall back to RouteSignal

The error payload should show `route_signal_fallback_used: false`.

## Do Not Do

- do not enable live TTS
- do not use real customer data
- do not paste private transcripts
- do not use PROD-102
- do not expect email/calendar/CRM writes
- do not expect generated audio in dry-run mode
- do not interpret typed rehearsal output as a real customer record
