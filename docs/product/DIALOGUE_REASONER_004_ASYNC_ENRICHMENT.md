# DIALOGUE-REASONER-004 Async Enrichment

`DIALOGUE-REASONER-004` wires the hybrid reasoning layer as optional async enrichment behind deterministic routing.

## Scope

- Preserve the `DIALOGUE-REASONER-003` guard shape: 30 deterministic guard cases, 30 invocation-gate cases, and 40 reasoning-enrichment cases.
- Prove that the deterministic customer response is available before any provider result is needed.
- Keep provider calls default-off unless `--live --consent-confirmed` is passed.
- Store async enrichment evidence as a separate packet; the customer response is not blocked.
- Attach the packet to `LIVE-DEMO-001` private turn evidence only; the spoken response path still ignores it.

## Boundary

- deterministic routing remains in control for `dialogue_act`, `buyer_intent`, `resolved_topic`, `sales_stage`, `response_strategy`, `safety_boundary`, call control, pricing, scheduling, ASR repair, handoff, security, and integration boundaries.
- The provider may only return the `DIALOGUE-REASONER-003` enrichment schema.
- The async packet stores response fingerprints and counts, not customer-facing response text.
- Provider results cannot mutate `final_response`, route labels, voice delivery, or call-control decisions.
- In `LIVE-DEMO-001`, the attached packet makes no provider call and does not upload transcript text to the reasoning provider.
- `PROD-102 stays closed`.

## Acceptance

- Guard batch: `30/30`.
- Invocation gate batch: `30/30`.
- Async planned cases: `40`.
- Queued before provider: `40/40`.
- Deterministic response available before provider: `40/40`.
- Provider cases in dry-run: `0`.
- Customer response blocked on provider: `0`.
- Final response changed by provider: `0`.
- Live-demo attached evidence: provider call `false`, text sent to provider `false`, final response changed `false`.

## Commands

Dry-run without provider calls:

```powershell
python scripts\run_dialogue_reasoner_004_async_enrichment.py
```

Validate the async enrichment boundary, dry-run evidence, missing-config live block, docs, and runtime manifest:

```powershell
python scripts\validate_dialogue_reasoner_004_async_enrichment.py
```

Live smoke after filling ignored local provider config and confirming synthetic transcript upload:

```powershell
python scripts\run_dialogue_reasoner_004_async_enrichment.py --live --consent-confirmed --temperature 1 --max-reasoning-cases 1
```
