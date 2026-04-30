# RESP-001 Guarded Response Generation Implementation Plan

## Objective

Add the first reusable guarded response-generation layer for the sales agent.

This checkpoint proves the architecture where the deterministic realtime core owns what is allowed, and the response generator improves how it is said.

## Constraints

- No real LLM call.
- No API key.
- No provider SDK dependency.
- No secret storage.
- No call-control override.
- Must stay campaign-agnostic and use `SalesCampaign` guardrails.

## Steps

1. Add a failing validator for the RESP-001 contract.
2. Implement `scripts/generate_guarded_response.py`.
3. Reuse the existing realtime turn decision path.
4. Build guardrails from universal rules plus campaign config.
5. Compose a local candidate response for common sales difficulties.
6. Validate candidate response against forbidden claims.
7. Fall back to the policy response when validation fails.
8. Write JSON and Markdown generated artifacts.
9. Document the product contract and experiment.
10. Run focused validation, existing voice/runtime regression checks, and secret scans.
11. Commit and push as a checkpoint.

## Acceptance Criteria

- Safe price-objection sample passes validation.
- Safe sample final response differs from the policy fallback.
- Unsafe candidate with forbidden promises fails validation.
- Unsafe sample final response equals policy fallback.
- Output includes `llm_used: false` and `requires_api_key: false`.
- Output includes campaign guardrails and decision snapshot.
- Report states that no LLM/API call was made.
- No secret-like tokens are detected in generated outputs or changed files.

## Files

- `scripts/generate_guarded_response.py`
- `scripts/validate_resp_001_guarded_response_generation.py`
- `docs/product/RESP_001_GUARDED_RESPONSE_GENERATION.md`
- `research/experiments/RESP-001-guarded-response-generation.md`
- `research/experiments/generated/RESP-001-guarded-response-result.json`
- `research/experiments/generated/RESP-001-guarded-response-report.md`
