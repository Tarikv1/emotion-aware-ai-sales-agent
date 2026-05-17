# PROD-085 English Guided Option Selection Rewrite Review Import

`PROD-085` imports Tarik's `PROD-084` review decision.

This is import-only. It does not patch runtime behavior, response text, classifier reachability, retrieval, payment handling, spoken naturalness behavior, or production promotion.

## Imported Decision

- Decision: approve rewrite for policy probe with payment wording edit
- Narrow policy probe approved after required edit: `true`
- Narrow policy probe approved as written: `false`
- Approved as-written examples: `7`
- Required edit examples: `1`
- Review HTML created: `false`
- Runtime candidate promoted: `false`
- Recommended next checkpoint: `PROD-086-english-guided-option-selection-narrow-policy-probe`

## Payment Wording Edit

- Status: approved after required payment wording edit
- Source artifact preserved: `true`
- Source issue: remove the `companyname.com` placeholder from the generic payment example.
- Final candidate: `No payment on this call. I'll send you the link by email, and you can review the plan and register there.`
- No payment on this call remains the default.

## Candidate Packet

- Candidate examples: `8`
- The payment example is the only changed source example.
- The final candidate packet does not include the `companyname.com` placeholder.

## Probe Readiness

- Requires plan feature matrix: `true`
- Requires customer facts for steering: `true`
- Requires no payment on call default: `true`
- Requires no company domain in generic payment wording: `true`

## Imported Notes

Reviewer liked the rewritten examples except example seven. The payment-path response should be shorter and should not include a companyname.com email placeholder. Use a shorter email-link wording such as sending the link by email so the customer can review the plan and register there.

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
