# ELEVENLABS-VOICE-RESOLUTION-AUDIT-001

- Status: `pass`
- Voice ID source: `local_voice_ids:elevenlabs.en`
- Voice ID present: `true`
- Voice ID length: `20`
- Voice ID hash: `433413ba`
- Raw value logged: `false`
- Hardcoded voice findings: `0`
- Raw logging findings: `0`

## Precedence

1. ELEVENLABS_VOICE_ID_EN from active process environment
2. ELEVENLABS_VOICE_ID from active process environment
3. runtime/config/local/voice_ids.json if present
4. config/local/voice_ids.json legacy local fallback if runtime local file is absent
5. no documented fallback voice id if no env/config exists
