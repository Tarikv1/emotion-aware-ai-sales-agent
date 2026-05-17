# PROD-098 English Recommendation Roleplay Review Import

`PROD-098` imports Tarik's `PROD-097` recommendation-roleplay review.

This is import-only. It does not patch runtime behavior, response text, classifier reachability, retrieval, payment handling, spoken naturalness behavior, or production promotion.

## Imported Decision

- Decision: approve for policy probe with two wording edits
- Narrow policy probe approved after required edits: `true`
- Narrow policy probe approved as written: `false`
- Approved examples: `7`
- Required edit examples: `2`
- Review HTML created: `false`
- Runtime candidate promoted: `false`
- Recommended next checkpoint: `PROD-099-english-recommendation-roleplay-narrow-policy-probe`

## Required Wording Edits

- `prod-097-direct-recommendation`: `Based on [customer pain], I would recommend $59. If budget is the main concern, start with $29 and upgrade later if you need to.`
- `prod-097-decide-for-me-control`: `I cannot decide for you, but I can show what each plan covers and why one may fit your needs better.`

## Probe Readiness

- Requires customer facts for recommendation: `true`
- Requires agency preservation: `true`
- Requires no agent decides for customer: `true`
- Requires no value guarantee: `true`

## Imported Notes

All examples are approved except for two small wording edits. Example 3 should add 'if you need to' after upgrade later to make the option feel less pushy. Example 5 should soften the second sentence with a but/though style connector so the agent preserves customer choice while still offering help.

## Boundary Status

- runtime behavior changed: `false`
- response text behavior changed: `false`
- classifier behavior changed: `false`
- retrieval enabled: `false`
- provider calls made: `false`
- llm used: `false`
- llm judging used: `false`
- private data read: `false`
- voice playback unblocked: `false`
- public demo polish unblocked: `false`
- real customer use unblocked: `false`
- payment collection allowed: `false`
- contract signing allowed: `false`
- production runtime promotion allowed: `false`
- german exact phrase promotion allowed: `false`
- german naturalness claimed: `false`
- legal compliance claimed: `false`
