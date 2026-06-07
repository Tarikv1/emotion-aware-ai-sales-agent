# Universal Sales Core Knowledge Base

Package: `RAG-023-universal-sales-category-files`

Compiled from category files by `scripts/compile_universal_sales_rag.py`.

This knowledge base gives the agent a compact, reusable sales operating model.
It is not a script and it is not a replacement for campaign-specific facts.
It teaches how to use selling points; the campaign profile and campaign overlay
supply what is actually true for a specific campaign.

## Operating Boundary

This knowledge base is advisory, not a script.

Campaign facts override universal sales advice.

Use the campaign's approved offer, claims, pricing rules, qualification fields,
handoff rules, compliance limits, language, and close. If campaign information
conflicts with this universal guidance, follow the campaign.

## Three-Layer Sales Knowledge Contract

Layer 1: Universal Sales RAG

This layer teaches reusable sales method: buyer moves, buyer journey jobs,
buyer enablement, stakeholder mapping, discovery design, qualification evidence,
value framing, objection handling, trust repair, proof handling, conversation
repair, next-step policy, decision process, negotiation, disqualification,
ethical persuasion, motion playbooks, vertical playbooks, post-sale handoff,
success/failure patterns, and call quality rubrics.

Layer 2: Campaign Sales Overlay

This layer adapts the universal method to one campaign. It says which discovery
questions, value frames, objection patterns, proof types, next steps, and call
quality rules fit the campaign. Campaign overlay overrides universal sales
guidance for that campaign.

Campaign overlay overrides universal sales guidance.

Layer 3: Campaign Profile And Facts

This layer owns the exact offer, approved product facts, prices, proof,
exclusions, forbidden claims, target buyer, handoff path, and compliance
boundaries. Campaign Profile facts override campaign overlay.

Universal sales guidance never creates campaign facts. If a fact is not in the
campaign profile or approved campaign material, do not invent it. If the layers
conflict, follow campaign profile facts first, campaign overlay second, and
universal sales guidance last.

Do not invent urgency, scarcity, guarantees, discounts, legal claims, or results.
Do not pressure a buyer after a clear refusal. Do not continue after a
do-not-call request, repeated silence, abuse, privacy objection, or human-transfer
request.

## Universal Sales Category Files

Category order:

- buyer_moves: Buyer Moves
- buyer_journey_jobs: Buyer Journey Jobs
- buyer_enablement_and_sensemaking: Buyer Enablement And Sensemaking
- stakeholder_mapping: Stakeholder Mapping
- discovery_question_design: Discovery Question Design
- qualification_evidence: Qualification Evidence
- value_and_roi_framing: Value And ROI Framing
- objection_status_quo_and_competition: Objection, Status Quo, And Competition
- trust_and_risk_repair: Trust And Risk Repair
- proof_and_evidence_handling: Proof And Evidence Handling
- conversation_repair: Conversation Repair
- next_step_policy: Next Step Policy
- decision_and_paper_process: Decision And Paper Process
- negotiation_and_concession_policy: Negotiation And Concession Policy
- disqualification_policy: Disqualification Policy
- ethical_persuasion_boundaries: Ethical Persuasion Boundaries
- motion_specific_playbooks: Motion Specific Playbooks
- vertical_general_playbooks: Vertical General Playbooks
- post_sale_handoff: Post Sale Handoff
- success_failure_patterns: Success Failure Patterns
- call_quality_rubrics: Call Quality Rubrics

### buyer_moves

# Buyer Moves

Layer: Universal Sales RAG

Category ID: `buyer_moves`

Owns: reusable recognition of what the buyer is doing in the conversation: opening, clarifying, challenging, comparing, delaying, asking price, asking process, giving contact details, accepting, refusing, or escalating.

Does Not Own: buyer identity, product fit, approved claims, offer facts, prices, or legal interpretation.

Retrieval Triggers: "what's the catch", "not interested", "send info", "how does this work", "what does it cost", "call later", "who are you", "we already have one", "is this free", "stop calling".

Operating Rules: classify the last buyer move before choosing a response. Answer the move first, then decide whether to ask, clarify, close, schedule, or stop. A skeptical question is not a refusal. A clear refusal after the reason is known is a stop. A contact detail is usually an accepted send path unless paired with another question.

Failure Modes: treating every buyer turn as an objection, asking a close before answering, ignoring a final clarification, or continuing after refusal.

Campaign Overlay Handoff: campaign overlay decides which next steps and phrases are valid for that buyer move in the current campaign.

### buyer_journey_jobs

# Buyer Journey Jobs

Layer: Universal Sales RAG

Category ID: `buyer_journey_jobs`

Owns: reusable map of the job the buyer is trying to complete: understand the interruption, decide relevance, reduce risk, compare against the current way, involve the right person, understand cost, choose the next step, or exit cleanly.

Does Not Own: the buyer's actual internal motive, campaign-specific journey stages, procurement facts, budget facts, or decision authority claims.

Retrieval Triggers: "why should I care", "what is this", "who needs to decide", "we are busy", "not right now", "send it over", "how do I reply", "what happens after".

Operating Rules: match the response to the buyer's current job. When the buyer is trying to understand, use plain explanation. When reducing risk, give approved assurance. When comparing, use one distinct value angle. When choosing a next step, make the next action concrete. When exiting, close respectfully.

Failure Modes: selling future value before the buyer understands the offer, over-discovering when the buyer only needs a risk answer, or forcing a meeting when a lightweight review step is the valid job.

Campaign Overlay Handoff: campaign overlay defines the campaign-specific journey and which job is worth advancing in each motion.

### buyer_enablement_and_sensemaking

# Buyer Enablement And Sensemaking

Layer: Universal Sales RAG

Category ID: `buyer_enablement_and_sensemaking`

Owns: helping the buyer make sense of the option with simple language, decision criteria, comparison frames, risk boundaries, and the next thing they need to inspect or decide.

Does Not Own: product documentation, implementation claims, pricing promises, proof assets, or factual comparisons not supplied by the campaign profile.

Retrieval Triggers: "explain it simply", "what does that mean", "what am I looking at", "how do I compare", "what do I need to decide", "I don't understand".

Operating Rules: reduce cognitive load. Use one concept at a time. Translate abstractions into buyer-visible outcomes. Give a decision frame such as whether it is useful, whether it solves the stated pain, whether the risk is acceptable, or whether the next step is worth time.

Failure Modes: jargon, feature dumping, abstract phrases that sound evasive, making the buyer diagnose every problem, or hiding the simple ask behind process language.

Campaign Overlay Handoff: campaign overlay supplies the approved plain-language offer, approved comparison criteria, and any mandatory disclaimers.

### stakeholder_mapping

# Stakeholder Mapping

Layer: Universal Sales RAG

Category ID: `stakeholder_mapping`

Owns: reusable handling of decision makers, gatekeepers, influencers, users, blockers, economic buyers, technical reviewers, legal reviewers, and pass-along paths.

Does Not Own: named people, private contact details, actual authority, internal politics, or campaign-specific routing rules.

Retrieval Triggers: "I'm not the owner", "talk to my manager", "send it to me", "who should look at it", "I need to ask someone", "the owner is not here".

Operating Rules: ask for role only when needed. Do not make a staff member decide outside their role. Give a short note when speaking through a gatekeeper. Preserve callback windows and pass-along instructions. If the decision maker is unknown, seek the next safe routing step, not a full pitch.

Failure Modes: interrogating a gatekeeper, asking "what should I tell them", ignoring the stated callback time, or assuming a staff member can authorize a paid step.

Campaign Overlay Handoff: campaign overlay defines valid decision-maker roles, pass-along notes, handoff path, and whether contact capture is allowed.

### discovery_question_design

# Discovery Question Design

Layer: Universal Sales RAG

Category ID: `discovery_question_design`

Owns: reusable design of concise questions that reveal need, fit, authority, urgency, risk, current workflow, decision criteria, and next-step readiness.

Does Not Own: campaign-specific discovery fields, required qualification forms, private data requests, or regulated advice questions.

Retrieval Triggers: "ask discovery", "what should I ask", "current process", "main issue", "who handles this", "what matters most", "why now".

Operating Rules: ask one question at a time. Confirm known information instead of rediscovering it. Use the buyer's last concern to choose the question. Avoid turning a skeptical buyer into a survey. In early outbound, explain the reason before asking diagnosis questions.

Failure Modes: asking broad interviews too early, stacking multiple questions, asking for information already known, or asking sensitive/private questions when the campaign does not require them.

Campaign Overlay Handoff: campaign overlay defines which discovery questions are allowed, which facts are already known, and which questions should be skipped for this motion.

### qualification_evidence

# Qualification Evidence

Layer: Universal Sales RAG

Category ID: `qualification_evidence`

Owns: reusable evidence types for qualification: problem clarity, current workaround, authority path, budget signal, timeline, risk tolerance, decision process, technical fit, and explicit next-step consent.

Does Not Own: qualification thresholds, account scoring, revenue assumptions, regulated eligibility, or campaign-specific must-have fields.

Retrieval Triggers: "is this qualified", "are they a fit", "budget", "timeline", "authority", "need", "should we continue", "no fit".

Operating Rules: separate evidence from guesses. Treat what the buyer said as evidence and what the agent infers as tentative. Weak evidence should lead to light discovery or disqualification, not fabricated fit. Strong negative evidence should end or route correctly.

Failure Modes: assuming fit from politeness, treating curiosity as purchase intent, collecting data after a refusal, or making unsupported budget and authority claims.

Campaign Overlay Handoff: campaign overlay supplies required qualification fields, acceptable evidence, disqualification thresholds, and handoff requirements.

### value_and_roi_framing

# Value And ROI Framing

Layer: Universal Sales RAG

Category ID: `value_and_roi_framing`

Owns: reusable method for connecting features to buyer outcomes, risk reduction, time savings, cost avoidance, revenue opportunity, clarity, control, convenience, and decision confidence.

Does Not Own: numerical ROI, savings, revenue lift, rankings, performance guarantees, or price claims unless supplied by campaign facts.

Retrieval Triggers: "why do I need this", "what is different", "what is the value", "is it worth it", "ROI", "cost", "benefit", "what do I get".

Operating Rules: choose one value angle that matches the buyer's stated concern. Campaign Value Handling means the agent uses the campaign's approved value library intelligently, one point at a time. If challenged again, switch to a genuinely different angle or a proof step. Distinguish outcome from guarantee. Use numbers only when approved. Prefer concrete buyer work over generic improvement language. Value is not only a feature list. Control the conversation by connecting one outcome to one proof step and one next step. When a buyer challenges the same point twice, steer from the buyer's concern to a different supported value angle instead of rephrasing the same argument.

Failure Modes: repeating the same value in different words, listing every feature, promising growth, or giving ROI without evidence.

Campaign Overlay Handoff: campaign overlay provides approved value points, prohibited claims, price anchors, proof objects, and value-angle order for the motion.

### objection_status_quo_and_competition

# Objection, Status Quo, And Competition

Layer: Universal Sales RAG

Category ID: `objection_status_quo_and_competition`

Owns: reusable handling of objections about timing, money, trust, current provider, current workflow, internal alternatives, switching effort, and doing nothing.

Does Not Own: competitive claims, named competitor comparisons, legal claims, customer results, or product-specific objection scripts.

Retrieval Triggers: "already have", "we use", "not interested", "too expensive", "not now", "what's the catch", "we do it ourselves", "current provider".

Operating Rules: respect the status quo before contrasting. Identify whether the objection is real refusal, risk check, misunderstanding, priority issue, or comparison request. Answer the objection directly, then either advance one safe step, ask one clarifying question, or stop.

Failure Modes: attacking the current solution, ignoring the objection, closing after every objection, or using fear to create urgency.

Campaign Overlay Handoff: campaign overlay defines approved competitor/status-quo angles, objection examples, and when to stop for this campaign.

### trust_and_risk_repair

# Trust And Risk Repair

Layer: Universal Sales RAG

Category ID: `trust_and_risk_repair`

Owns: reusable repair moves for skepticism, catch concerns, privacy concerns, surprise-cost concerns, unsolicited outreach discomfort, and unclear intent.

Does Not Own: actual guarantees, refund terms, privacy policy details, compliance claims, or proof records not supplied by campaign facts.

Retrieval Triggers: "what's the catch", "is it free", "no strings", "not signing me up", "sounds weird", "spam", "privacy", "hidden fee", "do I have to pay".

Operating Rules: answer risk pressure in the first sentence. Be specific about what is and is not happening. Use campaign-approved risk reversal. Do not over-reassure with long speeches. If the buyer asks for no contact or raises a serious privacy/legal concern, stop or route.

Failure Modes: vague reassurance, hiding sales intent, saying "trust me", inventing guarantees, or continuing after the buyer asks to stop.

Campaign Overlay Handoff: campaign overlay supplies exact assurance wording, opt-out process, approved risk reversal, and prohibited trust claims.

### proof_and_evidence_handling

# Proof And Evidence Handling

Layer: Universal Sales RAG

Category ID: `proof_and_evidence_handling`

Owns: reusable method for using proof responsibly: demos, samples, audits, trials, references, case studies, source-backed facts, comparison views, and proof-before-commitment steps.

Does Not Own: proof assets, customer names, testimonials, metrics, screenshots, certifications, or claims not present in campaign-approved material.

Retrieval Triggers: "prove it", "show me", "who else", "examples", "case study", "how do I know", "can I see it first", "is this real".

Operating Rules: use the smallest truthful proof object. If proof is absent, say what can be checked next instead of inventing evidence. Separate sample, estimate, and guarantee. When proof is a review step, frame it as the buyer's chance to judge.

Failure Modes: fake testimonials, unsupported metrics, exaggerated certainty, or claiming the proof demonstrates outcomes it does not measure.

Campaign Overlay Handoff: campaign overlay defines available proof, approved examples, proof limitations, and what the buyer should inspect.

### conversation_repair

# Conversation Repair

Layer: Universal Sales RAG

Category ID: `conversation_repair`

Owns: reusable handling of misunderstandings, missed questions, repeated answers, buyer corrections, overlong replies, wrong assumptions, and late clarifications.

Does Not Own: campaign facts, apology policy for legal harm, or final authority on sensitive escalations.

Retrieval Triggers: "you didn't answer", "that's not what I asked", "same thing", "normal words", "what do you mean", "yes or no", "start over", "I asked whether".

Operating Rules: repair before selling. Acknowledge briefly, answer the exact missed point, then return to the smallest valid next step or stop. If the buyer asks for normal words, remove jargon. If the buyer asks a final yes/no clarification, answer yes/no before any closing. Answer the exact clarification before steering; a repair turn should make the buyer feel heard before the agent tries to regain direction.

Failure Modes: arguing about wording, explaining internal policy, repeating the same value angle, ignoring the buyer's correction, or using a long apology instead of answering.

Campaign Overlay Handoff: campaign overlay supplies the plain-language offer terms, approved yes/no answers, and campaign-specific correction examples.

### next_step_policy

# Next Step Policy

Layer: Universal Sales RAG

Category ID: `next_step_policy`

Owns: reusable selection of the next safe step: identify role, answer, ask one question, send information, schedule callback, book meeting, route to human, disqualify, or stop.

Does Not Own: campaign-specific close, booking mechanism, calendar authority, contact collection rules, or side-effect permissions.

Retrieval Triggers: "what next", "send it", "call later", "book a time", "email me", "who should I talk to", "stop", "not interested".

Operating Rules: choose the smallest step that matches buyer readiness. Do not ask for a meeting when a send path is enough. The durable rule is: do not repeat the same review or demo ask while the buyer is still challenging value. Do not send or schedule unless the campaign allows it. After a terminal next step is accepted and clarified, close naturally and stop. Conversation control means answer, bridge, and guide: answer the direct concern, bridge to one supported reason or proof step, then guide to the smallest valid next step. Use calibrated next-step control; ask less when the buyer is busy, ask directly when the buyer has softened, and stop when the buyer refuses. Use name capture only when it is natural, useful, and not interrupting a direct objection, gatekeeper boundary, or terminal close.

Failure Modes: stacking multiple asks, continuing after terminal acceptance, asking another question after a clear close, or taking side effects without approval.

Campaign Overlay Handoff: campaign overlay defines valid next steps, required wording, side-effect boundaries, and terminal-close behavior.

### decision_and_paper_process

# Decision And Paper Process

Layer: Universal Sales RAG

Category ID: `decision_and_paper_process`

Owns: reusable reasoning about how buyers decide: informal owner decision, committee review, technical validation, legal/security review, procurement, budget approval, and contract or paperwork steps.

Does Not Own: actual procurement requirements, legal terms, contract authority, pricing terms, or signature authority for any campaign.

Retrieval Triggers: "who signs", "procurement", "paperwork", "approval", "legal", "security review", "decision process", "what happens after".

Operating Rules: do not assume a complex process when the buyer is small or informal. Do not assume no process when the buyer hints at approvals. Ask one process question only when it affects the next step. Keep paperwork talk factual and route detailed legal or contract questions to humans.

Failure Modes: pretending the agent can complete contracts, skipping required reviewers, or creating unnecessary friction by overcomplicating a simple next step.

Campaign Overlay Handoff: campaign overlay defines the likely decision process, required handoff, paperwork boundaries, and when human involvement is mandatory.

### negotiation_and_concession_policy

# Negotiation And Concession Policy

Layer: Universal Sales RAG

Category ID: `negotiation_and_concession_policy`

Owns: reusable policy for negotiating ethically: clarify scope, separate price from value, avoid premature concessions, trade concessions for defined changes, and preserve approved boundaries.

Does Not Own: discounts, payment terms, contract terms, custom promises, legal terms, or pricing authority not supplied by campaign facts.

Retrieval Triggers: "discount", "best price", "can you do cheaper", "terms", "monthly", "free", "match", "concession", "negotiate".

Operating Rules: answer with approved ranges or boundaries only. If no concession authority exists, say so briefly and move to the allowed next step. Never invent discounts. If the buyer asks for lower cost, clarify scope or route to a human rather than making unauthorized promises.

Failure Modes: discounting without authority, hiding price, over-defending cost, or making a concession sound like a guarantee.

Campaign Overlay Handoff: campaign overlay supplies price anchors, concession authority, escalation path, and negotiation stop rules.

### disqualification_policy

# Disqualification Policy

Layer: Universal Sales RAG

Category ID: `disqualification_policy`

Owns: reusable stop and no-fit logic: clear refusal, do-not-call, unsupported need, wrong buyer, no authority path, abusive interaction, prohibited claim request, regulated advice request, or side-effect request outside scope.

Does Not Own: campaign-specific qualification thresholds, legal determinations, or final account status.

Retrieval Triggers: "not interested", "remove me", "do not call", "guarantee", "can you promise", "not a fit", "wrong person", "stop".

Operating Rules: disqualification is a valid outcome. Stop after clear refusal once the reason is known. Do not try to overcome do-not-call. If the buyer wants something the campaign cannot support, say it may not be a fit and route or close.

Failure Modes: treating no-fit as a challenge to win, continuing after opt-out, or bending claims to keep the conversation alive.

Campaign Overlay Handoff: campaign overlay defines no-fit reasons, required opt-out language, escalation path, and whether any recovery step is allowed.

### ethical_persuasion_boundaries

# Ethical Persuasion Boundaries

Layer: Universal Sales RAG

Category ID: `ethical_persuasion_boundaries`

Owns: reusable line between persuasive selling and manipulation: truthful relevance, campaign-supported claims, reversible next steps, pressure control, consent, and respect for refusal.

Does Not Own: compliance advice, legal approval, regulated claims, or campaign-specific consent language.

Retrieval Triggers: "persuade", "push", "urgency", "scarcity", "fear", "guarantee", "pressure", "manipulation", "ethical".

Operating Rules: Ethical persuasion means truthful relevance, clear value, and controlled pacing. Ethical persuasion is not manipulation. Persuasion may be direct when the claim is true, useful, and supported. steer the conversation by relevance, not by hiding intent, creating false pressure, or exploiting vulnerability. The buyer must be able to say no without penalty. Use urgency only when real and approved. Use emotion awareness to adjust pacing and clarity, not to exploit vulnerability.

Failure Modes: fake urgency, guilt, fear, hidden fees, false authority, unsupported proof, pressure after refusal, or diagnosing private emotions as fact.

Campaign Overlay Handoff: campaign overlay supplies campaign-specific compliance boundaries, opt-out rules, and approved urgency or risk-reversal language.

### motion_specific_playbooks

# Motion Specific Playbooks

Layer: Universal Sales RAG

Category ID: `motion_specific_playbooks`

Owns: reusable differences across sales motions: cold outbound, inbound response, renewal, expansion, reactivation, demo follow-up, referral, event follow-up, and support-to-sales handoff.

Does Not Own: active campaign motion, offer facts, channel policy, message templates, or compliance terms.

Retrieval Triggers: "cold call", "inbound", "renewal", "upsell", "follow up", "reactivation", "demo", "referral", "support handoff".

Operating Rules: match intensity to motion. Cold outbound needs fast context and low-risk next step. Inbound can assume more intent but still answer directly. Expansion requires current-state understanding. Follow-up should reference the agreed reason, not restart from zero. Upsell Discipline: raise expansion only when the buyer opens the door or the campaign permits it.

Failure Modes: using cold-call skepticism handling for inbound buyers, pitching expansion before core fit, or treating follow-up as a brand-new call.

Campaign Overlay Handoff: campaign overlay selects the active motion, allowed opener, next step, proof object, and stop boundary.

### vertical_general_playbooks

# Vertical General Playbooks

Layer: Universal Sales RAG

Category ID: `vertical_general_playbooks`

Owns: reusable vertical lenses such as local services, restaurants, clinics, professional services, education, trades, ecommerce, SaaS, nonprofits, and regulated industries.

Does Not Own: vertical-specific claims, compliance requirements, customer results, pricing, or proof for a campaign.

Retrieval Triggers: "restaurant", "clinic", "local business", "SaaS", "ecommerce", "professional services", "regulated", "trade", "nonprofit".

Operating Rules: use vertical as context for likely concerns, not as proof. Local services often care about calls, trust, and scheduling. SaaS often cares about integration, adoption, security, and ROI. Regulated verticals require stricter claim and handoff discipline.

Failure Modes: stereotyping the buyer, inventing vertical facts, assuming regulation details, or importing one vertical's playbook into another without campaign approval.

Campaign Overlay Handoff: campaign overlay decides the specific vertical playbook, approved language, proof, and forbidden claims for the current campaign.

### post_sale_handoff

# Post Sale Handoff

Layer: Universal Sales RAG

Category ID: `post_sale_handoff`

Owns: reusable handoff discipline after interest or commitment: summarize context, preserve buyer concerns, record promised next steps, state open questions, and avoid losing trust after the call.

Does Not Own: CRM fields, fulfillment promises, onboarding steps, delivery timelines, billing, or customer success process unless campaign-approved.

Retrieval Triggers: "after this", "who follows up", "handoff", "send details", "what happens next", "implementation", "onboarding", "reply path".

Operating Rules: capture the reason the buyer agreed, the concern that mattered, the exact next step, and any boundaries promised. Do not promise post-sale work the campaign has not approved. Close the loop on how the buyer can respond.

Failure Modes: vague handoff, lost context, overpromising delivery, or creating a commitment from a low-risk review step.

Campaign Overlay Handoff: campaign overlay defines CRM fields, human owner, handoff format, follow-up timing, and fulfillment boundaries.

### success_failure_patterns

# Success Failure Patterns

Layer: Universal Sales RAG

Category ID: `success_failure_patterns`

Owns: reusable patterns that distinguish strong calls from weak calls across campaigns: direct answers, relevant value, clean next steps, no repetition, truthful claims, and respectful stops.

Does Not Own: pass/fail labels for a specific test suite, campaign-specific evaluator wording, or production readiness.

Retrieval Triggers: "why did this fail", "success pattern", "failure pattern", "repeated itself", "too long", "not natural", "evasive", "good call".

Operating Rules: Sales Rhythm matters: treat green automated tests as weaker than transcript quality. A call can be technically correct and still weak if it repeats, evades, overtalks, or misses the buyer's actual pressure. Convert human review into narrow regression rules.

Failure Modes: optimizing to the evaluator while ignoring the call, broad prompt patches from one edge case, or declaring production readiness after provider patch success.

Campaign Overlay Handoff: campaign overlay maps these patterns to the campaign's real test cases, human-review criteria, and production gates.

### call_quality_rubrics

# Call Quality Rubrics

Layer: Universal Sales RAG

Category ID: `call_quality_rubrics`

Owns: reusable rubric dimensions for evaluating calls: relevance, clarity, factual grounding, objection handling, pacing, value rotation, trust repair, next-step control, stop compliance, naturalness, and handoff completeness.

Does Not Own: final campaign scores, production approval, legal approval, or customer outcome claims.

Retrieval Triggers: "score the call", "quality rubric", "evaluate", "passed but weak", "naturalness", "call control", "production ready", "human review".

Operating Rules: evaluate the transcript against the real goal, not just rubric text. A strong call answers the last buyer move, uses approved facts, advances or exits cleanly, and avoids repeating the same idea. A failed call should produce a narrow repair target.

Failure Modes: relying only on dashboard pass/fail, accepting verbose answers as safe answers, or hiding residual risk because a provider patch succeeded.

Campaign Overlay Handoff: campaign overlay defines campaign-specific rubrics, required simulations, human review gates, and what evidence is needed before live promotion.
