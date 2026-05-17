# PROD-077 English Provider-Comparison Narrow Probe Design

`PROD-077` designs the smallest safe English `provider-comparison` probe after Tarik's constrained approval.

This is design-only. It does not patch runtime behavior, response text, classifier reachability, or retrieval.

## Design

- Route: `provider-comparison`
- Required signal group: `compare_or_difference_signal`
- Required signal group: `known_comparison_target_signal`
- Comparison target required: `true`
- Generic provider or terms comparison allowed: `false`
- Insert before `existing-provider-gap` if a later runtime patch is opened
- Candidate response: Fair. We can compare fit against what you use now before you decide.
- Source response word count: `19`
- Candidate response word count: `13`

## Current Runtime Gap

- Positive probe cases: `4`
- Current runtime positive gap count: `0`
- Recommended next checkpoint: `PROD-078-english-provider-comparison-runtime-patch`

## Exclusions

- `payment_or_card_details`
- `contract_or_signup`
- `price_only`
- `generic_product_question`
- `provider_exists_without_comparison_request`

## Boundary Status

- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- Classifier behavior changed: `false`
- Retrieval enabled: `false`
- Provider calls made: `false`
- LLM used: `false`
- LLM judging used: `false`
- Private data read: `false`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`
- Real customer use unblocked: `false`
- Payment collection allowed: `false`
- Contract signing allowed: `false`
- Production runtime promotion allowed: `false`
- German exact-phrase promotion allowed: `false`
- German naturalness claimed: `false`
- Legal compliance claimed: `false`
- Review HTML created: `false`
