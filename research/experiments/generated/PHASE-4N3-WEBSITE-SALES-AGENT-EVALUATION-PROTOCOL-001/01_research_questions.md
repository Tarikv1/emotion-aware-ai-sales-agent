# Research Questions

## Primary Questions

1. Does a structured campaign-specific sales-agent package improve micro-close success compared with a generic voice sales prompt?
2. Does vertical-specific sales knowledge improve relevance and objection handling?
3. Does explicit buyer-state and objection handling improve sales progression?
4. Can the agent maintain safety boundaries while still acting as a strong seller?
5. What failure modes remain when using a hosted voice-agent platform?

## Operational Hypotheses

H1: The Atlas 4N2 agent will produce a higher micro_close_success_rate than the generic baseline on cases where the target is free_mockup_yes or review_call_yes.

H2: The Atlas 4N2 agent will score higher on vertical_relevance and pain_to_value_bridge because the knowledge base contains local-business vertical playbooks.

H3: The Atlas 4N2 agent will score higher on objection_handling and buyer_state_adaptation in cases involving price, spam concern, bad prior agency experience, partner approval, or SEO ranking demand.

H4: The Atlas 4N2 agent should not increase fake_guarantee, fake_identity, pressure_after_stop_request, or hallucinated_business_claim failures.

H5: Hosted voice-agent platform limits may still cause overtalking, weak call control, internal wording leakage, inconsistent stop handling, or unnatural spoken quality.

## Evidence That Would Change The Recommendation

Prefer the generic baseline if it matches Atlas on micro-close success while showing fewer hard failures, lower complexity, and better spoken naturalness.

Prefer revising Atlas if it improves sales scores but causes safety, trust, or compliance regressions.

Keep Atlas as the stronger thesis design only if it improves sales outcomes and preserves hard safety boundaries across the fixed case matrix.
