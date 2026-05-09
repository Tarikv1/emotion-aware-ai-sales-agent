# PROD-022 PROD-021 Review Gap Packet

Status: completed local checkpoint.

PROD-022 reads the completed `PROD-021` live-shaped dialogue-policy simulation and turns the failed gate into a compact review gap packet. It records the exact customer turns, exact agent answers, policy action misses, call-control misses, hook decisions, and narrow fix targets needed before runtime promotion.

## Boundary

- Local/offline only.
- Reads only the generated `PROD-021` result artifact.
- No provider calls.
- No LLM calls.
- No private data reads.
- No dataset download.
- No runtime behavior change.
- Retrieval default enabled: `false`.
- Composer hook flag default enabled: `false`.

## Files

```text
scripts/prod_022_prod_021_review_gap_packet.py
scripts/run_prod_022_prod_021_review_gap_packet.py
scripts/validate_prod_022_prod_021_review_gap_packet.py
research/experiments/generated/PROD-022-prod-021-review-gap-packet/result.json
research/experiments/generated/PROD-022-prod-021-review-gap-packet/report.md
```

## Current Result

- Source customer turns: `19`
- Source policy action correctness: `0.4737`
- Source call-control correctness: `0.8421`
- Gap turns: `10`
- Policy action misses: `10`
- Call-control misses: `3`
- Protected context gaps: `0`
- Hook gain turns: `4`
- Hard failures: `0`
- Leakage findings: `0`
- Runtime promotion allowed: `false`
- Next checkpoint recommended: `PROD-023-runtime-policy-call-control-fix`

## Interpretation

The PROD-021 failure is not a hook-safety failure. The hooks improved four turns and did not create hard failures, leakage findings, protected-context regressions, or payment collection.

The remaining blocker is narrower: the runtime policy layer collapses too many states into generic clarification or autonomy moves, and call control misses sale-ready and procurement-delay cases.

Keep composer hooks opt-in. The next product step should fix runtime policy routing and call-control before any bounded demo or default-runtime discussion.
