# PUBLIC-OPENAI-LIVE-TTS-GATE-AUDIT-001

- Status: `pass`
- Classification: `missing_live_tts_flag`
- Behavior: `intended_gate_behavior`
- Matching packets: `12`
- Selected mode: `generic config dry-run`
- Live TTS enabled: `false`
- Live TTS used: `false`
- Required command: `python scripts\run_live_demo_001_agent_voice_call.py --campaign-config runtime/campaigns/examples/public-openai-chatgpt-plans.json --live-tts --consent-confirmed --allow-generic-live-tts`

## Gate Fields

```json
{
  "audio_file_created": false,
  "fallback_reason": "dry-run-mode",
  "generic_selected_campaign_live_tts_allowed": false,
  "mode": "generic config dry-run",
  "packet_mode": "dry-run",
  "selected_live_tts_enabled": false,
  "tts_live_call_requested": false,
  "tts_provider_calls_made": false
}
```
