# PROD-090 English Guided Option Synonym Coverage Narrow Probe

`PROD-090` probes whether two near-synonym guided-option gaps can use the existing reviewed guardrails before any runtime trigger expansion.

This checkpoint is policy-probe-only. It changes no runtime behavior, response text, classifier reachability, retrieval, provider usage, private-data handling, voice playback, payment handling, contract signing, legal readiness, German wording, or production runtime promotion.

## Result

- Policy probe only: `true`
- Policy probe passed: `true`
- Selected gap count: `2`
- Positive case count: `4`
- Control case count: `9`
- Failed policy case count: `0`
- Current runtime gap count: `2`
- Requires human review before next checkpoint: `false`
- Recommended next checkpoint requires human review: `false`
- Review HTML created: `false`
- Recommended next checkpoint: `PROD-091-english-guided-option-synonym-coverage-runtime-patch`

## Runtime Gaps

- `prod-081-guided-option-02` -> `unknown-runtime-signal`: Should I start small or go with the fuller option?
- `prod-081-plan-difference-02` -> `unknown-runtime-signal`: Can you show me both options side by side?

## Candidate Positive Cases

- `prod-090-start-small-fuller` passed `true`: I mean, start with $29 if [feature X] and [feature Y] is enough. If you want [feature A] and [feature B] included, $59 fits better.
- `prod-090-side-by-side` passed `true`: $29 covers [feature X] and [feature Y]. $59 includes that plus [feature A] and [feature B].
- `prod-090-safer-start-small` passed `true`: I mean, start with $29 if [feature X] and [feature Y] is enough. If you want [feature A] and [feature B] included, $59 fits better.
- `prod-090-fuller-worth-it` passed `true`: $59 is worth considering if [feature A] and [feature B] helps [customer goal]. If not, $29 is enough to start.

## Boundary Status

- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- Classifier behavior changed: `false`
- Retrieval enabled: `false`
- Provider calls made: `false`
- Llm used: `false`
- Llm judging used: `false`
- Private data read: `false`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`
- Real customer use unblocked: `false`
- Payment collection allowed: `false`
- Contract signing allowed: `false`
- Production runtime promotion allowed: `false`
- German exact phrase promotion allowed: `false`
- German naturalness claimed: `false`
- Legal compliance claimed: `false`
