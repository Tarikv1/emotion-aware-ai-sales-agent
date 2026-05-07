# RAG-019 Sales Communication Source Expansion

RAG-019 adds public-source-backed, project-owned advisory rules for sales communication. It stores paraphrases only.

## Summary

- Sources reviewed: `25`
- Knowledge items accepted: `31`
- Requested topic groups covered: `15`
- Runtime retrieval enabled: `False`
- Source excerpt text stored: `False`
- Copied scripts stored: `False`

## Covered Topic Groups

- `cold_calling`
- `objection_handling`
- `closing_techniques`
- `consultative_selling`
- `sales_psychology`
- `emotional_intelligence_in_sales`
- `negotiation`
- `voice_and_speech_delivery`
- `conversation_design`
- `call_center_communication`
- `persuasion_frameworks`
- `storytelling_for_sales`
- `german_sales_communication`
- `real_sales_call_breakdowns`
- `ethics_and_compliance`

## Sources

- `rag019-source-001` Gong Labs cold-call openers from 300M calls - https://www.gong.io/blog/the-best-and-worst-cold-call-openers-backed-by-data-from-300m-calls
- `rag019-source-002` Huthwaite SPIN methodology - https://www.huthwaiteinternational.com/spin-methodology
- `rag019-source-003` Apollo common sales objections - https://www.apollo.io/insights/common-sales-objections
- `rag019-source-004` Apollo handling objections in sales - https://www.apollo.io/insights/handling-objections-in-sales
- `rag019-source-005` Influence at Work Cialdini Code of Ethics - https://www.influenceatwork.com/about-iaw/
- `rag019-source-006` Influence at Work principles overview - https://www.influenceatwork.com/
- `rag019-source-007` Kahneman and Tversky prospect theory record - https://www.econometricsociety.org/publications/econometrica/browse/1979/03/01/prospect-theory-analysis-decision-under-risk
- `rag019-source-008` Stanford Encyclopedia of Philosophy: The Ethics of Manipulation - https://plato.stanford.edu/entries/ethics-manipulation/
- `rag019-source-009` FBI Law Enforcement Bulletin active listening skills for crisis negotiators - https://leb.fbi.gov/articles/focus/focus-on-training-an-evaluation-tool-for-crisis-negotiators
- `rag019-source-010` World Economic Forum / Quartz tactical empathy interview with Chris Voss - https://www.weforum.org/stories/2022/01/tactical-empathy-key-workplace-negotiations-voss/
- `rag019-source-011` Harvard Program on Negotiation anchoring in negotiation - https://www.pon.harvard.edu/daily/negotiation-skills-daily/what-is-anchoring-in-negotiation/
- `rag019-source-012` Google conversation design: turn-taking - https://developers.google.com/assistant/conversation-design/learn-about-conversation
- `rag019-source-013` Microsoft Copilot Studio graceful fallbacks and handoffs - https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/cux-fallbacks
- `rag019-source-014` Amazon Nova Sonic barge-in documentation - https://docs.aws.amazon.com/nova/latest/nova2-userguide/sonic-barge-in.html
- `rag019-source-015` ICMI communication with angry customers - https://www.icmi.com/resources/2020/tips-for-contact-centers-to-communicate-with-angry-customers
- `rag019-source-016` HubSpot service recovery strategies - https://blog.hubspot.com/service/service-recovery
- `rag019-source-017` Zendesk escalation management - https://www.zendesk.com/blog/escalation-management/
- `rag019-source-018` FTC Telemarketing Sales Rule compliance guide - https://www.ftc.gov/business-guidance/resources/complying-telemarketing-sales-rule
- `rag019-source-019` FTC Keep your AI claims in check - https://www.ftc.gov/business-guidance/blog/2023/02/keep-your-ai-claims-check
- `rag019-source-020` FTC AI deception for sale - https://www.ftc.gov/business-guidance/blog/2023/03/chatbots-deepfakes-voice-clones-ai-deception-sale
- `rag019-source-021` Bundesnetzagentur unerlaubte Telefonwerbung - https://www.bundesnetzagentur.de/DE/Vportal/TK/Aerger/Faelle/UEW/start.html
- `rag019-source-022` Germany UWG Section 7 - https://www.gesetze-im-internet.de/uwg_2004/__7.html
- `rag019-source-023` Germany UWG Section 7a - https://www.gesetze-im-internet.de/uwg_2004/__7a.html
- `rag019-source-024` IHK Ulm telephone advertising guidance - https://www.ihk.de/ulm/recht-und-steuern/wettbewerbsrecht/wettbewerbsrecht/telefon-werbung-4239498
- `rag019-source-025` Stanford GSB business storytelling case - https://www.gsb.stanford.edu/faculty-research/case-studies/how-harness-stories-business

## Runtime Boundary

- Items are advisory-only public-source paraphrases.
- No source excerpts, copied scripts, private customer data, provider calls, embeddings, or vector database are used.
- Runtime retrieval remains opt-in through RAG-017/RAG-018 guardrails.
- Compliance, refusal, protected text, and human escalation override every sales rule.
