# PROD-047 Campaign Profile Contract Validator

PROD-047 creates a reusable deterministic campaign-profile contract and validator. It does not modify runtime behavior.

## Results

- Validation cases: 10
- Valid campaigns: 2
- Invalid campaigns: 8
- Unexpected results: 0
- Policy group coverage: 12 / 12
- PROD-046 source result passed: `True`

## Validator Behavior

- Valid English and German campaigns pass only for offline regression/internal product review by default.
- Readiness defaults remain `blocked_for_voice`, `blocked_for_public_demo`, and `blocked_for_customer_use` unless explicit review statuses are present.
- German voice/demo/customer promotion remains blocked unless native review and explicit promotion statuses are present.
- Internal customer-facing terms, malformed German interpolation, unsafe payment/contract flags, missing regulated boundaries, missing native review status, and missing close criteria fail deterministically.

## Campaign Examples

- `campaign-prod-047-valid-en-internal-review`: valid=`True`, expected=`True`
- `campaign-prod-047-valid-de-source-informed`: valid=`True`, expected=`True`
- `campaign-prod-047-invalid-de-fragment-interpolation`: valid=`False`, expected=`False`
- `campaign-prod-047-invalid-en-internal-copy`: valid=`False`, expected=`False`
- `campaign-prod-047-invalid-payment-enabled`: valid=`False`, expected=`False`
- `campaign-prod-047-invalid-missing-regulated-boundary`: valid=`False`, expected=`False`
- `campaign-prod-047-invalid-missing-native-review-status`: valid=`False`, expected=`False`
- `campaign-prod-047-invalid-sale-ready-without-close-criteria`: valid=`False`, expected=`False`
- `campaign-prod-047-invalid-support-cancellation-route-label`: valid=`False`, expected=`False`
- `campaign-prod-047-incomplete-identity-reason`: valid=`False`, expected=`False`

## Boundaries

- Runtime behavior changed: `false`
- Retrieval enabled: `false`
- Provider calls made: `false`
- LLM used: `false`
- Private data read: `false`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`
- Payment collection allowed: `false`
- Contract signing allowed: `false`
- Production runtime promotion allowed: `false`

Next recommended checkpoint: `PROD-048-native-german-wording-review`.
