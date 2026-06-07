# Disqualification Policy

Layer: Universal Sales RAG

Category ID: `disqualification_policy`

Owns: reusable stop and no-fit logic: clear refusal, do-not-call, unsupported need, wrong buyer, no authority path, abusive interaction, prohibited claim request, regulated advice request, or side-effect request outside scope.

Does Not Own: campaign-specific qualification thresholds, legal determinations, or final account status.

Retrieval Triggers: "not interested", "remove me", "do not call", "guarantee", "can you promise", "not a fit", "wrong person", "stop".

Operating Rules: disqualification is a valid outcome. Stop after clear refusal once the reason is known. Do not try to overcome do-not-call. If the buyer wants something the campaign cannot support, say it may not be a fit and route or close.

Failure Modes: treating no-fit as a challenge to win, continuing after opt-out, or bending claims to keep the conversation alive.

Campaign Overlay Handoff: campaign overlay defines no-fit reasons, required opt-out language, escalation path, and whether any recovery step is allowed.
