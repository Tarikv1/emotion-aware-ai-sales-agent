# PROD-045 Core Sales Policy Regression Rerun

PROD-045 hardens the deterministic evaluator before accepting runtime policy changes. The old generic clarification response is now a negative control and must fail required-boundary moves.

## Applied Runtime Policy Updates

- `policy-price-first-direct-answer`
- `policy-written-info-and-email-boundary`
- `policy-identity-repair-before-discovery`
- `policy-payment-and-scam-safety-boundary`
- `policy-support-and-cancellation-routing`
- `policy-specialist-handoff-for-technical-security-healthcare`
- `policy-existing-provider-gap-isolation`
- `policy-decision-maker-review-path`
- `policy-sale-ready-interest-guarded-next-step`

All applied updates are deterministic, campaign-guarded, and localized to the realtime turn policy surface. The reusable core still relies on campaign/profile fields for pricing, identity, support, cancellation, technical, healthcare, and sale-ready facts.

## Evaluator-Only Hardening

- Strict required-action checks by customer move.
- Generic clarification negative controls.
- Sale-ready guarded-next-step checks.

## Blocked Updates

- `retrieval_default_enablement`
- `provider_or_llm_calling`
- `voice_playback_unblock`
- `public_demo_polish`
- `payment_collection`
- `contract_signing`
- `unsupported_claim_expansion`

## Results

- Regression cases: 23
- Regression passes: 23
- Regression failures: 0
- Generic clarification unexpected passes: 0
- Payment collection violations: 0
- Unsupported claim violations: 0

## Boundaries

- Runtime behavior changed: `true`
- Retrieval enabled: `false`
- Provider calls made: `false`
- LLM used: `false`
- Private data read: `false`
- Dataset download performed: `false`
- Production runtime promotion allowed: `false`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`
- Payment collection allowed: `false`
- Contract signing allowed: `false`

## Remaining Limitations

- PROD-045 does not enable retrieval or live provider calls.
- Campaign facts in the regression harness are synthetic approved test facts.
- Human review is still needed before broader runtime promotion.

Next recommended checkpoint: `PROD-046-core-sales-policy-human-review`.
