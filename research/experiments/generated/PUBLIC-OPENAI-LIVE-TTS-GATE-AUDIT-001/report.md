# PUBLIC-OPENAI-LIVE-TTS-GATE-AUDIT-001

- Status: `pass`
- Classification: `none`
- Reason: Live TTS gate, ElevenLabs call, and audio artifact evidence are present.
- Latest current packet: `data/private/live-demo-001/LIVE-DEMO-001-turn-20260525-030205.json`
- Matching packet count: `50`
- Current packet count: `9`
- Live TTS enabled: `true`
- Live TTS used: `true`
- ElevenLabs call made: `true`
- TTS provider calls made: `true`
- Audio file created: `true`
- Generic live TTS allowed: `true`
- Fallback reason: `None`

## Gate Fields

```json
{
  "audio_file_created": true,
  "elevenlabs_call_made": true,
  "fallback_reason": null,
  "generic_live_tts_allowed": true,
  "http_status": 200,
  "live_tts_enabled": true,
  "live_tts_used": true,
  "provider_id": "elevenlabs-stream",
  "response_content_type": "audio/mpeg",
  "selected_campaign_id": "public-openai-chatgpt-plans",
  "selected_campaign_path": "runtime/campaigns/examples/public-openai-chatgpt-plans.json",
  "selected_mode": "generic config live TTS gated",
  "tts_provider_calls_made": true
}
```
