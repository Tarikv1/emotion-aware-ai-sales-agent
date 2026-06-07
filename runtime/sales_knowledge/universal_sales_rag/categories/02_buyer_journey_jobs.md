# Buyer Journey Jobs

Layer: Universal Sales RAG

Category ID: `buyer_journey_jobs`

Owns: reusable map of the job the buyer is trying to complete: understand the interruption, decide relevance, reduce risk, compare against the current way, involve the right person, understand cost, choose the next step, or exit cleanly.

Does Not Own: the buyer's actual internal motive, campaign-specific journey stages, procurement facts, budget facts, or decision authority claims.

Retrieval Triggers: "why should I care", "what is this", "who needs to decide", "we are busy", "not right now", "send it over", "how do I reply", "what happens after".

Operating Rules: match the response to the buyer's current job. When the buyer is trying to understand, use plain explanation. When reducing risk, give approved assurance. When comparing, use one distinct value angle. When choosing a next step, make the next action concrete. When exiting, close respectfully.

Failure Modes: selling future value before the buyer understands the offer, over-discovering when the buyer only needs a risk answer, or forcing a meeting when a lightweight review step is the valid job.

Campaign Overlay Handoff: campaign overlay defines the campaign-specific journey and which job is worth advancing in each motion.
