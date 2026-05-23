# LIVE-DEMO-REHEARSAL-FAILURE-TRIAGE-001 Report

## Summary
- Total rehearsal records: `460`
- Flagged records: `78`
- Current-runtime-marked records: `0`
- Unknown-version records: `425`

## Freshness Summary
- `stale_pre_current_runtime_artifact`: `35`
- `unknown_version_private_artifact`: `425`

## Current Runtime Defect Count
- `current_live_runtime_defect`: `0`
- Unknown-version private records are not counted as current runtime defects.

## Classification Counts
- `current_live_runtime_defect`: `0`
- `evidence_generator_false_positive`: `0`
- `expected_terminal_or_error_record`: `0`
- `incomplete_or_invalid_private_record`: `0`
- `needs_human_review`: `0`
- `provider_audio_artifact_issue`: `2`
- `stale_pre_current_runtime_artifact`: `0`
- `unknown_version_private_artifact`: `104`

## Mechanical Issue Counts
- `audio_url_missing_when_provider_called`: `1`
- `call_control_unexpected`: `19`
- `final_response_missing`: `27`
- `provider_audio_failed`: `1`
- `repeated_response`: `28`
- `response_too_long_for_live_voice`: `3`
- `tts_input_missing`: `27`

## Provider Audio Issue Classification
- Provider audio artifact issues: `2`

## Missing Response/TTS Classification
- Incomplete or invalid private records: `0`

## Issue Counts By Freshness Classification
- `stale_pre_current_runtime_artifact`: {'call_control_unexpected': 1}
- `unknown_version_private_artifact`: {'audio_url_missing_when_provider_called': 1, 'call_control_unexpected': 18, 'final_response_missing': 27, 'provider_audio_failed': 1, 'repeated_response': 28, 'response_too_long_for_live_voice': 3, 'tts_input_missing': 27}

## Issue Counts By Campaign
- `campaign-prod-005-b2b-software`: {'audio_url_missing_when_provider_called': 1, 'call_control_unexpected': 16, 'final_response_missing': 17, 'provider_audio_failed': 1, 'repeated_response': 21, 'response_too_long_for_live_voice': 3, 'tts_input_missing': 17}
- `campaign-prod-005-b2c-telecom`: {'repeated_response': 3}
- `synthetic-automotive-service-review`: {'repeated_response': 2}
- `synthetic-insurance-review`: {'call_control_unexpected': 2, 'repeated_response': 2}
- `synthetic-telecom-plan-review`: {'call_control_unexpected': 1}
- `unknown`: {'final_response_missing': 10, 'tts_input_missing': 10}

## Safety Boundary Summary
- Future metadata probe provider calls made: `false`
- Future metadata probe live TTS calls made: `false`
- Future metadata probe local LLM calls made: `false`
- Validator provider/TTS/LLM/email/calendar/CRM/PROD-102 side effects: `false`

## Clean Current Evidence Instructions
1. Pull latest `main`.
2. Start a fresh dry-run demo with `python scripts\run_live_demo_001_agent_voice_call.py --force-key-missing`.
3. Run RouteSignal normal path: permission, `callbacks are a problem`, `it causes delays`, `tomorrow at 3 works`.
4. Run generic insurance path: select synthetic insurance, product-detail question, tentative coverage fit, active confirmation, impact.
5. Run ASR stress path: `yeah that would be good`, `okay that would be good`, `call me tomorrow at 3`, then noisy/short phrases.
6. Run campaign selector switch path: RouteSignal -> synthetic insurance -> RouteSignal, and confirm metadata does not mix.
7. Regenerate `LIVE-DEMO-COMMERCIAL-REHEARSAL-001` and check `current_runtime_marked_record_count`.

## Recommended Patch Scope
- Do not patch dialogue behavior from unknown-version private artifacts.
- Patch only after a current-runtime-marked rehearsal reproduces a classified current defect.
