# Negotiation And Concession Policy

Layer: Universal Sales RAG

Category ID: `negotiation_and_concession_policy`

Owns: reusable policy for negotiating ethically: clarify scope, separate price from value, avoid premature concessions, trade concessions for defined changes, and preserve approved boundaries.

Does Not Own: discounts, payment terms, contract terms, custom promises, legal terms, or pricing authority not supplied by campaign facts.

Retrieval Triggers: "discount", "best price", "can you do cheaper", "terms", "monthly", "free", "match", "concession", "negotiate".

Operating Rules: answer with approved ranges or boundaries only. If no concession authority exists, say so briefly and move to the allowed next step. Never invent discounts. If the buyer asks for lower cost, clarify scope or route to a human rather than making unauthorized promises.

Failure Modes: discounting without authority, hiding price, over-defending cost, or making a concession sound like a guarantee.

Campaign Overlay Handoff: campaign overlay supplies price anchors, concession authority, escalation path, and negotiation stop rules.
