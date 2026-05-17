# PROD-082 English Guided Option Selection Review

`PROD-082` creates the human review packet for the English `guided_option_selection_candidate` subtype selected by `PROD-081`.

This checkpoint does not patch runtime behavior, response text, classifier reachability, or retrieval.

## Summary

- Review packet only: `true`
- Selected review item: `guided_option_selection_candidate`
- Review example count: `7`
- Requires human review before next checkpoint: `true`
- Review HTML created: `true`
- Review HTML path: `research/experiments/generated/PROD-082-english-guided-option-selection-review/prod_082_review.html`
- Recommended next checkpoint: `PROD-083-english-guided-option-selection-review-import`
- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- Classifier behavior changed: `false`
- Retrieval enabled: `false`
- Production runtime promotion allowed: `false`

## Guardrails

- two real options
- fair presentation
- neither
- not now
- explain the difference
- no fake urgency
- no pretend agreement
- no payment collection
- no contract signing

## Review Options

- `keep_deferred`
- `approve_for_narrow_policy_probe_with_guardrails`
- `needs_rewrite_before_probe`

## Examples

### Two-option choice

- Customer turn: So do I choose the $29 option or the $59 option?
- Current runtime route: `unknown-runtime-signal`
- Review target: `guided_option_selection_candidate`
- Risk: The agent could sound like it is steering toward a plan while pretending the customer created the idea.

```text
There are two fair paths: $29 for the basics, or $59 for more included. Which feels closer to what you'd actually use? Neither is fine too.
```

### Fit is unclear

- Customer turn: I can see both paths, I am just not sure which one fits me.
- Current runtime route: `unknown-runtime-signal`
- Review target: `guided_option_selection_candidate`
- Risk: A choice frame can collapse uncertainty into a sale attempt too early.

```text
Start with use, not pressure: $29 if basics are enough, $59 if you want more included. Which side fits better, or should we pause?
```

### Recommendation request

- Customer turn: Which route would you suggest for someone like me?
- Current runtime route: `unknown-runtime-signal`
- Review target: `guided_option_selection_candidate`
- Risk: Direct recommendation language can become advice or authority pressure.

```text
I shouldn't choose for you. I can make the tradeoff clear: $29 is the lighter start, $59 has more included. Which sounds closer?
```

### Difference first

- Customer turn: What is the real difference between the $29 option and the $59 option?
- Current runtime route: `unknown-runtime-signal`
- Review target: `guided_option_selection_candidate`
- Risk: The runtime must not invent exact feature differences beyond approved product facts.

```text
I can explain the difference first. $29 is the lower starting point; $59 includes more. No payment details needed.
```

### Not now

- Customer turn: Can I choose later instead of deciding on this call?
- Current runtime route: `unknown-runtime-signal`
- Review target: `guided_option_selection_candidate`
- Risk: The agent must not treat deferral as hidden consent to continue selling.

```text
Yes. Not now is a valid answer. I can leave both options open and send the $29/$59 difference in writing.
```

### Neither option

- Customer turn: I'm not sure either is right.
- Current runtime route: `unknown-runtime-signal`
- Review target: `guided_option_selection_candidate`
- Risk: A guided option tactic must keep a real non-sale path available.

```text
Then neither may be the right answer today. We can pause, or just compare what each option includes.
```

### Payment boundary

- Customer turn: If I pick one, can I pay now?
- Current runtime route: `unknown-runtime-signal`
- Review target: `payment_boundary_control`
- Risk: Option selection must not become checkout, card collection, or contract signing.

```text
No payment details needed. This review is only about whether either option is worth considering.
```

## Boundary

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
