# Qualification Evidence

Layer: Universal Sales RAG

Category ID: `qualification_evidence`

Owns: reusable evidence types for qualification: problem clarity, current workaround, authority path, budget signal, timeline, risk tolerance, decision process, technical fit, and explicit next-step consent.

Does Not Own: qualification thresholds, account scoring, revenue assumptions, regulated eligibility, or campaign-specific must-have fields.

Retrieval Triggers: "is this qualified", "are they a fit", "budget", "timeline", "authority", "need", "should we continue", "no fit".

Operating Rules: separate evidence from guesses. Treat what the buyer said as evidence and what the agent infers as tentative. Weak evidence should lead to light discovery or disqualification, not fabricated fit. Strong negative evidence should end or route correctly.

Failure Modes: assuming fit from politeness, treating curiosity as purchase intent, collecting data after a refusal, or making unsupported budget and authority claims.

Campaign Overlay Handoff: campaign overlay supplies required qualification fields, acceptable evidence, disqualification thresholds, and handoff requirements.
