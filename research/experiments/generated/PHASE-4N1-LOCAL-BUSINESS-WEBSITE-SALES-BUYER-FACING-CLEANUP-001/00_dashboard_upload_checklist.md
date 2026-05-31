# ElevenLabs Upload Checklist

Before uploading to ElevenLabs, replace every [AGENCY_NAME] placeholder with the real agency name. Do not upload with the placeholder still present.

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

- Keep outbound calling disabled.
- Keep autodialing disabled.
- Keep API, provider, model, and TTS actions disabled unless a later reviewed setup explicitly allows them.
- Keep CRM, email, calendar, payment, and account actions disabled.
- Do not import scraped leads.
- Do not use private transcript or private audio.
- Run manual tests before any buyer contact.
- Complete compliance review before real calls.

## Manual Setup Checks

- Confirm the agency name replacement is complete.
- Confirm the voice agent identifies itself as calling from the agency.
- Confirm no prompt or knowledge file says the agent is Google, Meta, Yelp, OpenAI, a directory, a review platform, a chamber of commerce, or the local business.
- Confirm the agent refuses lead, revenue, and ranking guarantees.
- Confirm stop requests end the interaction immediately.
- Confirm the first conversion goal is the free mockup/demo, not payment.
