# ELEVENLABS-VOICE-RESOLUTION-AUDIT-001

- Status: `pass`
- Active evidence source: `latest_current_private_openai_live_packet`
- Voice ID source: `local_voice_ids:elevenlabs.en`
- Voice ID present: `true`
- Voice ID length: `20`
- Voice ID hash: `433413ba`
- Raw value logged: `false`
- Hardcoded voice findings: `0`
- Raw logging findings: `0`
- Voice source expectation: `non_env_source_observed_review_operator_environment`

## Current Packet Voice Diagnostics

```json
{
  "raw_value_logged": false,
  "voice_id_hash": "433413ba",
  "voice_id_length": 20,
  "voice_id_present": true,
  "voice_id_source": "local_voice_ids:elevenlabs.en"
}
```

## Precedence

1. ELEVENLABS_VOICE_ID_EN from active process environment
2. ELEVENLABS_VOICE_ID from active process environment
3. runtime/config/local/voice_ids.json if present
4. config/local/voice_ids.json legacy local fallback if runtime local file is absent
5. no documented fallback voice id if no env/config exists
