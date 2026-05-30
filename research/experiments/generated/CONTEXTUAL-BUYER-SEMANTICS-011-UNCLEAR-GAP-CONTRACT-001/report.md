# CONTEXTUAL-BUYER-SEMANTICS-011 Unclear Gap Contract

## Decision

`the estimate is unclear` is not a confirmed pain statement. It should be classified as `gap_specific_unclear_context` for the `estimate_or_property_details` gap.

## Rationale

The utterance identifies a relevant gap area, but it does not confirm that the gap is currently causing a buyer pain, urgency, or purchase-relevant problem. In a generic campaign, treating ambiguous unclear language as confirmed pain would let the agent move toward value mapping or appointment closing before the buyer has actually confirmed the problem.

The safer autonomous sales-closing behavior is to ask a clarification question first: what is unclear, what a qualified human would check, or whether it matters here. Explicit pain language remains confirmable; the 011 validator keeps `the estimate is a problem` as `pain_confirmed`.

## Contract

- `the estimate is unclear` -> `gap_specific_unclear_context`
- `the estimate is a problem` -> `pain_confirmed`
- Safety flags remain false: no provider calls, local LLM calls, email, calendar, CRM, TTS, or prod-102 behavior.
- RouteSignal behavior and action-selector shadow logging are unchanged.

## Recommendation

Continue only with limited offline/sanitized shadow logging expansion. Do not enable live selector control.
