# Human Semantic Review Packet 001

## 1. Executive Summary For Reviewer

This packet contains sanitized deterministic sales-agent conversations for manual semantic review. The runtime goal is appointment-setting and lead qualification, not full sale closure. The reviewed agent does not use live LLM final speech here; responses are deterministic runtime outputs. Provider calls, live TTS, email sending, calendar creation, CRM writes, and PROD-102 are disabled.

Judge what the deterministic agent still gets wrong: buyer meaning, next action, appointment pressure, state drift, repeated questions, refusal handling, regulated caution quality, campaign leakage, generic wording quality, and long-conversation realism.

Conversation count: 96
Turn record count: 414

## 2. Review Instructions

For each conversation, score whether the agent understood the buyer, acknowledged correctly, chose the right next action, preserved confirmed and cleared gaps, used appropriate appointment pressure, respected refusal or stop, handled send-info and contact capture safely, handled right-person routing, sounded natural, preserved meaning between final response and TTS text, avoided campaign leakage, handled regulated claims safely, and suggests any new validator case.

## 3. Architecture Snapshot

- `contextual_buyer_semantics`: Deterministic buyer-move and gap classification.
- `dialogue_manager`: Deterministic action planning, memory updates, anti-loop and stability guards.
- `campaign_playbook_adapter`: Resolves RouteSignal or synthetic campaign playbooks.
- `universal_sales_knowledge`: Shared pain and qualification dimensions.
- `vertical_sales_playbooks`: Reusable vertical defaults for generic campaigns.
- `generic_campaign_turn`: Reusable dry-run generic campaign turn packet entrypoint.
- `live_voice_session_policy`: Session policy and fallback wording for live-demo and generic runtime paths.
- `voice_tts_dry_run`: Dry-run voice/TTS text shaping with provider calls disabled.
- `validators`: Deterministic project validators for semantics, memory, generic campaigns, fallback leakage, wording, spoken text, and long conversations.

## 4. Campaign And Vertical Coverage

### b2b_saas - synthetic-b2b-saas-regression-001

- Product/offer: Operations Workflow Review
- Human follow-up owner: implementation specialist
- Appointment target: operations fit review
- RouteSignal-specific terms allowed: False
- Blocked claims: integration guarantee, security guarantee, ROI guarantee
- Diagnostic gaps:
  - `manual_work`: manual work - review focus: manual workflow load
  - `integration_risk`: integration risk - review focus: integration and security review
  - `visibility_gap`: visibility gap - review focus: visibility into workflow status
- Regulated cautions: Specific promises require human review of verified details.; Integration and security claims require technical review.

### insurance - synthetic-insurance-regression-001

- Product/offer: Policy Review Call
- Human follow-up owner: licensed insurance specialist
- Appointment target: licensed coverage review
- RouteSignal-specific terms allowed: False
- Blocked claims: coverage guarantee, claim approval promise, premium guarantee
- Diagnostic gaps:
  - `coverage_fit`: coverage fit - review focus: coverage fit against policy details
  - `premium_or_budget`: premium or budget - review focus: premium and budget pressure
  - `renewal_or_timing`: renewal or timing - review focus: renewal timing and next-step urgency
- Regulated cautions: Specific promises require human review of verified details.; Licensed staff review coverage and policy details.

### telecom - synthetic-telecom-regression-001

- Product/offer: Plan Review Call
- Human follow-up owner: telecom plan specialist
- Appointment target: plan and coverage review
- RouteSignal-specific terms allowed: False
- Blocked claims: coverage guarantee, speed guarantee, contract cancellation promise
- Diagnostic gaps:
  - `coverage_or_availability`: coverage or availability - review focus: coverage and availability fit
  - `plan_fit`: plan fit - review focus: plan fit and usage needs
  - `contract_or_switching`: contract or switching - review focus: contract timing and switching friction
- Regulated cautions: Specific promises require human review of verified details.; Coverage and availability require human review against the current service map.; Account-specific terms require an authorized specialist.

### home_services - synthetic-home-services-regression-001

- Product/offer: Service Estimate Call
- Human follow-up owner: service advisor
- Appointment target: service estimate review
- RouteSignal-specific terms allowed: False
- Blocked claims: exact price without inspection, repair outcome promise
- Diagnostic gaps:
  - `service_need`: service need - review focus: service need and property context
  - `scheduling_urgency`: scheduling urgency - review focus: schedule urgency
  - `estimate_or_property_details`: estimate or property details - review focus: estimate details and property context
- Regulated cautions: Specific promises require human review of verified details.

### healthcare_admin_or_medical_equipment - synthetic-healthcare-admin-regression-001

- Product/offer: Admin Equipment Review
- Human follow-up owner: specialist review coordinator
- Appointment target: specialist admin review
- RouteSignal-specific terms allowed: False
- Blocked claims: clinical advice, equipment outcome guarantee, diagnosis
- Diagnostic gaps:
  - `admin_workflow_need`: admin workflow need - review focus: admin workflow need
  - `equipment_or_service_fit`: equipment or service fit - review focus: equipment or service fit
  - `specialist_review_needed`: specialist review needed - review focus: specialist review need
- Regulated cautions: Specific promises require human review of verified details.

### automotive_service - synthetic-automotive-service-regression-001

- Product/offer: Service Advisor Review
- Human follow-up owner: service advisor
- Appointment target: service advisor inspection review
- RouteSignal-specific terms allowed: False
- Blocked claims: exact diagnosis, guaranteed repair cost, warranty guarantee
- Diagnostic gaps:
  - `vehicle_issue`: vehicle issue - review focus: vehicle issue
  - `repair_timing`: repair timing - review focus: repair timing
  - `warranty_or_estimate`: warranty or estimate - review focus: warranty or estimate
- Regulated cautions: Specific promises require human review of verified details.

### membership_or_subscription - synthetic-membership-regression-001

- Product/offer: Membership Plan Review
- Human follow-up owner: membership specialist
- Appointment target: membership account review
- RouteSignal-specific terms allowed: False
- Blocked claims: hidden cancellation terms, billing outcome promise, guaranteed savings
- Diagnostic gaps:
  - `plan_fit`: plan fit - review focus: plan fit
  - `renewal_or_cancellation`: renewal or cancellation - review focus: renewal or cancellation terms
  - `usage_or_value`: usage or value - review focus: usage and value fit
- Regulated cautions: Specific promises require human review of verified details.

### retail_or_ecommerce_support_sales - synthetic-retail-ecommerce-regression-001

- Product/offer: Product Support Review
- Human follow-up owner: support sales specialist
- Appointment target: product support review
- RouteSignal-specific terms allowed: False
- Blocked claims: refund guarantee, stock guarantee, warranty outcome promise
- Diagnostic gaps:
  - `product_fit`: product fit - review focus: product fit
  - `availability_or_delivery`: availability or delivery - review focus: availability or delivery timing
  - `return_or_warranty`: return or warranty - review focus: return or warranty policy
- Regulated cautions: Specific promises require human review of verified details.

### routesignal_live_demo - campaign-prod-005-b2b-software

- Product/offer: RouteSignal CRM
- Human follow-up owner: verified implementation reviewer
- Appointment target: None
- RouteSignal-specific terms allowed: True
- Blocked claims: None listed
- Diagnostic gaps:
- Regulated cautions: None listed

## 5. Conversation Review Records

### generic-b2b-saas-opening-and-permission-001

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-b2b-saas-regression-001`
- Vertical: `b2b_saas`
- Scenario type: `opening_and_permission`
- Edge buckets: permission_acknowledgement
- Risk tags: baseline
- Expected high-level behavior: Agent opens with campaign-aware reason, then starts one concise diagnostic after permission.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-b2b-saas-current-gap-clear-002

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-b2b-saas-regression-001`
- Vertical: `b2b_saas`
- Scenario type: `current_gap_clear`
- Edge buckets: no_pain_current_issue_clear
- Risk tags: state_memory
- Expected high-level behavior: Agent treats manual work as cleared and asks about remaining campaign gaps.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | manual work is handled | Got it, manual work is clear. Should I check integration risk or visibility gap, or stop here? | Got it, manual work is clear. Should I check integration risk or visibility gap, or stop here? | current_gap_clear | manual_work | manual_work |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "current_gap_clear", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-b2b-saas-pain-confirmed-003

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-b2b-saas-regression-001`
- Vertical: `b2b_saas`
- Scenario type: `pain_confirmed`
- Edge buckets: pain_confirmed
- Risk tags: appointment_pressure
- Expected high-level behavior: Agent confirms the campaign-specific pain and moves toward a human follow-up without full sale closure.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | visibility is the problem | Got it, visibility into workflow status is the real gap. The next step would be a short operations fit review; what time works for that review? | Got it, visibility into workflow status is the real gap. The next step would be a short operations fit review; what time works for that review? | pain_confirmed | visibility_gap |  | visibility_gap | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "pain_confirmed", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-b2b-saas-possible-pain-then-confusion-004

- Source checkpoint: `GENERIC-CAMPAIGN-BUYER-MOVE-PARAPHRASE-001`
- Campaign: `synthetic-b2b-saas-regression-001`
- Vertical: `b2b_saas`
- Scenario type: `possible_pain_then_confusion`
- Edge buckets: possible_pain_ambiguity, confusion
- Risk tags: hard_case, edge_case, wrong_next_action_risk
- Expected high-level behavior: Agent should not create false pain and should clarify the prior diagnostic without appointment pressure.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | okay quick | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | sometimes maybe | I am checking manual work, integration risk, or visibility gap for a possible operations fit review. Which part should I ask about first, if any? | I am checking manual work, integration risk, or visibility gap for a possible operations fit review. Which part should I ask about first, if any? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | what do you mean? | Sorry, I meant the areas in this fit check: manual work, integration risk, or visibility gap. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: manual work, integration risk, or visibility gap. Which part causes trouble, if any? | previous_question_clarification |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "previous_question_clarification", "source": "... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-b2b-saas-send-info-email-capture-005

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-b2b-saas-regression-001`
- Vertical: `b2b_saas`
- Scenario type: `send_info_email_capture`
- Edge buckets: send_info
- Risk tags: hard_case, edge_case, contact_capture
- Expected high-level behavior: Agent opens send-info state, captures redacted email/hash, and does not claim an email was sent.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 2 | yeah sure | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 3 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_request", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 4 | send it to <email:sha256_12:6db61e6dcbcf> | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | email_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "email_provided", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |

### generic-b2b-saas-callback-timing-capture-006

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-b2b-saas-regression-001`
- Vertical: `b2b_saas`
- Scenario type: `callback_timing_capture`
- Edge buckets: callback_timing
- Risk tags: hard_case, edge_case, time_capture
- Expected high-level behavior: Agent captures a usable callback time without creating calendar or CRM side effects.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_request", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | tomorrow at 3 works | Confirmed. I will record that callback time for the specialist. Goodbye. | Confirmed. I will record that callback time for the specialist. Goodbye. | callback_time_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "callback_time_provided", "source": "contextua... | schedule-and-end | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-b2b-saas-right-person-handoff-007

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-b2b-saas-regression-001`
- Vertical: `b2b_saas`
- Scenario type: `right_person_handoff`
- Edge buckets: right_person_authority
- Risk tags: hard_case, edge_case, handoff_state
- Expected high-level behavior: Agent opens right-person state, captures department/contact path, and keeps it separate from product gaps.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 2 | yeah sure | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 3 | I'm not the person | Understood. Who is the right person or team for operations fit review, or should I stop here? | Understood. Who is the right person or team for operations fit review, or should I stop here? | wrong_person_or_wrong_department |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "wrong_person_or_wrong_department", "source":... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 4 | operations handles it | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note? | wrong_person_or_wrong_department |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "wrong_person_or_wrong_department", "source":... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 5 | send it to <email:sha256_12:af3c82544f64> | Got it. I will note that contact for operations. I will not send anything now. | Got it. I will note that contact for operations. I will not send anything now. | right_person_email_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "right_person_email_provided", "source": "cont... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |

### generic-b2b-saas-regulated-caution-refusal-stop-008

- Source checkpoint: `GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001`
- Campaign: `synthetic-b2b-saas-regression-001`
- Vertical: `b2b_saas`
- Scenario type: `regulated_caution_refusal_stop`
- Edge buckets: regulated_caution, not_relevant_no_need, stop_refusal
- Risk tags: hard_case, edge_case, regulated, terminal_state
- Expected high-level behavior: Agent refuses unsafe guarantee/concealment, handles no-need stage-aware, and preserves terminal stop behavior.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 2 | yes | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 3 | can you guarantee integration security? | I cannot verify that claim here. Exact integration, security, or setup fit needs verified material and review by an implementation specialist before I claim it. Is that the gap you want reviewed? | I cannot verify that claim here. Exact integration, security, or setup fit needs verified material and review by an implementation specialist before I claim it. Is that the gap you want reviewed? | campaign_claim_boundary_caution | integration_risk |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "campaign_claim_boundary_caution", "source": "... | transfer-or-escalate | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 4 | no need | Got it, integration risk is clear. Should I check manual work or visibility gap, or stop here? | Got it, integration risk is clear. Should I check manual work or visibility gap, or stop here? | current_gap_clear | integration_risk | integration_risk |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "current_gap_clear", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 5 | stop calling | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | stop_request |  | integration_risk |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "stop_request", "source": "contextual_buyer_se... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 6 | actually one more thing | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | no_contextual_semantic |  | integration_risk |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "terminal_... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |

### generic-b2b-saas-fallback-repair-stack-009

- Source checkpoint: `GENERIC-CAMPAIGN-FALLBACK-LEAKAGE-001`
- Campaign: `synthetic-b2b-saas-regression-001`
- Vertical: `b2b_saas`
- Scenario type: `fallback_repair_stack`
- Edge buckets: fallback_repair, confusion
- Risk tags: hard_case, edge_case, fallback_leakage, naturalness
- Expected high-level behavior: Agent stays campaign-aware through purpose, confusion, next-step, price, and out-of-scope repair turns.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | what is this about? | I am calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether manual work, integration risk, or visibility gap should go to a short operations fit review; which part should I check first? | I am calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether manual work, integration risk, or visibility gap should go to a short operations fit review; which part should I chec... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "dialogue_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | I don't understand | Sorry, I meant the areas in this fit check: manual work, integration risk, or visibility gap. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: manual work, integration risk, or visibility gap. Which part causes trouble, if any? | confusion_not_clear |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "confusion_not_clear", "source": "contextual_b... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 5 | what happens next? | I am checking manual work, integration risk, or visibility gap for a possible operations fit review. Which part should I ask about first, if any? | I am checking manual work, integration risk, or visibility gap for a possible operations fit review. Which part should I ask about first, if any? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 6 | is it expensive? | I do not have approved pricing to quote here. An implementation specialist should confirm cost and terms before any next step. | I do not have approved pricing to quote here. An implementation specialist should confirm cost and terms before any next step. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 7 | can you help with my password? | The next step would be a short operations fit review. An implementation specialist can review the details, or I can stop here. | The next step would be a short operations fit review. An implementation specialist can review the details, or I can stop here. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-b2b-saas-long-mixed-state-drift-010

- Source checkpoint: `GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001`
- Campaign: `synthetic-b2b-saas-regression-001`
- Vertical: `b2b_saas`
- Scenario type: `long_mixed_state_drift`
- Edge buckets: long_conversation_state_drift
- Risk tags: hard_case, edge_case, state_drift, duplicate_question_risk
- Expected high-level behavior: Agent should preserve cleared/confirmed/contact/terminal state across a realistic longer conversation.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah go ahead | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | I do not handle this | Understood. Who is the right person or team for operations fit review, or should I stop here? | Understood. Who is the right person or team for operations fit review, or should I stop here? | wrong_person_or_wrong_department |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "wrong_person_or_wrong_department", "source":... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | operations handles it | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note? | wrong_person_or_wrong_department |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "wrong_person_or_wrong_department", "source":... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 5 | send it to <email:sha256_12:af3c82544f64> | Got it. I will note that contact for operations. I will not send anything now. | Got it. I will note that contact for operations. I will not send anything now. | right_person_email_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "right_person_email_provided", "source": "cont... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 6 | can you help with my password? | I cannot help with account support on this call. I can only note operations for operations fit review, or stop here. | I cannot help with account support on this call. I can only note operations for operations fit review, or stop here. | handoff_support_boundary |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "handoff_support_boundary", "source": "context... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-insurance-opening-and-permission-001

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-insurance-regression-001`
- Vertical: `insurance`
- Scenario type: `opening_and_permission`
- Edge buckets: permission_acknowledgement
- Risk tags: baseline
- Expected high-level behavior: Agent opens with campaign-aware reason, then starts one concise diagnostic after permission.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-insurance-current-gap-clear-002

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-insurance-regression-001`
- Vertical: `insurance`
- Scenario type: `current_gap_clear`
- Edge buckets: no_pain_current_issue_clear
- Risk tags: state_memory
- Expected high-level behavior: Agent treats coverage fit as cleared and asks about remaining campaign gaps.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | coverage fit is handled | Got it, coverage fit is clear. Should I check premium or budget or renewal or timing, or stop here? | Got it, coverage fit is clear. Should I check premium or budget or renewal or timing, or stop here? | current_gap_clear | coverage_fit | coverage_fit |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "current_gap_clear", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-insurance-pain-confirmed-003

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-insurance-regression-001`
- Vertical: `insurance`
- Scenario type: `pain_confirmed`
- Edge buckets: pain_confirmed
- Risk tags: appointment_pressure
- Expected high-level behavior: Agent confirms the campaign-specific pain and moves toward a human follow-up without full sale closure.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | premium is a problem | Got it, premium and budget pressure is the real gap. The next step would be a short licensed coverage review; what time works for that review? | Got it, premium and budget pressure is the real gap. The next step would be a short licensed coverage review; what time works for that review? | pain_confirmed | premium_or_budget |  | premium_or_budget | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "pain_confirmed", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-insurance-possible-pain-then-confusion-004

- Source checkpoint: `GENERIC-CAMPAIGN-BUYER-MOVE-PARAPHRASE-001`
- Campaign: `synthetic-insurance-regression-001`
- Vertical: `insurance`
- Scenario type: `possible_pain_then_confusion`
- Edge buckets: possible_pain_ambiguity, confusion
- Risk tags: hard_case, edge_case, wrong_next_action_risk
- Expected high-level behavior: Agent should not create false pain and should clarify the prior diagnostic without appointment pressure.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | okay quick | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | sometimes maybe | I am checking coverage fit, premium or budget, or renewal or timing for a possible licensed coverage review. Which part should I ask about first, if any? | I am checking coverage fit, premium or budget, or renewal or timing for a possible licensed coverage review. Which part should I ask about first, if any? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | what do you mean? | Sorry, I meant the areas in this fit check: coverage fit, premium or budget, or renewal or timing. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: coverage fit, premium or budget, or renewal or timing. Which part causes trouble, if any? | previous_question_clarification |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "previous_question_clarification", "source": "... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-insurance-send-info-email-capture-005

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-insurance-regression-001`
- Vertical: `insurance`
- Scenario type: `send_info_email_capture`
- Edge buckets: send_info
- Risk tags: hard_case, edge_case, contact_capture
- Expected high-level behavior: Agent opens send-info state, captures redacted email/hash, and does not claim an email was sent.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 2 | yeah sure | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 3 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_request", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 4 | send it to <email:sha256_12:6db61e6dcbcf> | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | email_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "email_provided", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |

### generic-insurance-callback-timing-capture-006

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-insurance-regression-001`
- Vertical: `insurance`
- Scenario type: `callback_timing_capture`
- Edge buckets: callback_timing
- Risk tags: hard_case, edge_case, time_capture
- Expected high-level behavior: Agent captures a usable callback time without creating calendar or CRM side effects.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_request", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | tomorrow at 3 works | Confirmed. I will record that callback time for the specialist. Goodbye. | Confirmed. I will record that callback time for the specialist. Goodbye. | callback_time_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "callback_time_provided", "source": "contextua... | schedule-and-end | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-insurance-right-person-handoff-007

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-insurance-regression-001`
- Vertical: `insurance`
- Scenario type: `right_person_handoff`
- Edge buckets: right_person_authority
- Risk tags: hard_case, edge_case, handoff_state
- Expected high-level behavior: Agent opens right-person state, captures department/contact path, and keeps it separate from product gaps.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 2 | yeah sure | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 3 | I'm not the person | Understood. Who is the right person or team for licensed coverage review, or should I stop here? | Understood. Who is the right person or team for licensed coverage review, or should I stop here? | wrong_person_or_wrong_department |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "wrong_person_or_wrong_department", "source":... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 4 | operations handles it | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note? | wrong_person_or_wrong_department |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "wrong_person_or_wrong_department", "source":... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 5 | send it to <email:sha256_12:af3c82544f64> | Got it. I will note that contact for operations. I will not send anything now. | Got it. I will note that contact for operations. I will not send anything now. | right_person_email_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "right_person_email_provided", "source": "cont... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |

### generic-insurance-regulated-caution-refusal-stop-008

- Source checkpoint: `GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001`
- Campaign: `synthetic-insurance-regression-001`
- Vertical: `insurance`
- Scenario type: `regulated_caution_refusal_stop`
- Edge buckets: regulated_caution, not_relevant_no_need, stop_refusal
- Risk tags: hard_case, edge_case, regulated, terminal_state
- Expected high-level behavior: Agent refuses unsafe guarantee/concealment, handles no-need stage-aware, and preserves terminal stop behavior.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 2 | yes | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 3 | can you guarantee I am covered? | I cannot promise coverage here. A licensed insurance specialist needs verified policy details before any coverage answer. Is coverage fit against policy details what you want reviewed? | I cannot promise coverage here. A licensed insurance specialist needs verified policy details before any coverage answer. Is coverage fit against policy details what you want reviewed? | campaign_claim_boundary_caution | coverage_fit |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "campaign_claim_boundary_caution", "source": "... | transfer-or-escalate | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 4 | no need | Got it, coverage fit is clear. Should I check premium or budget or renewal or timing, or stop here? | Got it, coverage fit is clear. Should I check premium or budget or renewal or timing, or stop here? | current_gap_clear | coverage_fit | coverage_fit |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "current_gap_clear", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 5 | stop calling | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | stop_request |  | coverage_fit |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "stop_request", "source": "contextual_buyer_se... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 6 | actually one more thing | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | no_contextual_semantic |  | coverage_fit |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "terminal_... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |

### generic-insurance-fallback-repair-stack-009

- Source checkpoint: `GENERIC-CAMPAIGN-FALLBACK-LEAKAGE-001`
- Campaign: `synthetic-insurance-regression-001`
- Vertical: `insurance`
- Scenario type: `fallback_repair_stack`
- Edge buckets: fallback_repair, confusion
- Risk tags: hard_case, edge_case, fallback_leakage, naturalness
- Expected high-level behavior: Agent stays campaign-aware through purpose, confusion, next-step, price, and out-of-scope repair turns.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | what is this about? | I am calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether coverage fit, premium or budget, or renewal or timing should go to a short licensed coverage review; which part should I check first? | I am calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether coverage fit, premium or budget, or renewal or timing should go to a short licensed coverage review; which part should I che... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "dialogue_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | I don't understand | Sorry, I meant the areas in this fit check: coverage fit, premium or budget, or renewal or timing. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: coverage fit, premium or budget, or renewal or timing. Which part causes trouble, if any? | confusion_not_clear |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "confusion_not_clear", "source": "contextual_b... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 5 | what happens next? | I am checking coverage fit, premium or budget, or renewal or timing for a possible licensed coverage review. Which part should I ask about first, if any? | I am checking coverage fit, premium or budget, or renewal or timing for a possible licensed coverage review. Which part should I ask about first, if any? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 6 | is it expensive? | I do not have approved pricing to quote here. A licensed insurance specialist should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A licensed insurance specialist should confirm cost and terms before any next step. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 7 | can you help with my password? | The next step would be a short licensed coverage review. A licensed insurance specialist can review the details, or I can stop here. | The next step would be a short licensed coverage review. A licensed insurance specialist can review the details, or I can stop here. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-insurance-long-mixed-state-drift-010

- Source checkpoint: `GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001`
- Campaign: `synthetic-insurance-regression-001`
- Vertical: `insurance`
- Scenario type: `long_mixed_state_drift`
- Edge buckets: long_conversation_state_drift
- Risk tags: hard_case, edge_case, state_drift, duplicate_question_risk
- Expected high-level behavior: Agent should preserve cleared/confirmed/contact/terminal state across a realistic longer conversation.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | coverage fit is handled | Got it, coverage fit is clear. Should I check premium or budget or renewal or timing, or stop here? | Got it, coverage fit is clear. Should I check premium or budget or renewal or timing, or stop here? | current_gap_clear | coverage_fit | coverage_fit |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "current_gap_clear", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | premium is a problem | Got it, premium and budget pressure is the real gap. The next step would be a short licensed coverage review; what time works for that review? | Got it, premium and budget pressure is the real gap. The next step would be a short licensed coverage review; what time works for that review? | pain_confirmed | premium_or_budget | coverage_fit | premium_or_budget | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "pain_confirmed", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 5 | send me details first | No problem. I can send a short summary focused on premium and budget pressure. What email or callback time should I note? | No problem. I can send a short summary focused on premium and budget pressure. What email or callback time should I note? | send_info_with_confirmed_pain | premium_or_budget | coverage_fit | premium_or_budget | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_with_confirmed_pain", "source": "co... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 6 | send it to <email:sha256_12:6db61e6dcbcf> | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | email_provided |  | coverage_fit | premium_or_budget | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "email_provided", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 7 | what happens next? | That sounds like the area to review, so the next step would be a short licensed coverage review. A licensed insurance specialist can review premium and budget pressure against the details; what time works? | That sounds like the area to review, so the next step would be a short licensed coverage review. A licensed insurance specialist can review premium and budget pressure against the details; what time works? | no_contextual_semantic |  | coverage_fit | premium_or_budget | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "dialogue_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-telecom-opening-and-permission-001

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-telecom-regression-001`
- Vertical: `telecom`
- Scenario type: `opening_and_permission`
- Edge buckets: permission_acknowledgement
- Risk tags: baseline
- Expected high-level behavior: Agent opens with campaign-aware reason, then starts one concise diagnostic after permission.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-telecom-current-gap-clear-002

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-telecom-regression-001`
- Vertical: `telecom`
- Scenario type: `current_gap_clear`
- Edge buckets: no_pain_current_issue_clear
- Risk tags: state_memory
- Expected high-level behavior: Agent treats coverage or availability as cleared and asks about remaining campaign gaps.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | coverage is fine | Got it, coverage or availability is clear. Should I check plan fit or contract or switching, or stop here? | Got it, coverage or availability is clear. Should I check plan fit or contract or switching, or stop here? | current_gap_clear | coverage_or_availability | coverage_or_availability |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "current_gap_clear", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-telecom-pain-confirmed-003

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-telecom-regression-001`
- Vertical: `telecom`
- Scenario type: `pain_confirmed`
- Edge buckets: pain_confirmed
- Risk tags: appointment_pressure
- Expected high-level behavior: Agent confirms the campaign-specific pain and moves toward a human follow-up without full sale closure.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | coverage is the issue | Got it, coverage and availability fit is the real gap. The next step would be a short plan and coverage review; what time works for that review? | Got it, coverage and availability fit is the real gap. The next step would be a short plan and coverage review; what time works for that review? | pain_confirmed | coverage_or_availability |  | coverage_or_availability | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "pain_confirmed", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-telecom-possible-pain-then-confusion-004

- Source checkpoint: `GENERIC-CAMPAIGN-BUYER-MOVE-PARAPHRASE-001`
- Campaign: `synthetic-telecom-regression-001`
- Vertical: `telecom`
- Scenario type: `possible_pain_then_confusion`
- Edge buckets: possible_pain_ambiguity, confusion
- Risk tags: hard_case, edge_case, wrong_next_action_risk
- Expected high-level behavior: Agent should not create false pain and should clarify the prior diagnostic without appointment pressure.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | okay quick | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | sometimes maybe | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. Which part should I ask about first, if any? | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. Which part should I ask about first, if any? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | what do you mean? | Sorry, I meant the areas in this fit check: coverage or availability, plan fit, or contract or switching. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: coverage or availability, plan fit, or contract or switching. Which part causes trouble, if any? | previous_question_clarification |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "previous_question_clarification", "source": "... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-telecom-send-info-email-capture-005

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-telecom-regression-001`
- Vertical: `telecom`
- Scenario type: `send_info_email_capture`
- Edge buckets: send_info
- Risk tags: hard_case, edge_case, contact_capture
- Expected high-level behavior: Agent opens send-info state, captures redacted email/hash, and does not claim an email was sent.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 2 | yeah sure | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 3 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_request", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 4 | send it to <email:sha256_12:6db61e6dcbcf> | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | email_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "email_provided", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |

### generic-telecom-callback-timing-capture-006

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-telecom-regression-001`
- Vertical: `telecom`
- Scenario type: `callback_timing_capture`
- Edge buckets: callback_timing
- Risk tags: hard_case, edge_case, time_capture
- Expected high-level behavior: Agent captures a usable callback time without creating calendar or CRM side effects.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_request", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | tomorrow at 3 works | Confirmed. I will record that callback time for the specialist. Goodbye. | Confirmed. I will record that callback time for the specialist. Goodbye. | callback_time_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "callback_time_provided", "source": "contextua... | schedule-and-end | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-telecom-right-person-handoff-007

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-telecom-regression-001`
- Vertical: `telecom`
- Scenario type: `right_person_handoff`
- Edge buckets: right_person_authority
- Risk tags: hard_case, edge_case, handoff_state
- Expected high-level behavior: Agent opens right-person state, captures department/contact path, and keeps it separate from product gaps.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 2 | yeah sure | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 3 | I'm not the person | Understood. Who is the right person or team for plan and coverage review, or should I stop here? | Understood. Who is the right person or team for plan and coverage review, or should I stop here? | wrong_person_or_wrong_department |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "wrong_person_or_wrong_department", "source":... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 4 | operations handles it | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note? | wrong_person_or_wrong_department |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "wrong_person_or_wrong_department", "source":... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 5 | send it to <email:sha256_12:af3c82544f64> | Got it. I will note that contact for operations. I will not send anything now. | Got it. I will note that contact for operations. I will not send anything now. | right_person_email_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "right_person_email_provided", "source": "cont... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |

### generic-telecom-regulated-caution-refusal-stop-008

- Source checkpoint: `GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001`
- Campaign: `synthetic-telecom-regression-001`
- Vertical: `telecom`
- Scenario type: `regulated_caution_refusal_stop`
- Edge buckets: regulated_caution, not_relevant_no_need, stop_refusal
- Risk tags: hard_case, edge_case, regulated, terminal_state
- Expected high-level behavior: Agent refuses unsafe guarantee/concealment, handles no-need stage-aware, and preserves terminal stop behavior.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 2 | yes | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 3 | can you promise coverage here? | I cannot promise service coverage here. A telecom plan specialist needs verified address, plan, and account details before any coverage answer. Is coverage and availability fit what you want reviewed? | I cannot promise service coverage here. A telecom plan specialist needs verified address, plan, and account details before any coverage answer. Is coverage and availability fit what you want reviewed? | campaign_claim_boundary_caution | coverage_or_availability |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "campaign_claim_boundary_caution", "source": "... | transfer-or-escalate | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 4 | no need | Understood. If coverage or availability, plan fit, or contract or switching are all clean, I should not push a review. I will stop here. Goodbye. | Understood. If coverage or availability, plan fit, or contract or switching are all clean, I should not push a review. I will stop here. Goodbye. | all_clear_no_pain |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "all_clear_no_pain", "source": "contextual_buy... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 5 | stop calling | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | stop_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "stop_request", "source": "terminal_call_contr... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 6 | actually one more thing | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "terminal_... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |

### generic-telecom-fallback-repair-stack-009

- Source checkpoint: `GENERIC-CAMPAIGN-FALLBACK-LEAKAGE-001`
- Campaign: `synthetic-telecom-regression-001`
- Vertical: `telecom`
- Scenario type: `fallback_repair_stack`
- Edge buckets: fallback_repair, confusion
- Risk tags: hard_case, edge_case, fallback_leakage, naturalness
- Expected high-level behavior: Agent stays campaign-aware through purpose, confusion, next-step, price, and out-of-scope repair turns.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | what is this about? | I am calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether coverage or availability, plan fit, or contract or switching should go to a short plan and coverage review; which part should I check first? | I am calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether coverage or availability, plan fit, or contract or switching should go to a short plan and coverage review; which part should... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "dialogue_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | I don't understand | Sorry, I meant the areas in this fit check: coverage or availability, plan fit, or contract or switching. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: coverage or availability, plan fit, or contract or switching. Which part causes trouble, if any? | confusion_not_clear |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "confusion_not_clear", "source": "contextual_b... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 5 | what happens next? | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. Which part should I ask about first, if any? | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. Which part should I ask about first, if any? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 6 | is it expensive? | I do not have approved pricing to quote here. A telecom plan specialist should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A telecom plan specialist should confirm cost and terms before any next step. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 7 | can you help with my password? | The next step would be a short plan and coverage review. A telecom plan specialist can review the details, or I can stop here. | The next step would be a short plan and coverage review. A telecom plan specialist can review the details, or I can stop here. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-telecom-long-mixed-state-drift-010

- Source checkpoint: `GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001`
- Campaign: `synthetic-telecom-regression-001`
- Vertical: `telecom`
- Scenario type: `long_mixed_state_drift`
- Edge buckets: long_conversation_state_drift
- Risk tags: hard_case, edge_case, state_drift, duplicate_question_risk
- Expected high-level behavior: Agent should preserve cleared/confirmed/contact/terminal state across a realistic longer conversation.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | okay quick | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | coverage is sometimes an issue | Got it, coverage and availability fit is the real gap. The next step would be a short plan and coverage review; what time works for that review? | Got it, coverage and availability fit is the real gap. The next step would be a short plan and coverage review; what time works for that review? | pain_confirmed | coverage_or_availability |  | coverage_or_availability | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "pain_confirmed", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | what do you mean? | Sorry, I meant the areas in this fit check: coverage or availability, plan fit, or contract or switching. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: coverage or availability, plan fit, or contract or switching. Which part causes trouble, if any? | previous_question_clarification |  |  | coverage_or_availability | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "previous_question_clarification", "source": "... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 5 | coverage is the issue | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. Which part should I ask about first, if any? | I am checking coverage or availability, plan fit, or contract or switching for a possible plan and coverage review. Which part should I ask about first, if any? | pain_confirmed | coverage_or_availability |  | coverage_or_availability | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "pain_confirmed", "source": "duplicate_respons... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 6 | call me next Tuesday at 10 | Confirmed. I will note that time for the plan and coverage review. Goodbye. | Confirmed. I will note that time for the plan and coverage review. Goodbye. | appointment_time_given | coverage_or_availability |  | coverage_or_availability | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "appointment_time_given", "source": "contextua... | schedule-and-end | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-home-services-opening-and-permission-001

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-home-services-regression-001`
- Vertical: `home_services`
- Scenario type: `opening_and_permission`
- Edge buckets: permission_acknowledgement
- Risk tags: baseline
- Expected high-level behavior: Agent opens with campaign-aware reason, then starts one concise diagnostic after permission.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-home-services-current-gap-clear-002

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-home-services-regression-001`
- Vertical: `home_services`
- Scenario type: `current_gap_clear`
- Edge buckets: no_pain_current_issue_clear
- Risk tags: state_memory
- Expected high-level behavior: Agent treats service need as cleared and asks about remaining campaign gaps.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | scheduling is fine | Got it, scheduling urgency is clear. Should I check service need or estimate or property details, or stop here? | Got it, scheduling urgency is clear. Should I check service need or estimate or property details, or stop here? | current_gap_clear | scheduling_urgency | scheduling_urgency |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "current_gap_clear", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-home-services-pain-confirmed-003

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-home-services-regression-001`
- Vertical: `home_services`
- Scenario type: `pain_confirmed`
- Edge buckets: pain_confirmed
- Risk tags: appointment_pressure
- Expected high-level behavior: Agent confirms the campaign-specific pain and moves toward a human follow-up without full sale closure.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | estimate is unclear | Got it, estimate details and property context is the real gap. The next step would be a short service estimate review; what time works for that review? | Got it, estimate details and property context is the real gap. The next step would be a short service estimate review; what time works for that review? | pain_confirmed | estimate_or_property_details |  | estimate_or_property_details | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "pain_confirmed", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-home-services-possible-pain-then-confusion-004

- Source checkpoint: `GENERIC-CAMPAIGN-BUYER-MOVE-PARAPHRASE-001`
- Campaign: `synthetic-home-services-regression-001`
- Vertical: `home_services`
- Scenario type: `possible_pain_then_confusion`
- Edge buckets: possible_pain_ambiguity, confusion
- Risk tags: hard_case, edge_case, wrong_next_action_risk
- Expected high-level behavior: Agent should not create false pain and should clarify the prior diagnostic without appointment pressure.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | okay quick | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | sometimes maybe | I am checking service need, scheduling urgency, or estimate or property details for a possible service estimate review. Which part should I ask about first, if any? | I am checking service need, scheduling urgency, or estimate or property details for a possible service estimate review. Which part should I ask about first, if any? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | what do you mean? | Sorry, I meant the areas in this fit check: service need, scheduling urgency, or estimate or property details. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: service need, scheduling urgency, or estimate or property details. Which part causes trouble, if any? | previous_question_clarification |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "previous_question_clarification", "source": "... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-home-services-send-info-email-capture-005

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-home-services-regression-001`
- Vertical: `home_services`
- Scenario type: `send_info_email_capture`
- Edge buckets: send_info
- Risk tags: hard_case, edge_case, contact_capture
- Expected high-level behavior: Agent opens send-info state, captures redacted email/hash, and does not claim an email was sent.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 2 | yeah sure | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 3 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_request", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 4 | send it to <email:sha256_12:6db61e6dcbcf> | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | email_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "email_provided", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |

### generic-home-services-callback-timing-capture-006

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-home-services-regression-001`
- Vertical: `home_services`
- Scenario type: `callback_timing_capture`
- Edge buckets: callback_timing
- Risk tags: hard_case, edge_case, time_capture
- Expected high-level behavior: Agent captures a usable callback time without creating calendar or CRM side effects.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_request", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | tomorrow at 3 works | Confirmed. I will record that callback time for the specialist. Goodbye. | Confirmed. I will record that callback time for the specialist. Goodbye. | callback_time_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "callback_time_provided", "source": "contextua... | schedule-and-end | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-home-services-right-person-handoff-007

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-home-services-regression-001`
- Vertical: `home_services`
- Scenario type: `right_person_handoff`
- Edge buckets: right_person_authority
- Risk tags: hard_case, edge_case, handoff_state
- Expected high-level behavior: Agent opens right-person state, captures department/contact path, and keeps it separate from product gaps.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 2 | yeah sure | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 3 | I'm not the person | Understood. Who is the right person or team for service estimate review, or should I stop here? | Understood. Who is the right person or team for service estimate review, or should I stop here? | wrong_person_or_wrong_department |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "wrong_person_or_wrong_department", "source":... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 4 | operations handles it | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note? | wrong_person_or_wrong_department |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "wrong_person_or_wrong_department", "source":... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 5 | send it to <email:sha256_12:af3c82544f64> | Got it. I will note that contact for operations. I will not send anything now. | Got it. I will note that contact for operations. I will not send anything now. | right_person_email_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "right_person_email_provided", "source": "cont... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |

### generic-home-services-regulated-caution-refusal-stop-008

- Source checkpoint: `GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001`
- Campaign: `synthetic-home-services-regression-001`
- Vertical: `home_services`
- Scenario type: `regulated_caution_refusal_stop`
- Edge buckets: regulated_caution, not_relevant_no_need, stop_refusal
- Risk tags: hard_case, edge_case, regulated, terminal_state
- Expected high-level behavior: Agent refuses unsafe guarantee/concealment, handles no-need stage-aware, and preserves terminal stop behavior.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 2 | yes | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 3 | can you quote exact price now? | I cannot give an exact price without property details or inspection. A service advisor needs verified details before quoting. Is estimate details and property context what you want reviewed? | I cannot give an exact price without property details or inspection. A service advisor needs verified details before quoting. Is estimate details and property context what you want reviewed? | campaign_claim_boundary_caution | estimate_or_property_details |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "campaign_claim_boundary_caution", "source": "... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 4 | no need | Got it, service need is clear. Should I check estimate or property details, or stop here? | Got it, service need is clear. Should I check estimate or property details, or stop here? | current_gap_clear | service_need | service_need |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "current_gap_clear", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 5 | stop calling | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | stop_request |  | service_need |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "stop_request", "source": "contextual_buyer_se... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 6 | actually one more thing | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | no_contextual_semantic |  | service_need |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "terminal_... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |

### generic-home-services-fallback-repair-stack-009

- Source checkpoint: `GENERIC-CAMPAIGN-FALLBACK-LEAKAGE-001`
- Campaign: `synthetic-home-services-regression-001`
- Vertical: `home_services`
- Scenario type: `fallback_repair_stack`
- Edge buckets: fallback_repair, confusion
- Risk tags: hard_case, edge_case, fallback_leakage, naturalness
- Expected high-level behavior: Agent stays campaign-aware through purpose, confusion, next-step, price, and out-of-scope repair turns.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | what is this about? | I am calling from Synthetic Home Services about Service Estimate Call. I am checking whether service need, scheduling urgency, or estimate or property details should go to a short service estimate review; which part should I check first? | I am calling from Synthetic Home Services about Service Estimate Call. I am checking whether service need, scheduling urgency, or estimate or property details should go to a short service estimate review; which part s... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "dialogue_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | I don't understand | Sorry, I meant the areas in this fit check: service need, scheduling urgency, or estimate or property details. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: service need, scheduling urgency, or estimate or property details. Which part causes trouble, if any? | confusion_not_clear |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "confusion_not_clear", "source": "contextual_b... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 5 | what happens next? | I am checking service need, scheduling urgency, or estimate or property details for a possible service estimate review. Which part should I ask about first, if any? | I am checking service need, scheduling urgency, or estimate or property details for a possible service estimate review. Which part should I ask about first, if any? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 6 | is it expensive? | I do not have approved pricing to quote here. A service advisor should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A service advisor should confirm cost and terms before any next step. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 7 | can you help with my password? | The next step would be a short service estimate review. A service advisor can review the details, or I can stop here. | The next step would be a short service estimate review. A service advisor can review the details, or I can stop here. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-home-services-long-mixed-state-drift-010

- Source checkpoint: `GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001`
- Campaign: `synthetic-home-services-regression-001`
- Vertical: `home_services`
- Scenario type: `long_mixed_state_drift`
- Edge buckets: long_conversation_state_drift
- Risk tags: hard_case, edge_case, state_drift, duplicate_question_risk
- Expected high-level behavior: Agent should preserve cleared/confirmed/contact/terminal state across a realistic longer conversation.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yes | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | can you quote exact price now? | I cannot give an exact price without property details or inspection. A service advisor needs verified details before quoting. Is estimate details and property context what you want reviewed? | I cannot give an exact price without property details or inspection. A service advisor needs verified details before quoting. Is estimate details and property context what you want reviewed? | campaign_claim_boundary_caution | estimate_or_property_details |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "campaign_claim_boundary_caution", "source": "... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | no need | Got it, service need is clear. Should I check estimate or property details, or stop here? | Got it, service need is clear. Should I check estimate or property details, or stop here? | current_gap_clear | service_need | service_need |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "current_gap_clear", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 5 | stop calling | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | stop_request |  | service_need |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "stop_request", "source": "contextual_buyer_se... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 6 | actually one more thing | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | no_contextual_semantic |  | service_need |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "terminal_... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-healthcare-admin-or-medical-equipment-opening-and-permission-001

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-healthcare-admin-regression-001`
- Vertical: `healthcare_admin_or_medical_equipment`
- Scenario type: `opening_and_permission`
- Edge buckets: permission_acknowledgement
- Risk tags: baseline
- Expected high-level behavior: Agent opens with campaign-aware reason, then starts one concise diagnostic after permission.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-healthcare-admin-or-medical-equipment-current-gap-clear-002

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-healthcare-admin-regression-001`
- Vertical: `healthcare_admin_or_medical_equipment`
- Scenario type: `current_gap_clear`
- Edge buckets: no_pain_current_issue_clear
- Risk tags: state_memory
- Expected high-level behavior: Agent treats admin workflow need as cleared and asks about remaining campaign gaps.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | equipment fit is handled | Got it, equipment or service fit is clear. Should I check admin workflow need or specialist review needed, or stop here? | Got it, equipment or service fit is clear. Should I check admin workflow need or specialist review needed, or stop here? | current_gap_clear | equipment_or_service_fit | equipment_or_service_fit |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "current_gap_clear", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-healthcare-admin-or-medical-equipment-pain-confirmed-003

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-healthcare-admin-regression-001`
- Vertical: `healthcare_admin_or_medical_equipment`
- Scenario type: `pain_confirmed`
- Edge buckets: pain_confirmed
- Risk tags: appointment_pressure
- Expected high-level behavior: Agent confirms the campaign-specific pain and moves toward a human follow-up without full sale closure.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | specialist review is needed | Got it, specialist review need is the real gap. The next step would be a short specialist admin review; what time works for that review? | Got it, specialist review need is the real gap. The next step would be a short specialist admin review; what time works for that review? | pain_confirmed | specialist_review_needed |  | specialist_review_needed | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "pain_confirmed", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-healthcare-admin-or-medical-equipment-possible-pain-then-confusion-004

- Source checkpoint: `GENERIC-CAMPAIGN-BUYER-MOVE-PARAPHRASE-001`
- Campaign: `synthetic-healthcare-admin-regression-001`
- Vertical: `healthcare_admin_or_medical_equipment`
- Scenario type: `possible_pain_then_confusion`
- Edge buckets: possible_pain_ambiguity, confusion
- Risk tags: hard_case, edge_case, wrong_next_action_risk
- Expected high-level behavior: Agent should not create false pain and should clarify the prior diagnostic without appointment pressure.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | okay quick | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | sometimes maybe | I am checking admin workflow need, equipment or service fit, or specialist review needed for a possible specialist admin review. Which part should I ask about first, if any? | I am checking admin workflow need, equipment or service fit, or specialist review needed for a possible specialist admin review. Which part should I ask about first, if any? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | what do you mean? | Sorry, I meant the areas in this fit check: admin workflow need, equipment or service fit, or specialist review needed. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: admin workflow need, equipment or service fit, or specialist review needed. Which part causes trouble, if any? | previous_question_clarification |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "previous_question_clarification", "source": "... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-healthcare-admin-or-medical-equipment-send-info-email-capture-005

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-healthcare-admin-regression-001`
- Vertical: `healthcare_admin_or_medical_equipment`
- Scenario type: `send_info_email_capture`
- Edge buckets: send_info
- Risk tags: hard_case, edge_case, contact_capture
- Expected high-level behavior: Agent opens send-info state, captures redacted email/hash, and does not claim an email was sent.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 2 | yeah sure | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 3 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_request", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 4 | send it to <email:sha256_12:6db61e6dcbcf> | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | email_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "email_provided", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |

### generic-healthcare-admin-or-medical-equipment-callback-timing-capture-006

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-healthcare-admin-regression-001`
- Vertical: `healthcare_admin_or_medical_equipment`
- Scenario type: `callback_timing_capture`
- Edge buckets: callback_timing
- Risk tags: hard_case, edge_case, time_capture
- Expected high-level behavior: Agent captures a usable callback time without creating calendar or CRM side effects.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_request", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | tomorrow at 3 works | Confirmed. I will record that callback time for the specialist. Goodbye. | Confirmed. I will record that callback time for the specialist. Goodbye. | callback_time_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "callback_time_provided", "source": "contextua... | schedule-and-end | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-healthcare-admin-or-medical-equipment-right-person-handoff-007

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-healthcare-admin-regression-001`
- Vertical: `healthcare_admin_or_medical_equipment`
- Scenario type: `right_person_handoff`
- Edge buckets: right_person_authority
- Risk tags: hard_case, edge_case, handoff_state
- Expected high-level behavior: Agent opens right-person state, captures department/contact path, and keeps it separate from product gaps.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 2 | yeah sure | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 3 | I'm not the person | Understood. Who is the right person or team for specialist admin review, or should I stop here? | Understood. Who is the right person or team for specialist admin review, or should I stop here? | wrong_person_or_wrong_department |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "wrong_person_or_wrong_department", "source":... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 4 | operations handles it | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note? | wrong_person_or_wrong_department |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "wrong_person_or_wrong_department", "source":... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 5 | send it to <email:sha256_12:af3c82544f64> | Got it. I will note that contact for operations. I will not send anything now. | Got it. I will note that contact for operations. I will not send anything now. | right_person_email_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "right_person_email_provided", "source": "cont... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |

### generic-healthcare-admin-or-medical-equipment-regulated-caution-refusal-stop-008

- Source checkpoint: `GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001`
- Campaign: `synthetic-healthcare-admin-regression-001`
- Vertical: `healthcare_admin_or_medical_equipment`
- Scenario type: `regulated_caution_refusal_stop`
- Edge buckets: regulated_caution, not_relevant_no_need, stop_refusal
- Risk tags: hard_case, edge_case, regulated, terminal_state
- Expected high-level behavior: Agent refuses unsafe guarantee/concealment, handles no-need stage-aware, and preserves terminal stop behavior.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 2 | yes | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 3 | can you guarantee this equipment solves the issue? | I cannot promise an equipment or service outcome here. A specialist review coordinator needs verified admin and specialist details first. Is specialist review need what you want reviewed? | I cannot promise an equipment or service outcome here. A specialist review coordinator needs verified admin and specialist details first. Is specialist review need what you want reviewed? | campaign_claim_boundary_caution | specialist_review_needed |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "campaign_claim_boundary_caution", "source": "... | transfer-or-escalate | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 4 | no need | Understood. If admin workflow need, equipment or service fit, or specialist review needed are all clean, I should not push a review. I will stop here. Goodbye. | Understood. If admin workflow need, equipment or service fit, or specialist review needed are all clean, I should not push a review. I will stop here. Goodbye. | all_clear_no_pain |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "all_clear_no_pain", "source": "contextual_buy... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 5 | stop calling | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | stop_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "stop_request", "source": "terminal_call_contr... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 6 | actually one more thing | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "terminal_... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |

### generic-healthcare-admin-or-medical-equipment-fallback-repair-stack-009

- Source checkpoint: `GENERIC-CAMPAIGN-FALLBACK-LEAKAGE-001`
- Campaign: `synthetic-healthcare-admin-regression-001`
- Vertical: `healthcare_admin_or_medical_equipment`
- Scenario type: `fallback_repair_stack`
- Edge buckets: fallback_repair, confusion
- Risk tags: hard_case, edge_case, fallback_leakage, naturalness
- Expected high-level behavior: Agent stays campaign-aware through purpose, confusion, next-step, price, and out-of-scope repair turns.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | what is this about? | I am calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether admin workflow need, equipment or service fit, or specialist review needed should go to a short specialist admin review; which part should I check first? | I am calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether admin workflow need, equipment or service fit, or specialist review needed should go to a short specialist admin review;... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "dialogue_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | I don't understand | Sorry, I meant the areas in this fit check: admin workflow need, equipment or service fit, or specialist review needed. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: admin workflow need, equipment or service fit, or specialist review needed. Which part causes trouble, if any? | confusion_not_clear |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "confusion_not_clear", "source": "contextual_b... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 5 | what happens next? | I am checking admin workflow need, equipment or service fit, or specialist review needed for a possible specialist admin review. Which part should I ask about first, if any? | I am checking admin workflow need, equipment or service fit, or specialist review needed for a possible specialist admin review. Which part should I ask about first, if any? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 6 | is it expensive? | I do not have approved pricing to quote here. A specialist review coordinator should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A specialist review coordinator should confirm cost and terms before any next step. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 7 | can you help with my password? | The next step would be a short specialist admin review. A specialist review coordinator can review the details, or I can stop here. | The next step would be a short specialist admin review. A specialist review coordinator can review the details, or I can stop here. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-healthcare-admin-or-medical-equipment-long-mixed-state-drift-010

- Source checkpoint: `GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001`
- Campaign: `synthetic-healthcare-admin-regression-001`
- Vertical: `healthcare_admin_or_medical_equipment`
- Scenario type: `long_mixed_state_drift`
- Edge buckets: long_conversation_state_drift
- Risk tags: hard_case, edge_case, state_drift, duplicate_question_risk
- Expected high-level behavior: Agent should preserve cleared/confirmed/contact/terminal state across a realistic longer conversation.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | equipment fit is handled | Got it, equipment or service fit is clear. Should I check admin workflow need or specialist review needed, or stop here? | Got it, equipment or service fit is clear. Should I check admin workflow need or specialist review needed, or stop here? | current_gap_clear | equipment_or_service_fit | equipment_or_service_fit |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "current_gap_clear", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | specialist review is needed | Got it, specialist review need is the real gap. The next step would be a short specialist admin review; what time works for that review? | Got it, specialist review need is the real gap. The next step would be a short specialist admin review; what time works for that review? | pain_confirmed | specialist_review_needed | equipment_or_service_fit | specialist_review_needed | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "pain_confirmed", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 5 | what happens next? | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | no_contextual_semantic |  | equipment_or_service_fit | specialist_review_needed | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 6 | tomorrow at 3 works | Confirmed. I will note that time for the specialist admin review. Goodbye. | Confirmed. I will note that time for the specialist admin review. Goodbye. | appointment_time_given | specialist_review_needed | equipment_or_service_fit | specialist_review_needed | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "appointment_time_given", "source": "contextua... | schedule-and-end | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-automotive-service-opening-and-permission-001

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-automotive-service-regression-001`
- Vertical: `automotive_service`
- Scenario type: `opening_and_permission`
- Edge buckets: permission_acknowledgement
- Risk tags: baseline
- Expected high-level behavior: Agent opens with campaign-aware reason, then starts one concise diagnostic after permission.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-automotive-service-current-gap-clear-002

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-automotive-service-regression-001`
- Vertical: `automotive_service`
- Scenario type: `current_gap_clear`
- Edge buckets: no_pain_current_issue_clear
- Risk tags: state_memory
- Expected high-level behavior: Agent treats vehicle issue as cleared and asks about remaining campaign gaps.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | repair timing is handled | Got it, repair timing is clear. Should I check vehicle issue or warranty or estimate, or stop here? | Got it, repair timing is clear. Should I check vehicle issue or warranty or estimate, or stop here? | current_gap_clear | repair_timing | repair_timing |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "current_gap_clear", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-automotive-service-pain-confirmed-003

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-automotive-service-regression-001`
- Vertical: `automotive_service`
- Scenario type: `pain_confirmed`
- Edge buckets: pain_confirmed
- Risk tags: appointment_pressure
- Expected high-level behavior: Agent confirms the campaign-specific pain and moves toward a human follow-up without full sale closure.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | warranty estimate is the problem | Got it, warranty or estimate is the real gap. The next step would be a short service advisor inspection review; what time works for that review? | Got it, warranty or estimate is the real gap. The next step would be a short service advisor inspection review; what time works for that review? | pain_confirmed | warranty_or_estimate |  | warranty_or_estimate | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "pain_confirmed", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-automotive-service-possible-pain-then-confusion-004

- Source checkpoint: `GENERIC-CAMPAIGN-BUYER-MOVE-PARAPHRASE-001`
- Campaign: `synthetic-automotive-service-regression-001`
- Vertical: `automotive_service`
- Scenario type: `possible_pain_then_confusion`
- Edge buckets: possible_pain_ambiguity, confusion
- Risk tags: hard_case, edge_case, wrong_next_action_risk
- Expected high-level behavior: Agent should not create false pain and should clarify the prior diagnostic without appointment pressure.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | okay quick | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | sometimes maybe | I am checking vehicle issue, repair timing, or warranty or estimate for a possible service advisor inspection review. Which part should I ask about first, if any? | I am checking vehicle issue, repair timing, or warranty or estimate for a possible service advisor inspection review. Which part should I ask about first, if any? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | what do you mean? | Sorry, I meant the areas in this fit check: vehicle issue, repair timing, or warranty or estimate. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: vehicle issue, repair timing, or warranty or estimate. Which part causes trouble, if any? | previous_question_clarification |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "previous_question_clarification", "source": "... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-automotive-service-send-info-email-capture-005

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-automotive-service-regression-001`
- Vertical: `automotive_service`
- Scenario type: `send_info_email_capture`
- Edge buckets: send_info
- Risk tags: hard_case, edge_case, contact_capture
- Expected high-level behavior: Agent opens send-info state, captures redacted email/hash, and does not claim an email was sent.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 2 | yeah sure | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 3 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_request", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 4 | send it to <email:sha256_12:6db61e6dcbcf> | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | email_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "email_provided", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |

### generic-automotive-service-callback-timing-capture-006

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-automotive-service-regression-001`
- Vertical: `automotive_service`
- Scenario type: `callback_timing_capture`
- Edge buckets: callback_timing
- Risk tags: hard_case, edge_case, time_capture
- Expected high-level behavior: Agent captures a usable callback time without creating calendar or CRM side effects.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_request", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | tomorrow at 3 works | Confirmed. I will record that callback time for the specialist. Goodbye. | Confirmed. I will record that callback time for the specialist. Goodbye. | callback_time_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "callback_time_provided", "source": "contextua... | schedule-and-end | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-automotive-service-right-person-handoff-007

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-automotive-service-regression-001`
- Vertical: `automotive_service`
- Scenario type: `right_person_handoff`
- Edge buckets: right_person_authority
- Risk tags: hard_case, edge_case, handoff_state
- Expected high-level behavior: Agent opens right-person state, captures department/contact path, and keeps it separate from product gaps.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 2 | yeah sure | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 3 | I'm not the person | Understood. Who is the right person or team for service advisor inspection review, or should I stop here? | Understood. Who is the right person or team for service advisor inspection review, or should I stop here? | wrong_person_or_wrong_department |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "wrong_person_or_wrong_department", "source":... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 4 | operations handles it | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note? | wrong_person_or_wrong_department |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "wrong_person_or_wrong_department", "source":... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 5 | send it to <email:sha256_12:af3c82544f64> | Got it. I will note that contact for operations. I will not send anything now. | Got it. I will note that contact for operations. I will not send anything now. | right_person_email_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "right_person_email_provided", "source": "cont... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |

### generic-automotive-service-regulated-caution-refusal-stop-008

- Source checkpoint: `GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001`
- Campaign: `synthetic-automotive-service-regression-001`
- Vertical: `automotive_service`
- Scenario type: `regulated_caution_refusal_stop`
- Edge buckets: regulated_caution, not_relevant_no_need, stop_refusal
- Risk tags: hard_case, edge_case, regulated, terminal_state
- Expected high-level behavior: Agent refuses unsafe guarantee/concealment, handles no-need stage-aware, and preserves terminal stop behavior.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 2 | yes | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 3 | can you guarantee repair cost? | I cannot promise repair cost or warranty outcome here. A service advisor needs verified vehicle details or inspection first. Is warranty or estimate what you want reviewed? | I cannot promise repair cost or warranty outcome here. A service advisor needs verified vehicle details or inspection first. Is warranty or estimate what you want reviewed? | campaign_claim_boundary_caution | warranty_or_estimate |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "campaign_claim_boundary_caution", "source": "... | bridge-then-continue | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 4 | no need | Understood. If vehicle issue, repair timing, or warranty or estimate are all clean, I should not push a review. I will stop here. Goodbye. | Understood. If vehicle issue, repair timing, or warranty or estimate are all clean, I should not push a review. I will stop here. Goodbye. | all_clear_no_pain |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "all_clear_no_pain", "source": "contextual_buy... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 5 | stop calling | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | stop_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "stop_request", "source": "terminal_call_contr... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 6 | actually one more thing | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "terminal_... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |

### generic-automotive-service-fallback-repair-stack-009

- Source checkpoint: `GENERIC-CAMPAIGN-FALLBACK-LEAKAGE-001`
- Campaign: `synthetic-automotive-service-regression-001`
- Vertical: `automotive_service`
- Scenario type: `fallback_repair_stack`
- Edge buckets: fallback_repair, confusion
- Risk tags: hard_case, edge_case, fallback_leakage, naturalness
- Expected high-level behavior: Agent stays campaign-aware through purpose, confusion, next-step, price, and out-of-scope repair turns.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | what is this about? | I am calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether vehicle issue, repair timing, or warranty or estimate should go to a short service advisor inspection review; which part should I check first? | I am calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether vehicle issue, repair timing, or warranty or estimate should go to a short service advisor inspection review; which pa... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "dialogue_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | I don't understand | Sorry, I meant the areas in this fit check: vehicle issue, repair timing, or warranty or estimate. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: vehicle issue, repair timing, or warranty or estimate. Which part causes trouble, if any? | confusion_not_clear |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "confusion_not_clear", "source": "contextual_b... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 5 | what happens next? | I am checking vehicle issue, repair timing, or warranty or estimate for a possible service advisor inspection review. Which part should I ask about first, if any? | I am checking vehicle issue, repair timing, or warranty or estimate for a possible service advisor inspection review. Which part should I ask about first, if any? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 6 | is it expensive? | I do not have approved pricing to quote here. A service advisor should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A service advisor should confirm cost and terms before any next step. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 7 | can you help with my password? | The next step would be a short service advisor inspection review. A service advisor can review the details, or I can stop here. | The next step would be a short service advisor inspection review. A service advisor can review the details, or I can stop here. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-automotive-service-long-mixed-state-drift-010

- Source checkpoint: `GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001`
- Campaign: `synthetic-automotive-service-regression-001`
- Vertical: `automotive_service`
- Scenario type: `long_mixed_state_drift`
- Edge buckets: long_conversation_state_drift
- Risk tags: hard_case, edge_case, state_drift, duplicate_question_risk
- Expected high-level behavior: Agent should preserve cleared/confirmed/contact/terminal state across a realistic longer conversation.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | I do not understand | Sorry, I meant the areas in this fit check: vehicle issue, repair timing, or warranty or estimate. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: vehicle issue, repair timing, or warranty or estimate. Which part causes trouble, if any? | confusion_not_clear |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "confusion_not_clear", "source": "contextual_b... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | what is this about? | I am calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether vehicle issue, repair timing, or warranty or estimate should go to a short service advisor inspection review; which part should I check first? | I am calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether vehicle issue, repair timing, or warranty or estimate should go to a short service advisor inspection review; which pa... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "dialogue_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 5 | what happens next? | I am checking vehicle issue, repair timing, or warranty or estimate for a possible service advisor inspection review. Which part should I ask about first, if any? | I am checking vehicle issue, repair timing, or warranty or estimate for a possible service advisor inspection review. Which part should I ask about first, if any? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 6 | maybe | No problem. I mean inbound leads where someone asks for a demo or more information. The simple check is whether one person is clearly responsible for the next reply. Does that ever get fuzzy? | No problem. I mean inbound leads where someone asks for a demo or more information. The simple check is whether one person is clearly responsible for the next reply. Does that ever get fuzzy? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 7 | not sure | The next step would be a short service advisor inspection review. A service advisor can review the details, or I can stop here. | The next step would be a short service advisor inspection review. A service advisor can review the details, or I can stop here. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "duplicate... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 8 | warranty estimate is the problem | Got it, warranty or estimate is the real gap. The next step would be a short service advisor inspection review; what time works for that review? | Got it, warranty or estimate is the real gap. The next step would be a short service advisor inspection review; what time works for that review? | pain_confirmed | warranty_or_estimate |  | warranty_or_estimate | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "pain_confirmed", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 9 | I already told you | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | No problem. I will not schedule anything without a specific time; we can leave this for a later human review. | no_contextual_semantic |  |  | warranty_or_estimate | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 10 | tomorrow at 3 works | Confirmed. I will note that time for the service advisor inspection review. Goodbye. | Confirmed. I will note that time for the service advisor inspection review. Goodbye. | appointment_time_given | warranty_or_estimate |  | warranty_or_estimate | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "appointment_time_given", "source": "contextua... | schedule-and-end | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-membership-or-subscription-opening-and-permission-001

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-membership-regression-001`
- Vertical: `membership_or_subscription`
- Scenario type: `opening_and_permission`
- Edge buckets: permission_acknowledgement
- Risk tags: baseline
- Expected high-level behavior: Agent opens with campaign-aware reason, then starts one concise diagnostic after permission.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-membership-or-subscription-current-gap-clear-002

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-membership-regression-001`
- Vertical: `membership_or_subscription`
- Scenario type: `current_gap_clear`
- Edge buckets: no_pain_current_issue_clear
- Risk tags: state_memory
- Expected high-level behavior: Agent treats plan fit as cleared and asks about remaining campaign gaps.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | plan fit is fine | Got it, plan fit is clear. Should I check renewal or cancellation or usage or value, or stop here? | Got it, plan fit is clear. Should I check renewal or cancellation or usage or value, or stop here? | current_gap_clear | plan_fit | plan_fit |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "current_gap_clear", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-membership-or-subscription-pain-confirmed-003

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-membership-regression-001`
- Vertical: `membership_or_subscription`
- Scenario type: `pain_confirmed`
- Edge buckets: pain_confirmed
- Risk tags: appointment_pressure
- Expected high-level behavior: Agent confirms the campaign-specific pain and moves toward a human follow-up without full sale closure.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | renewal is the issue | Got it, renewal or cancellation terms is the real gap. The next step would be a short membership account review; what time works for that review? | Got it, renewal or cancellation terms is the real gap. The next step would be a short membership account review; what time works for that review? | pain_confirmed | renewal_or_cancellation |  | renewal_or_cancellation | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "pain_confirmed", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-membership-or-subscription-possible-pain-then-confusion-004

- Source checkpoint: `GENERIC-CAMPAIGN-BUYER-MOVE-PARAPHRASE-001`
- Campaign: `synthetic-membership-regression-001`
- Vertical: `membership_or_subscription`
- Scenario type: `possible_pain_then_confusion`
- Edge buckets: possible_pain_ambiguity, confusion
- Risk tags: hard_case, edge_case, wrong_next_action_risk
- Expected high-level behavior: Agent should not create false pain and should clarify the prior diagnostic without appointment pressure.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | okay quick | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | sometimes maybe | I am checking plan fit, renewal or cancellation, or usage or value for a possible membership account review. Which part should I ask about first, if any? | I am checking plan fit, renewal or cancellation, or usage or value for a possible membership account review. Which part should I ask about first, if any? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | what do you mean? | Sorry, I meant the areas in this fit check: plan fit, renewal or cancellation, or usage or value. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: plan fit, renewal or cancellation, or usage or value. Which part causes trouble, if any? | previous_question_clarification |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "previous_question_clarification", "source": "... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-membership-or-subscription-send-info-email-capture-005

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-membership-regression-001`
- Vertical: `membership_or_subscription`
- Scenario type: `send_info_email_capture`
- Edge buckets: send_info
- Risk tags: hard_case, edge_case, contact_capture
- Expected high-level behavior: Agent opens send-info state, captures redacted email/hash, and does not claim an email was sent.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 2 | yeah sure | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 3 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_request", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 4 | send it to <email:sha256_12:6db61e6dcbcf> | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | email_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "email_provided", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |

### generic-membership-or-subscription-callback-timing-capture-006

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-membership-regression-001`
- Vertical: `membership_or_subscription`
- Scenario type: `callback_timing_capture`
- Edge buckets: callback_timing
- Risk tags: hard_case, edge_case, time_capture
- Expected high-level behavior: Agent captures a usable callback time without creating calendar or CRM side effects.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_request", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | tomorrow at 3 works | Confirmed. I will record that callback time for the specialist. Goodbye. | Confirmed. I will record that callback time for the specialist. Goodbye. | callback_time_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "callback_time_provided", "source": "contextua... | schedule-and-end | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-membership-or-subscription-right-person-handoff-007

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-membership-regression-001`
- Vertical: `membership_or_subscription`
- Scenario type: `right_person_handoff`
- Edge buckets: right_person_authority
- Risk tags: hard_case, edge_case, handoff_state
- Expected high-level behavior: Agent opens right-person state, captures department/contact path, and keeps it separate from product gaps.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 2 | yeah sure | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 3 | I'm not the person | Understood. Who is the right person or team for membership account review, or should I stop here? | Understood. Who is the right person or team for membership account review, or should I stop here? | wrong_person_or_wrong_department |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "wrong_person_or_wrong_department", "source":... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 4 | operations handles it | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note? | wrong_person_or_wrong_department |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "wrong_person_or_wrong_department", "source":... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 5 | send it to <email:sha256_12:af3c82544f64> | Got it. I will note that contact for operations. I will not send anything now. | Got it. I will note that contact for operations. I will not send anything now. | right_person_email_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "right_person_email_provided", "source": "cont... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |

### generic-membership-or-subscription-regulated-caution-refusal-stop-008

- Source checkpoint: `GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001`
- Campaign: `synthetic-membership-regression-001`
- Vertical: `membership_or_subscription`
- Scenario type: `regulated_caution_refusal_stop`
- Edge buckets: regulated_caution, not_relevant_no_need, stop_refusal
- Risk tags: hard_case, edge_case, regulated, terminal_state
- Expected high-level behavior: Agent refuses unsafe guarantee/concealment, handles no-need stage-aware, and preserves terminal stop behavior.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 2 | yes | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 3 | can you hide cancellation terms? | I cannot hide cancellation terms or make account-specific billing promises. A membership specialist should review the policy details transparently. Is renewal or cancellation terms what you want reviewed? | I cannot hide cancellation terms or make account-specific billing promises. A membership specialist should review the policy details transparently. Is renewal or cancellation terms what you want reviewed? | campaign_claim_boundary_caution | renewal_or_cancellation |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "campaign_claim_boundary_caution", "source": "... | transfer-or-escalate | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 4 | no need | Got it, renewal or cancellation is clear. Should I check plan fit or usage or value, or stop here? | Got it, renewal or cancellation is clear. Should I check plan fit or usage or value, or stop here? | current_gap_clear | renewal_or_cancellation | renewal_or_cancellation |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "current_gap_clear", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 5 | stop calling | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | stop_request |  | renewal_or_cancellation |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "stop_request", "source": "contextual_buyer_se... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 6 | actually one more thing | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | no_contextual_semantic |  | renewal_or_cancellation |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "terminal_... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |

### generic-membership-or-subscription-fallback-repair-stack-009

- Source checkpoint: `GENERIC-CAMPAIGN-FALLBACK-LEAKAGE-001`
- Campaign: `synthetic-membership-regression-001`
- Vertical: `membership_or_subscription`
- Scenario type: `fallback_repair_stack`
- Edge buckets: fallback_repair, confusion
- Risk tags: hard_case, edge_case, fallback_leakage, naturalness
- Expected high-level behavior: Agent stays campaign-aware through purpose, confusion, next-step, price, and out-of-scope repair turns.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | what is this about? | I am calling from Synthetic Membership Services about Membership Plan Review. I am checking whether plan fit, renewal or cancellation, or usage or value should go to a short membership account review; which part should I check first? | I am calling from Synthetic Membership Services about Membership Plan Review. I am checking whether plan fit, renewal or cancellation, or usage or value should go to a short membership account review; which part shoul... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "dialogue_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | I don't understand | Sorry, I meant the areas in this fit check: plan fit, renewal or cancellation, or usage or value. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: plan fit, renewal or cancellation, or usage or value. Which part causes trouble, if any? | confusion_not_clear |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "confusion_not_clear", "source": "contextual_b... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 5 | what happens next? | I am checking plan fit, renewal or cancellation, or usage or value for a possible membership account review. Which part should I ask about first, if any? | I am checking plan fit, renewal or cancellation, or usage or value for a possible membership account review. Which part should I ask about first, if any? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 6 | is it expensive? | I do not have approved pricing to quote here. A membership specialist should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A membership specialist should confirm cost and terms before any next step. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 7 | can you help with my password? | The next step would be a short membership account review. A membership specialist can review the details, or I can stop here. | The next step would be a short membership account review. A membership specialist can review the details, or I can stop here. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-membership-or-subscription-long-mixed-state-drift-010

- Source checkpoint: `GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001`
- Campaign: `synthetic-membership-regression-001`
- Vertical: `membership_or_subscription`
- Scenario type: `long_mixed_state_drift`
- Edge buckets: long_conversation_state_drift
- Risk tags: hard_case, edge_case, state_drift, duplicate_question_risk
- Expected high-level behavior: Agent should preserve cleared/confirmed/contact/terminal state across a realistic longer conversation.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yes | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | plan fit is fine | Got it, plan fit is clear. Should I check renewal or cancellation or usage or value, or stop here? | Got it, plan fit is clear. Should I check renewal or cancellation or usage or value, or stop here? | current_gap_clear | plan_fit | plan_fit |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "current_gap_clear", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | renewal is handled | Got it, those parts are clear. Should I check usage or value, or stop here? | Got it, those parts are clear. Should I check usage or value, or stop here? | current_gap_clear | renewal_or_cancellation | plan_fit, renewal_or_cancellation |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "current_gap_clear", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 5 | usage is fine | Understood. If plan fit, renewal or cancellation, and usage or value are clean, I should not push this further. Is there any other gap worth checking, or should I stop here? | Understood. If plan fit, renewal or cancellation, and usage or value are clean, I should not push this further. Is there any other gap worth checking, or should I stop here? | current_gap_clear | usage_or_value | plan_fit, renewal_or_cancellation, usage_or_value |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "current_gap_clear", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 6 | no need | Understood. If plan fit, renewal or cancellation, or usage or value are all clean, I should not push a review. I will stop here. Goodbye. | Understood. If plan fit, renewal or cancellation, or usage or value are all clean, I should not push a review. I will stop here. Goodbye. | all_clear_no_pain |  | plan_fit, renewal_or_cancellation, usage_or_value |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "all_clear_no_pain", "source": "contextual_buy... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 7 | all of it | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | no_contextual_semantic |  | plan_fit, renewal_or_cancellation, usage_or_value |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "terminal_... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-retail-or-ecommerce-support-sales-opening-and-permission-001

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-retail-ecommerce-regression-001`
- Vertical: `retail_or_ecommerce_support_sales`
- Scenario type: `opening_and_permission`
- Edge buckets: permission_acknowledgement
- Risk tags: baseline
- Expected high-level behavior: Agent opens with campaign-aware reason, then starts one concise diagnostic after permission.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-retail-or-ecommerce-support-sales-current-gap-clear-002

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-retail-ecommerce-regression-001`
- Vertical: `retail_or_ecommerce_support_sales`
- Scenario type: `current_gap_clear`
- Edge buckets: no_pain_current_issue_clear
- Risk tags: state_memory
- Expected high-level behavior: Agent treats product fit as cleared and asks about remaining campaign gaps.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | product fit is fine | Got it, product fit is clear. Should I check availability or delivery or return or warranty, or stop here? | Got it, product fit is clear. Should I check availability or delivery or return or warranty, or stop here? | current_gap_clear | product_fit | product_fit |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "current_gap_clear", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-retail-or-ecommerce-support-sales-pain-confirmed-003

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-retail-ecommerce-regression-001`
- Vertical: `retail_or_ecommerce_support_sales`
- Scenario type: `pain_confirmed`
- Edge buckets: pain_confirmed
- Risk tags: appointment_pressure
- Expected high-level behavior: Agent confirms the campaign-specific pain and moves toward a human follow-up without full sale closure.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | return policy is the concern | Got it, return or warranty policy is the real gap. The next step would be a short product support review; what time works for that review? | Got it, return or warranty policy is the real gap. The next step would be a short product support review; what time works for that review? | pain_confirmed | return_or_warranty |  | return_or_warranty | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "pain_confirmed", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-retail-or-ecommerce-support-sales-possible-pain-then-confusion-004

- Source checkpoint: `GENERIC-CAMPAIGN-BUYER-MOVE-PARAPHRASE-001`
- Campaign: `synthetic-retail-ecommerce-regression-001`
- Vertical: `retail_or_ecommerce_support_sales`
- Scenario type: `possible_pain_then_confusion`
- Edge buckets: possible_pain_ambiguity, confusion
- Risk tags: hard_case, edge_case, wrong_next_action_risk
- Expected high-level behavior: Agent should not create false pain and should clarify the prior diagnostic without appointment pressure.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | okay quick | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | sometimes maybe | I am checking product fit, availability or delivery, or return or warranty for a possible product support review. Which part should I ask about first, if any? | I am checking product fit, availability or delivery, or return or warranty for a possible product support review. Which part should I ask about first, if any? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | what do you mean? | Sorry, I meant the areas in this fit check: product fit, availability or delivery, or return or warranty. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: product fit, availability or delivery, or return or warranty. Which part causes trouble, if any? | previous_question_clarification |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "previous_question_clarification", "source": "... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-retail-or-ecommerce-support-sales-send-info-email-capture-005

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-retail-ecommerce-regression-001`
- Vertical: `retail_or_ecommerce_support_sales`
- Scenario type: `send_info_email_capture`
- Edge buckets: send_info
- Risk tags: hard_case, edge_case, contact_capture
- Expected high-level behavior: Agent opens send-info state, captures redacted email/hash, and does not claim an email was sent.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 2 | yeah sure | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 3 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_request", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 4 | send it to <email:sha256_12:6db61e6dcbcf> | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary? | email_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "email_provided", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |

### generic-retail-or-ecommerce-support-sales-callback-timing-capture-006

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-retail-ecommerce-regression-001`
- Vertical: `retail_or_ecommerce_support_sales`
- Scenario type: `callback_timing_capture`
- Edge buckets: callback_timing
- Risk tags: hard_case, edge_case, time_capture
- Expected high-level behavior: Agent captures a usable callback time without creating calendar or CRM side effects.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. I can keep it to a short written summary. What email or callback time should I note? | send_info_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_request", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | tomorrow at 3 works | Confirmed. I will record that callback time for the specialist. Goodbye. | Confirmed. I will record that callback time for the specialist. Goodbye. | callback_time_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "callback_time_provided", "source": "contextua... | schedule-and-end | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-retail-or-ecommerce-support-sales-right-person-handoff-007

- Source checkpoint: `GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001`
- Campaign: `synthetic-retail-ecommerce-regression-001`
- Vertical: `retail_or_ecommerce_support_sales`
- Scenario type: `right_person_handoff`
- Edge buckets: right_person_authority
- Risk tags: hard_case, edge_case, handoff_state
- Expected high-level behavior: Agent opens right-person state, captures department/contact path, and keeps it separate from product gaps.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 2 | yeah sure | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 3 | I'm not the person | Understood. Who is the right person or team for product support review, or should I stop here? | Understood. Who is the right person or team for product support review, or should I stop here? | wrong_person_or_wrong_department |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "wrong_person_or_wrong_department", "source":... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 4 | operations handles it | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note? | wrong_person_or_wrong_department |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "wrong_person_or_wrong_department", "source":... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 5 | send it to <email:sha256_12:af3c82544f64> | Got it. I will note that contact for operations. I will not send anything now. | Got it. I will note that contact for operations. I will not send anything now. | right_person_email_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "right_person_email_provided", "source": "cont... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |

### generic-retail-or-ecommerce-support-sales-regulated-caution-refusal-stop-008

- Source checkpoint: `GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001`
- Campaign: `synthetic-retail-ecommerce-regression-001`
- Vertical: `retail_or_ecommerce_support_sales`
- Scenario type: `regulated_caution_refusal_stop`
- Edge buckets: regulated_caution, not_relevant_no_need, stop_refusal
- Risk tags: hard_case, edge_case, regulated, terminal_state
- Expected high-level behavior: Agent refuses unsafe guarantee/concealment, handles no-need stage-aware, and preserves terminal stop behavior.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 2 | yes | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 3 | can you guarantee refund? | I cannot promise a refund, warranty, stock, or delivery outcome here. A support sales specialist needs verified policy and order details first. Is return or warranty policy what you want reviewed? | I cannot promise a refund, warranty, stock, or delivery outcome here. A support sales specialist needs verified policy and order details first. Is return or warranty policy what you want reviewed? | campaign_claim_boundary_caution | return_or_warranty |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "campaign_claim_boundary_caution", "source": "... | transfer-or-escalate | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 4 | no need | Understood. If product fit, availability or delivery, or return or warranty are all clean, I should not push a review. I will stop here. Goodbye. | Understood. If product fit, availability or delivery, or return or warranty are all clean, I should not push a review. I will stop here. Goodbye. | all_clear_no_pain |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "all_clear_no_pain", "source": "contextual_buy... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 5 | stop calling | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | stop_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "stop_request", "source": "terminal_call_contr... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |
| 6 | actually one more thing | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "terminal_... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the response avoid guarantees and route safely to human or policy review?; Was th... |

### generic-retail-or-ecommerce-support-sales-fallback-repair-stack-009

- Source checkpoint: `GENERIC-CAMPAIGN-FALLBACK-LEAKAGE-001`
- Campaign: `synthetic-retail-ecommerce-regression-001`
- Vertical: `retail_or_ecommerce_support_sales`
- Scenario type: `fallback_repair_stack`
- Edge buckets: fallback_repair, confusion
- Risk tags: hard_case, edge_case, fallback_leakage, naturalness
- Expected high-level behavior: Agent stays campaign-aware through purpose, confusion, next-step, price, and out-of-scope repair turns.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | what is this about? | I am calling from Synthetic Retail Support about Product Support Review. I am checking whether product fit, availability or delivery, or return or warranty should go to a short product support review; which part should I check first? | I am calling from Synthetic Retail Support about Product Support Review. I am checking whether product fit, availability or delivery, or return or warranty should go to a short product support review; which part shoul... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "dialogue_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | I don't understand | Sorry, I meant the areas in this fit check: product fit, availability or delivery, or return or warranty. Which part causes trouble, if any? | Sorry, I meant the areas in this fit check: product fit, availability or delivery, or return or warranty. Which part causes trouble, if any? | confusion_not_clear |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "confusion_not_clear", "source": "contextual_b... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 5 | what happens next? | I am checking product fit, availability or delivery, or return or warranty for a possible product support review. Which part should I ask about first, if any? | I am checking product fit, availability or delivery, or return or warranty for a possible product support review. Which part should I ask about first, if any? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 6 | is it expensive? | I do not have approved pricing to quote here. A support sales specialist should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A support sales specialist should confirm cost and terms before any next step. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 7 | can you help with my password? | The next step would be a short product support review. A support sales specialist can review the details, or I can stop here. | The next step would be a short product support review. A support sales specialist can review the details, or I can stop here. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### generic-retail-or-ecommerce-support-sales-long-mixed-state-drift-010

- Source checkpoint: `GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001`
- Campaign: `synthetic-retail-ecommerce-regression-001`
- Vertical: `retail_or_ecommerce_support_sales`
- Scenario type: `long_mixed_state_drift`
- Edge buckets: long_conversation_state_drift
- Risk tags: hard_case, edge_case, state_drift, duplicate_question_risk
- Expected high-level behavior: Agent should preserve cleared/confirmed/contact/terminal state across a realistic longer conversation.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | return policy is the concern | Got it, return or warranty policy is the real gap. The next step would be a short product support review; what time works for that review? | Got it, return or warranty policy is the real gap. The next step would be a short product support review; what time works for that review? | pain_confirmed | return_or_warranty |  | return_or_warranty | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "pain_confirmed", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | how much does it cost? | I do not have approved pricing to quote here. A support sales specialist should confirm cost and terms before any next step. | I do not have approved pricing to quote here. A support sales specialist should confirm cost and terms before any next step. | no_contextual_semantic |  |  | return_or_warranty | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 5 | can you guarantee refund? | I cannot promise a refund, warranty, stock, or delivery outcome here. A support sales specialist needs verified policy and order details first. Is return or warranty policy what you want reviewed? | I cannot promise a refund, warranty, stock, or delivery outcome here. A support sales specialist needs verified policy and order details first. Is return or warranty policy what you want reviewed? | campaign_claim_boundary_caution | return_or_warranty |  | return_or_warranty | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "campaign_claim_boundary_caution", "source": "... | transfer-or-escalate | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 6 | tomorrow at 3 works | Confirmed. I will note that time for the product support review. Goodbye. | Confirmed. I will note that time for the product support review. Goodbye. | appointment_time_given | return_or_warranty |  | return_or_warranty | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "appointment_time_given", "source": "contextua... | schedule-and-end | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### routesignal-live-demo-opening-permission-001

- Source checkpoint: `LIVE-DEMO-013-reasoner-route-guard`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario type: `opening_permission`
- Edge buckets: permission_acknowledgement
- Risk tags: baseline
- Expected high-level behavior: RouteSignal opening and diagnostic start remain allowed.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. Do you have a minute? | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. <break time="0.225s... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### routesignal-live-demo-callbacks-clear-002

- Source checkpoint: `LIVE-DEMO-014-clear-pain-callback-followup`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario type: `callbacks_clear`
- Edge buckets: no_pain_current_issue_clear, routesignal_preservation
- Risk tags: state_memory
- Expected high-level behavior: Callbacks are cleared and remaining RouteSignal gaps are asked.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. Do you have a minute? | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. <break time="0.225s... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | callbacks are fine | Got it, callbacks are clear. Should I check manual tracking or handoffs, or stop here? | Got it, callbacks are clear, well, should I check manual tracking or handoffs, or stop here? | current_gap_clear | callbacks | callbacks |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "current_gap_clear", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### routesignal-live-demo-handoffs-pain-003

- Source checkpoint: `LIVE-DEMO-013-reasoner-route-guard`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario type: `handoffs_pain`
- Edge buckets: pain_confirmed, routesignal_preservation
- Risk tags: appointment_pressure
- Expected high-level behavior: Handoffs pain is confirmed and RouteSignal/Northstar wording is allowed.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. Do you have a minute? | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. <break time="0.225s... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | handoffs get messy | Got it, handoff ownership is the real gap. RouteSignal helps each demo lead keep a clear owner and next reply. The next step is a short workflow review with someone from Northstar. They would check handoff ownership against your actual follow-up flow. What... | Got it, handoff ownership is the real gap, well, RouteSignal helps each demo lead keep a clear owner and next reply. The next step is a short workflow review with someone from Northstar. They would check handoff owner... | pain_confirmed | handoffs |  | handoffs | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "pain_confirmed", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### routesignal-live-demo-send-info-yes-004

- Source checkpoint: `LIVE-DEMO-013-reasoner-route-guard`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario type: `send_info_yes`
- Edge buckets: send_info, routesignal_preservation
- Risk tags: hard_case, edge_case
- Expected high-level behavior: Send-info state opens without fake send.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. Do you have a minute? | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. <break time="0.225s... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 3 | send me details first | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem. Um, I can keep it to a short written summary. <break time="0.24s" /> What email or callback time should I note? | send_info_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_request", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |
| 4 | yes send it | Sure. What email should I note for the summary, or what callback time should I use? | Sure. Um, what email should I note for the summary, <break time="0.24s" /> or what callback time should I use? | send_info_affirmed_without_contact |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_affirmed_without_contact", "source"... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was contact capture safe without implying an email was sent? |

### routesignal-live-demo-callback-time-005

- Source checkpoint: `LIVE-DEMO-014-clear-pain-callback-followup`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario type: `callback_time`
- Edge buckets: callback_timing, routesignal_preservation
- Risk tags: hard_case, edge_case
- Expected high-level behavior: Callback time capture works through live-demo path.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. Do you have a minute? | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. <break time="0.225s... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | send me details | No problem. I can keep it to a short written summary. What email or callback time should I note? | No problem, so, I can keep it to a short written summary. <break time="0.24s" /> What email or callback time should I note? | send_info_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_request", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | tomorrow at 3 works | Confirmed. I will record that callback time for the specialist. Goodbye. | Confirmed. I will record that callback time for the specialist. Goodbye. | callback_time_provided |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "callback_time_provided", "source": "contextua... | schedule-and-end | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### routesignal-live-demo-right-person-006

- Source checkpoint: `LIVE-DEMO-013-reasoner-route-guard`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario type: `right_person`
- Edge buckets: right_person_authority, routesignal_preservation
- Risk tags: hard_case, edge_case
- Expected high-level behavior: Wrong-person route remains safe.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. Do you have a minute? | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. <break time="0.225s... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 3 | I'm not the person | Understood. Who is the right person or team for demo follow-up, or should I stop here? | Understood, well, <break time="0.24s" /> who is the right person or team for demo follow-up, or should I stop here? | wrong_person_or_wrong_department |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "wrong_person_or_wrong_department", "source":... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |
| 4 | operations handles it | Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note? | Understood, operations handles that, so, who is the right person there, or what contact, email, or callback path should I note? | wrong_person_or_wrong_department |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "wrong_person_or_wrong_department", "source":... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Did the agent keep contact routing separate from product-gap routing? |

### routesignal-live-demo-stop-terminal-007

- Source checkpoint: `LIVE-DEMO-013-reasoner-route-guard`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario type: `stop_terminal`
- Edge buckets: stop_refusal, routesignal_preservation
- Risk tags: hard_case, edge_case
- Expected high-level behavior: Stop ends call and terminal behavior persists.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. Do you have a minute? | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. <break time="0.225s... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was the stop/refusal respected without continued selling? |
| 2 | stop calling | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | stop_request |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "stop_request", "source": "contextual_buyer_se... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was the stop/refusal respected without continued selling? |
| 3 | actually one more thing | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "terminal_... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call?; Was the stop/refusal respected without continued selling? |

### routesignal-live-demo-confusion-repair-008

- Source checkpoint: `LIVE-DEMO-013-reasoner-route-guard`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario type: `confusion_repair`
- Edge buckets: confusion, routesignal_preservation
- Risk tags: hard_case
- Expected high-level behavior: Confusion gets a repair rather than appointment pressure.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. Do you have a minute? | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. <break time="0.225s... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | I don't understand | Sorry, I meant the follow-up after an inbound demo request: callbacks, manual tracking, or handoffs. Which part causes trouble, if any? | Sorry, I meant the follow-up after an inbound demo request: callbacks, <break time="0.154s" /> manual tracking, or handoffs, so, which part causes trouble, if any? | confusion_not_clear |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "confusion_not_clear", "source": "contextual_b... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | what do you mean? | I meant: an inbound demo request needs one clear owner for the next reply. Can owner, callback, or handoff steps sit waiting? | I meant: an inbound demo request needs one clear owner for the next reply, so, can owner, callback, or handoff steps sit waiting? | previous_question_clarification |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "previous_question_clarification", "source": "... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### routesignal-live-demo-price-question-009

- Source checkpoint: `LIVE-DEMO-013-reasoner-route-guard`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario type: `price_question`
- Edge buckets: fallback_repair, routesignal_preservation
- Risk tags: hard_case
- Expected high-level behavior: Price question is answered only within live-demo policy.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. Do you have a minute? | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. <break time="0.225s... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | how much does it cost? | Starter is $29/month for basic routing. Growth is $59/month with priority routing, reminders, and handoff review. Which gap costs more time today: routing, callbacks, or handoffs? | Starter is $29/month for basic routing. <break time="0.235s" /> Um, growth is $59/month with priority routing, reminders, and handoff review. Which gap costs more time today: routing, callbacks, or handoffs? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### routesignal-live-demo-no-need-010

- Source checkpoint: `LIVE-DEMO-013-reasoner-route-guard`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario type: `no_need`
- Edge buckets: not_relevant_no_need, routesignal_preservation
- Risk tags: hard_case
- Expected high-level behavior: No-need path should avoid continued selling loops.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. Do you have a minute? | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. <break time="0.225s... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | no need | Understood. If callbacks, manual tracking, and handoffs are all clean, I should not push a review. I will stop here. Goodbye. | Understood. If callbacks, manual tracking, and handoffs are all clean, I should not push a review. I will stop here. Goodbye. | all_clear_no_pain |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "all_clear_no_pain", "source": "contextual_buy... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | all of it | Understood. I will stop here. Goodbye. | Understood. I will stop here. Goodbye. | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "terminal_... | end-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### routesignal-live-demo-possible-pain-011

- Source checkpoint: `LIVE-DEMO-013-reasoner-route-guard`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario type: `possible_pain`
- Edge buckets: possible_pain_ambiguity, routesignal_preservation
- Risk tags: hard_case
- Expected high-level behavior: Possible pain should not create a false confirmed pain.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. Do you have a minute? | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. <break time="0.225s... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | sometimes maybe | If callback reminders for demo follow-up sit in a spreadsheet, they can slip. Which part is more familiar: manual tracking or missed callbacks? | If callback reminders for demo follow-up sit in a spreadsheet, they can slip. <break time="0.24s" /> Um, which part is more familiar: manual tracking or missed callbacks? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### routesignal-live-demo-next-step-012

- Source checkpoint: `LIVE-DEMO-013-reasoner-route-guard`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario type: `next_step`
- Edge buckets: fallback_repair, routesignal_preservation
- Risk tags: hard_case
- Expected high-level behavior: Next-step answer may mention Northstar in RouteSignal path only.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. Do you have a minute? | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. <break time="0.225s... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | what happens next? | If callback reminders for demo follow-up sit in a spreadsheet, they can slip. Which part is more familiar: manual tracking or missed callbacks? | If callback reminders for demo follow-up sit in a spreadsheet, they can slip, well, which part is more familiar: manual tracking or missed callbacks? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### routesignal-live-demo-manual-tracking-clear-013

- Source checkpoint: `LIVE-DEMO-013-reasoner-route-guard`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario type: `manual_tracking_clear`
- Edge buckets: no_pain_current_issue_clear, routesignal_preservation
- Risk tags: state_memory
- Expected high-level behavior: Manual tracking clear behavior remains stable.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. Do you have a minute? | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. <break time="0.225s... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | manual tracking is handled | Got it, manual tracking is clear. Should I check callbacks or handoffs, or stop here? | Got it, manual tracking is clear. <break time="0.178s" /> Um, should I check callbacks or handoffs, or stop here? | current_gap_clear | manual_tracking | manual_tracking |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "current_gap_clear", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### routesignal-live-demo-callbacks-pain-014

- Source checkpoint: `LIVE-DEMO-014-clear-pain-callback-followup`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario type: `callbacks_pain`
- Edge buckets: pain_confirmed, routesignal_preservation
- Risk tags: appointment_pressure
- Expected high-level behavior: Callbacks pain confirmation remains stable.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. Do you have a minute? | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. <break time="0.225s... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | callbacks are a problem | Got it, missed callbacks is the real gap. RouteSignal helps demo leads stay assigned, reminded, and followed up before callback gaps turn into lost opportunities. The next step is a short workflow review with someone from Northstar. They would check missed... | Got it, missed callbacks is the real gap, so, RouteSignal helps demo leads stay assigned, reminded, and followed up before callback gaps turn into lost opportunities. The next step is a short workflow review with some... | pain_confirmed | callbacks |  | callbacks | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "pain_confirmed", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### routesignal-live-demo-long-routesignal-015

- Source checkpoint: `LIVE-DEMO-014-clear-pain-callback-followup`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario type: `long_routesignal`
- Edge buckets: long_conversation_state_drift, routesignal_preservation
- Risk tags: hard_case, edge_case, state_drift
- Expected high-level behavior: Long RouteSignal preservation across clear, pain, send-info, and callback.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. Do you have a minute? | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. <break time="0.225s... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | callbacks are fine | Got it, callbacks are clear. Should I check manual tracking or handoffs, or stop here? | Got it, callbacks are clear, well, should I check manual tracking or handoffs, or stop here? | current_gap_clear | callbacks | callbacks |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "current_gap_clear", "source": "contextual_buy... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 4 | handoffs get messy | Got it, handoff ownership is the real gap. RouteSignal helps each demo lead keep a clear owner and next reply. The next step is a short workflow review with someone from Northstar. They would check handoff ownership against your actual follow-up flow. What... | Got it, handoff ownership is the real gap, well, RouteSignal helps each demo lead keep a clear owner and next reply. The next step is a short workflow review with someone from Northstar. They would check handoff owner... | pain_confirmed | handoffs | callbacks | handoffs | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "pain_confirmed", "source": "contextual_buyer_... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 5 | send me details first | No problem. I can send a short summary focused on handoff ownership. What email or callback time should I note? | No problem, well, I can send a short summary focused on handoff ownership. <break time="0.184s" /> What email or callback time should I note? | send_info_with_confirmed_pain | handoffs | callbacks | handoffs | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_with_confirmed_pain", "source": "co... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 6 | yes send it | Sure. What email should I note for the summary, or what callback time should I use? | Sure. Um, what email should I note for the summary, <break time="0.24s" /> or what callback time should I use? | send_info_affirmed_without_contact |  | callbacks | handoffs | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "send_info_affirmed_without_contact", "source"... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 7 | tomorrow at 3 works | Confirmed. I will record that callback time for the specialist. Goodbye. | Confirmed. I will record that callback time for the specialist. Goodbye. | callback_time_provided |  | callbacks | handoffs | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "callback_time_provided", "source": "contextua... | schedule-and-end | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

### routesignal-live-demo-odd-out-of-scope-016

- Source checkpoint: `LIVE-DEMO-013-reasoner-route-guard`
- Campaign: `campaign-prod-005-b2b-software`
- Vertical: `routesignal_live_demo`
- Scenario type: `odd_out_of_scope`
- Edge buckets: fallback_repair, routesignal_preservation
- Risk tags: hard_case, edge_case
- Expected high-level behavior: Out-of-scope fallback should not break live-demo behavior.

| Turn | Buyer | Agent final response | TTS input | Semantic | Target gap | Cleared | Confirmed | Action | Call control | Reviewer prompts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | __agent_open__ | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. Do you have a minute? | Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I'm looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. <break time="0.225s... | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "live_voic... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 2 | yeah sure | Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | Thanks, well, <break time="0.24s" /> quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today? | permission_acknowledgement |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "permission_acknowledgement", "source": "conte... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |
| 3 | can you help with my password? | If callback reminders for demo follow-up sit in a spreadsheet, they can slip. Which part is more familiar: manual tracking or missed callbacks? | If callback reminders for demo follow-up sit in a spreadsheet, they can slip, well, which part is more familiar: manual tracking or missed callbacks? | no_contextual_semantic |  |  |  | {"memory_update_key": null, "next_action": null, "question_type": null, "response_strategy": null, "semantic": "no_contextual_semantic", "source": "pre_speec... | continue-call | Did the agent understand this buyer turn correctly?; Did the next action match the conversation state?; Is the wording natural enough for a live appointment-setting call? |

## 6. Edge-Case Buckets

- `callback_timing`: 9 conversations
- `confusion`: 17 conversations
- `fallback_repair`: 11 conversations
- `long_conversation_state_drift`: 9 conversations
- `no_pain_current_issue_clear`: 10 conversations
- `not_relevant_no_need`: 9 conversations
- `pain_confirmed`: 10 conversations
- `permission_acknowledgement`: 9 conversations
- `possible_pain_ambiguity`: 9 conversations
- `regulated_caution`: 8 conversations
- `right_person_authority`: 9 conversations
- `routesignal_preservation`: 15 conversations
- `send_info`: 9 conversations
- `stop_refusal`: 9 conversations

## 7. Known Validator-Passed But Human-Questionable Examples

### generic-b2b-saas-possible-pain-then-confusion-004

- Scenario: `possible_pain_then_confusion`
- Last buyer turn: what do you mean?
- Last agent response: Sorry, I meant the areas in this fit check: manual work, integration risk, or visibility gap. Which part causes trouble, if any?
- Semantic: `previous_question_clarification`
- Call control: `continue-call`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-b2b-saas-send-info-email-capture-005

- Scenario: `send_info_email_capture`
- Last buyer turn: send it to <email:sha256_12:6db61e6dcbcf>
- Last agent response: Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary?
- Semantic: `email_provided`
- Call control: `continue-call`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-b2b-saas-callback-timing-capture-006

- Scenario: `callback_timing_capture`
- Last buyer turn: tomorrow at 3 works
- Last agent response: Confirmed. I will record that callback time for the specialist. Goodbye.
- Semantic: `callback_time_provided`
- Call control: `schedule-and-end`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-b2b-saas-right-person-handoff-007

- Scenario: `right_person_handoff`
- Last buyer turn: send it to <email:sha256_12:af3c82544f64>
- Last agent response: Got it. I will note that contact for operations. I will not send anything now.
- Semantic: `right_person_email_provided`
- Call control: `continue-call`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-b2b-saas-regulated-caution-refusal-stop-008

- Scenario: `regulated_caution_refusal_stop`
- Last buyer turn: actually one more thing
- Last agent response: Understood. I will stop here. Goodbye.
- Semantic: `no_contextual_semantic`
- Call control: `end-call`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-b2b-saas-fallback-repair-stack-009

- Scenario: `fallback_repair_stack`
- Last buyer turn: can you help with my password?
- Last agent response: The next step would be a short operations fit review. An implementation specialist can review the details, or I can stop here.
- Semantic: `no_contextual_semantic`
- Call control: `continue-call`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-b2b-saas-long-mixed-state-drift-010

- Scenario: `long_mixed_state_drift`
- Last buyer turn: can you help with my password?
- Last agent response: I cannot help with account support on this call. I can only note operations for operations fit review, or stop here.
- Semantic: `handoff_support_boundary`
- Call control: `continue-call`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-insurance-possible-pain-then-confusion-004

- Scenario: `possible_pain_then_confusion`
- Last buyer turn: what do you mean?
- Last agent response: Sorry, I meant the areas in this fit check: coverage fit, premium or budget, or renewal or timing. Which part causes trouble, if any?
- Semantic: `previous_question_clarification`
- Call control: `continue-call`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-insurance-send-info-email-capture-005

- Scenario: `send_info_email_capture`
- Last buyer turn: send it to <email:sha256_12:6db61e6dcbcf>
- Last agent response: Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary?
- Semantic: `email_provided`
- Call control: `continue-call`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-insurance-callback-timing-capture-006

- Scenario: `callback_timing_capture`
- Last buyer turn: tomorrow at 3 works
- Last agent response: Confirmed. I will record that callback time for the specialist. Goodbye.
- Semantic: `callback_time_provided`
- Call control: `schedule-and-end`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-insurance-right-person-handoff-007

- Scenario: `right_person_handoff`
- Last buyer turn: send it to <email:sha256_12:af3c82544f64>
- Last agent response: Got it. I will note that contact for operations. I will not send anything now.
- Semantic: `right_person_email_provided`
- Call control: `continue-call`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-insurance-regulated-caution-refusal-stop-008

- Scenario: `regulated_caution_refusal_stop`
- Last buyer turn: actually one more thing
- Last agent response: Understood. I will stop here. Goodbye.
- Semantic: `no_contextual_semantic`
- Call control: `end-call`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-insurance-fallback-repair-stack-009

- Scenario: `fallback_repair_stack`
- Last buyer turn: can you help with my password?
- Last agent response: The next step would be a short licensed coverage review. A licensed insurance specialist can review the details, or I can stop here.
- Semantic: `no_contextual_semantic`
- Call control: `continue-call`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-insurance-long-mixed-state-drift-010

- Scenario: `long_mixed_state_drift`
- Last buyer turn: what happens next?
- Last agent response: That sounds like the area to review, so the next step would be a short licensed coverage review. A licensed insurance specialist can review premium and budget pressure against the details; what time works?
- Semantic: `no_contextual_semantic`
- Call control: `continue-call`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-telecom-possible-pain-then-confusion-004

- Scenario: `possible_pain_then_confusion`
- Last buyer turn: what do you mean?
- Last agent response: Sorry, I meant the areas in this fit check: coverage or availability, plan fit, or contract or switching. Which part causes trouble, if any?
- Semantic: `previous_question_clarification`
- Call control: `continue-call`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-telecom-send-info-email-capture-005

- Scenario: `send_info_email_capture`
- Last buyer turn: send it to <email:sha256_12:6db61e6dcbcf>
- Last agent response: Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary?
- Semantic: `email_provided`
- Call control: `continue-call`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-telecom-callback-timing-capture-006

- Scenario: `callback_timing_capture`
- Last buyer turn: tomorrow at 3 works
- Last agent response: Confirmed. I will record that callback time for the specialist. Goodbye.
- Semantic: `callback_time_provided`
- Call control: `schedule-and-end`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-telecom-right-person-handoff-007

- Scenario: `right_person_handoff`
- Last buyer turn: send it to <email:sha256_12:af3c82544f64>
- Last agent response: Got it. I will note that contact for operations. I will not send anything now.
- Semantic: `right_person_email_provided`
- Call control: `continue-call`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-telecom-regulated-caution-refusal-stop-008

- Scenario: `regulated_caution_refusal_stop`
- Last buyer turn: actually one more thing
- Last agent response: Understood. I will stop here. Goodbye.
- Semantic: `no_contextual_semantic`
- Call control: `end-call`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-telecom-fallback-repair-stack-009

- Scenario: `fallback_repair_stack`
- Last buyer turn: can you help with my password?
- Last agent response: The next step would be a short plan and coverage review. A telecom plan specialist can review the details, or I can stop here.
- Semantic: `no_contextual_semantic`
- Call control: `continue-call`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-telecom-long-mixed-state-drift-010

- Scenario: `long_mixed_state_drift`
- Last buyer turn: call me next Tuesday at 10
- Last agent response: Confirmed. I will note that time for the plan and coverage review. Goodbye.
- Semantic: `appointment_time_given`
- Call control: `schedule-and-end`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-home-services-possible-pain-then-confusion-004

- Scenario: `possible_pain_then_confusion`
- Last buyer turn: what do you mean?
- Last agent response: Sorry, I meant the areas in this fit check: service need, scheduling urgency, or estimate or property details. Which part causes trouble, if any?
- Semantic: `previous_question_clarification`
- Call control: `continue-call`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-home-services-send-info-email-capture-005

- Scenario: `send_info_email_capture`
- Last buyer turn: send it to <email:sha256_12:6db61e6dcbcf>
- Last agent response: Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary?
- Semantic: `email_provided`
- Call control: `continue-call`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

### generic-home-services-callback-timing-capture-006

- Scenario: `callback_timing_capture`
- Last buyer turn: tomorrow at 3 works
- Last agent response: Confirmed. I will record that callback time for the specialist. Goodbye.
- Semantic: `callback_time_provided`
- Call control: `schedule-and-end`
- Why review:
  - Validator pass does not prove the response feels human.
  - State transitions and appointment pressure may still be debatable.
  - This case is useful for finding validator gaps rather than runtime crashes.

## 8. Suggested Human Review Rubric

Score each dimension 1 to 5, where 1 is poor and 5 is ready for live dry-run review.

- buyer meaning understood
- acknowledgement quality
- next action correctness
- appointment-setting appropriateness
- naturalness
- safety/compliance
- state consistency
- overall readiness

Failure categories:

- `missed_buyer_meaning`
- `wrong_semantic`
- `wrong_next_action`
- `too_pushy`
- `too_passive`
- `repeated_question`
- `unnatural_wording`
- `campaign_leakage`
- `unsafe_claim`
- `state_drift`
- `contact_capture_issue`
- `right_person_issue`
- `stop_refusal_issue`
- `tts_meaning_drift`
- `validator_gap`

## 9. Open Questions For Reviewer

- Which failures should become validators?
- Which issues are just copy polish?
- Which issues require semantic architecture changes?
- Which issues require campaign config changes?
- Which issues require live audio review?
- Is an LLM evaluator worth building after this packet?

## 10. Redaction And Safety Summary

- Synthetic examples only.
- No private transcripts.
- Raw synthetic emails are redacted as stable hash tokens.
- No secrets, API keys, env values, audio, or customer data are included.
- Provider calls false.
- Local LLM calls false.
- Live TTS false.
- Email/calendar/CRM writes false.
- PROD-102 false.
