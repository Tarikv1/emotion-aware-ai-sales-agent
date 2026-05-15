# Compact English Psychology Layer Review

`PROD-053B` reviews the `PROD-053A` candidate rules and compresses them into an English-only deterministic response-shape policy for `PROD-053C`.

It makes no runtime behavior or response text change.

## Summary

- Source candidate rules: `8`
- Accepted rules: `8`
- Accepted with constraints: `3`
- Compact policy rules: `8`
- Current English cases audited: `4`
- Current English cases requiring PROD-053C rewrite: `2`
- Runtime behavior changed: `False`
- Response text behavior changed: `False`
- LLM used: `False`
- Provider calls made: `False`

## Compact English Policy

### en_response_001_answer_then_continue - Answer, then continue.

- Instruction: Use a tiny acknowledgement, answer the customer move, then offer one low-friction next step.
- Blocked shape: Do not open a menu of facts, explanations, and options before answering the customer.
- Review status: `accepted_for_prod_053c`

### en_response_002_plain_relief - Keep relief plain.

- Instruction: When relief matters, say it briefly: no commitment today, take a look, let me know.
- Blocked shape: Do not list every legal or commercial non-commitment as a policy dump.
- Review status: `accepted_for_prod_053c`

### en_response_003_mirror_only_for_repair - Mirror only for repair.

- Instruction: Use a short partial repeat only when it repairs ambiguity or invites useful detail.
- Blocked shape: Do not repeat the customer's full category such as manager, spouse, boss, or partner in every answer.
- Review status: `accepted_with_constraint_for_prod_053c`

### en_response_004_one_small_decision - One small decision.

- Instruction: Offer or ask for one small next step per turn.
- Blocked shape: Do not ask the buyer to process summary, pricing, terms, booking, and contract details in one turn.
- Review status: `accepted_for_prod_053c`

### en_response_005_friction_not_personality - Diagnose friction, not personality.

- Instruction: If hesitation is unclear, ask one small friction question about price, timing, authority, risk, or usefulness.
- Blocked shape: Do not label hidden emotions or personality traits.
- Review status: `accepted_with_constraint_for_prod_053c`

### en_response_006_autonomy_visible - Make autonomy visible.

- Instruction: Keep pause, review, decline, compare, or human handoff visible when the next step could feel like pressure.
- Blocked shape: Do not turn a review step into a forced booking, hidden obligation, or scarcity close.
- Review status: `accepted_with_constraint_for_prod_053c`

### en_response_007_trust_gap_specific - Answer the specific trust gap.

- Instruction: For trust concerns, answer ability, interest, or honesty gaps with only the relevant verified path.
- Blocked shape: Do not use generic reassurance, testimonials, or confidence as a universal trust answer.
- Review status: `accepted_for_prod_053c`

### en_response_008_stop_after_question - Ask, then stop.

- Instruction: If the turn asks a question, stop after the question.
- Blocked shape: Do not ask a question and then continue explaining the answer options.
- Review status: `accepted_for_prod_053c`

## Current English Case Audit

### prod-045-price-first

- Current response: The starter plan is 29 per user per month, and I can send the exact terms in writing. If useful, I can briefly explain what is included before I send them. No payment or commitment on this call.
- Policy issues: `none`
- PROD-053C decision: `carry_forward`
- Policy-shape suggestion: The starter plan is 29 per user per month. I can send the exact terms in writing. No payment or commitment on this call.

### prod-045-send-info

- Current response: Of course, I can tailor the summary to your main point. Then I can send it over, so it is more useful to you.
- Policy issues: `none`
- PROD-053C decision: `carry_forward`
- Policy-shape suggestion: Of course. I can tailor it to your main point, then send it over.

### prod-045-manager

- Current response: Of course. I can send it over. No commitment today. Take a look and let me know.
- Policy issues: `live_turn_too_long`
- PROD-053C decision: `rewrite_candidate`
- Policy-shape suggestion: Of course. I can send it over. No commitment today. Take a look and let me know.

### prod-045-spouse

- Current response: Of course. I can send it over. No commitment today. Take a look and let me know.
- Policy issues: `live_turn_too_long`
- PROD-053C decision: `rewrite_candidate`
- Policy-shape suggestion: Of course. I can send it over. No commitment today. Take a look and let me know.

## Boundaries

- English-only review.
- No German exact phrase promotion.
- No runtime behavior or response text changed.
- No LLM judging, no LLM calls, no provider calls, no retrieval enablement, and no private data reads.
- Rejected or deferred PROD-053A tactics remain blocked.
