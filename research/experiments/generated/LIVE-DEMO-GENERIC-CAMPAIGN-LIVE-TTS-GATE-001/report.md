# LIVE-DEMO-GENERIC-CAMPAIGN-LIVE-TTS-GATE-001

- Default generic dry-run: `passed`
- Blocked without explicit gate: `passed`
- Allowed with forced missing key: `passed`
- Metadata gate visibility: `passed`
- Browser HTML warnings: `passed`
- RouteSignal preservation: `passed`
- Generic selected live-gated forced missing: `passed`
- Provider calls made: `false`
- Customer audio sent to Python: `false`
- Customer audio sent to TTS provider: `false`

## Real Generic Insurance Live TTS Command

Run only after confirming ElevenLabs env/voice configuration and provider approval:

`python scripts\run_live_demo_001_agent_voice_call.py --campaign-config runtime/campaigns/examples/synthetic-insurance-review.json --live-tts --consent-confirmed --allow-generic-live-tts`

## Failures

- None
