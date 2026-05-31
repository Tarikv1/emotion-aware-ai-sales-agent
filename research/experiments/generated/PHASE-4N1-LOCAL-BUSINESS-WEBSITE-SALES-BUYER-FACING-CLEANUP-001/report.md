# 4N1 Local Business Website Sales Buyer-Facing Cleanup Report

## Outcome

Created a cleaned successor to 4N0 for manual ElevenLabs setup. The upload-facing prompt and knowledge files now sound like an official sales agent for the agency, not a bot rehearsal, evaluator, or engineering artifact.

Recommendation: upload 4N1, not 4N0.

## What Was Fixed From 4N0

- Removed buyer-facing references to scripts, simulated runs, unavailable tools, and engineering labels.
- Rewrote the system prompt around direct selling, quick diagnosis, business value, and a free mockup/demo micro-close.
- Reworked objections so each response has acknowledgement, business-value reframe, low-risk mockup close, and a clean exit.
- Added missing objection paths for wrong person and stop calling.
- Split compliance into buyer-facing boundaries and internal deployment restrictions.
- Updated upload mapping so only the system prompt and selected knowledge files are uploaded.

## Files Ready To Upload

- `01_agent_system_prompt.md` as the ElevenLabs system prompt.
- `02_website_offer_and_packages.md` as knowledge.
- `03_vertical_playbooks.md` as knowledge.
- `04_objection_handling_playbook.md` as knowledge.
- `05_discovery_and_qualification.md` as knowledge.
- `06_close_paths.md` as knowledge.
- `07_compliance_and_calling_boundaries.md` as knowledge, because buyer-facing and internal sections are clearly separated.

## Files Not To Upload

- `result.json`
- `report.md`
- `00_dashboard_upload_checklist.md`
- `08_manual_eval_script.md`
- `09_upload_manifest.json`
- `10_tests_to_create_in_elevenlabs.md`

## Buyer-Facing Phrase Cleanup Summary

- Buyer-facing internal-test phrase count: 0
- RouteSignal references in buyer-facing files: 0
- Northstar references in buyer-facing files: 0
- Fake third-party identity claims: 0
- Fake lead, revenue, or ranking guarantees: 0
- Bracketed emotion/internal labels: 0

## Remaining Manual Step

Before uploading to ElevenLabs, replace every `[AGENCY_NAME]` placeholder with the real agency name. Do not upload with the placeholder still present.

## Safety Confirmations

- No real outbound calls enabled.
- No provider calls made.
- No ElevenLabs calls made.
- No OpenAI API calls made.
- No model or TTS calls made.
- No CRM calls made.
- No email calls made.
- No calendar calls made.
- No payment calls made.
- No account side effects made.
- No live readiness claimed.
