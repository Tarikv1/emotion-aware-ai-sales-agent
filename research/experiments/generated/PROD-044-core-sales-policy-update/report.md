# PROD-044 Core Sales Policy Update Review Packet

PROD-044 reviews PROD-043 evidence and prepares targeted runtime-policy updates. It does not apply runtime changes.

## Decision

- Runtime policy update justified: `true`
- Runtime changes performed: `false`
- Apply runtime changes now: `false`
- Candidate policy update count: `4`
- Blocked update count: `6`
- Required campaign-fact guard count: `16`

## Candidate Policy Updates

### policy-existing-provider-gap-isolation

- Title: Isolate a gap without claiming replacement superiority
- Status: `candidate_not_applied`
- Moves: `existing_provider`
- Runtime probe evidence: `probe-existing_provider`
- Required campaign guards: `guard-no-competitor-superiority-claim, guard-campaign-fit-gap-only`
- Runtime change performed: `false`
- Summary: When the customer has an existing provider, the core should avoid replacement or competitor-superiority claims and ask only whether there is a specific uncovered gap.

### policy-identity-repair-before-discovery

- Title: Identify caller and reason before continuing
- Status: `candidate_not_applied`
- Moves: `who_are_you`
- Runtime probe evidence: `probe-who_are_you`
- Required campaign guards: `guard-approved-identity-and-reason`
- Runtime change performed: `false`
- Summary: When the customer asks who is calling, the core should identify the caller/company/role and brief reason using campaign facts before any pitch or discovery.

### policy-payment-and-scam-safety-boundary

- Title: State no payment or card collection on safety fears
- Status: `candidate_not_applied`
- Moves: `payment_safety_fear`
- Runtime probe evidence: `probe-payment_safety_fear`
- Required campaign guards: `guard-no-payment-collection, guard-approved-verification-path`
- Runtime change performed: `false`
- Summary: When the customer raises scam, card, or payment fear, the core should explicitly say no payment/card details are collected and offer a safe verification or written-info path.

### policy-specialist-handoff-for-technical-security-healthcare

- Title: Handoff technical, security, coverage, and healthcare boundaries
- Status: `candidate_not_applied`
- Moves: `security_review`
- Runtime probe evidence: `probe-security_review`
- Required campaign guards: `guard-approved-technical-scope, guard-specialist-route-available, guard-no-medical-or-coverage-advice`
- Runtime change performed: `false`
- Summary: For technical, security, coverage, or healthcare questions beyond approved campaign facts, the core should avoid guessing and route to a specialist or qualified reviewer.

## Blocked Updates

- `blocked-enable-retrieval-default`: PROD-043 validates offline artifact lookup only; it does not prove live retrieval should be enabled.
- `blocked-broaden-product-claims`: PROD-043 evidence supports safer turn policy, not broader claims, guarantees, ROI, medical, coverage, security, or competitor assertions.
- `blocked-voice-playback-or-demo-polish`: PROD-043 is a single-turn offline evaluator and does not unblock voice playback, public demo polish, or synthetic dialogue promotion.
- `blocked-payment-or-contract-close`: The product boundary remains no payment collection, no contract signing, and no unsupported close.
- `blocked-full-conversation-generation`: PROD-044 is a policy review packet, not a scenario simulator or synthetic conversation generator.
- `blocked-runtime-change-without-regression`: Any future runtime edit must be covered by deterministic regression tests before being marked applied.

## Campaign-Fact Guards

- `guard-approved-pricing-facts`: fields `pricing_summary, pricing_boundary_text`. Allows price-first handling without inventing price, discounts, ROI, or contract terms.
- `guard-no-callback-before-price-answer`: fields `callback_offer_allowed_after_direct_answer`. Prevents scheduling pressure before the customer's explicit price question is addressed.
- `guard-approved-written-summary`: fields `approved_written_summary, approved_email_followup_scope`. Allows send-info and email-only responses without creating unsupported product copy.
- `guard-contact-channel-boundary`: fields `allowed_contact_channels, respect_email_only_boundary`. Keeps email-only handling from turning into callback pressure.
- `guard-approved-identity-and-reason`: fields `caller_identity, company_or_campaign_name, approved_reason_for_call`. Allows identity repair without hype or private/provider-specific claims.
- `guard-no-payment-collection`: fields `payment_collection_allowed`. Keeps payment/card handling safety-perfect.
- `guard-approved-verification-path`: fields `approved_verification_path`. Gives scam-fear customers a safe verification route without asking for sensitive data.
- `guard-support-route-available`: fields `support_route, support_boundary_text`. Stops support issues from drifting into sales continuation.
- `guard-cancellation-route-available`: fields `cancellation_route, cancellation_boundary_text`. Stops cancellation requests from becoming retention pressure.
- `guard-approved-technical-scope`: fields `approved_technical_scope, unknown_technical_answer_boundary`. Allows only supported technical answers and routes unknown details.
- `guard-specialist-route-available`: fields `specialist_handoff_route`. Gives technical, security, coverage, and healthcare boundary turns a safe next action.
- `guard-no-medical-or-coverage-advice`: fields `regulated_advice_boundary_text`. Blocks medical, legal, financial, or coverage advice outside approved campaign facts.
- `guard-no-competitor-superiority-claim`: fields `competitor_comparison_boundary_text`. Prevents unsupported competitor superiority or replacement claims.
- `guard-campaign-fit-gap-only`: fields `approved_gap_isolation_question`. Keeps existing-provider handling to one concrete fit gap.
- `guard-review-summary-only`: fields `approved_review_summary`. Supports manager/spouse review without pressure or commitment.
- `guard-no-decision-maker-bypass`: fields `decision_maker_bypass_forbidden`. Prevents bypassing the person who must approve.

## Boundary

Runtime behavior, retrieval defaults, provider usage, LLM usage, private-data access, voice playback, public demo polish, payment collection, and production runtime promotion remain unchanged and blocked.
