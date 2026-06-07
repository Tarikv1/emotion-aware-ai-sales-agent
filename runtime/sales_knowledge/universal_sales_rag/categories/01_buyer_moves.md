# Buyer Moves

Layer: Universal Sales RAG

Category ID: `buyer_moves`

Owns: reusable recognition of what the buyer is doing in the conversation: opening, clarifying, challenging, comparing, delaying, asking price, asking process, giving contact details, accepting, refusing, or escalating.

Does Not Own: buyer identity, product fit, approved claims, offer facts, prices, or legal interpretation.

Retrieval Triggers: "what's the catch", "not interested", "send info", "how does this work", "what does it cost", "call later", "who are you", "we already have one", "is this free", "stop calling".

Operating Rules: classify the last buyer move before choosing a response. Answer the move first, then decide whether to ask, clarify, close, schedule, or stop. A skeptical question is not a refusal. A clear refusal after the reason is known is a stop. A contact detail is usually an accepted send path unless paired with another question.

Failure Modes: treating every buyer turn as an objection, asking a close before answering, ignoring a final clarification, or continuing after refusal.

Campaign Overlay Handoff: campaign overlay decides which next steps and phrases are valid for that buyer move in the current campaign.
