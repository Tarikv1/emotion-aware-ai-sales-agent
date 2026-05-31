# PHASE-4L4-OPENAI-SOURCE-REFRESH-PLAN-TAXONOMY-001

- Status: pass
- Official source access status: succeeded
- Primary benchmark campaign: public OpenAI ChatGPT plans
- Captured individual taxonomy: Free, Go, Plus, Pro
- Captured Business/Enterprise taxonomy: Business, Enterprise
- Go-specific case pass count: 8
- Go-specific case fail count: 0
- 4L3 regression status: pass
- 4L3 single-turn regression count: 0
- 4L3 multi-turn fail count: 0
- RouteSignal contamination count: 0
- Selector control remains blocked.
- Response replacement remains blocked.
- No provider/model/TTS/CRM/email/calendar/payment/account side-effect path was enabled.
- No raw private transcript/audio was added to public evidence.
- No live readiness claim was made.

## Official Sources Inspected

- https://chatgpt.com/pricing/ (official_pricing_page): current plan names, plan grouping, Go placement, Business/Enterprise route, pricing/terms caveat
- https://help.openai.com/en/articles/11989085-what-is-chatgpt-go (official_help_article): Go positioning, Go features, signup/profile route, pricing-change caveat

## Stale Assumptions Found / Fixed

- PLAN_LABELS omitted Go.
- The main individual plan category response skipped Go.
- Several spoken responses treated Plus as the first paid individual step.
- The price/terms response answered Plus/Pro while claiming current paid-plan coverage.
- The 4L2/4L3 matrices did not exercise Go-specific plan-fit, price, or team-boundary cases.

## Go-Specific Case Matrix

### plan_category_includes_go

- Buyer utterance: Can you explain Free, Go, Plus, Pro, Business, and Enterprise in plain English?
- Expected behavior: Explain all current plan names and separate individual from Business/Enterprise routes.
- Actual semantic/action/response summary: semantic=public_plan_orientation_plan_category_explanation; action=continue_with_session_policy; focus=plan_explanation; summary=Simple version: Free is basic, Go is the lower-cost paid individual step, Plus and Pro are stronger individual upgrades, Business is for teams, and Enterprise is for larger organizations with admin, procurement, or security needs
- Pass: true
- Failures: []
- Actual response: Simple version: Free is basic, Go is the lower-cost paid individual step, Plus and Pro are stronger individual upgrades, Business is for teams, and Enterprise is for larger organizations with admin, procurement, or security needs. Are you deciding as an individual, a team, or for procurement and security review?

### what_is_go

- Buyer utterance: What is Go?
- Expected behavior: Answer that Go is a lower-cost paid individual step with expanded access beyond Free.
- Actual semantic/action/response summary: semantic=public_plan_go_taxonomy_answered; action=continue_with_session_policy; focus=plan_fit; summary=Go is positioned as a lower-cost paid plan that gives more access to popular ChatGPT features than Free
- Pass: true
- Failures: []
- Actual response: Go is positioned as a lower-cost paid plan that gives more access to popular ChatGPT features than Free. Go is mainly for more access to common tools such as image generation, file uploads, data analysis, memory, projects, tasks, and custom GPTs. It is an individual step between Free and Plus; Business and Enterprise are separate team or organization routes. Exact current terms can change, so use the official ChatGPT plans page as the final source for plan fit before you decide.

### light_user_free_or_go

- Buyer utterance: I use ChatGPT lightly for personal tasks; is Free or Go enough?
- Expected behavior: Avoid pushing Plus/Pro and frame Free or Go as enough for light individual use.
- Actual semantic/action/response summary: semantic=public_plan_go_taxonomy_answered; action=continue_with_session_policy; focus=plan_fit; summary=For light personal use, Free may be enough
- Pass: true
- Failures: []
- Actual response: For light personal use, Free may be enough. Go is the next lower-cost paid step only if Free limits the common tools you need. I would not jump to Plus or Pro unless advanced tools, heavier usage, or limits matter.

### lower_cost_paid_before_plus

- Buyer utterance: I want a lower-cost paid option before Plus or Pro. What should I compare?
- Expected behavior: Name Go as the lower-cost paid step before Plus/Pro, with official-page caveat.
- Actual semantic/action/response summary: semantic=public_plan_go_taxonomy_answered; action=continue_with_session_policy; focus=plan_fit; summary=Compare Go first as the lower-cost paid step before Plus and Pro
- Pass: true
- Failures: []
- Actual response: Compare Go first as the lower-cost paid step before Plus and Pro. Plus is the stronger individual paid plan, and Pro is for heavier individual use. Exact current terms can change, so use the official ChatGPT plans page as the final source for plan fit before you decide.

### go_plus_pro_fit

- Buyer utterance: How do I decide between Go, Plus, and Pro?
- Expected behavior: Frame Go/Plus/Pro as individual paid steps with increasing access and usage headroom.
- Actual semantic/action/response summary: semantic=public_plan_go_taxonomy_answered; action=continue_with_session_policy; focus=plan_fit; summary=For individual plans: Go is the lower-cost paid step beyond Free, Plus is for broader advanced access, and Pro is for heavier use or more headroom
- Pass: true
- Failures: []
- Actual response: For individual plans: Go is the lower-cost paid step beyond Free, Plus is for broader advanced access, and Pro is for heavier use or more headroom. The deciding factor is how often limits or advanced tools matter.

### go_cost_current_pricing

- Buyer utterance: What does Go cost right now, and is that current?
- Expected behavior: Do not invent a Go price; route exact Go price and current terms to the official plan page.
- Actual semantic/action/response summary: semantic=public_plan_go_taxonomy_answered; action=continue_with_session_policy; focus=plan_fit; summary=For Go, I would not quote a fixed price here
- Pass: true
- Failures: []
- Actual response: For Go, I would not quote a fixed price here. The official ChatGPT plans page is the source for exact current pricing, availability, and terms, because they can change. Plan-fit wise, Go sits between Free and Plus.

### business_enterprise_separate_from_individual

- Buyer utterance: Are Business and Enterprise separate from Go, Plus, and Pro?
- Expected behavior: Separate Go/Plus/Pro individual plans from Business/Enterprise organization routes.
- Actual semantic/action/response summary: semantic=public_plan_go_taxonomy_answered; action=continue_with_session_policy; focus=plan_fit; summary=Yes
- Pass: true
- Failures: []
- Actual response: Yes. Go, Plus, and Pro are individual plans. Business is the team workspace route, and Enterprise is for larger organization needs like admin controls, security review, procurement, or contact sales.

### go_is_not_team_plan

- Buyer utterance: Is Go for teams?
- Expected behavior: Say Go is an individual plan, while Business/Enterprise cover team or organization needs.
- Actual semantic/action/response summary: semantic=public_plan_go_taxonomy_answered; action=continue_with_session_policy; focus=plan_fit; summary=Go is an individual plan, not the team workspace route
- Pass: true
- Failures: []
- Actual response: Go is an individual plan, not the team workspace route. For team workspace/admin needs, compare Business; for organization-level controls like SSO, SCIM, procurement, or security review, use Enterprise/contact sales.

## No-side-effect Confirmation

- Selector control blocked: true
- Response replacement blocked: true
- Side-effect provider paths enabled: false
- Live readiness claimed: false
