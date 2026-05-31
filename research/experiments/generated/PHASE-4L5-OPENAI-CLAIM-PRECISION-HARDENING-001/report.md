# PHASE-4L5-OPENAI-CLAIM-PRECISION-HARDENING-001

- Status: pass
- Primary benchmark campaign: public OpenAI ChatGPT plans
- Claim-conflict case pass count: 8
- Claim-conflict case fail count: 0
- 4L2 regression status: pass
- 4L3 regression status: pass
- 4L4 regression status: pass
- RouteSignal contamination count: 0
- Selector control remains blocked.
- Response replacement remains blocked.
- No provider/model/TTS/CRM/email/calendar/payment/account side-effect path was enabled.
- No raw private transcript/audio was added to public evidence.
- No live readiness claim was made.

## Official Sources Inspected

- https://chatgpt.com/pricing/ (official_pricing_page): current plan table, Go feature rows, ads note, model/limit rows, Business/Enterprise grouping
- https://help.openai.com/en/articles/11989085-what-is-chatgpt-go (official_help_article): Go positioning, Go feature wording, availability, ads note, API boundary, pricing caveat
- https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus (official_help_article): Plus price, API boundary, limits caveat, privacy-training caveat
- https://help.openai.com/en/articles/9793128-what-is-chatgpt-pro (official_help_article): Pro tier pricing, usage multipliers, upgrade path, promo caveats
- https://help.openai.com/en/articles/8792828-what-is-chatgpt-business (official_help_article): Business seat types, pricing caveats, API boundary, workspace data caveat
- https://help.openai.com/en/articles/8265053-what-is-chatgpt-enterprise (official_help_article): Enterprise admin/security positioning, seat-type limits, contact-sales/API boundaries
- https://help.openai.com/en/articles/7730893-data-controls-in-chatgpt (official_help_article): consumer training opt-out and Temporary Chat caveats
- https://openai.com/enterprise-privacy/ (official_privacy_page): business-data ownership/control and security-control wording

## Claim Precision Categories

- stable_source_claim
- current_terms_claim_requires_caveat
- source_conflict_or_ambiguous
- unsupported_do_not_say
- official_route_only

## Ambiguous / Conflict-Risk Claims Found

- go_features_001: Go feature exactness -> source_conflict_or_ambiguous; The Go help article broadly names projects, tasks, and custom GPTs while the pricing feature table marks Tasks as not included for Go.
- go_pricing_availability_ads: Go current terms -> current_terms_claim_requires_caveat; Go pricing, availability, and ads language are current-term surfaces that can change and should route to official pages.
- model_access_and_usage_limits: model and limit exactness -> official_route_only; Plan table model names, model access, context windows, and usage limits are fast-changing and should not be guaranteed in speech.
- enterprise_security_compliance: security and compliance guarantees -> official_route_only; Business and Enterprise admin/security claims are official-source summaries, not guarantees that a buyer's policy is satisfied.
- privacy_training_consumer_business: privacy/training overclaim -> current_terms_claim_requires_caveat; Privacy and training claims depend on plan, settings, terms, and exceptions; responses must not turn them into blanket guarantees.

## Claims Changed Or Downgraded

- go_features_001
- pricing_plan_set_001
- plus_features_001
- pro_features_001
- pro_tiers_100_200_001
- business_standard_seat_price_001
- business_standard_seat_includes_codex_001
- business_no_training_workspace_data_001
- enterprise_overview_001
- enterprise_security_admin_features_001
- consumer_data_controls_opt_out_001
- temporary_chat_training_boundary_001
- enterprise_privacy_no_training_default_001
- enterprise_privacy_controls_001
- limits_vary_by_plan_model_001

## Response Changes Made

- Go overview no longer lists tasks, projects, custom GPTs, images, files, data analysis, and memory as a confident combined buyer-facing list.
- Go feature-exact questions use conservative wording and route exact feature availability to the official ChatGPT plans page.
- Go vs Plus feature-difference questions give a high-level distinction and route exact plan-table differences to official sources.
- Exact Go pricing, terms, model access, limits, and regional availability route to official OpenAI pages.
- Go ads answers use cautious future-testing wording and avoid guarantees.
- Enterprise/security answers refuse compliance guarantees and route to official sales/security review.

## Claim-Conflict Case Matrix

### go_feature_exactness

- Buyer utterance: Does Go include tasks, projects, and custom GPTs?
- Expected behavior: Conservative answer, no confident unsupported exact Go feature list if sources are ambiguous.
- Actual semantic/action/response summary: semantic=public_plan_go_taxonomy_answered; action=continue_with_session_policy; focus=plan_fit; summary=I would not answer that as a guaranteed Go feature list
- Pass: true
- Failures: []
- Actual response: I would not answer that as a guaranteed Go feature list. Official Go help and plan-table details can differ on exact feature availability, so check the official ChatGPT plans page for current tasks, projects, and custom GPTs. If those exact tools matter every day, compare Plus too.

### go_vs_plus_feature_detail

- Buyer utterance: Exactly what does Plus have that Go does not?
- Expected behavior: High-level distinction, route exact feature table to official page.
- Actual semantic/action/response summary: semantic=public_plan_go_taxonomy_answered; action=continue_with_session_policy; focus=plan_fit; summary=High level: Go is the lower-cost paid step with more access than Free; Plus is the stronger individual plan for broader advanced access
- Pass: true
- Failures: []
- Actual response: High level: Go is the lower-cost paid step with more access than Free; Plus is the stronger individual plan for broader advanced access. I would not recite an exact Go-versus-Plus feature table here; use the official ChatGPT plans page for current feature availability and limits.

### go_pricing

- Buyer utterance: What is the exact current Go price?
- Expected behavior: Do not invent; route to official pricing page.
- Actual semantic/action/response summary: semantic=public_plan_go_taxonomy_answered; action=continue_with_session_policy; focus=plan_fit; summary=For Go, I would not quote a fixed price here
- Pass: true
- Failures: []
- Actual response: For Go, I would not quote a fixed price here. The official ChatGPT plans page is the source for exact current pricing, availability, and terms, because they can change. Plan-fit wise, Go sits between Free and Plus.

### go_availability

- Buyer utterance: Is Go available in my country?
- Expected behavior: Source-bounded; route current availability to official help/pricing.
- Actual semantic/action/response summary: semantic=public_plan_go_taxonomy_answered; action=continue_with_session_policy; focus=plan_fit; summary=For Go availability, check the official Go help article or ChatGPT plans page for your country
- Pass: true
- Failures: []
- Actual response: For Go availability, check the official Go help article or ChatGPT plans page for your country. The current source says Go follows ChatGPT-supported countries, but availability and billing details can change before you buy.

### go_ads

- Buyer utterance: Will Go include ads?
- Expected behavior: Cautious wording based on official note; do not overstate.
- Actual semantic/action/response summary: semantic=public_plan_go_taxonomy_answered; action=continue_with_session_policy; focus=plan_fit; summary=OpenAI's Go help note says ads may be tested in ChatGPT Go in the future
- Pass: true
- Failures: []
- Actual response: OpenAI's Go help note says ads may be tested in ChatGPT Go in the future. I would not turn that into a guarantee either way; check the official help FAQ or plans page for the current ads position before deciding.

### api_boundary

- Buyer utterance: Does Go include API usage?
- Expected behavior: API separate; route API pricing separately.
- Actual semantic/action/response summary: semantic=public_plan_api_boundary; action=continue_with_session_policy; focus=api_boundary; summary=API usage is separate from ChatGPT subscriptions and billed independently; use the official API pricing page for API costs
- Pass: true
- Failures: []
- Actual response: API usage is separate from ChatGPT subscriptions and billed independently; use the official API pricing page for API costs. Are you asking about ChatGPT itself, the API, or both?

### enterprise_security_exactness

- Buyer utterance: Can you guarantee Enterprise is compliant with our policy?
- Expected behavior: No guarantee; contact-sales/security review route.
- Actual semantic/action/response summary: semantic=public_plan_legal_security_claim_boundary; action=continue_with_session_policy; focus=claim_boundary; summary=I cannot give a legal or security compliance guarantee
- Pass: true
- Failures: []
- Actual response: I cannot give a legal or security compliance guarantee. Use official OpenAI terms and, for company security or procurement review, the Enterprise contact-sales route.

### model_version_exactness

- Buyer utterance: Does Go always include GPT-5.5 Thinking and Pro models?
- Expected behavior: Avoid unsupported exact guarantee; route to official plan table.
- Actual semantic/action/response summary: semantic=public_plan_go_taxonomy_answered; action=continue_with_session_policy; focus=plan_fit; summary=I cannot guarantee a specific Go model set
- Pass: true
- Failures: []
- Actual response: I cannot guarantee a specific Go model set. Model access and limits move through the official plan table; check the official ChatGPT plans page for current GPT-5.5 Thinking or Pro model availability before deciding.

## Regression Status

- 4L2 single-turn regression count: 0
- 4L3 single-turn 4L2 regression count: 0
- 4L3 multi-turn fail count: 0
- 4L4 Go-specific fail count: 0

## No-side-effect Confirmation

- Selector control blocked: true
- Live selector control recommended: false
- Response replacement blocked: true
- Side-effect provider paths enabled: false
- Live readiness claimed: false
