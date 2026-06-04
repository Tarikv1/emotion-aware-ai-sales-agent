# ELEVENLABS-005 Mike's Kitchen Scenario Tests

Package ID: `ELEVENLABS-005-mikes-kitchen-scenario-tests`

## Decision

Scenario tests should use multi-turn chat history plus dynamic variables.

ElevenLabs Scenario Testing evaluates one next agent response after a provided
conversation context. This checkpoint uses 8-10 chat-history messages per test
and keeps the final message as the buyer turn to satisfy the response-test
schema.

## What This Adds

- `runtime/providers/elevenlabs_agents/tests/web_design_mikes_kitchen_scenario_tests.json`
- `runtime/providers/elevenlabs_agents/manifests/web_design_mikes_kitchen_scenario_tests.package.json`
- support for explicit `chat_history` in the ElevenLabs automation runner
- support for creating or reusing an ElevenLabs test folder and bulk-moving
  created tests into it
- `scripts/validate_elevenlabs_005_mikes_kitchen_scenario_tests.py`

The target ElevenLabs test folder is:

`Atlas Web Studio - Mike's Kitchen Scenarios`

## Commands

Validate without provider calls:

```powershell
python scripts\validate_elevenlabs_005_mikes_kitchen_scenario_tests.py
```

Build the dry-run API request bundle:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_mikes_kitchen_scenario_tests.package.json `
  --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty `
  --test-folder-name "Atlas Web Studio - Mike's Kitchen Scenarios" `
  --out research\experiments\generated\ELEVENLABS-005-mikes-kitchen-scenario-tests\automation_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-005-mikes-kitchen-scenario-tests\api_requests.json
```

Create the scenario tests in ElevenLabs and move them into the folder after
loading `ELEVENLABS_API_KEY` into the process environment:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_mikes_kitchen_scenario_tests.package.json `
  --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty `
  --test-folder-name "Atlas Web Studio - Mike's Kitchen Scenarios" `
  --operation create-tests `
  --live `
  --confirm-provider-write `
  --out research\experiments\generated\ELEVENLABS-005-mikes-kitchen-scenario-tests\automation_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-005-mikes-kitchen-scenario-tests\api_requests.json
```

## Boundary

- The tests are created in the ElevenLabs Tests surface.
- The tests are moved into a named ElevenLabs test folder.
- The tests are not attached to the agent by PATCH in this checkpoint.
- Test output stores safe provider response summaries only.
- The API key remains environment-only and must not be committed.
- Real client campaign facts require a separate privacy review before upload.
