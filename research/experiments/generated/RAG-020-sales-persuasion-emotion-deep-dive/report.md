# RAG-020 Sales Persuasion Emotion Deep Dive

RAG-020 adds public-source-backed, project-owned advisory rules for ethical persuasion, buyer confidence, and emotion understanding limits. It stores paraphrases only.

## Summary

- Sources reviewed: `12`
- Knowledge items accepted: `20`
- Deep-dive topic groups covered: `8`
- Runtime retrieval enabled: `False`
- Source excerpt text stored: `False`
- Copied scripts stored: `False`

## Covered Topic Groups

- `insight_led_selling`
- `behavior_change_design`
- `autonomy_supportive_persuasion`
- `buyer_decision_confidence`
- `negotiation_readiness`
- `emotional_understanding_limits`
- `deescalation_and_affect_labeling`
- `ai_risk_and_compliance`

## Sources

- `rag020-source-001` Gartner Challenger Sales Model overview - https://www.gartner.com/smarterwithgartner/power-challenger-sales-model
- `rag020-source-002` Stanford Behavior Design Lab Fogg Behavior Model - https://behaviordesign.stanford.edu/resources/fogg-behavior-model
- `rag020-source-003` Michie, van Stralen, and West Behaviour Change Wheel / COM-B - https://implementationscience.biomedcentral.com/articles/10.1186/1748-5908-6-42
- `rag020-source-004` SAMHSA TIP 35 motivational interviewing - https://library.samhsa.gov/product/tip-35-enhancing-motivation-change-substance-use-disorder-treatment/pep19-02-01-003
- `rag020-source-005` Harvard Program on Negotiation BATNA explainer - https://www.pon.harvard.edu/daily/batna/translate-your-batna-to-the-current-deal/
- `rag020-source-006` Oxford Bibliographies Elaboration Likelihood Model overview - https://academic.oup.com/reference/62347/reference-article/554213168
- `rag020-source-007` Barrett et al. Emotional Expressions Reconsidered - https://journals.sagepub.com/doi/10.1177/1529100619832930
- `rag020-source-008` Lieberman et al. affect labeling PubMed record - https://pubmed.ncbi.nlm.nih.gov/17576282/
- `rag020-source-009` NIST AI Risk Management Framework - https://doi.org/10.6028/NIST.AI.100-1
- `rag020-source-010` NIST Generative AI Profile - https://doi.org/10.6028/NIST.AI.600-1
- `rag020-source-011` EUR-Lex Regulation (EU) 2024/1689 Artificial Intelligence Act - https://eur-lex.europa.eu/eli/reg/2024/1689/oj
- `rag020-source-012` FTC AI deception guidance for chatbots, deepfakes, and voice clones - https://www.ftc.gov/business-guidance/blog/2023/03/chatbots-deepfakes-voice-clones-ai-deception-sale

## Emotion Understanding Limits

- Observable emotion cues are weak context, not proof of a hidden state.
- The agent should use tentative repair language and invite correction before persuading.
- Biometric or unvalidated emotion recognition is blocked from runtime use.

## Runtime Boundary

- Items are advisory-only public-source paraphrases.
- No source excerpts, copied scripts, private customer data, provider calls, embeddings, or vector database are used.
- RAG-020 is not imported into the RAG-017 runtime registry in this pass.
- Runtime use requires a separate registry rebuild and RAG-018 guarded-retrieval evaluation.
- Compliance, refusal, protected text, and human escalation override every persuasion rule.
