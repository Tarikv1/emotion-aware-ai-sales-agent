# Motion Specific Playbooks

Layer: Universal Sales RAG

Category ID: `motion_specific_playbooks`

Owns: reusable differences across sales motions: cold outbound, inbound response, renewal, expansion, reactivation, demo follow-up, referral, event follow-up, and support-to-sales handoff.

Does Not Own: active campaign motion, offer facts, channel policy, message templates, or compliance terms.

Retrieval Triggers: "cold call", "inbound", "renewal", "upsell", "follow up", "reactivation", "demo", "referral", "support handoff".

Operating Rules: match intensity to motion. Cold outbound needs fast context and low-risk next step. Inbound can assume more intent but still answer directly. Expansion requires current-state understanding. Follow-up should reference the agreed reason, not restart from zero. Upsell Discipline: raise expansion only when the buyer opens the door or the campaign permits it.

Failure Modes: using cold-call skepticism handling for inbound buyers, pitching expansion before core fit, or treating follow-up as a brand-new call.

Campaign Overlay Handoff: campaign overlay selects the active motion, allowed opener, next step, proof object, and stop boundary.
