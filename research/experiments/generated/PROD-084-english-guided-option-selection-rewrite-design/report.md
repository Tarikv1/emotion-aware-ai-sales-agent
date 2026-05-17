# PROD-084 English Guided Option Selection Rewrite Design

`PROD-084` creates rewritten guided option selection examples for human review.

This checkpoint does not patch runtime behavior, response text, classifier reachability, retrieval, payment handling, or spoken naturalness behavior.

## Summary

- Review packet only: `true`
- Selected review item: `guided_option_selection_rewritten_examples`
- Review example count: `8`
- Requires human review before next checkpoint: `true`
- Review HTML created: `true`
- Review HTML path: `research/experiments/generated/PROD-084-english-guided-option-selection-rewrite-design/prod_084_review.html`
- Recommended next checkpoint: `PROD-085-english-guided-option-selection-rewrite-review-import`
- Narrow policy probe approved: `false`
- Runtime candidate promoted: `false`
- Random fillers allowed: `false`
- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- Classifier behavior changed: `false`
- Retrieval enabled: `false`
- Production runtime promotion allowed: `false`

## Review-Only Plan Feature Matrix

- `$29`: [feature X], [feature Y], [feature Z]
- `$59`: [feature X], [feature Y], [feature Z], [feature A], [feature B], [feature C]

## Sparse Discourse Markers

- Examples with discourse markers: `3`
- Sensitive boundary marker violations: `none`

## Examples

### Direct choice

- Customer turn: So do I choose the $29 option or the $59 option?
- Uses discourse marker: `true`
- Word count: `22`
- Review focus: Answer fit directly without repeating that one option is cheaper.

```text
I mean, if you only need [feature X] and [feature Y], start with $29. If [feature A] matters too, $59 fits better.
```

### Fit is unclear

- Customer turn: I can see both paths, I am just not sure which one fits me.
- Uses discourse marker: `false`
- Word count: `26`
- Review focus: Steer from customer facts while preserving the upgrade path.

```text
Based on what you said, $59 sounds stronger if [feature A] saves you time. If not, $29 is the safer start and you can upgrade later.
```

### Recommendation request

- Customer turn: Which route would you suggest for someone like me?
- Uses discourse marker: `true`
- Word count: `27`
- Review focus: Allow a recommendation without pretending to choose for the customer.

```text
Honestly, like, if your main issue is [customer pain], I would lean $59 because it adds [feature A] and [feature B]. If budget matters more, start $29.
```

### Explain the difference

- Customer turn: What is the real difference between the $29 option and the $59 option?
- Uses discourse marker: `false`
- Word count: `25`
- Review focus: Answer the real difference using approved plan facts.

```text
$29 covers [feature X], [feature Y], and [feature Z]. $59 adds [feature A] and [feature B], so it fits better if you need [customer goal].
```

### Decide later

- Customer turn: Can I choose later instead of deciding on this call?
- Uses discourse marker: `false`
- Word count: `17`
- Review focus: Keep deferral short and avoid saying the same thing twice.

```text
Yes. I can send the differences in writing and keep both options open for the follow-up.
```

### Neither feels right

- Customer turn: I'm not sure either is right.
- Uses discourse marker: `true`
- Word count: `26`
- Review focus: Use acknowledgement plus light persuasion instead of ending the opportunity.

```text
I get that, you know, it may just mean we should match the plan to [customer goal] first, then see whether $29 or $59 makes sense.
```

### Payment path

- Customer turn: If I pick one, can I pay now?
- Uses discourse marker: `false`
- Word count: `23`
- Review focus: Explain the approved campaign payment path without collecting payment.

```text
No payment on this call. I'll send the companyname.com email with the link, and you can review the plan and finish registration there.
```

### Start cheaper, upgrade later

- Customer turn: Could I start smaller and change later if it works?
- Uses discourse marker: `false`
- Word count: `25`
- Review focus: Use the upgrade path as a selling bridge when campaign rules allow it.

```text
You can start with $29 if [feature X] covers enough. If you later need [feature A] or [feature B], we can move you to $59.
```

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
