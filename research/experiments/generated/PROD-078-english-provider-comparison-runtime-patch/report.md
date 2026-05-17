# PROD-078 English Provider-Comparison Runtime Patch

`PROD-078` applies the `PROD-077` narrow English `provider-comparison` runtime patch.

This is an English provider-comparison narrow runtime patch. It changes classifier reachability and English response text for `provider-comparison` only.

No human review required because PROD-076 imported Tarik's constrained approval and PROD-077 converted it into a deterministic design.

## Decision

- Decision: `english_provider_comparison_runtime_patch_applied`
- Runtime path: `runtime/core/realtime_turns.py`
- Patched sales difficulty: `provider-comparison`
- Patched response: `Fair. We can compare fit against what you use now before you decide.`
- Inserted before `existing-provider-gap`
- Comparison target required: `true`
- Generic provider or terms comparison allowed: `false`
- Runtime behavior changed: `true`
- Response text behavior changed: `true`
- Classifier behavior changed: `true`
- Review HTML created: `false`
- Recommended next checkpoint: `PROD-079-english-provider-comparison-post-patch-regression`
- Production runtime promotion allowed: `false`

## Runtime Patch Reviews

### prod-077-current-provider-difference

- Case type: `positive_probe`
- Customer turn: How is this different from our current provider?
- Passed: `true`
- Issue codes: `none`
- Sales difficulty: `provider-comparison`
- Next action: `ask-follow-up`
- Call control: `continue-call`

### prod-077-compare-current-use

- Case type: `positive_probe`
- Customer turn: Can you compare this with what we already use?
- Passed: `true`
- Issue codes: `none`
- Sales difficulty: `provider-comparison`
- Next action: `ask-follow-up`
- Call control: `continue-call`

### prod-077-versus-current-setup

- Case type: `positive_probe`
- Customer turn: What would be different versus our current setup?
- Passed: `true`
- Issue codes: `none`
- Sales difficulty: `provider-comparison`
- Next action: `ask-follow-up`
- Call control: `continue-call`

### prod-077-current-terms-comparison

- Case type: `positive_probe`
- Customer turn: How does this compare with our current terms?
- Passed: `true`
- Issue codes: `none`
- Sales difficulty: `provider-comparison`
- Next action: `ask-follow-up`
- Call control: `continue-call`

### prod-078-compare-terms-with-what-we-have

- Case type: `positive_probe`
- Customer turn: Can you compare your terms with what we already have?
- Passed: `true`
- Issue codes: `none`
- Sales difficulty: `provider-comparison`
- Next action: `ask-follow-up`
- Call control: `continue-call`

### prod-077-existing-provider-no-comparison

- Case type: `negative_control`
- Customer turn: We already have a provider and I do not want to switch.
- Passed: `true`
- Issue codes: `none`
- Sales difficulty: `existing-provider-gap`
- Next action: `ask-follow-up`
- Call control: `continue-call`

### prod-077-generic-offer

- Case type: `negative_control`
- Customer turn: What do you offer?
- Passed: `true`
- Issue codes: `none`
- Sales difficulty: `unknown-runtime-signal`
- Next action: `ask-follow-up`
- Call control: `continue-call`

### prod-077-better-generic

- Case type: `negative_control`
- Customer turn: Is it better?
- Passed: `true`
- Issue codes: `none`
- Sales difficulty: `unknown-runtime-signal`
- Next action: `ask-follow-up`
- Call control: `continue-call`

### prod-077-price-only

- Case type: `negative_control`
- Customer turn: What does this cost?
- Passed: `true`
- Issue codes: `none`
- Sales difficulty: `price-first-direct`
- Next action: `answer-and-continue`
- Call control: `bridge-then-continue`

### prod-077-written-info

- Case type: `negative_control`
- Customer turn: Just send me the details in writing.
- Passed: `true`
- Issue codes: `none`
- Sales difficulty: `written-info-request`
- Next action: `answer-and-continue`
- Call control: `bridge-then-continue`

### prod-077-payment-details

- Case type: `protected_control`
- Customer turn: Can you take payment or card details if it is better?
- Passed: `true`
- Issue codes: `none`
- Sales difficulty: `payment-safety-boundary`
- Next action: `create-follow-up-task`
- Call control: `end-call`

### prod-077-sign-up

- Case type: `protected_control`
- Customer turn: Can you sign me up if this is better?
- Passed: `true`
- Issue codes: `none`
- Sales difficulty: `unknown-runtime-signal`
- Next action: `ask-follow-up`
- Call control: `continue-call`

## Boundary Status

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
