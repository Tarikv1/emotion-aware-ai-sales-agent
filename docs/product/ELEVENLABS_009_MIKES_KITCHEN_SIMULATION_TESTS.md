# ELEVENLABS-009 Mike's Kitchen Simulation Tests

Package ID: `ELEVENLABS-009-mikes-kitchen-simulation-tests`

## Decision

The current next-reply tests are too narrow to prove whether the agent can sell
through a dynamic conversation. They only evaluate one response after a fixed
history.

This checkpoint adds ElevenLabs `simulation` tests. These tests define the
buyer scenario, the full-conversation success condition, dynamic variables, and
maximum conversation turns. They do not preload exact 8-10 turn transcripts.

## What This Adds

- `runtime/providers/elevenlabs_agents/tests/web_design_mikes_kitchen_simulation_tests.json`
- `runtime/providers/elevenlabs_agents/manifests/web_design_mikes_kitchen_simulation_tests.package.json`
- `scripts/validate_elevenlabs_009_mikes_kitchen_simulation_tests.py`
- simulation-test support in `runtime/providers/elevenlabs_agents/automation.py`

The current repaired ElevenLabs test folder is:

`Atlas Web Studio - Mike's Kitchen Simulation Repair V17`

## Scenario Coverage

- skeptical owner who needs concrete value before reviewing the mockup
- cost-sensitive owner asking about catch, surprise pricing, and website cost
- busy manager where callback brevity matters more than pitching
- gatekeeper who can only pass along a short note or callback time
- phone-only reservation boundary with no online booking push
- confused buyer asking for plain-language explanation
- Instagram and Google Maps objection without attacking existing channels
- clear refusal and reachable do-not-call handling
- optional booking as future scope only when the buyer opens the door

## Commands

Validate without provider calls:

```powershell
python scripts\validate_elevenlabs_009_mikes_kitchen_simulation_tests.py
```

Build the dry-run API request bundle:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_mikes_kitchen_simulation_tests.package.json `
  --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty `
  --test-folder-name "Atlas Web Studio - Mike's Kitchen Simulation Repair V17" `
  --out research\experiments\generated\ELEVENLABS-009-mikes-kitchen-simulation-tests\simulation_tests_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-009-mikes-kitchen-simulation-tests\simulation_tests_requests.json
```

Create the simulation tests in ElevenLabs and move them into the folder after
loading `ELEVENLABS_API_KEY` into the process environment:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_mikes_kitchen_simulation_tests.package.json `
  --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty `
  --test-folder-name "Atlas Web Studio - Mike's Kitchen Simulation Repair V17" `
  --operation create-tests `
  --live `
  --confirm-provider-write `
  --out research\experiments\generated\ELEVENLABS-009-mikes-kitchen-simulation-tests\simulation_tests_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-009-mikes-kitchen-simulation-tests\simulation_tests_requests.json
```

Run the created simulation tests:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_mikes_kitchen_simulation_tests.package.json `
  --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty `
  --operation run-tests `
  --created-test-ids <test_id_1> <test_id_2> `
  --live `
  --confirm-provider-write `
  --out research\experiments\generated\ELEVENLABS-009-mikes-kitchen-simulation-tests\simulation_run_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-009-mikes-kitchen-simulation-tests\simulation_run_requests.json
```

## Boundary

- These are dashboard Simulation Tests, not next-reply tests.
- The test scenarios are synthetic and public-safe. No client private data is
  included.
- Passing these tests is evidence of better dynamic behavior, not proof of real
  outbound-call performance.
- Real production calls still need live conversation review and a growing
  regression set from actual failed calls.

## Live Result

Repaired V17 suite is the current human-reviewed repair clean target. V17 keeps
the real failures in scope: repeated closes before softening, weak campaign-value
rotation, direct price/hosting answers, terminal closings, and unapproved
bracketed delivery tags. It does not treat normal bare words like `Great` or
`Perfect` as an automatic failure unless they are used as bracketed content-like
tags or scripted openers.

Current V17 suite created and ran on 2026-06-05:

- folder: `Atlas Web Studio - Mike's Kitchen Simulation Repair V17`
- folder ID: `tfld_6201ktd2m9ywexx8tbbpktt8z23r`
- suite ID: `suite_6201ktd2ndhpf6psdpyej9x4ae2w`
- result: `9/9` simulation tests passed
- sanitized summary: `research/experiments/generated/ELEVENLABS-009-mikes-kitchen-simulation-tests/simulation_results_summary.json`

Previous repaired V2 suite created and ran on 2026-06-05:

- folder: `Atlas Web Studio - Mike's Kitchen Simulation Repair V2`
- folder ID: `tfld_6801ktcf5vy8f06854rjwn763rxw`
- suite ID: `suite_6501ktcfdp4nf51tjd0cfajkcgtq`
- result: `9/9` simulation tests passed
- sanitized summary: `research/experiments/generated/ELEVENLABS-009-mikes-kitchen-simulation-tests/simulation_results_summary.json`

This was useful evidence, but it is no longer sufficient by itself. The original
009 baseline passed too easily, and later human review exposed repeated-close,
weak campaign-value, direct-cost-answer, and terminal-closing defects. V8-V16
also exposed a persistent Instagram/Google Maps value-rotation failure before
V17 passed. Do not treat any green suite as final production approval until
transcripts continue to pass human review.

## Audio Tag Note

Suggested audio tags such as warm, patient, confident, or calm may help spoken
delivery, but they are secondary to conversation strategy. These simulation
tests should not treat one approved delivery tag as the main failure when the
sales behavior is sound. They should still fail unapproved bracketed delivery
tags, tag spam, content-like tags such as `[Great]`, or fake reactions such as
giggling.
