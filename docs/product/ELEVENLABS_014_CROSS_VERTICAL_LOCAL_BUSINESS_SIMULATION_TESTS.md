# ELEVENLABS-014 Cross-Vertical Local-Business Simulation Tests

Package ID: `ELEVENLABS-014-cross-vertical-local-business-simulation-tests`

## Decision

The next useful test is not another Mike's Kitchen variant. That would mostly
retest restaurant-specific wording. The risk after `RAG-023` is broader: the
agent may look stable on one restaurant campaign while failing to adapt the same
sales behavior to other local-business verticals.

This checkpoint adds a deterministic cross-vertical simulation pack for the
ElevenLabs dashboard Simulation Tests surface. It uses synthetic evaluation
fixtures, not real prospects and not campaign-profile replacements.

These are synthetic evaluation fixtures only.

## What This Adds

- `runtime/providers/elevenlabs_agents/tests/web_design_cross_vertical_local_business_simulation_tests.json`
- `runtime/providers/elevenlabs_agents/manifests/web_design_cross_vertical_local_business_simulation_tests.package.json`
- `scripts/validate_elevenlabs_014_cross_vertical_local_business_simulation_tests.py`

Target folder for a future provider upload:

`Atlas Web Studio - Cross-Vertical Local Business Simulation V1`

## Scenario Coverage

- plumbing company defending Google emergency-call status quo
- dental office manager protecting compliance and new-patient claim boundaries
- auto repair owner pressing on catch, price, and trust claims
- HVAC dispatcher where callback brevity matters more than pitching
- hair salon owner defending Instagram and DM appointment flow
- home-cleaning gatekeeper who can only pass a short note or callback window

## Why Deterministic, Not Random

Random local-business generation would create noisy failures. A failed live run
would be harder to debug because the scenario itself could change.

This pack is dynamic in the useful ElevenLabs sense: each simulation carries its
own business-specific dynamic variables. It is deterministic so repeated runs
can be compared against the same verticals, pressures, and success criteria.

## Evaluation Target

The pack checks whether the current hosted web-design agent can:

- use per-test dynamic variables rather than Mike's Kitchen defaults
- avoid restaurant leakage in non-restaurant calls
- rotate value angles by vertical
- keep the free-mockup assurance and price boundaries intact
- preserve callback, gatekeeper, refusal, and send-path closings

This is not a campaign-profile replacement. If a real plumber, dental office,
or HVAC campaign is launched, it still needs its own campaign overlay and
campaign profile/facts file.

## Commands

Validate without provider calls:

```powershell
python scripts\validate_elevenlabs_014_cross_vertical_local_business_simulation_tests.py
```

Build the dry-run API request bundle:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_cross_vertical_local_business_simulation_tests.package.json `
  --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty `
  --test-folder-name "Atlas Web Studio - Cross-Vertical Local Business Simulation V1" `
  --out research\experiments\generated\ELEVENLABS-014-cross-vertical-local-business-simulation-tests\simulation_tests_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-014-cross-vertical-local-business-simulation-tests\simulation_tests_requests.json
```

Create the simulation tests in ElevenLabs after explicitly loading
`ELEVENLABS_API_KEY` into the process environment:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_cross_vertical_local_business_simulation_tests.package.json `
  --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty `
  --test-folder-name "Atlas Web Studio - Cross-Vertical Local Business Simulation V1" `
  --operation create-tests `
  --live `
  --confirm-provider-write `
  --out research\experiments\generated\ELEVENLABS-014-cross-vertical-local-business-simulation-tests\simulation_tests_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-014-cross-vertical-local-business-simulation-tests\simulation_tests_requests.json
```

## Boundary

- Provider writes remain blocked by default.
- No private customer data is included.
- No customer audio is included.
- No API key value is stored in tracked files.
- Synthetic businesses are evaluation fixtures only.
- Passing this pack would not prove production readiness.
- Failing this pack would be useful evidence that the current hosted web-design
  agent is still too restaurant-specific.

provider writes remain blocked unless explicitly requested.
