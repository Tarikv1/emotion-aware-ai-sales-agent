# ELEVENLABS-001 Universal Sales Core

Package ID: `ELEVENLABS-001-universal-sales-core`

## Decision

Repo remains the source of truth.

ElevenLabs dashboard is the managed runtime and manual upload surface.

This checkpoint creates the first curated universal sales knowledge package for
ElevenLabs Agents. It does not create a provider-side agent, call the ElevenLabs
API, upload documents, or change live runtime behavior.

No live provider call is made by this checkpoint.

## Why This Is Narrow

A large raw sales dump would be weak retrieval material. It would add noise,
conflicting advice, and generic coaching language. The better first package is a
compact operating core that teaches stable boundaries:

- permission-based cold-call framing
- observable customer-state reading
- objection handling
- ethical persuasion
- low-pressure meeting setting
- campaign-fact priority
- hard stop rules

Universal sales advice must stay subordinate to campaign facts.

The next campaign package can add the website-business offer, approved claims,
mockup/demo close, qualification fields, and campaign-specific tests.

## Files

- `runtime/providers/elevenlabs_agents/README.md`
- `runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_core.md`
- `runtime/providers/elevenlabs_agents/tests/universal_sales_core_baseline_tests.json`
- `runtime/providers/elevenlabs_agents/manifests/universal_sales_core.package.json`
- `scripts/validate_elevenlabs_001_universal_sales_core.py`

## Boundaries

- Provider calls: `false`
- Private customer data used: `false`
- Provider credential required: `false`
- Dashboard edits as source of truth: `false`
- Campaign-specific facts required before customer use: `true`
- Production customer calls allowed: `false`

## Validation

Run:

```powershell
python scripts\validate_elevenlabs_001_universal_sales_core.py
```

The validator checks package shape, required sales boundaries, baseline test
coverage, no tracked private-data markers, no credential markers, runtime
manifest visibility, and no provider-call unblocking.

