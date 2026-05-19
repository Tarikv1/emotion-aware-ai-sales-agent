# DIALOGUE-REASONER-003 Hybrid Gate Evaluation

`DIALOGUE-REASONER-003` tests the hybrid gate architecture Tarik actually wants: deterministic runtime routing remains in control, and the LLM provider is only a reasoning-enrichment layer for allowed turns.

## Scope

- 30 guard cases reused from `DIALOGUE-REASONER-001`: deterministic routing must remain `30/30`, and provider override stays blocked.
- 30 invocation cases: 15 protected turns must block provider calls, and 15 enrichment-eligible turns may allow provider calls.
- 40 reasoning cases: the provider may return only reasoning-enrichment fields, never protected runtime route fields.

## Boundary

- The LLM must not own `dialogue_act`, `buyer_intent`, `resolved_topic`, `sales_stage`, `response_strategy`, `safety_boundary`, call control, pricing truth, scheduling, handoff, ASR repair, or security/integration boundaries.
- Provider calls are default-off and require `--live --consent-confirmed`.
- API key values are never written to generated evidence.
- The live-demo response path is not changed by this evaluation.
- `PROD-102 stays closed`.

## Acceptance

- Guard batch: `30/30`.
- Invocation gate batch: `30/30`.
- Reasoning schema/no-override: every provider result must use the hybrid reasoning schema only.
- Reasoning quality: target `36/40` on the full live batch.
- Provider errors, schema errors, route override attempts, invented pricing/security/integration claims, and private-data use are failures.

## Commands

Dry-run without provider calls:

```powershell
python scripts\run_dialogue_reasoner_003_hybrid_gate.py
```

Validate the dry-run, local guard behavior, missing-config live block, docs, and runtime manifest:

```powershell
python scripts\validate_dialogue_reasoner_003_hybrid_gate.py
```

Live provider evaluation after filling ignored local provider config:

```powershell
python scripts\run_dialogue_reasoner_003_hybrid_gate.py --live --consent-confirmed --temperature 1
```
