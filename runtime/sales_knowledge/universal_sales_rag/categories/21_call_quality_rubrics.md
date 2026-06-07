# Call Quality Rubrics

Layer: Universal Sales RAG

Category ID: `call_quality_rubrics`

Owns: reusable rubric dimensions for evaluating calls: relevance, clarity, factual grounding, objection handling, pacing, value rotation, trust repair, next-step control, stop compliance, naturalness, and handoff completeness.

Does Not Own: final campaign scores, production approval, legal approval, or customer outcome claims.

Retrieval Triggers: "score the call", "quality rubric", "evaluate", "passed but weak", "naturalness", "call control", "production ready", "human review".

Operating Rules: evaluate the transcript against the real goal, not just rubric text. A strong call answers the last buyer move, uses approved facts, advances or exits cleanly, and avoids repeating the same idea. A failed call should produce a narrow repair target.

Failure Modes: relying only on dashboard pass/fail, accepting verbose answers as safe answers, or hiding residual risk because a provider patch succeeded.

Campaign Overlay Handoff: campaign overlay defines campaign-specific rubrics, required simulations, human review gates, and what evidence is needed before live promotion.
