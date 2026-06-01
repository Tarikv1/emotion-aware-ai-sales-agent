# ElevenLabs Upload Checklist

This is a reference checklist for the manual ElevenLabs dashboard setup. Do not upload this checklist.

Brand/caller values for this internal test package:

- Agency name: Atlas Web Studio
- Agent name: Emma
- Placeholder count in uploadable files: 0

## Upload

- Use `01_agent_system_prompt.md` as the system prompt.
- Add these knowledge files:
  - `02_website_offer_and_packages.md`
  - `03_vertical_playbooks.md`
  - `04_objection_handling_playbook.md`
  - `05_discovery_and_qualification.md`
  - `06_close_paths.md`
  - `07_compliance_and_calling_boundaries.md`

## Do Not Upload

- `result.json`
- `report.md`
- `00_dashboard_upload_checklist.md`
- `08_manual_eval_script.md`
- `09_upload_manifest.json`
- `10_tests_to_create_in_elevenlabs.md`

## Setup Boundaries

- Atlas Web Studio is an internal testing brand for now.
- Do not claim trademark clearance, domain availability, social handle availability, or public launch readiness.
- Keep outbound calling disabled.
- Keep autodialing disabled.
- Keep API, provider, model, and TTS actions disabled unless a later reviewed setup explicitly allows them.
- Keep CRM, email, calendar, payment, and account actions disabled.
- Do not import scraped leads.
- Do not use private transcript or private audio.
- Run manual tests before any buyer contact.
- Complete compliance review before real calls.

## Manual Setup Checks

- Confirm the voice agent identifies itself as Emma from Atlas Web Studio.
- Confirm no prompt or knowledge file says the agent is Google, Meta, Yelp, OpenAI, a directory, a review platform, a chamber of commerce, or the local business.
- Confirm the agent refuses lead, revenue, and ranking guarantees.
- Confirm stop requests end the interaction immediately.
- Confirm the first conversion goal is the free mockup/demo, not payment.
