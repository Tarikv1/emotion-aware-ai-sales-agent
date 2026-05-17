# PROD-079 English Provider-Comparison Post-Patch Regression

`PROD-079` verifies the `PROD-078` English provider-comparison runtime patch after application.

This is regression only. It changes no runtime behavior, response text, classifier reachability, or retrieval.

## Summary

- Provider-comparison positive cases: `5`
- Existing-provider-gap controls: `3`
- Adjacent/protected controls: `5`
- Failed regression case count: `0`
- Stable English guard passed: `true`
- Review HTML created: `false`
- Recommended next checkpoint: `PROD-080-english-customer-move-remaining-slice-selection`

## Regression Cases

### prod-079-01

- Case type: `provider_comparison_positive`
- Customer turn: How is this different from our current provider?
- Expected sales difficulty: `provider-comparison`
- Observed sales difficulty: `provider-comparison`
- Passed: `true`

### prod-079-02

- Case type: `provider_comparison_positive`
- Customer turn: Can you compare this with what we already use?
- Expected sales difficulty: `provider-comparison`
- Observed sales difficulty: `provider-comparison`
- Passed: `true`

### prod-079-03

- Case type: `provider_comparison_positive`
- Customer turn: What would be different versus our current setup?
- Expected sales difficulty: `provider-comparison`
- Observed sales difficulty: `provider-comparison`
- Passed: `true`

### prod-079-04

- Case type: `provider_comparison_positive`
- Customer turn: How does this compare with our current terms?
- Expected sales difficulty: `provider-comparison`
- Observed sales difficulty: `provider-comparison`
- Passed: `true`

### prod-079-05

- Case type: `provider_comparison_positive`
- Customer turn: Can you compare your terms with what we already have?
- Expected sales difficulty: `provider-comparison`
- Observed sales difficulty: `provider-comparison`
- Passed: `true`

### prod-079-06

- Case type: `existing_provider_control`
- Customer turn: We already have a provider and I do not want to switch.
- Expected sales difficulty: `existing-provider-gap`
- Observed sales difficulty: `existing-provider-gap`
- Passed: `true`

### prod-079-07

- Case type: `existing_provider_control`
- Customer turn: We have another provider.
- Expected sales difficulty: `existing-provider-gap`
- Observed sales difficulty: `existing-provider-gap`
- Passed: `true`

### prod-079-08

- Case type: `existing_provider_control`
- Customer turn: We already use another provider.
- Expected sales difficulty: `existing-provider-gap`
- Observed sales difficulty: `existing-provider-gap`
- Passed: `true`

### prod-079-09

- Case type: `adjacent_control`
- Customer turn: What does this cost?
- Expected sales difficulty: `price-first-direct`
- Observed sales difficulty: `price-first-direct`
- Passed: `true`

### prod-079-10

- Case type: `adjacent_control`
- Customer turn: What do you offer?
- Expected sales difficulty: `unknown-runtime-signal`
- Observed sales difficulty: `unknown-runtime-signal`
- Passed: `true`

### prod-079-11

- Case type: `adjacent_control`
- Customer turn: Just send me the details in writing.
- Expected sales difficulty: `written-info-request`
- Observed sales difficulty: `written-info-request`
- Passed: `true`

### prod-079-12

- Case type: `protected_control`
- Customer turn: Can you take payment or card details if it is better?
- Expected sales difficulty: `payment-safety-boundary`
- Observed sales difficulty: `payment-safety-boundary`
- Passed: `true`

### prod-079-13

- Case type: `protected_control`
- Customer turn: Can you sign me up if this is better?
- Expected sales difficulty: `unknown-runtime-signal`
- Observed sales difficulty: `unknown-runtime-signal`
- Passed: `true`

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
