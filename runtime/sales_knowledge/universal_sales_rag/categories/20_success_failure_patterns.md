# Success Failure Patterns

Layer: Universal Sales RAG

Category ID: `success_failure_patterns`

Owns: reusable patterns that distinguish strong calls from weak calls across campaigns: direct answers, relevant value, clean next steps, no repetition, truthful claims, and respectful stops.

Does Not Own: pass/fail labels for a specific test suite, campaign-specific evaluator wording, or production readiness.

Retrieval Triggers: "why did this fail", "success pattern", "failure pattern", "repeated itself", "too long", "not natural", "evasive", "good call".

Operating Rules: Sales Rhythm matters: treat green automated tests as weaker than transcript quality. A call can be technically correct and still weak if it repeats, evades, overtalks, or misses the buyer's actual pressure. Convert human review into narrow regression rules.

Failure Modes: optimizing to the evaluator while ignoring the call, broad prompt patches from one edge case, or declaring production readiness after provider patch success.

Campaign Overlay Handoff: campaign overlay maps these patterns to the campaign's real test cases, human-review criteria, and production gates.
