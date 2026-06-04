# ELEVENLABS-004 Mike's Kitchen Dynamic Tests

Package ID: `ELEVENLABS-004-mikes-kitchen-dynamic-tests`

## Decision

Campaign-specific ElevenLabs tests should be created from repo-owned JSON test
packs with explicit dynamic variables.

The Mike's Kitchen values are not treated as private customer data in this
checkpoint. They are synthetic/sample campaign values for the Atlas Web Studio
restaurant website outreach demo.

## What This Adds

- `runtime/providers/elevenlabs_agents/tests/web_design_mikes_kitchen_dynamic_tests.json`
- `runtime/providers/elevenlabs_agents/manifests/web_design_mikes_kitchen_tests.package.json`
- automation support for suite-level and per-test `dynamic_variables`
- `scripts/validate_elevenlabs_004_mikes_kitchen_dynamic_tests.py`

The test pack includes ten response tests covering:

- permission-based opener with known restaurant context
- Instagram and Google Maps context without redundant discovery
- phone-reservation-path positioning
- busy owner brevity
- non-decision-maker routing
- no-full-website objection handling
- free mockup and pricing boundary
- send-info without invented contact details
- reservation guarantee boundary
- do-not-call stop rule

## Commands

Validate without provider calls:

```powershell
python scripts\validate_elevenlabs_004_mikes_kitchen_dynamic_tests.py
```

Build the dry-run API request bundle:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_mikes_kitchen_tests.package.json `
  --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty `
  --out research\experiments\generated\ELEVENLABS-004-mikes-kitchen-dynamic-tests\automation_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-004-mikes-kitchen-dynamic-tests\api_requests.json
```

Create the tests in ElevenLabs after loading `ELEVENLABS_API_KEY` into the
process environment:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_mikes_kitchen_tests.package.json `
  --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty `
  --operation create-tests `
  --live `
  --confirm-provider-write `
  --out research\experiments\generated\ELEVENLABS-004-mikes-kitchen-dynamic-tests\automation_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-004-mikes-kitchen-dynamic-tests\api_requests.json
```

## Boundary

- The tests are created in the ElevenLabs Tests surface.
- The tests are not attached to the agent by PATCH in this checkpoint.
- Test output stores safe provider response summaries only.
- The API key remains environment-only and must not be committed.
- Real client campaign facts require a separate privacy review before upload.
