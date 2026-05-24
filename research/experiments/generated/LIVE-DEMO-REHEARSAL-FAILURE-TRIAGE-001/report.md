# LIVE-DEMO-REHEARSAL-FAILURE-TRIAGE-001 Report

## Summary
- Total rehearsal records: `0`
- Flagged records: `0`
- Current-runtime-marked records: `0`
- Unknown-version records: `430`

## Freshness Summary
- `stale_pre_current_runtime_artifact`: `84`
- `unknown_version_private_artifact`: `430`

## Current Runtime Defect Count
- `current_live_runtime_defect`: `0`
- Unknown-version private records are not counted as current runtime defects.

## Classification Counts
- `current_live_runtime_defect`: `0`
- `evidence_generator_false_positive`: `0`
- `expected_terminal_or_error_record`: `0`
- `incomplete_or_invalid_private_record`: `0`
- `needs_human_review`: `0`
- `provider_audio_artifact_issue`: `0`
- `stale_pre_current_runtime_artifact`: `0`
- `unknown_version_private_artifact`: `0`

## Mechanical Issue Counts

## Provider Audio Issue Classification
- Provider audio artifact issues: `0`

## Missing Response/TTS Classification
- Incomplete or invalid private records: `0`

## Issue Counts By Freshness Classification

## Issue Counts By Campaign

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
