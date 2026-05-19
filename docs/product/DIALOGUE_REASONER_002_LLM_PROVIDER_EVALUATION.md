# DIALOGUE-REASONER-002 LLM Provider Evaluation

`DIALOGUE-REASONER-002` evaluates whether an external LLM can improve the structured dialogue reasoning layer from `DIALOGUE-REASONER-001`.

This is an evaluation harness, not a live-demo promotion. The live demo still uses the repository-owned deterministic runtime path unless a later checkpoint explicitly wires a proven reasoner into response composition.

`PROD-102 stays closed`.

## Goal

Run the same 30 frozen `DIALOGUE-REASONER-001` cases against a provider model and compare:

- structured JSON validity
- dialogue-act accuracy
- buyer-intent accuracy
- topic/stage/strategy accuracy
- safety-boundary accuracy
- latency
- provider errors
- cost/usage metadata when the provider returns it

## Provider Boundary

Dry-run is the default and makes no network calls.

Live provider evaluation requires both:

```powershell
--live --consent-confirmed
```

The runner uses an OpenAI-compatible chat/completions shape. It does not use a provider agent, voice API, audio upload, browser session, or telephony adapter.

Required live configuration:

```text
runtime/config/local/dialogue_reasoner.env
```

The local env file is ignored by git. A tracked example lives at `runtime/config/local/dialogue_reasoner.env.example`.

The file keys are:

```text
DIALOGUE_REASONER_API_KEY=
DIALOGUE_REASONER_BASE_URL=
DIALOGUE_REASONER_MODEL=
```

Do not commit API keys. Do not paste keys into docs, generated reports, screenshots, or chat. The validator removes common provider key environment variables before safety checks and asserts that key values are not logged.

## Files

- Provider client: `runtime/providers/dialogue_reasoner_llm_client.py`
- Runner: `scripts/run_dialogue_reasoner_002_provider_evaluation.py`
- Validator: `scripts/validate_dialogue_reasoner_002_provider_evaluation.py`
- Dry-run evidence:
  - `research/experiments/generated/DIALOGUE-REASONER-002/dry_run_result.json`
  - `research/experiments/generated/DIALOGUE-REASONER-002/dry_run_report.md`

## Commands

Validate the dry-run and missing-config provider boundary:

```powershell
python scripts\validate_dialogue_reasoner_002_provider_evaluation.py
```

Run default dry-run evidence:

```powershell
python scripts\run_dialogue_reasoner_002_provider_evaluation.py
```

Run a live provider evaluation only after filling the three local env values above:

```powershell
python scripts\run_dialogue_reasoner_002_provider_evaluation.py --live --consent-confirmed
```

## Acceptance

Before any live provider result can affect the demo:

- `DIALOGUE-REASONER-001` remains 30/30.
- `DIALOGUE-REASONER-002` validates dry-run and missing-provider-config safety.
- Live provider run uses the same frozen 30 cases.
- Provider results are strict JSON and schema-valid.
- Provider pass rate beats or materially improves the deterministic baseline on cases deterministic routing handles poorly.
- Median latency is acceptable for a voice turn.
- No provider output writes API keys or raw secret values.
- Live-demo response behavior remains unchanged until a later explicit wiring checkpoint.
