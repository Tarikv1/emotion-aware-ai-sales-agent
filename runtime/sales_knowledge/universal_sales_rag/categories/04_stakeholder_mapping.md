# Stakeholder Mapping

Layer: Universal Sales RAG

Category ID: `stakeholder_mapping`

Owns: reusable handling of decision makers, gatekeepers, influencers, users, blockers, economic buyers, technical reviewers, legal reviewers, and pass-along paths.

Does Not Own: named people, private contact details, actual authority, internal politics, or campaign-specific routing rules.

Retrieval Triggers: "I'm not the owner", "talk to my manager", "send it to me", "who should look at it", "I need to ask someone", "the owner is not here".

Operating Rules: ask for role only when needed. Do not make a staff member decide outside their role. Give a short note when speaking through a gatekeeper. Preserve callback windows and pass-along instructions. If the decision maker is unknown, seek the next safe routing step, not a full pitch.

Name capture should identify the human speaker when rapport matters and the speaker has confirmed decision-maker or manager status. Ask once, briefly, and use the name sparingly. Do not ask for a name before answering a direct objection, during a busy callback, during a gatekeeper pass-along, or after a terminal next step has already been accepted.

Failure Modes: interrogating a gatekeeper, asking "what should I tell them", ignoring the stated callback time, or assuming a staff member can authorize a paid step.

Campaign Overlay Handoff: campaign overlay defines valid decision-maker roles, pass-along notes, handoff path, and whether contact capture is allowed.
