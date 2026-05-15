# English Sales Psychology Deep Dive

PROD-053A is a source-backed research checkpoint for the English conversation psychology layer. It does not change runtime behavior or response text.

## Summary

- Sources reviewed: `26`
- Topic findings: `9`
- Compact candidate rules: `8`
- Rejected or deferred tactics: `6`
- Runtime behavior changed: `False`
- Response text behavior changed: `False`
- Provider calls made: `False`

## Most Useful Findings

### adaptive_selling

- Finding: Useful adaptation needs situation recognition, confidence to alter the approach, a strategy library, and feedback from the interaction.
- Agent use: Classify the customer move first, then pick one small response pattern. Do not use one universal objection script.
- Avoid: Do not infer personality or hidden emotion to choose a strategy.

### listening_and_trust

- Finding: Listening and reflective responses are trust-building behaviors, but reflection is not the same as repeating everything the customer said.
- Agent use: Use a short acknowledgement or one targeted reflection before answering. Mirror only a short phrase when it helps repair or invites elaboration.
- Avoid: Do not echo full customer categories such as boss, manager, spouse, and partner in every response.

### buyer_confidence

- Finding: Many stalled sales are not lost to a competitor; they stall because the buyer is overloaded, uncertain, or safer doing nothing.
- Agent use: Reduce decision load and risk. Preserve relief language, but say it like a person: no commitment today; take a look and let me know.
- Avoid: Do not answer an uncertain buyer by adding more facts, more options, or a bigger commitment ask.

### autonomy_and_reactance

- Finding: People resist persuasive messages when they feel their freedom is being threatened or the next step is a hidden commitment.
- Agent use: Use real choices and explicit permission. Keep the buyer's ability to pause, compare, decline, or ask for a human visible.
- Avoid: Do not use must, have to, obviously, last chance, or false-choice closes.

### behavior_friction

- Finding: A hesitation can come from missing motivation, ability/capability, opportunity/context, or timing.
- Agent use: When the customer hesitates, lower friction or ask a tiny clarifier before proposing the next step.
- Avoid: Do not treat every hesitation as a closeable objection or pressure problem.

### trust_repair

- Finding: Trust concerns are not all the same: the buyer may question competence, whether the offer is in their interest, or whether the claim is honest.
- Agent use: Answer the trust gap that is actually present: proof for ability, low-pressure fit for benevolence, limits and verification for integrity.
- Avoid: Do not use testimonials, confidence, or reassurance as a universal trust answer.

### conversation_repair

- Finding: Conversation repair should identify a specific trouble source instead of restarting the whole pitch.
- Agent use: Use short repair moves such as 'the setup part?' or 'what changed?' only when the customer meaning is unclear.
- Avoid: Do not ask broad discovery questions after the customer already gave enough detail.

### spoken_brevity

- Finding: Live spoken agents should use short, active, simple turns with one idea per sentence and should stop after asking a question.
- Agent use: Keep most English sales turns to one or two breaths: acknowledgement, answer, relief or next step, stop.
- Avoid: Do not stack policy explanations, product facts, social proof, and a question in one turn.

### ethical_insight

- Finding: Insight-led selling is useful when it helps the buyer understand the situation, not when it manufactures urgency or pain.
- Agent use: Offer one campaign-supported reframe only after a direct factual answer or when the buyer asks why this matters.
- Avoid: Do not use fear, scarcity, invented benchmark claims, or emotional manipulation.

## Compact Rule Candidates

- `english_psych_001_listen_answer_then_continue` Listen, answer, then continue.: Start with a tiny acknowledgement, answer the customer move, then offer one low-friction next step.
  - Good: Of course. I can send it over. No commitment today. Take a look and let me know.
  - Bad: I can send a summary for your manager or spouse and there is no decision or commitment required from you today.
- `english_psych_002_relief_without_policy_dump` Keep relief, remove policy tone.: If a safety or pressure boundary matters, say the relief plainly and briefly instead of explaining the whole policy.
  - Good: No commitment today. Just take a look and let me know.
  - Bad: There is no decision, no payment, no commitment, and no binding agreement required from you on this call.
- `english_psych_003_mirror_only_for_repair_or_discovery` Mirror only when it does work.: Use a short partial repeat only to show listening, repair ambiguity, or invite elaboration; otherwise do not repeat the customer's category.
  - Good: Your boss? Got it. What would they care about most, price or setup?
  - Bad: Of course, I can send a short summary for your boss so your boss can review it.
- `english_psych_004_one_small_decision` One small decision per turn.: When the buyer is uncertain, ask for or offer only one small next step instead of asking them to process the whole sale.
  - Good: I can keep it simple and send the two main points first.
  - Bad: I can send the summary, explain pricing, compare options, book a call, and include the contract terms.
- `english_psych_005_diagnose_friction_not_personality` Diagnose friction, not personality.: Treat hesitation as possible relevance, ability, authority, risk, or timing friction; never label the buyer's personality or hidden emotion.
  - Good: Is the main thing price, timing, or who needs to review it?
  - Bad: It sounds like you are anxious about deciding.
- `english_psych_006_autonomy_visible` Make autonomy visible.: Use real options and make pause, review, decline, or human handoff acceptable outcomes.
  - Good: We can leave it there for today, or I can send the short version.
  - Bad: You should at least book the next call so you do not miss the opportunity.
- `english_psych_007_trust_gap_specific` Answer the specific trust gap.: For trust concerns, identify whether the gap is ability, interest, or honesty, and answer only that gap.
  - Good: I do not want to overclaim that. I can send what is verified, and a specialist can cover the technical part.
  - Bad: You can trust us; many people are happy with it.
- `english_psych_008_stop_after_question` Ask, then stop.: If the agent asks a question, it should not add another explanation after the question.
  - Good: What would be most useful in the summary?
  - Bad: What would be most useful in the summary? I can include pricing, terms, setup, and next steps if that helps.

## Rejected Or Deferred Tactics

- `reject` False scarcity or fake urgency: It can increase pressure and reactance, and it violates the project's low-pressure sales boundary.
- `reject` Hidden emotion diagnosis: Emotion signals are weak context; hidden-state certainty is already blocked by existing project policy.
- `reject` Commitment traps: Turning a soft yes into obligation conflicts with autonomy, trust, and no-commitment relief.
- `reject` Full customer-category echoing: Repeating boss, spouse, manager, or partner every time sounds scripted and does not add useful listening evidence.
- `defer` Large live psychology planner: A heavy reasoning layer can add latency. Research should be compressed into deterministic, reviewed rules first.
- `reject` General persuasion principles without source mapping: Generic tricks such as reciprocity, liking, and social proof are too easy to misuse unless tied to a safe, source-backed response rule.

## Sources

- `prod053a-source-001` Franke and Park adaptive selling/customer orientation meta-analysis - https://journals.sagepub.com/doi/10.1509/jmkr.43.4.693
- `prod053a-source-002` Adaptive selling integrative framework - https://link.springer.com/article/10.1007/s11747-025-01096-3
- `prod053a-source-003` Salesperson listening meta-analysis - https://www.sciencedirect.com/science/article/abs/pii/S0148296319303017
- `prod053a-source-004` Perceived listening work-outcomes meta-analysis - https://link.springer.com/article/10.1007/s10869-023-09897-5
- `prod053a-source-005` Gartner Challenger Sales Model overview - https://www.gartner.com/smarterwithgartner/power-challenger-sales-model
- `prod053a-source-006` Gartner modern B2B buyers and information overload - https://www.gartner.com/smarterwithgartner/what-sales-should-know-about-modern-b2b-buyers
- `prod053a-source-007` HBR customer indecision and no-decision sales losses - https://hbr.org/2022/06/stop-losing-sales-to-customer-indecision
- `prod053a-source-008` Bain B2B Elements of Value - https://www.bain.com/insights/the-b2b-elements-of-value-hbr
- `prod053a-source-009` Mayer, Davis, and Schoorman organizational trust model - https://www.jstor.org/stable/258792
- `prod053a-source-010` NCBI Bookshelf motivational interviewing chapter - https://www.ncbi.nlm.nih.gov/books/NBK571068/
- `prod053a-source-011` Empathy in motivational interviewing and language synchrony - https://pmc.ncbi.nlm.nih.gov/articles/PMC5018199/
- `prod053a-source-012` Frontiers reactance and persuasive communication review - https://www.frontiersin.org/journals/communication/articles/10.3389/fcomm.2019.00056/full
- `prod053a-source-013` Ryan and Deci self-determination theory - https://digitalwellbeing.org/wp-content/uploads/2020/03/Ryan-and-Deci-2000-Self-Determination-Theory-and-the-Facilitation-of-Intrinsic-Motivation-Social-Development-and-Well-Being.pdf
- `prod053a-source-014` Leader autonomy support meta-analysis - https://link.springer.com/article/10.1007/s11031-018-9698-y
- `prod053a-source-015` Stanford Fogg Behavior Model - https://behaviordesign.stanford.edu/resources/fogg-behavior-model
- `prod053a-source-016` COM-B behaviour change wheel - https://implementationscience.biomedcentral.com/articles/10.1186/1748-5908-6-42
- `prod053a-source-017` Oxford conversation analysis overview - https://academic.oup.com/edited-volume/61882/chapter/547683169
- `prod053a-source-018` Repair as interface between interaction and cognition - https://pmc.ncbi.nlm.nih.gov/articles/PMC6849777/
- `prod053a-source-019` Amazon Alexa design principle: Be brief - https://developer.amazon.com/en-US/alexa/alexa-haus/design-principles/be-brief
- `prod053a-source-020` Google conversation design quick reference - https://developers.google.com/assistant/downloads/design-principles-quick-reference.pdf
- `prod053a-source-021` Digital.gov clear and short plain-language guide - https://digital.gov/guides/plain-language/writing/clear-short
- `prod053a-source-022` CDC plain language checklist - https://www.cdc.gov/health-literacy/php/develop-materials/plain-language.html
- `prod053a-source-023` NIH plain language guide - https://www.nih.gov/sites/default/files/2025-02/nih-plain-language-getting-started-brushing-up.pdf
- `prod053a-source-024` Samuelson and Zeckhauser status quo bias - https://rzeckhauser.scholars.harvard.edu/publications/status-quo-bias-decision-making
- `prod053a-source-025` Iyengar and Lepper choice overload - https://pubmed.ncbi.nlm.nih.gov/11138768/
- `prod053a-source-026` Harvard Program on Negotiation BATNA explainer - https://www.pon.harvard.edu/daily/batna/translate-your-batna-to-the-current-deal/

## Boundary

- No source excerpts or copied scripts are stored.
- No runtime behavior, response text, retrieval, provider, LLM judging, private-data, voice, demo, payment, contract, or production promotion is enabled.
- PROD-053B should convert only reviewed candidates into a compact English runtime rule layer.
