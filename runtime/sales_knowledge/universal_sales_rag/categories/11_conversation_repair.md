# Conversation Repair

Layer: Universal Sales RAG

Category ID: `conversation_repair`

Owns: reusable handling of misunderstandings, missed questions, repeated answers, buyer corrections, overlong replies, wrong assumptions, and late clarifications.

Does Not Own: campaign facts, apology policy for legal harm, or final authority on sensitive escalations.

Retrieval Triggers: "you didn't answer", "that's not what I asked", "same thing", "normal words", "what do you mean", "yes or no", "start over", "I asked whether".

Operating Rules: repair before selling. Acknowledge briefly, answer the exact missed point, then return to the smallest valid next step or stop. If the buyer asks for normal words, remove jargon. If the buyer asks a final yes/no clarification, answer yes/no before any closing. Answer the exact clarification before steering; a repair turn should make the buyer feel heard before the agent tries to regain direction.

Failure Modes: arguing about wording, explaining internal policy, repeating the same value angle, ignoring the buyer's correction, or using a long apology instead of answering.

Campaign Overlay Handoff: campaign overlay supplies the plain-language offer terms, approved yes/no answers, and campaign-specific correction examples.
