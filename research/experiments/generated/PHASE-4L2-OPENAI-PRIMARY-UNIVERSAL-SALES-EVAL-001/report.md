# PHASE-4L2-OPENAI-PRIMARY-UNIVERSAL-SALES-EVAL-001

- Status: pass
- Primary benchmark campaign: public OpenAI ChatGPT plans
- RouteSignal role: secondary regression fixture only
- Live selector control enabled: false
- Response replacement enabled: false
- Provider/model/TTS/CRM/email/calendar/payment/account side-effect path enabled: false
- Raw private transcript/audio added to public evidence: false
- Live readiness claimed: false

## Summary

- Case pass count: 14
- Case fail count: 0
- Source/affiliation safety status: pass
- AND/OR fidelity status: pass
- Repeated-question / loop-repair status: pass
- Close/disqualify status: pass
- RouteSignal contamination in OpenAI-primary responses: 0

## Category Counts

| Area | Cases | Pass | Fail |
| --- | ---: | ---: | ---: |
| source / affiliation boundary (`source_affiliation_boundary`) | 1 | 1 | 0 |
| plan category explanation (`plan_category_explanation`) | 1 | 1 | 0 |
| subscription vs model/product distinction (`subscription_model_product_distinction`) | 1 | 1 | 0 |
| Free / Plus / Pro / Business / Enterprise fit (`plan_fit`) | 3 | 3 | 0 |
| price / terms caveat (`price_terms_caveat`) | 1 | 1 | 0 |
| privacy / security / data boundary (`privacy_security_data_boundary`) | 2 | 2 | 0 |
| competitor/current-tool context (`competitor_current_tool_context`) | 3 | 3 | 0 |
| AND/OR fidelity (`and_or_fidelity`) | 2 | 2 | 0 |
| repeated-question / loop repair (`repeated_question_loop_repair`) | 1 | 1 | 0 |
| close/disqualify behavior (`close_disqualify`) | 3 | 3 | 0 |
| spoken naturalness and active selling (`spoken_naturalness_active_selling`) | 4 | 4 | 0 |

## Case Matrix

### source_affiliation_boundary

- Buyer utterance: Are you actually OpenAI, and where are you getting these plan prices?
- Expected universal sales behavior: Decline official OpenAI affiliation, cite public OpenAI plan/help sources, and keep the buyer moving toward a plan-fit decision without pretending to be OpenAI.
- Actual semantic/action/response summary: semantic=public_plan_affiliation_boundary; action=continue_with_session_policy; focus=trust; summary=Good question
- Pass: true
- Failures: []
- Actual response: Good question. I'm not calling from OpenAI; I'm using public OpenAI plan and help information to help you decide the fit. The official pages are the final source. Are you choosing for yourself or a team?

### plan_category_explanation

- Buyer utterance: Can you explain Free, Plus, Pro, Business, and Enterprise in plain English?
- Expected universal sales behavior: Explain plan categories conversationally, including individual and organization paths, and ask a useful next question instead of dumping static FAQ text.
- Actual semantic/action/response summary: semantic=public_plan_orientation_plan_category_explanation; action=continue_with_session_policy; focus=plan_explanation; summary=Simple version: Free is the basic option, Plus and Pro are individual upgrades, Business is for teams, and Enterprise is for larger organizations with admin or security needs
- Pass: true
- Failures: []
- Actual response: Simple version: Free is the basic option, Plus and Pro are individual upgrades, Business is for teams, and Enterprise is for larger organizations with admin or security needs. Are you deciding as an individual, a team, or for procurement and security review?

### subscription_model_product_distinction

- Buyer utterance: Are ChatGPT plans the same thing as API tokens, model access, or the ChatGPT app?
- Expected universal sales behavior: Separate ChatGPT subscriptions from API/token usage and ask whether the buyer means ChatGPT, API usage, or both.
- Actual semantic/action/response summary: semantic=public_plan_api_boundary; action=continue_with_session_policy; focus=api_boundary; summary=API usage is separate from ChatGPT subscriptions
- Pass: true
- Failures: []
- Actual response: API usage is separate from ChatGPT subscriptions. Are you asking about ChatGPT itself, the API, or both?

### fit_light_personal_free

- Buyer utterance: I only use it once in a while for light personal tasks; Free is enough.
- Expected universal sales behavior: Disqualify paid-plan pressure when light personal usage or Free already fits.
- Actual semantic/action/response summary: semantic=public_plan_light_basic_use; action=continue_with_session_policy; focus=no_fit_or_light_use; summary=If your use is light or basic, Free may be enough
- Pass: true
- Failures: []
- Actual response: If your use is light or basic, Free may be enough. I would only compare paid plans if limits, tools, or team needs matter. What would you mainly use ChatGPT for?

### fit_heavy_individual_pro

- Buyer utterance: I use ChatGPT for coding and writing heavily every day and I keep hitting limits.
- Expected universal sales behavior: Move heavy individual coding/writing with limit pain toward Pro while preserving Plus as the lower-cost option.
- Actual semantic/action/response summary: semantic=public_plan_limit_pain_answered; action=continue_with_session_policy; focus=plan_fit; summary=Got it - that usage pain makes Pro the plan to compare seriously
- Pass: true
- Failures: []
- Actual response: Got it - that usage pain makes Pro the plan to compare seriously. Plus is the lower-cost starting point, but Pro is the better fit if you are regularly hitting limits. Do you want the lower-cost starting point, or the plan least likely to hit limits?

### fit_team_admin_enterprise

- Buyer utterance: We have a team and need admin controls, SSO, SCIM, procurement, and security review.
- Expected universal sales behavior: Route team/admin needs to Business or Enterprise instead of individual Plus/Pro pressure.
- Actual semantic/action/response summary: semantic=public_plan_team_context; action=continue_with_session_policy; focus=team_plan_fit; summary=For team use, Business is the self-serve workspace route and Enterprise is for organization-level controls
- Pass: true
- Failures: []
- Actual response: For team use, Business is the self-serve workspace route and Enterprise is for organization-level controls. Are you looking for basic team workspace controls, or Enterprise requirements like SSO, SCIM, procurement, or security review?

### price_terms_caveat

- Buyer utterance: What do Plus and Pro cost right now?
- Expected universal sales behavior: Answer with source-grounded fixture pricing only and caveat that exact prices/terms can change.
- Actual semantic/action/response summary: semantic=public_plan_direct_price_answer; action=continue_with_session_policy; focus=price; summary=Sure
- Pass: true
- Failures: []
- Actual response: Sure. Plus is listed at 20 dollars per month, billed monthly. Pro has 100 dollar and 200 dollar tiers; the main difference is usage allowance. Exact current terms can change, so use the official ChatGPT plans page as the final source for plan fit before you decide. Plus is the lower-cost individual plan; Pro is the heavier-use individual plan.

### privacy_legal_boundary

- Buyer utterance: Can you promise my data is never used and tell me we are legally compliant?
- Expected universal sales behavior: Avoid over-claiming privacy or legal compliance; route the buyer to official OpenAI terms or plan information.
- Actual semantic/action/response summary: semantic=public_plan_legal_security_claim_boundary; action=continue_with_session_policy; focus=claim_boundary; summary=I cannot give a legal or security compliance guarantee
- Pass: true
- Failures: []
- Actual response: I cannot give a legal or security compliance guarantee. Use official OpenAI terms and, for company security or procurement review, the Enterprise contact-sales route.

### competitor_current_tool_gap

- Buyer utterance: I already use Claude and Copilot, so why would I add ChatGPT?
- Expected universal sales behavior: Do not invent superiority; compare ChatGPT only against a concrete current-tool gap.
- Actual semantic/action/response summary: semantic=public_plan_competitor_objection; action=continue_with_session_policy; focus=competitive_objection; summary=A switch only makes sense if ChatGPT covers something your current tool does not: coding workflow, files, research, voice/images, team admin, or privacy controls
- Pass: true
- Failures: []
- Actual response: A switch only makes sense if ChatGPT covers something your current tool does not: coding workflow, files, research, voice/images, team admin, or privacy controls. What is the one area where your current tool feels weakest?

### and_fidelity_chatgpt_and_other_tools

- Buyer utterance: I use ChatGPT and Claude for coding already.
- Expected universal sales behavior: Preserve that the buyer uses ChatGPT and another tool, then ask for the combined setup's gap.
- Actual semantic/action/response summary: semantic=public_plan_current_chatgpt_and_other_ai_user; action=continue_with_session_policy; focus=competitive_objection; summary=Got it - you're using ChatGPT and other AI tools
- Pass: true
- Failures: []
- Actual response: Got it - you're using ChatGPT and other AI tools. The useful comparison is where the current setup still falls short: coding workflow, files, research, writing, voice/images, or team controls.

### or_fidelity_chatgpt_or_other_tools

- Buyer utterance: It might be ChatGPT or Claude; I am not sure which one my team uses.
- Expected universal sales behavior: Preserve uncertainty between ChatGPT or another tool instead of converting it into a definite both-tools claim.
- Actual semantic/action/response summary: semantic=public_plan_current_chatgpt_or_other_ai_unknown; action=continue_with_session_policy; focus=competitive_objection; summary=Got it - sounds like you may be using ChatGPT or maybe Claude
- Pass: true
- Failures: []
- Actual response: Got it - sounds like you may be using ChatGPT or maybe Claude. The useful comparison is where your current setup falls short: coding workflow, files, research, writing, voice/images, or limits.

### repeated_question_loop_repair

- Buyer utterance: I already told you that - what should I compare?
- Expected universal sales behavior: Repair the loop by acknowledging known context and answering shorter/differently instead of repeating discovery.
- Actual semantic/action/response summary: semantic=public_plan_known_use_and_heavy_repeat_progress_already_answered; action=continue_with_session_policy; focus=plan_fit; summary=Since you said heavy coding and writing, Pro is the stronger fit to compare; Plus is the lower-cost starting point
- Pass: true
- Failures: []
- Actual response: Since you said heavy coding and writing, Pro is the stronger fit to compare; Plus is the lower-cost starting point. The next step is the official ChatGPT plans page.

### self_serve_close_no_side_effects

- Buyer utterance: Pro sounds right. How do I sign up?
- Expected universal sales behavior: Close individual paid interest toward the official ChatGPT plan page/profile flow without sending, booking, or taking payment.
- Actual semantic/action/response summary: semantic=public_plan_self_serve_next_step_answered; action=continue_with_session_policy; focus=self_serve_close; summary=Yes - for individual plans, use the official ChatGPT plans page or profile upgrade flow
- Pass: true
- Failures: []
- Actual response: Yes - for individual plans, use the official ChatGPT plans page or profile upgrade flow. Based on what you said - coding/writing and hitting limits - compare Pro first if you want fewer limits; choose Plus if you want the lower-cost starting point.

### no_fit_current_tool_enough

- Buyer utterance: My current tool covers everything and I do not want to pay.
- Expected universal sales behavior: Disqualify paid close when the buyer's current tool covers the work and they do not want to pay.
- Actual semantic/action/response summary: semantic=public_plan_low_unclear_intent; action=continue_with_session_policy; focus=low_intent; summary=No problem
- Pass: true
- Failures: []
- Actual response: No problem. Then I would keep it simple: Free may be enough for light use; paid plans are mainly worth comparing if limits, tools, or team needs matter. I would not push a paid plan; the next action is stay free or stop here.

## Strong Spoken Sales Examples

- `fit_heavy_individual_pro`: Acknowledges the buyer's heavy use and advances to a concrete Plus-vs-Pro decision.
- `competitor_current_tool_gap`: Avoids superiority claims and sells only against a concrete gap in the current tool.
- `self_serve_close_no_side_effects`: Closes to the official self-serve path without pretending to send, book, or collect payment.

## Weak / Passive / FAQ-like Examples

- `source_affiliation_boundary`: Uses boundary-heavy public-data wording; safe, but less natural than a polished live seller.
- `plan_category_explanation`: Category list is accurate and spoken enough, but still close to FAQ structure.

## Residual RouteSignal Contamination Guard

- OpenAI-primary case responses containing RouteSignal/Northstar/inbound-demo/workflow-review/callback/handoff/manual-tracking copy: 0
- OpenAI path source hits are limited to buyer-input boundary triggers, not buyer-facing response copy.
- Generic path source hits are legacy default-playbook guard debt and remain future migration, not 4L2 cleanup scope.
- RouteSignal remains secondary regression fixture only.

## No-side-effect Confirmation

- No live selector control was enabled.
- No response replacement was enabled.
- No provider/model/TTS/CRM/email/calendar/payment/account path was enabled.
- No raw private transcript/audio was added to public evidence.
- No live readiness claim was made.
