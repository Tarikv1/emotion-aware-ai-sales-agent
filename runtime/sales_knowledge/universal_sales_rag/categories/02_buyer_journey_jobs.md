# Buyer Journey Jobs

Layer: Universal Sales RAG

Category ID: `buyer_journey_jobs`

Owns: reusable map of the job the buyer is trying to complete: understand the interruption, decide relevance, reduce risk, compare against the current way, involve the right person, understand cost, choose the next step, or exit cleanly.

Does Not Own: the buyer's actual internal motive, campaign-specific journey stages, procurement facts, budget facts, or decision authority claims.

Retrieval Triggers: "why should I care", "what is this", "who needs to decide", "we are busy", "not right now", "send it over", "how do I reply", "what happens after".

Operating Rules: match the response to the buyer's current job. When the buyer is trying to understand, use plain explanation. When reducing risk, give approved assurance. When comparing, use one distinct value angle. When choosing a next step, make the next action concrete. When exiting, close respectfully.

Demand-creation sequence: after the buyer understands the interruption, the agent may connect four pieces in order: the likely problem, the offered solution, the buyer gain, and the curiosity/proof step. Treat the problem as a campaign-supported hypothesis, not a diagnosis. The problem must be concrete enough to create demand; "a clearer page" is usually too weak by itself. Prefer the campaign's strongest safe mechanism, such as local visibility support, risk reduction, time savings, cost avoidance, access to proof, or a simpler route to the buyer's current goal. If the buyer rejects the problem, switch to a different supported problem hypothesis or stop.

Failure Modes: selling future value before the buyer understands the offer, over-discovering when the buyer only needs a risk answer, or forcing a meeting when a lightweight review step is the valid job.

Campaign Overlay Handoff: campaign overlay defines the campaign-specific journey and which job is worth advancing in each motion.
