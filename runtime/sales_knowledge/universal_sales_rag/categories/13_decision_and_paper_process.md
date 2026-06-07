# Decision And Paper Process

Layer: Universal Sales RAG

Category ID: `decision_and_paper_process`

Owns: reusable reasoning about how buyers decide: informal owner decision, committee review, technical validation, legal/security review, procurement, budget approval, and contract or paperwork steps.

Does Not Own: actual procurement requirements, legal terms, contract authority, pricing terms, or signature authority for any campaign.

Retrieval Triggers: "who signs", "procurement", "paperwork", "approval", "legal", "security review", "decision process", "what happens after".

Operating Rules: do not assume a complex process when the buyer is small or informal. Do not assume no process when the buyer hints at approvals. Ask one process question only when it affects the next step. Keep paperwork talk factual and route detailed legal or contract questions to humans.

Failure Modes: pretending the agent can complete contracts, skipping required reviewers, or creating unnecessary friction by overcomplicating a simple next step.

Campaign Overlay Handoff: campaign overlay defines the likely decision process, required handoff, paperwork boundaries, and when human involvement is mandatory.
