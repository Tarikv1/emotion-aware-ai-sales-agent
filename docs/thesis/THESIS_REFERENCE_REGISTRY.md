# Thesis Reference Registry

## Purpose

Track the external resources that have influenced the thesis and product work so they are not lost in chat history.

This registry is not a final bibliography. It is a working source map for later thesis writing.

## Source Categories

Use the source categories carefully:

- Academic source: suitable for related work or methodology discussion after proper citation formatting.
- Dataset source: suitable for data chapter or experiment setup after access and license checks.
- Provider documentation: suitable for implementation and system-design discussion, not as academic proof of quality.
- Product inspiration: useful for product design attribution, not necessarily thesis evidence.
- Open-source inspiration: useful for attribution and process notes, not a runtime dependency unless separately reviewed.
- Unverified source: mentioned in project history but exact URL, license, or access conditions need follow-up.

## RAG And NotebookLM Workflow Sources

### NotebookLM supported source types

- Type: provider documentation and research workflow source
- Source: https://support.google.com/notebooklm/answer/16215270?hl=en
- Project use: informs RAG-001/RAG-002 source-intake assumptions for websites, YouTube videos, PDFs, text, Markdown, Google Docs/Slides, and audio sources.
- Current project status: used for workflow design only. RAG-001/RAG-002 do not call NotebookLM and do not store raw source text.
- Thesis caution: provider documentation describes tool capability, not scientific evidence for sales-agent performance.

### NotebookLM reports, data tables, and exports

- Type: provider documentation and research workflow source
- Source: https://support.google.com/notebooklm/answer/16206563?hl=en
- Project use: informs the RAG-002 decision to use generated reports/data-table style outputs and exported/copied JSON as the handoff from NotebookLM to the local validator.
- Current project status: used for workflow design only. RAG-002 still requires manual NotebookLM UI use and local validation before any extracted notes are promoted.
- Thesis caution: exported NotebookLM artifacts should be treated as intermediate extraction notes; the thesis should cite original sources, not NotebookLM.

### NotebookLM Enterprise API

- Type: provider documentation and possible future automation source
- Source: https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks-sources
- Project use: records that programmatic NotebookLM notebook/source workflows exist in NotebookLM Enterprise, while RAG-001 remains local and manual by default.
- Current project status: no NotebookLM API call is implemented or required.
- Thesis caution: future automation would need separate provider, privacy, retention, and cost review.

## Primary Public Dataset Sources

### IEMOCAP

- Type: dataset source
- Main source: https://sail.usc.edu/iemocap/iemocap_info.htm
- USC SAIL database page: https://sail.usc.edu/software/databases/
- Project use: speech emotion reference and possible audio-emotion baseline.
- Current project status: local file appears to be a repackaged CSV-style export, not the full official corpus structure.
- Thesis caution: do not make official-IEMOCAP claims from the local export until provenance and access conditions are verified.

### MELD

- Type: dataset source
- Project page: https://affective-meld.github.io/
- GitHub: https://github.com/declare-lab/MELD
- Paper: https://huggingface.co/papers/1810.02508
- Project use: conversation-level emotion labels, sentiment labels, and multimodal emotion-in-conversation grounding.
- Current project status: downloaded and extracted locally.
- Thesis caution: MELD is based on TV dialogue, so it is useful for emotion/context grounding but not a real sales-call corpus.

### Persuasion for Good

- Type: dataset and academic source
- ACL Anthology paper: https://aclanthology.org/P19-1566/
- ConvoKit corpus page: https://convokit.cornell.edu/documentation/persuasionforgood.html
- GitHub dataset/code reference: https://github.com/ohyj1002/persuasionforgood
- Project use: persuasion strategy taxonomy, persuasive-dialogue analysis, and success/failure reasoning.
- Current project status: downloaded and extracted locally.
- Thesis caution: the task is charity persuasion, not commercial outbound sales. Use it for strategy grounding, not direct product-performance claims.

### CallCenterEN / AIxBlock real-world call-center scripts

- Type: dataset and academic source
- Hugging Face dataset: https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english
- Dataset file tree: https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english/tree/main
- arXiv paper: https://arxiv.org/abs/2507.02958
- Project use: pattern grounding only for `PROD-006` full-sale scenario-bank design, `PROD-012` CallCenterEN scenario evaluation, `PROD-013` abstract pattern extraction, `PROD-014` scenario-bank generation, `PROD-015` old-runtime versus opt-in retrieval comparison, `PROD-016` retrieval no-gain diagnosis, `PROD-017` specificity/objection-fit scoring, `PROD-018` offline composer-hook candidate testing, `PROD-019` opt-in guarded runtime composer-hook evaluation, `PROD-020` naturalized customer-turn evaluation, `PROD-041A` conditional scenario diversity expansion, `PROD-042` turn-level sales pattern playbook extraction, `PROD-043` offline playbook adapter evaluation, `PROD-044` offline core sales-policy review/design, `PROD-045` deterministic regression-gated core sales-policy updates, `PROD-046A` German intent-equivalent regression, and `PROD-046B` German customer-facing wording-quality checks, including opening styles, call direction, domain mix, customer intents, objection types, emotion transitions, discovery questions, persuasion tactics, close attempts, support-only patterns, escalation patterns, close resistance, hard failure rate, leakage failure rate, non-sale correctness tests, safe-close correctness tests, retrieval no-gain evidence, composer influence gap analysis, scoring blind-spot analysis, scenario/campaign evaluation-shape diagnosis, safe-specific versus safe-generic answer scoring, guarded composer-hook candidate evaluation, rubric-token robustness checks, deterministic strategy detection, deterministic emotion handling, failure taxonomy coverage, customer-move/tactic/reaction/state-transition extraction, next-best-action patterning, deterministic playbook evaluation rules, offline customer-move classification, playbook retrieval, single-turn agent-response evaluation, evidence-backed candidate runtime-policy design, evaluator-hardening regression evidence for targeted runtime-policy changes, multilingual intent-routing checks, and German wording-risk checks before human review.
- Current project status: no dataset download is required by default. The implementation uses project-owned synthetic scenarios and can scan ignored local ZIP/JSON/JSONL files transiently for leakage checks or abstract pattern extraction after explicit download approval.
- License and reuse status: observed as `cc-by-nc-4.0` on 2026-05-09. The dataset card and paper frame it as non-commercial research material. Do not use it as commercial runtime training data without separate license clearance.
- Thesis caution: do not copy transcript sentences, high-similarity paraphrases, or raw transcript bodies into tracked scenarios, prompts, generated reports, runtime memory, or commercial runtime prompts. Scenarios must be project-owned rewrites combined from multiple source patterns.

## Public Product Source Bundles

### Public OpenAI ChatGPT plan-fit fixture

- Type: official public product source bundle
- Source bundle: `research/sources/public_openai_chatgpt_plans/source_manifest.json`
- Source notes: `research/sources/public_openai_chatgpt_plans/source_notes.md`
- Retrieved at: `2026-05-24T18:18:00Z`
- Checkpoints:
  - `research/experiments/generated/PUBLIC-OPENAI-SOURCE-BUNDLE-001/`
  - `research/experiments/generated/PUBLIC-OPENAI-CAMPAIGN-FIXTURE-001/`
  - `research/experiments/generated/PUBLIC-OPENAI-CAMPAIGN-DIALOGUE-001/`
  - `research/experiments/generated/PUBLIC-OPENAI-UNIVERSAL-ISOLATION-001/`
  - `research/experiments/generated/PUBLIC-OPENAI-CROSS-CAMPAIGN-CONTAMINATION-001/`
  - `research/experiments/generated/PUBLIC-OPENAI-CLOSE-SEMANTICS-001/`
- Official sources:
  - ChatGPT plans page: https://chatgpt.com/pricing/
  - ChatGPT FAQ: https://help.openai.com/en/articles/12677804-what-is-chatgpt-faq
  - ChatGPT capabilities overview: https://help.openai.com/en/articles/9260256-chatgpt-capabilities-overview
  - ChatGPT Go help article: https://help.openai.com/en/articles/11989085-what-is-chatgpt-go
  - ChatGPT Plus help article: https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus
  - ChatGPT Pro help article: https://help.openai.com/en/articles/9793128-what-is-chatgpt-pro
  - ChatGPT Business help article: https://help.openai.com/en/articles/8792828-what-is-chatgpt-business
  - ChatGPT Enterprise help article: https://help.openai.com/en/articles/8265053-what-is-chatgpt-enterprise
  - ChatGPT data controls help article: https://help.openai.com/en/articles/7730893-data-controls-in-chatgpt
  - OpenAI enterprise privacy page: https://openai.com/enterprise-privacy/
- Project use: source-grounded real-product campaign fixture for testing plan-fit dialogue, plan comparison, self-serve close, contact-sales close, API-separate boundaries, privacy/training boundaries, unsupported-claim refusal, and cross-campaign isolation.
- Current project status: the campaign fixture records 33 source-grounded claims from 10 official sources, covers Free, Go, Plus, Pro, Business Codex, Business ChatGPT & Codex, and Enterprise, and keeps OpenAI facts isolated from universal dialogue runtime files.
- Reuse status: paraphrased source-grounded claims only. Short quote excerpts are stored only where useful for traceability in the source manifest. This is an internal public-data simulation and is not an official OpenAI sales agent.
- Thesis caution: use this bundle as product-grounding and claim-governance evidence, not as proof of sales effectiveness or OpenAI authorization. Re-check official source pages before final thesis submission because plans, prices, features, and privacy terms can change.

## Sales Communication And Compliance Sources

### PROD-028 synthetic CRM product grounding sources

- Type: product inspiration and public SaaS/CRM packaging source pack
- Sources:
  - HubSpot Sales Hub public product/pricing page: https://www.hubspot.com/products/sales
  - Pipedrive public CRM pricing page: https://www.pipedrive.com/en/pricing
  - Salesforce Sales Cloud public pricing page: https://www.salesforce.com/sales/pricing/
  - Zendesk public pricing page: https://www.zendesk.com/pricing/
- Project use: inspiration only for `PROD-028` synthetic campaign knowledge grounding, including realistic SaaS/CRM patterns such as per-seat tiers, annual billing, trials, onboarding and migration fees, integrations, support/security tiers, cancellation boundaries, specialist quote handling, and add-on/package thinking.
- Current project status: encoded into `research/experiments/generated/PROD-028-synthetic-campaign-knowledge-grounding/synthetic_campaign.json` as fictional project-owned campaign facts for `Northstar Workflow Labs` and `RouteSignal CRM`.
- Reuse status: no copied real-company wording, plan names, brand identity, customer claims, or sales copy. Reuse label is `inspiration only`.

### LIVE-DEMO-001 lead-routing campaign inspiration sources

- Type: product inspiration and public lead-routing workflow source pack
- Sources:
  - Chili Piper lead routing software public page: https://info.chilipiper.com/lead-routing-software
  - Calendly Routing public page: https://calendly.com/features/routing
  - HubSpot lead scoring public page: https://www.hubspot.com/products/lead-scoring
  - LeanData Speed to Lead public page: https://www.leandata.com/platform/speed-to-lead/
- Project use: inspiration only for the `LIVE-DEMO-001` fictional `Northstar Workflow Labs` / `RouteSignal CRM` campaign profile, including realistic lead capture, qualification, account-owner routing, scheduling, duplicate-check, reminder, handoff-review, reporting, and security/integration-boundary patterns.
- Current project status: encoded into `research/experiments/cases/live-demo-001-fictional-b2b-sales-campaign.json` and used only by the supervised local live-demo wrapper.
- Reuse status: no copied real-company wording, plan names, brand identity, customer claims, or sales copy. Reuse label is `inspiration only`.
- Thesis caution: these are product-grounding references, not evidence that the sales agent improves real-world sales outcomes. Public pages can change, so later thesis writing should re-check dates and avoid citing synthetic prices as real market facts.

### RAG-019 public sales communication source expansion

- Type: public practitioner, academic, provider documentation, legal/compliance, and product-grounding source pack
- Cold calling and objection handling sources:
  - Gong cold-call opener analysis: https://www.gong.io/blog/the-best-and-worst-cold-call-openers-backed-by-data-from-300m-calls
  - Apollo common sales objections: https://www.apollo.io/insights/common-sales-objections
  - Apollo handling objections in sales: https://www.apollo.io/insights/handling-objections-in-sales
- Consultative selling and sales-methodology sources:
  - Huthwaite SPIN methodology: https://www.huthwaiteinternational.com/spin-methodology
  - Stanford GSB business storytelling case collection: https://www.gsb.stanford.edu/faculty-research/case-studies/how-harness-stories-business
- Persuasion and decision-science sources:
  - Influence at Work Cialdini overview: https://www.influenceatwork.com/about-iaw/
  - Influence at Work main site: https://www.influenceatwork.com/
  - Kahneman and Tversky prospect theory record: https://www.econometricsociety.org/publications/econometrica/browse/1979/03/01/prospect-theory-analysis-decision-under-risk
  - Stanford Encyclopedia of Philosophy manipulation entry: https://plato.stanford.edu/entries/ethics-manipulation/
- Negotiation and tactical empathy sources:
  - FBI crisis negotiation evaluation tool: https://leb.fbi.gov/articles/focus/focus-on-training-an-evaluation-tool-for-crisis-negotiators
  - World Economic Forum / Chris Voss tactical empathy interview: https://www.weforum.org/stories/2022/01/tactical-empathy-key-workplace-negotiations-voss/
  - Harvard Program on Negotiation anchoring explainer: https://www.pon.harvard.edu/daily/negotiation-skills-daily/what-is-anchoring-in-negotiation/
- Conversation design, call-center, and service recovery sources:
  - Google Assistant conversation design basics: https://developers.google.com/assistant/conversation-design/learn-about-conversation
  - Microsoft Copilot Studio fallback guidance: https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/cux-fallbacks
  - Amazon Nova Sonic barge-in documentation: https://docs.aws.amazon.com/nova/latest/nova2-userguide/sonic-barge-in.html
  - ICMI angry-customer communication guidance: https://www.icmi.com/resources/2020/tips-for-contact-centers-to-communicate-with-angry-customers
  - HubSpot service recovery overview: https://blog.hubspot.com/service/service-recovery
  - Zendesk escalation management overview: https://www.zendesk.com/blog/escalation-management/
- AI, telemarketing, and German compliance sources:
  - FTC Telemarketing Sales Rule business guidance: https://www.ftc.gov/business-guidance/resources/complying-telemarketing-sales-rule
  - FTC AI claims guidance: https://www.ftc.gov/business-guidance/blog/2023/02/keep-your-ai-claims-check
  - FTC AI deception guidance: https://www.ftc.gov/business-guidance/blog/2023/03/chatbots-deepfakes-voice-clones-ai-deception-sale
  - Bundesnetzagentur unerlaubte Telefonwerbung portal: https://www.bundesnetzagentur.de/DE/Vportal/TK/Aerger/Faelle/UEW/start.html
  - German UWG Section 7: https://www.gesetze-im-internet.de/uwg_2004/__7.html
  - German UWG Section 7a: https://www.gesetze-im-internet.de/uwg_2004/__7a.html
  - IHK Ulm telephone advertising overview: https://www.ihk.de/ulm/recht-und-steuern/wettbewerbsrecht/wettbewerbsrecht/telefon-werbung-4239498
- GER-001 / PROD-046D German customer-facing wording sources:
  - Verbraucherzentrale ungewollte Werbeanrufe: https://www.verbraucherzentrale.de/wissen/vertraege-reklamation/werbung/ungewollte-werbeanrufe-hilfe-gegen-telefonwerbung-13857
  - Verbraucherzentrale phone-scam caution about not being pressured into saying yes: https://www.verbraucherzentrale.de/wissen/digitale-welt/mobilfunk-und-festnetz/abzocke-am-telefon-moeglichst-nicht-ja-sagen-13496
  - Verbraucherzentrale unexpected-call scam warning: https://www.verbraucherzentrale.de/wissen/vertraege-reklamation/abzocke/unerwarteter-anruf-von-der-verbraucherzentrale-vorsicht-falle-11112
  - Polizeiliche Kriminalprävention fake customer-service/support scams: https://www.polizei-beratung.de/themen-und-tipps/sicher-handeln/onlinebetrug-maschen/fake-kundenservice-support-scams/
  - Polizeiliche Kriminalprävention false-police fraud background safety tone: https://www.polizei-beratung.de/themen-und-tipps/betrug/betrug-durch-falsche-polizisten/
  - Service Standard understandable writing with simple language: https://servicestandard.gov.de/handbuch/anleitungen/verstaendlich-schreiben-mit-einfacher-sprache/
  - AFZ Bremen verständliche Sprache: https://www.afz.bremen.de/verwaltung-nbspentwickeln/buerger-innenservice-und-kommunikation/kommunikation/verstaendliche-sprache-25926
  - Berlin standards for understandable language: https://www.berlin.de/lb/digitale-barrierefreiheit/anforderungen/berliner-standards/fuer-verstaendliche-sprache-1463990.php
  - Verbraucherzentrale unwanted energy contracts by phone, background pattern for written confirmation and phone-contract anxiety: https://www.verbraucherzentrale.de/wissen/energie/achtung-unerwuenschte-energievertraege-am-telefon-58483
  - Verbraucherzentrale plain-language help for advertising calls: https://www.verbraucherzentrale.de/vertraege-reklamation/hilfe-bei-werbeanrufen-100996
- Project use: source-backed paraphrased advisory rules for RAG-019 covering cold calling, objections, closing, consultative discovery, persuasion, negotiation, voice delivery, conversation design, call-center behavior, German formal sales communication, real-call review boundaries, and compliance.
- PROD-046D use: source-informed wording guidance for German customer-facing runtime responses only. The checkpoint does not claim legal compliance, does not copy source text, and rejects sales scripts as wording sources.
- Current project status: extracted into `research/experiments/cases/rag-019-sales-communication-source-expansion.json` as project-owned paraphrases with source URLs, hard limits, and no runtime eligibility by default.
- Thesis caution: practitioner sales pages are product-grounding inputs, not peer-reviewed effectiveness evidence. Legal/compliance pages guide system boundaries and are not legal advice. No copied sales scripts, article passages, or call transcripts are stored in the RAG.

### RAG-020 sales persuasion and emotion-understanding deep dive

- Type: public practitioner, academic, government, AI governance, legal/compliance, and product-grounding source pack
- Sales, persuasion, and negotiation sources:
  - Gartner Challenger Sales Model overview: https://www.gartner.com/smarterwithgartner/power-challenger-sales-model
  - Stanford Behavior Design Lab Fogg Behavior Model: https://behaviordesign.stanford.edu/resources/fogg-behavior-model
  - Michie, van Stralen, and West Behaviour Change Wheel / COM-B: https://implementationscience.biomedcentral.com/articles/10.1186/1748-5908-6-42
  - SAMHSA TIP 35 motivational interviewing: https://library.samhsa.gov/product/tip-35-enhancing-motivation-change-substance-use-disorder-treatment/pep19-02-01-003
  - Harvard Program on Negotiation BATNA explainer: https://www.pon.harvard.edu/daily/batna/translate-your-batna-to-the-current-deal/
  - Oxford Bibliographies Elaboration Likelihood Model overview: https://academic.oup.com/reference/62347/reference-article/554213168
- Emotion understanding and AI-risk sources:
  - Barrett et al. Emotional Expressions Reconsidered: https://journals.sagepub.com/doi/10.1177/1529100619832930
  - Lieberman et al. affect labeling PubMed record: https://pubmed.ncbi.nlm.nih.gov/17576282/
  - NIST AI Risk Management Framework: https://doi.org/10.6028/NIST.AI.100-1
  - NIST Generative AI Profile: https://doi.org/10.6028/NIST.AI.600-1
  - EUR-Lex Regulation (EU) 2024/1689 Artificial Intelligence Act: https://eur-lex.europa.eu/eli/reg/2024/1689/oj
  - FTC AI deception guidance for chatbots, deepfakes, and voice clones: https://www.ftc.gov/business-guidance/blog/2023/03/chatbots-deepfakes-voice-clones-ai-deception-sale
- Project use: source-backed paraphrased advisory rules for RAG-020 covering insight-led selling, behavior-change diagnosis, autonomy-supportive persuasion, buyer confidence, BATNA-style comparison, emotion-inference limits, affect-labeling repair, and AI/voice deception boundaries.
- Current project status: extracted into `research/experiments/cases/rag-020-sales-persuasion-emotion-deep-dive.json` as project-owned paraphrases with source URLs, hard limits, and no runtime eligibility by default.
- Thesis caution: RAG-020 is a source expansion and design-control checkpoint, not runtime evidence. It must not be treated as proof that sales outcomes improve until a separate registry rebuild, RAG-018 evaluation, and human review are completed.

### RAG-021 buyer trust and conversation-repair source expansion

- Type: public practitioner, academic, government, AI governance, and product-grounding source pack
- Buyer value, trust, autonomy, and clarity sources:
  - Bain B2B Elements of Value: https://www.bain.com/how-we-help/b2b-elements-of-value/
  - Mayer, Davis, and Schoorman organizational trust model: https://www.jstor.org/stable/258792
  - Leader autonomy support in the workplace meta-analysis: https://pubmed.ncbi.nlm.nih.gov/30237648/
  - Reactance and restoration of freedom in communication: https://academic.oup.com/hcr/article/33/2/219/4210793
  - Cognitive Load Theory review: https://link.springer.com/article/10.1007/s11251-009-9110-0
  - Digital.gov Plain Language guide: https://digital.gov/guides/plain-language
- Conversation repair, emotion support, action planning, and AI transparency sources:
  - Gross emerging field of emotion regulation: https://journals.sagepub.com/doi/10.1037/1089-2680.2.3.271
  - Schegloff, Jefferson, and Sacks conversation-repair archive page: https://www.conversationanalysis.org/schegloff-media-archive/preference-for-self-correction-in-repair-in-conversation-1977/
  - Implementation intentions and goal achievement meta-analysis: https://pubmed.ncbi.nlm.nih.gov/18096108/
  - OECD AI Principles: https://www.oecd.org/en/topics/ai-principles.html
- Project use: source-backed paraphrased advisory rules for RAG-021 covering buyer value mapping, trust repair, autonomy/reactance, cognitive-load reduction, plain-language summaries, conversation repair, emotion-regulation support, consented next-step planning, and AI transparency/human handoff.
- Current project status: extracted into `research/experiments/cases/rag-021-buyer-trust-conversation-repair.json` as project-owned paraphrases with source URLs, hard limits, and no runtime eligibility by default.
- Thesis caution: RAG-021 is a source expansion and design-control checkpoint, not runtime evidence. It must not be treated as proof that sales outcomes improve until a separate registry rebuild, RAG-018 evaluation, and human review are completed.

### PROD-053A English sales psychology deep dive

- Type: public academic, practitioner, government, and voice UX source pack
- Adaptive selling, sales listening, buyer confidence, and buyer value sources:
  - Franke and Park adaptive selling/customer orientation meta-analysis: https://journals.sagepub.com/doi/10.1509/jmkr.43.4.693
  - Adaptive selling integrative framework: https://link.springer.com/article/10.1007/s11747-025-01096-3
  - Salesperson listening meta-analysis: https://www.sciencedirect.com/science/article/abs/pii/S0148296319303017
  - Perceived listening work-outcomes meta-analysis: https://link.springer.com/article/10.1007/s10869-023-09897-5
  - Gartner modern B2B buyers and information overload: https://www.gartner.com/smarterwithgartner/what-sales-should-know-about-modern-b2b-buyers
  - HBR customer indecision and no-decision sales losses: https://hbr.org/2022/06/stop-losing-sales-to-customer-indecision
  - Bain B2B Elements of Value article: https://www.bain.com/insights/the-b2b-elements-of-value-hbr
- Communication psychology, autonomy, conversation repair, and decision psychology sources:
  - NCBI Bookshelf motivational interviewing chapter: https://www.ncbi.nlm.nih.gov/books/NBK571068/
  - Empathy in motivational interviewing and language synchrony: https://pmc.ncbi.nlm.nih.gov/articles/PMC5018199/
  - Frontiers reactance and persuasive communication review: https://www.frontiersin.org/journals/communication/articles/10.3389/fcomm.2019.00056/full
  - Ryan and Deci self-determination theory PDF mirror used for access: https://digitalwellbeing.org/wp-content/uploads/2020/03/Ryan-and-Deci-2000-Self-Determination-Theory-and-the-Facilitation-of-Intrinsic-Motivation-Social-Development-and-Well-Being.pdf
  - Leader autonomy support meta-analysis: https://link.springer.com/article/10.1007/s11031-018-9698-y
  - Oxford conversation analysis overview: https://academic.oup.com/edited-volume/61882/chapter/547683169
  - Repair as interface between interaction and cognition: https://pmc.ncbi.nlm.nih.gov/articles/PMC6849777/
  - Samuelson and Zeckhauser status quo bias: https://rzeckhauser.scholars.harvard.edu/publications/status-quo-bias-decision-making
  - Iyengar and Lepper choice overload PubMed record: https://pubmed.ncbi.nlm.nih.gov/11138768/
- Spoken interaction and plain-language sources:
  - Amazon Alexa design principle, be brief: https://developer.amazon.com/en-US/alexa/alexa-haus/design-principles/be-brief
  - Google conversation design quick reference: https://developers.google.com/assistant/downloads/design-principles-quick-reference.pdf
  - Digital.gov clear and short plain-language guide: https://digital.gov/guides/plain-language/writing/clear-short
  - CDC plain language checklist: https://www.cdc.gov/health-literacy/php/develop-materials/plain-language.html
  - NIH plain language guide: https://www.nih.gov/sites/default/files/2025-02/nih-plain-language-getting-started-brushing-up.pdf
- Project use: source-backed paraphrased research packet for PROD-053A, covering adaptive selling, salesperson listening, buyer confidence, no-decision risk, autonomy/reactance, behavior friction, trust repair, conversation repair, spoken brevity, decision psychology, and ethical insight-led selling.
- Current project status: extracted into `research/experiments/generated/PROD-053A-english-sales-psychology-deep-dive/` as project-owned paraphrased findings, compact English rule candidates, and rejected/deferred tactics. `PROD-053B` then compresses those candidates into reviewed English-only deterministic response-shape rules under `research/experiments/generated/PROD-053B-compact-english-psychology-layer-review/`. `PROD-053C` applies those rules as review criteria to the reachable English deterministic runtime response surface under `research/experiments/generated/PROD-053C-english-spoken-response-expansion-review/`, excluding already-approved carry-forward items and keeping runtime text unchanged. `PROD-053D` imports Tarik's English review decisions under `research/experiments/generated/PROD-053D-english-review-import/`, separating approved-as-written items from rework and behavior-design notes. No source excerpts, copied scripts, private customer data, provider outputs, LLM judging, or runtime import are used.
- Thesis caution: PROD-053A, PROD-053B, PROD-053C, and PROD-053D are research, design-control, and human-review evidence only. They are not proof that the agent improves sales outcomes, and exact runtime text is not changed until a later patch checkpoint applies reviewed wording and passes regression.

## Speech Realism Sources

Detailed notes live in `docs/thesis/SPEECH_REALISM_REFERENCES.md`.

### Vinh Giang / AskVinh communication corpus

- Type: practitioner/video source pack and RAG extraction source
- YouTube channel: https://www.youtube.com/@askvinh/videos
- Official site: https://www.vinhgiang.com/
- Free resources page: https://www.vinhgiang.com/resources/
- Channel metadata cross-check: https://vidiq.com/youtube-stats/channel/UC9K9Wnz6t4cLnCdTzAVrXqQ/
- Project use: imported through NotebookLM as a communication, vocal delivery, pacing, pausing, resonance, concise-response, rapport, and storytelling source pack for RAG voice/response review.
- Current project status: the NotebookLM report is stored under `research/experiments/generated/RAG-002-notebooklm-extraction-automation-bridge/imports/` and is included in refreshed RAG-003 through RAG-006 outputs.
- Thesis caution: use as practitioner training material, not academic evidence. No transcript text or video wording should be copied into runtime or thesis prose without separate quote clearance.

Per-video metadata reviewed on 2026-05-07:

- "10 Communication Skills That Will Make You Rich!" - YouTube: https://www.youtube.com/watch?v=uZRMykRmJRg - published 2025-11-14.
- "10 Speaking Techniques That Made Me A Top 1% Speaker" - YouTube: https://www.youtube.com/watch?v=TbB7hSBVKDM - published 2025-10-24.
- "13 Years of Communication Skills Knowledge in 53 minutes" - YouTube: https://www.youtube.com/watch?v=g0kzHjmvuYQ - published 2024-11-13.
- "2 Steps To Have Better Conversations" - YouTube: https://www.youtube.com/watch?v=fzW_vPrluU0 - published 2024-01-05.
- "3 Powerful Ways To Tell Stories Without Boring People" - YouTube: https://www.youtube.com/watch?v=xJBLuSHpPL0 - published 2024-05-15.
- "30 Day Plan to Master Your Communication [Complete Beginner's Guide] + FREE Workbook PDF" - YouTube: https://www.youtube.com/watch?v=U40qvUiefQo - published 2025-05-28.
- "33 Minutes Of Communication Skills Advice I Wish I Knew In My 20s" - YouTube: https://www.youtube.com/watch?v=DOdcGwUQvJM - published 2024-09-20.
- "43 minutes straight of SOLID communication skills advice" - YouTube: https://www.youtube.com/watch?v=6-shbSFc48E - published 2024-08-07.
- "5 Communication Secrets That Give You An Unfair Advantage Over Anyone Else" - YouTube: https://www.youtube.com/watch?v=PY-QiUZBFlw - published 2025-06-26.
- "5 communication hacks that will dramatically improve your confidence!" - YouTube: https://www.youtube.com/watch?v=8_-ZaOKBB9Y - published 2025-05-14.
- "7 Communication Cheat Codes To Speak Like A Pro!" - YouTube: https://www.youtube.com/watch?v=CBbapaz9v2E - published 2025-12-05.
- "7 POWERFUL Storytelling Secrets to Level Up Your Communication Skills" - YouTube: https://www.youtube.com/watch?v=YzbzIzgvRLY - published 2024-10-31.
- "9 Habits for Clearer Speaking (I Wish I Knew Sooner)" - metadata cross-check pending exact watch URL; channel cross-check lists this title as published through the Vinh Giang channel.
- "Communication Is Hard Until You Structure Your Thinking First!" - YouTube: https://www.youtube.com/watch?v=WVxCGgmmOmY - published 2026-02-20.
- "EASY 3-Step Exercise To INSTANTLY Improve Your Articulation!" - YouTube: https://www.youtube.com/watch?v=S5f0FKhPax0 - published 2024-08-12.
- "Give me 14 minutes and I'll help you think & speak faster" - YouTube: https://www.youtube.com/watch?v=DN5OnGxSWuY - published 2025-02-05.
- "How To Build Rapport FAST And Skip The Boring Small Talk" - YouTube: https://www.youtube.com/watch?v=B3plIDYxCbo - published 2025-03-26.
- "How To Change Your Communication Style Without Judgement From Others!" - metadata cross-check pending exact watch URL.
- "How To Make A Strong First Impression (That Lasts)" - YouTube: https://www.youtube.com/watch?v=YPnbERnTCkI - published 2026-04-03.
- "How To Move From Small Talk To Deep Conversation (#AskVinh Q&A Ep. 5)" - YouTube: https://www.youtube.com/watch?v=Nv6p-l60gxI - published 2024-03-20.
- "How to AVOID awkward small talk" - YouTube: https://www.youtube.com/watch?v=B7rQmzXj6tc - published 2024-02-05.
- "How to Answer Unexpected Questions Calmly & Confidently (In ANY Situation!)" - YouTube: https://www.youtube.com/watch?v=_NY-Mw97UsU - published 2024-05-29.
- "How to Build INSTANT Rapport With Strangers!" - YouTube: https://www.youtube.com/watch?v=V6hHNh97FIs - published 2025-07-30.
- "How to Communicate Effectively During Arguments (Without Making it Worse!)" - YouTube: https://www.youtube.com/watch?v=jMG6Q0MGdMc - published 2024-12-12.
- "How to Force Yourself To Speak Coherently" - YouTube: https://www.youtube.com/watch?v=aUBPWT-D5_U - published 2025-08-07.
- "How to Talk to ANYONE (Once You Know Their Color!)" - YouTube: https://www.youtube.com/watch?v=ikbcrpowlIs - published 2025-09-12.
- "How to Trick Your Brain Into Speaking Better INSTANTLY!" - YouTube: https://www.youtube.com/watch?v=VrUBS3xX0s4 - published 2025-10-10.
- "How to Turn That Difficult Conversation You Need to Have on EASY Mode" - metadata cross-check pending exact watch URL; podcast metadata lists a corresponding Public Speaking Foundations item dated 2025-07-10.
- "Listen to this if you want to level up your communication skills in 2026..." - YouTube: https://www.youtube.com/watch?v=LI57EB_T38c - published 2025-02-20.
- "Never Tell Stories Like This..." - metadata cross-check pending exact watch URL; current channel mirrors list this title but no verified watch URL was resolved during this pass.
- "Speak 10X Clearer: Do These 3 Vocal Exercises Every Day" - YouTube: https://www.youtube.com/watch?v=BEuwA7Cbbuc - published 2025-03-05.
- "Speak Better Than 99% of People (Everything You Need To Know)" - metadata cross-check pending exact watch URL; title may differ from the current public YouTube title.
- "Speaking Is Hard Until You Understand This!" - YouTube: https://www.youtube.com/watch?v=QNsvsnkUOL0 - published 2026-02-13.
- "The 3-2-1 Speaking Trick That Forces You To Stop Rambling!" - YouTube: https://www.youtube.com/watch?v=5m-C5mwpmxU - published 2025-04-24.
- "The Laziest Way To Be A Top 1% Communicator" - YouTube: https://www.youtube.com/watch?v=IMslBEcYXhk - published 2025-11-21.
- "The ONLY 3 Ingredients You Need To Be A Better Storyteller!" - YouTube: https://www.youtube.com/watch?v=5HfeNDleTS4 - published 2025-10-03.
- "The Only 8 Minutes You Need To Become A Better Communicator" - metadata cross-check pending exact watch URL; channel metadata lists this title as published 2026-04-10.
- "The Only Video You Need To Fix Your Communication Skills" - metadata cross-check pending exact watch URL; podcast/search metadata lists a corresponding item dated 2026-02-06.
- "Watch This If You Hate Small Talk" - metadata cross-check pending exact watch URL.
- "Why Nobody Listens To You (and how to fix it)" - YouTube: https://www.youtube.com/watch?v=QBXLNEMv5so - published 2025-08-14.

Core references:

- Cutler, Dahan, and van Donselaar (1997), prosody in spoken-language comprehension: https://doi.org/10.1177/002383099704000203
- Cutler, Dahan, and van Donselaar (1997), PubMed record: https://pubmed.ncbi.nlm.nih.gov/9509577/
- Wagner and Watson (2010), prosodic phrasing and prominence review: https://doi.org/10.1080/01690961003589492
- Wagner and Watson (2010), PubMed record: https://pubmed.ncbi.nlm.nih.gov/22096264/
- Banse and Scherer (1996), acoustic profiles of vocal emotion: https://doi.org/10.1037/0022-3514.70.3.614
- Banse and Scherer (1996), PubMed record: https://pubmed.ncbi.nlm.nih.gov/8851745/
- Juslin and Laukka (2003), vocal emotion communication review: https://doi.org/10.1037/0033-2909.129.5.770
- McAleer, Todorov, and Belin (2014), vocal first impressions: https://doi.org/10.1371/journal.pone.0090779
- McAleer, Todorov, and Belin (2014), PLOS page: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0090779
- Clark and Fox Tree (2002), English `uh` and `um`: https://doi.org/10.1016/S0010-0277(02)00017-3
- Kirjavainen, Crible, and Beeching (2022), filled pauses as linguistic items: https://doi.org/10.1177/00238309211011201
- Bortfeld et al. (2001), conversation disfluency rates by role/topic/relationship: https://doi.org/10.1177/00238309010440020101
- Levelt (1983), monitoring and self-repair in speech: https://doi.org/10.1016/0010-0277(83)90026-4
- Laserna, Seih, and Pennebaker (2014), filler-word categories and variation: https://doi.org/10.1177/0261927X14526993
- Bolden (2009), English discourse marker `so`: https://doi.org/10.1016/j.pragma.2008.10.004
- Heritage (1998), English `oh`-prefaced responses: https://doi.org/10.1017/S0047404598003017
- Swerts (1998), filled pauses and discourse boundaries: https://doi.org/10.1016/S0378-2166(98)00014-9
- Gosy (2023), filled pause positions and neighboring pauses/words: https://doi.org/10.3390/languages8010079
- Brennan and Williams (1995), prosody/fillers as perceived knowledge cues: https://doi.org/10.1006/jmla.1995.1017
- Kirkland et al. (2022), filler location, speech rate, f0, and confidence: https://doi.org/10.21437/Interspeech.2022-10973
- Dall et al. (2014), filled-pause insertion for speech synthesis: https://www.research.ed.ac.uk/en/publications/investigating-automatic-amp-human-filled-pause-insertion-for-spee/
- Elmers, O'Mahony, and Szekely (2023), pause-internal phonetic particles in speech synthesis: https://doi.org/10.21437/Interspeech.2023-2178
- Heritage (2015), English turn-initial `well`: https://doi.org/10.1016/j.pragma.2015.08.008
- Sacks, Schegloff, and Jefferson (1974), turn-taking organization: https://doi.org/10.2307/412243
- Sacks, Schegloff, and Jefferson (1974), MPI record: https://www.mpi.nl/publications/item2376846/simplest-systematics-organization-turn-taking-conversation
- Stivers et al. (2009), turn-taking timing across languages: https://doi.org/10.1073/pnas.0903616106
- Levinson and Torreira (2015), timing in turn-taking and processing: https://doi.org/10.3389/fpsyg.2015.00731
- Ward and Tsukahara (2000), prosodic cues for backchannels: https://doi.org/10.1016/S0378-2166(99)00109-5
- Heldner and Edlund (2010), pauses/gaps/overlaps in conversation: https://doi.org/10.1016/j.wocn.2010.08.002
- Heldner and Edlund (2010), article page: https://www.sciencedirect.com/science/article/pii/S0095447010000628
- Skantze (2021), turn-taking in conversational systems review: https://doi.org/10.1016/j.csl.2020.101178
- Skantze (2021), article page: https://www.sciencedirect.com/science/article/pii/S088523082030111X
- Witt (2015), user response timings in spoken dialog systems: https://doi.org/10.1007/s10772-014-9265-1
- Pardo (2006), phonetic convergence in conversation: https://doi.org/10.1121/1.2178720
- Pardo (2006), university record: https://digitalcommons.montclair.edu/psychology-facpubs/347/
- Weise et al. (2019), acoustic-prosodic entrainment: https://doi.org/10.1016/j.specom.2019.10.007
- Weise et al. (2019), university record: https://cris.biu.ac.il/en/publications/individual-differences-in-acoustic-prosodic-entrainment-in-spoken/
- Spoken BNC2014: https://corpora.lancs.ac.uk/bnc2014/
- Switchboard-1 Release 2, LDC page: https://catalog.ldc.upenn.edu/LDC97S62
- Switchboard-1 Release 2, DOI: https://doi.org/10.35111/sw3h-rw02
- Santa Barbara Corpus of Spoken American English, LDC Part I: https://catalog.ldc.upenn.edu/LDC2000S85
- Buckeye Corpus: https://buckeyecorpus.osu.edu/
- Buckeye Corpus paper: https://doi.org/10.1016/j.specom.2004.09.001
- DGD / FOLK spoken German portal: https://dgd.ids-mannheim.de/DGD2Web/jsp/Welcome.jsp
- German turn-beginning design, Deppermann (2013): https://doi.org/10.1016/j.pragma.2012.07.010
- German `also` and `dann` in talk-in-interaction, Deppermann and Helmer (2013): https://ids-pub.bsz-bw.de/frontdoor/index/index/docId/1304
- German sentence-position effects for `also`, Alm (2004): https://doi.org/10.21248/zaspil.35.2004.219
- German `okay` as a neutral acceptance token, Oloff (2018): https://doi.org/10.54563/lexique.924
- German response token `ja` and prosody, Golato and Fagyal (2008): https://doi.org/10.1080/08351810802237834
- German backchannels and fluencemes, Bottcher and Rossi (2025): https://doi.org/10.3389/fcomm.2025.1655049
- German/Austrian-German backchannel timing, Paierl, Kelterer, and Schuppler (2025): https://doi.org/10.3390/languages10080194
- Paierl, Kelterer, and Schuppler (2025), article page: https://www.mdpi.com/2226-471X/10/8/194
- Austrian German read/conversational corpus, Schuppler et al. (2017): https://doi.org/10.1016/j.specom.2017.09.003
- Schuppler et al. (2017), article page: https://www.sciencedirect.com/science/article/pii/S0167639317300535
- Kiel Corpus of Spoken German: https://www.isfas.uni-kiel.de/de/linguistik-und-phonetik/smile-if-you-can-see-this/forschung/kiel-corpus/the-kiel-corpus-of-spoken-german-read-and-spontaneous-speech
- German filler particles, Muhlack et al. (2023): https://www.mdpi.com/2226-471X/8/2/100
- Filler-particle terminology, Belz (2023): https://www.mdpi.com/2226-471X/8/1/57
- German `Ã¤h`/`Ã¤hm` phonetics, Belz (2021): https://doi.org/10.1007/978-3-662-62812-6
- German `Ã¤h`/`Ã¤hm` phonetics publisher page, Belz (2021): https://link.springer.com/book/10.1007/978-3-662-62812-6
- Reduced pronunciation variants, Ernestus and Warner (2011): https://doi.org/10.1016/S0095-4470(11)00055-6
- Reduced pronunciation variants, MPI record: https://www.mpi.nl/publications/item_1084571
- Text normalization for speech applications, Zhang et al. (2019): https://doi.org/10.1162/COLI_a_00349
- German schwa realization in spontaneous speech, Lange et al. (2024): https://doi.org/10.1515/zfs-2024-2011
- German schwa realization repository page: https://edoc.hu-berlin.de/items/2ca4d454-e829-4f9b-8938-bda2302dc6c2
- GAT 2 transcription system: https://ids-pub.bsz-bw.de/files/222/Selting_Auer_Barth-Weingarten_Gespraechsanalytisches_Transkriptionssystem_2009.pdf
- Inbreath noises, Trouvain et al. (2020): https://www.isca-archive.org/speechprosody_2020/trouvain20_speechprosody.html
- Pause variability, Werner et al. (2022): https://www.isca-archive.org/speechprosody_2022/werner22_speechprosody.html
- Breath-noise acoustics and modeling, Werner et al. (2024): https://doi.org/10.1044/2023_JSLHR-23-00112
- Smiled speech, Barthel and Quene (2015): https://dspace.library.uu.nl/handle/1874/356042
- Smiling and acoustic/perceptual effects on speech, Tartter (1980): https://doi.org/10.3758/BF03199901
- Call-center vocal cues and service success, Zhou et al. (2025): https://doi.org/10.1016/j.jbusres.2025.115282
- Speech rate, intonation, pitch, confidence, and persuasion, Guyer, Fabrigar, and Vaughan-Johnston (2019): https://doi.org/10.1177/0146167218787805
- Acoustic-prosodic charisma in business/keynote speech, Niebuhr, Vosse, and Brem (2016): https://doi.org/10.1016/j.chb.2016.06.059
- Niebuhr, Vosse, and Brem (2016), article page: https://www.sciencedirect.com/science/article/pii/S0747563216304873
- Acoustic charisma profiles for entrepreneurship, Niebuhr, Brem, and Tegtmeier (2017): https://doi.org/10.20396/joss.v6i1.14983
- Niebuhr, Brem, and Tegtmeier (2017), article page: https://econtents.sbu.unicamp.br/inpec/index.php/joss/article/view/14983
- ITU-T P.800 subjective speech-quality testing: https://www.itu.int/rec/T-REC-P.800
- Limits of MOS for speech synthesis evaluation, Le Maguer, King, and Harte (2024): https://doi.org/10.1016/j.csl.2023.101577
- Le Maguer, King, and Harte (2024), university record: https://www.research.ed.ac.uk/en/publications/the-limits-of-the-mean-opinion-score-for-speech-synthesis-evaluat/
- Blizzard Challenge 2023 speech-synthesis evaluation, Perrotin et al. (2024): https://doi.org/10.1016/j.csl.2024.101747
- Perrotin et al. (2024), university record: https://www.research.ed.ac.uk/en/publications/refining-the-evaluation-of-speech-synthesis-a-summary-of-the-bliz
- Synthetic vs human speech persuasiveness, Stern et al. (1999): https://doi.org/10.1518/001872099779656680
- Stern et al. (1999), PubMed record: https://pubmed.ncbi.nlm.nih.gov/10774129/
- ElevenLabs pacing and emotion prompting: https://elevenlabs.io/docs/product/prompting/pacing-and-emotion
- ElevenLabs Voice Design: https://elevenlabs.io/docs/creative-platform/voices/voice-design

Project use:

- `VOICE-023` speech-realism design
- thesis discussion of controlled speech naturalness
- `VOICE-025` filler-placement design
- `VOICE-026` planned interaction-prosody/backchannel design
- limitations around listener evaluation and language-specific behavior

## Privacy And Data Governance Sources

### European Commission GDPR Principles

- Type: legal/privacy reference
- Source: https://commission.europa.eu/law/law-topic/data-protection/rules-business-and-organisations/principles-gdpr/overview-principles/what-data-can-we-process-and-under-which-conditions_en
- Project use: data minimization, purpose limitation, storage limitation, integrity/confidentiality framing.
- Thesis use: private call-center data boundary and retention rationale.

### European Data Protection Board GDPR Basics

- Type: legal/privacy reference
- Processing principles: https://www.edpb.europa.eu/sme-data-protection-guide/faq-frequently-asked-questions/answer/what-are-basic-processing_en
- Legal bases: https://www.edpb.europa.eu/sme-data-protection-guide/faq-frequently-asked-questions/answer/what-are-legal-basics-processing_en
- Project use: private-data learning checkpoints, redaction, retention/deletion, and no-provider-upload default.
- Thesis caution: use these for high-level GDPR framing, not as legal advice.

## TTS And Voice Provider Sources

### VOICE-009 provider research

Detailed source index:

- `research/experiments/generated/VOICE-009/VOICE-009-tts-provider-research-report.md`

Provider sources used:

- Cartesia docs: https://docs.cartesia.ai/
- Cartesia Sonic 3: https://docs.cartesia.ai/build-with-cartesia/tts-models/sonic-3
- Cartesia realtime quickstart: https://docs.cartesia.ai/get-started/realtime-text-to-speech-quickstart
- Cartesia WebSocket API: https://docs.cartesia.ai/api-reference/tts/websocket
- Cartesia pricing: https://cartesia.ai/pricing
- ElevenLabs TTS: https://elevenlabs.io/docs/overview/capabilities/text-to-speech
- ElevenLabs models: https://elevenlabs.io/docs/models
- ElevenLabs TTS API: https://elevenlabs.io/text-to-speech-api
- OpenAI TTS guide: https://platform.openai.com/docs/guides/text-to-speech
- OpenAI audio quickstart: https://platform.openai.com/docs/guides/audio/quickstart
- OpenAI GPT-4o mini TTS model: https://platform.openai.com/docs/models/gpt-4o-mini-tts
- Azure AI Speech TTS: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech
- Azure language support: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support
- Azure TTS REST API: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-text-to-speech
- Google Cloud Chirp 3 HD: https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd
- Google Cloud streaming TTS: https://cloud.google.com/text-to-speech/docs/create-audio-text-streaming
- Google Cloud voices: https://cloud.google.com/text-to-speech/docs/voices
- Amazon Polly SynthesizeSpeech: https://docs.aws.amazon.com/polly/latest/dg/API_SynthesizeSpeech.html
- Amazon Polly streaming: https://docs.aws.amazon.com/polly/latest/dg/API_StartSpeechSynthesisStream.html
- Amazon Polly neural voices: https://docs.aws.amazon.com/polly/latest/dg/neural-voices.html
- Deepgram Aura voices: https://developers.deepgram.com/docs/tts-models
- Piper local TTS: https://github.com/rhasspy/piper
- Open Home Foundation Piper: https://github.com/OHF-Voice/piper1-gpl
- Open Home Foundation Piper releases: https://github.com/OHF-Voice/piper1-gpl/releases
- OpenAI pricing: https://platform.openai.com/docs/pricing
- Azure AI Speech pricing: https://azure.microsoft.com/en-gb/pricing/details/speech/
- Amazon Polly pricing: https://aws.amazon.com/polly/pricing/
- Deepgram pricing: https://deepgram.com/pricing
- Cartesia TTS bytes endpoint docs: https://docs.cartesia.ai/api-reference/tts/bytes
- Cartesia TTS endpoint comparison: https://docs.cartesia.ai/api-reference/tts/compare-tts-endpoints
- Cartesia alternate endpoint comparison: https://docs.cartesia.ai/use-the-api/compare-tts-endpoints
- Cartesia Sonic SSML tags: https://docs.cartesia.ai/build-with-cartesia/sonic-3/ssml-tags
- Cartesia Sonic volume, speed, and emotion controls: https://docs.cartesia.ai/build-with-cartesia/sonic-3/volume-speed-emotion
- ElevenLabs streaming TTS API: https://elevenlabs.io/docs/api-reference/text-to-speech/stream
- ElevenLabs WebSocket API: https://elevenlabs.io/docs/api-reference/websocket
- ElevenLabs latency concepts: https://elevenlabs.io/docs/eleven-api/concepts/latency
- ElevenLabs pacing and emotion prompting: https://elevenlabs.io/docs/product/prompting/pacing-and-emotion
- ElevenLabs API pause/SSML help article: https://help.elevenlabs.io/hc/en-us/articles/24352686926609-Do-pauses-and-SSML-phoneme-tags-work-with-the-API

Project use:

- provider-readiness matrix
- latency, German/English, privacy, and fallback criteria
- guarded TTS integration sequence

Thesis caution:

- provider docs justify engineering choices, not objective quality claims. Audio quality claims require measured runs and listening review.

### ULTRAVOX-001 realtime voice evaluation

Detailed source index:

- `research/experiments/generated/ULTRAVOX-001/ULTRAVOX-001-bounded-realtime-voice-evaluation-report.md`
- `research/experiments/generated/ULTRAVOX-002/ULTRAVOX-002-synthetic-live-smoke-report.md`
- `research/experiments/generated/ULTRAVOX-003/ULTRAVOX-003-synthetic-audio-turn-report.md`

Provider and open-source sources used:

- UltraVox overview: https://docs.ultravox.ai/overview
- UltraVox how it works: https://docs.ultravox.ai/gettingstarted/how-ultravox-works
- UltraVox Create Call API: https://docs.ultravox.ai/api-reference/calls/calls-post
- UltraVox calls API endpoint: https://api.ultravox.ai/api/calls
- UltraVox call delete endpoint template: https://api.ultravox.ai/api/calls/
- UltraVox WebSocket integration: https://docs.ultravox.ai/apps/websockets
- UltraVox custom tools: https://docs.ultravox.ai/tools/custom/overview
- UltraVox FAQ: https://docs.ultravox.ai/gettingstarted/faq
- UltraVox pricing: https://www.ultravox.ai/pricing
- fixie-ai/ultravox GitHub repository: https://github.com/fixie-ai/ultravox
- UltraVox v0.7 GLM 4.6 model card: https://huggingface.co/fixie-ai/ultravox-v0_7-glm-4_6
- UltraVox v0.6 Llama 3.1 8B model card: https://huggingface.co/fixie-ai/ultravox-v0_6-llama-3_1-8b

Project use:

- bounded realtime voice architecture evaluation
- synthetic hosted API smoke testing
- hosted API versus hosted console versus open-source self-hosting decision support
- provider boundary, retention, lock-in, and guarded-runtime control analysis

Current project status:

- `ULTRAVOX-001` is dry-run only
- `ULTRAVOX-002` is approved for one synthetic hosted API smoke test with env-only key handling
- `ULTRAVOX-003` ran one synthetic customer-audio hosted API turn with env-only key handling and fixture fallback; the result is transport-positive but latency/quality-inconclusive because no transcript or agent audio was received
- customer audio, voice cloning, durable provider agents, provider-owned business logic, and runtime integration remain blocked
- `PROD-102` remains closed

Thesis caution:

- UltraVox provider docs and model cards justify system-design hypotheses, not latency or quality claims. A future synthetic live run must measure latency and preserve protected-response exactness before any thesis or product claim.

### ElevenLabs voice design and remixing

Detailed source entry:

- `docs/third-party-inspirations.md`
- `docs/product/VOICE_020_ELEVENLABS_VOICE_DESIGN.md`

Sources:

- Voices overview: https://elevenlabs.io/docs/overview/capabilities/voices
- Voice Design: https://elevenlabs.io/docs/eleven-creative/voices/voice-design
- TTS best practices: https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices
- Voice settings API: https://elevenlabs.io/docs/api-reference/voices/settings/get
- Agent privacy docs: https://elevenlabs.io/docs/eleven-agents/customization/privacy
- Commercial-use help article: https://help.elevenlabs.io/hc/en-us/articles/13313564601361-Can-I-publish-the-content-I-generate-on-the-platform
- Voice Remixing: https://elevenlabs.io/docs/overview/capabilities/voice-remixing

Project use:

- voice prompt design
- voice remixing prompts
- live custom voice comparison
- provider privacy and logging boundaries

## Sales Objection And Product Sources

### Sales difficulty taxonomy

Project file:

- `docs/product/SALES_DIFFICULTY_TAXONOMY.md`

Sources found or recovered:

- Apollo common sales objections: https://www.apollo.io/insights/common-sales-objections
- Apollo handling objections in sales: https://www.apollo.io/insights/handling-objections-in-sales
- Salesgenie objection handling: https://www.salesgenie.com/blog/sales-objection-handling/
- Proposify sales objection handling: https://www.proposify.com/blog/sales-objection-handling
- Proposify four types of objections: https://www.proposify.com/blog/overcome-sales-objections
- B2B Vic objection handling framework: https://b2bvic.com/articles/objection-handling-b2b-sales.html

Project use:

- broad difficulty categories such as price, timing, authority, trust, status quo, competitor comparison, fit/risk, and brush-off.

Thesis caution:

- these are public sales-practice articles, not peer-reviewed evidence.
- use them as product grounding, not as academic proof.
- synthetic experiment cases should not copy example scripts from these pages.

## Open-Source And Workflow Inspirations

Detailed attribution lives in:

- `docs/third-party-inspirations.md`

Sources:

- OpenMythos: https://github.com/kyegomez/OpenMythos
- jcode: https://github.com/1jehuang/jcode
- autoresearch: https://github.com/karpathy/autoresearch
- gstack: https://github.com/garrytan/gstack
- GitNexus: https://github.com/abhigyanpatwari/GitNexus
- awesome-llm-apps: https://github.com/Shubhamsaboo/awesome-llm-apps
- graphify: https://github.com/safishamsi/graphify
- voicebox: https://github.com/jamiepine/voicebox
- VibeVoice: https://github.com/microsoft/VibeVoice
- hermes-agent: https://github.com/NousResearch/hermes-agent
- TRIBE v2: https://github.com/facebookresearch/tribev2

Project use:

- review workflow inspiration
- local relevant-file reading
- experiment discipline
- product review gates
- voice provenance caution
- future ASR and multimodal ideas

Thesis caution:

- cite only where these materially influenced methodology or implementation process.
- do not imply these repos are runtime dependencies.
- license restrictions are recorded in `docs/third-party-inspirations.md`.

## Browser And Local Prototype Sources

Project-relevant browser/local APIs:

- browser Web Speech API behavior was used in early browser speech demos
- Windows SAPI was tested as a local no-key TTS path

Current registry status:

- exact external documentation pages for Web Speech API and Windows SAPI are not yet captured in a thesis-ready source entry.

Follow-up:

- if browser speech recognition or Windows SAPI remains in the thesis prototype discussion, add MDN/Microsoft source links and limitations before final writing.

## Unverified Or Needs Follow-Up

These influenced project direction but should not be used as final thesis references yet:

- exact original download source and license for the local IEMOCAP CSV-style export
- exact original download source and license for the local MELD archive, beyond the official project/GitHub references
- exact original download source and license for the local Persuasion for Good archive, beyond the official paper/corpus references
- exact provider terms for production retention and logging beyond the implementation docs already cited
- final German outbound-calling, insurance-sales, and call-recording legal sources

## How To Use This Registry

For the thesis:

- use academic papers and dataset sources in related work, data, and methodology chapters
- use provider docs only when explaining engineering constraints and implementation decisions
- use sales-practice articles only as product-context grounding
- use open-source repos only for attribution and methodology/process inspiration
- disclose private-data influence separately and never include private artifacts

For product work:

- keep provider claims behind live tests and listening review
- keep private call-center audio local-only
- keep SalesCampaign profiles as the product boundary
- keep one reusable sales-agent core across verticals
- run `python scripts\check_thesis_reference_registry.py` before GitHub checkpoints so source-backed claims stay traceable
