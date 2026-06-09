# ELEVENLABS-028 Emotional Resistance Dynamic Simulation Tests

Checkpoint ID: `ELEVENLABS-028-emotional-resistance-dynamic-simulation-tests`

## Purpose

Add a separate Atlas Web Studio simulation pack for angry, avoidant, suspicious, terse, and bad-fit buyer behavior.

This is a test-only package. It does not change the active prompt, KB, first message, dynamic defaults, Analysis config, or live agent attachment.

## Provider Target

- Agent: `web design`
- Agent ID: `agent_7801kt0g32zxf4f8x5zkykj7syty`
- Test folder: `Atlas Web Studio - Emotional Resistance Dynamic Simulation V1`
- Test type: ElevenLabs simulation
- Simulated user model: `gemini-2.5-flash`
- Evaluation model: `gemini-2.5-flash`
- Maximum turns: `16-20`

## Files

- Manifest: `runtime/providers/elevenlabs_agents/manifests/web_design_emotional_resistance_dynamic_simulation_tests.package.json`
- Tests: `runtime/providers/elevenlabs_agents/tests/web_design_emotional_resistance_dynamic_simulation_tests.json`
- Validator: `scripts/validate_elevenlabs_028_emotional_resistance_dynamic_simulation_tests.py`

## Coverage

The suite adds eight simulation scenarios:

- angry owner interruption
- initial refusal that is not yet a do-not-call request
- scam or hidden-contract suspicion
- terse low-information buyer
- rapid-fire status quo objections
- hostile price and hidden-cost concerns
- angry spoken-email two-step close
- guaranteed SEO, calls, or pay-per-lead bad-fit disqualification

Each case uses dynamic variables for business context, buyer emotional state, conversation pressure, persuasion boundary, primary value mechanism, target outcome, and expected turn range.

## Contract

These tests stress persuasion under pressure without allowing unsafe chasing.

The agent should:

- use short spoken turns
- answer the current buyer move instead of dumping every value point
- persuade once when resistance is not a hard stop
- stop immediately on hard stop or do-not-call
- avoid guaranteed rankings, traffic, customers, calls, jobs, bookings, or revenue
- ask for email only after a real send signal
- confirm normalized email after email is provided
- close naturally after email confirmation
- disqualify buyers who only want guaranteed SEO or pay-per-lead performance

## Boundary

The suite uses deterministic synthetic local-business fixtures only. It contains no private customer data, no private transcripts, no customer audio, and no API keys.

provider writes remain blocked unless the operator explicitly runs the automation with `--live --confirm-provider-write`.

Passing these tests is not proof of production phone-call readiness. A live simulation run and human transcript review are still required.
