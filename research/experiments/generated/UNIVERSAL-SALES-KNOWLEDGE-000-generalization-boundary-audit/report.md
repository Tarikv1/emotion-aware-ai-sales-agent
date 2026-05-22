# UNIVERSAL-SALES-KNOWLEDGE-000 Generalization Boundary Audit

Audit date: 2026-05-21

Scope: targeted read of the contextual semantics runtime, dialogue manager, RouteSignal diagnostic playbook, live voice policy surfaces, validators 001 through 010, campaign profile, and relevant product/brain docs. This phase did not change runtime behavior and did not inspect private transcripts.

## Executive Recommendation

Do not turn the current RouteSignal diagnostic playbook into the universal sales knowledge layer.

The current implementation has a reusable semantic frame, action contract, call-control model, and local lead-follow-up state. Those pieces are good candidates for universal core logic. The new `sales_diagnostic_playbook.py`, however, is explicitly a RouteSignal/Northstar B2B SaaS campaign playbook. It should become a campaign playbook behind an adapter, not the base universal knowledge source.

The next implementation should be 4B1: add a compact `universal_sales_knowledge.py` module with no product facts. Then add vertical adapter skeletons and a campaign playbook adapter before migrating RouteSignal onto the new boundary.

## 1. Current Coupling Map

### Universal Pieces

- `runtime/core/contextual_buyer_semantics.py`
  - Semantic frame structure: semantic id, schema version, semantic label, target gap/topic, polarity, confidence, evidence, next action hint, must-not-do list, response/action hints, provider/local LLM safety flags.
  - Context-sensitive interpretation shape: previous agent question, conversation stage, active gap, confirmed gaps, cleared gaps, pending callback, pending appointment, terminal call-control state.
  - General buyer move families already modeled: permission acknowledgement, social acknowledgement, low-information continue, no-pain/current-gap clear, pain confirmed, confusion, term question, callback scheduling, appointment hesitation, send-info, wrong person, stop request.
  - Multi-turn state handling concepts: `cleared_gaps`, `confirmed_gaps`, `candidate_gaps`, `answered_gaps`, `outgoing_candidate_gaps`, active gap scope.

- `runtime/core/dialogue_manager.py`
  - Manager-level action selection and trace exposure.
  - Action/template/call-control tables for send-info, callback, appointment, right-person handoff, refusal, and stop handling.
  - Durable memory exposure for semantic frame, selected action, call control, `send_info_state`, `lead_followup_state`, and `handoff_target_state`.

- Send-info/contact-capture state
  - Structurally reusable across verticals: requested info, email/contact capture, callback time capture, refused contact, human follow-up needed, lead status.
  - Privacy and safety policy is universal: no email sending, no CRM write, no calendar event, redacted/hash evidence, provider calls false, local LLM calls false.

- Lead follow-up state
  - Structurally reusable: email-only lead, callback-time lead, workflow-review appointment lead, unclear contact, invalid email-like speech, ASR-spelled email, normalized callback time.

- Right-person/handoff state
  - Structurally reusable: wrong person, department/team capture, person name capture, contact detail capture, refusal, human follow-up needed.

- Call-control rules
  - Reusable control values: `continue-call`, `schedule-and-end`, `end-call`.
  - Terminal stop persistence is universal.

### Campaign-Specific Pieces

- `runtime/core/sales_diagnostic_playbook.py`
  - Explicit playbook id: `ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001`.
  - Campaign context: `RouteSignal CRM`, `Northstar`, appointment-setting objective.
  - Core gaps: callbacks, manual tracking, handoffs, routing, reminders, duplicates, visibility, right person.
  - Definitions, evidence phrases, value bridges, and review focus labels are tied to inbound demo follow-up.

- `runtime/core/live_voice_session_policy.py`
  - Campaign opener and protected wording mention Northstar, RouteSignal, inbound demo follow-up, callbacks, handoffs, and workflow review.
  - Pricing/plan responses mention Starter, Growth, `$29/month`, and `$59/month`.
  - Fallbacks and value bridges are written for the RouteSignal live demo.

- `research/experiments/cases/live-demo-001-fictional-b2b-sales-campaign.json`
  - Source campaign facts: Northstar Workflow Labs, RouteSignal CRM, B2B CRM category, demo/contact-sales requests, shared inbox/spreadsheet pains, plan/pricing facts, allowed and forbidden claims.

- Product checkpoint docs
  - `docs/product/LIVE_DEMO_014_CLEAR_PAIN_CALLBACK_FOLLOWUP.md`
  - `docs/product/DIALOGUE_MANAGER_003_PLAIN_SALES_CLARITY_AND_VAGUE_APPOINTMENT_TIME.md`
  - These define a RouteSignal live-demo behavior target, not a universal sales agent.

- Validator 010
  - `scripts/validate_contextual_buyer_semantics_010_diagnostic_playbook.py` is intentionally RouteSignal-specific. It asserts RouteSignal gaps, review focus labels, and routing/contact distinctions in the B2B SaaS demo context.

### Mixed Pieces

- `runtime/core/contextual_buyer_semantics.py`
  - The file name and semantic frame imply universal buyer semantics, but it imports the RouteSignal diagnostic playbook directly.
  - `CORE_DIAGNOSTIC_GAPS` is derived from the RouteSignal playbook and currently makes callbacks/manual tracking/handoffs the default diagnostic universe.
  - Some generated responses contain Northstar, RouteSignal, demo follow-up, Growth, or workflow-review wording.

- `runtime/core/dialogue_manager.py`
  - The action contract is mostly universal, but workflow-review and review-focus behavior currently assumes a RouteSignal-style appointment target.
  - Memory traces expose playbook metadata without a clean separation between universal knowledge and campaign playbook source.

- Validators 001 through 009
  - They test universal behavior classes, but most use RouteSignal gap IDs or live-demo conversation shape. They are valuable, but they cannot prove cross-vertical generality.

## 2. RouteSignal-Specific Assumptions Found

| File | Symbol or area | Why campaign-specific | Recommendation |
| --- | --- | --- | --- |
| `runtime/core/sales_diagnostic_playbook.py` | `PLAYBOOK_ID`, `PLAYBOOK`, `campaign_context` | Explicitly names RouteSignal CRM and Northstar. | Keep as RouteSignal campaign playbook behind adapter. |
| `runtime/core/sales_diagnostic_playbook.py` | `gaps.callbacks` | Demo/inbound callback follow-up pain. | Campaign gap, map to universal `missed_follow_up`. |
| `runtime/core/sales_diagnostic_playbook.py` | `gaps.manual_tracking` | Spreadsheet/shared-inbox follow-up tracking pain. | Campaign gap, map to universal `manual_work` and `follow_up_tracking`. |
| `runtime/core/sales_diagnostic_playbook.py` | `gaps.handoffs` | Demo lead ownership and next reply handoff. | Campaign gap, map to universal `ownership_confusion`. |
| `runtime/core/sales_diagnostic_playbook.py` | `gaps.routing` | Inbound demo lead owner assignment. | Campaign gap, separate from contact/right-person routing. |
| `runtime/core/sales_diagnostic_playbook.py` | `gaps.reminders`, `duplicates`, `visibility` | RouteSignal CRM value model. | Campaign or B2B SaaS vertical gaps, not universal defaults. |
| `runtime/core/sales_diagnostic_playbook.py` | `rank_confirmed_gaps`, `remaining_gaps`, matching helpers | Helper shape is reusable, but current evidence lists and ranking are RouteSignal-specific. | Move generic ranking policy to universal module; leave evidence in campaign playbook. |
| `runtime/core/contextual_buyer_semantics.py` | `from runtime.core import sales_diagnostic_playbook` | Universal semantics directly depends on RouteSignal facts. | Replace with campaign adapter input in 4B3. |
| `runtime/core/contextual_buyer_semantics.py` | `CORE_DIAGNOSTIC_GAPS` | Defaults to RouteSignal core gaps. | Source from campaign playbook through adapter, with universal fallback only for abstract pain dimensions. |
| `runtime/core/contextual_buyer_semantics.py` | Response helpers mentioning demo follow-up, RouteSignal, Growth, workflow review | Spoken text is campaign copy. | Move to campaign response adapter or template layer. |
| `runtime/core/dialogue_manager.py` | Workflow-review action wording and playbook trace | Useful action model, but review target is campaign-specific. | Keep action ids universal; campaign adapter supplies appointment target wording. |
| `runtime/core/live_voice_session_policy.py` | opener, price answer, plan boundary response | Direct Northstar/RouteSignal/Starter/Growth copy. | Keep as RouteSignal live-demo policy until adapter migration. |
| `research/experiments/cases/live-demo-001-fictional-b2b-sales-campaign.json` | Product/client/pricing/facts | Campaign source of truth. | Should feed campaign playbook adapter. |
| `scripts/validate_contextual_buyer_semantics_001.py` through `005.py` | callbacks/manual_tracking/handoffs examples | Universal state behavior using campaign gap IDs. | Keep as RouteSignal regressions and create universal equivalents. |
| `scripts/validate_contextual_buyer_semantics_006.py` through `009.py` | send-info/right-person scenarios | Workflow is universal, but still shaped by live-demo opener and callback examples. | Promote generic versions; keep RouteSignal variants. |
| `scripts/validate_contextual_buyer_semantics_010_diagnostic_playbook.py` | required playbook gaps and review labels | Intentionally asserts RouteSignal diagnostic playbook behavior. | Keep as RouteSignal campaign regression after adapter migration. |

## 3. Universal Sales Knowledge Contract Proposal

Module: `runtime/core/universal_sales_knowledge.py`

Purpose: deterministic, product-agnostic sales reasoning primitives. It must not mention RouteSignal, Northstar, pricing, demo leads, specific plans, or campaign-specific features.

Suggested contract:

```python
UNIVERSAL_SALES_KNOWLEDGE = {
    "knowledge_id": "UNIVERSAL-SALES-KNOWLEDGE-001",
    "schema_version": 1,
    "sales_stages": {...},
    "buyer_move_families": {...},
    "qualification_dimensions": {...},
    "generic_pain_dimensions": {...},
    "objection_families": {...},
    "safe_next_action_policies": {...},
    "call_control_policy": {...},
    "regulated_vertical_cautions": {...},
}
```

Required universal concepts:

- Sales stages
  - opening
  - permission
  - discovery
  - qualification
  - value_mapping
  - objection_or_resistance
  - send_info
  - callback_scheduling
  - appointment_setting
  - right_person_handoff
  - refusal_or_stop
  - close_or_end

- Buyer move families
  - permission acknowledgement
  - social acknowledgement
  - low-information continue
  - current issue clear
  - all clear or no pain
  - pain confirmed
  - possible pain but unclear
  - confusion or term question
  - objection
  - timing deferral
  - send-info request
  - callback request
  - appointment acceptance, hesitation, or time given
  - wrong person or authority unclear
  - refusal, not interested, stop request

- Qualification dimensions
  - need or pain
  - urgency
  - authority or right person
  - fit
  - current solution or status quo
  - budget or price sensitivity
  - timing
  - contact path
  - compliance or risk constraints

- Generic pain dimensions
  - missed follow-up
  - delay
  - ownership confusion
  - manual work
  - duplicate work
  - visibility gap
  - customer experience friction
  - trust or risk concern
  - cost or time waste
  - unclear next step

- Objection families
  - no need or all set
  - not relevant
  - not interested
  - timing
  - price
  - authority
  - existing vendor or process
  - trust
  - privacy or security
  - complexity
  - send info first
  - stop or do-not-contact

- Safe next-action policies
  - ask next diagnostic if current issue is clear and more relevant dimensions remain
  - clarify if buyer is confused
  - do not push appointment on confusion or no-pain
  - bridge to appointment only after credible pain or buyer interest
  - capture send-info contact without pretending an appointment exists
  - capture callback time before schedule-and-end
  - route wrong person toward right contact or polite close
  - end on explicit stop request

- Regulated vertical caution boundaries
  - no legal, medical, financial, or insurance advice
  - no coverage, diagnosis, guaranteed savings, guaranteed outcome, eligibility, compliance, or ROI claims unless campaign explicitly allows them
  - escalate to human for regulated advice, policy interpretation, clinical judgment, coverage decisions, contracts, payments, or cancellation disputes

## 4. Vertical Adapter Contract Proposal

Module: `runtime/core/vertical_sales_playbooks.py`

Purpose: vertical-level defaults between universal sales logic and campaign-specific facts. A vertical adapter should not know a specific client/product name unless it is passed through the campaign contract.

Suggested vertical adapter fields:

```python
{
    "vertical_id": "...",
    "schema_version": 1,
    "default_pain_dimensions": [],
    "typical_buyer_roles": [],
    "authority_signals": [],
    "common_objections": [],
    "qualification_defaults": [],
    "safe_appointment_targets": [],
    "regulated_cautions": [],
    "forbidden_default_claims": [],
    "human_escalation_triggers": [],
}
```

Required verticals:

- `b2b_saas`
  - Typical concerns: workflow inefficiency, adoption, integration, security, pricing, admin ownership.
  - Caution: do not claim integrations, certifications, uptime, ROI, or data processing posture unless campaign allows it.

- `insurance`
  - Typical concerns: coverage, premium, eligibility, renewal, claims, exclusions.
  - Caution: no coverage advice, legal advice, guaranteed premium savings, eligibility decisions, or policy interpretation. Human handoff for regulated questions.

- `telecom`
  - Typical concerns: plan fit, coverage, speed, contract, device, support, switching.
  - Caution: no guaranteed savings, coverage, speed, cancellation terms, or contract claims unless campaign allows it.

- `home_services`
  - Typical concerns: booking, urgency, estimate, availability, trust, licensing, service area.
  - Caution: no safety diagnosis, code/legal claims, guaranteed estimates, or emergency advice unless campaign allows it.

- `healthcare_admin_or_medical_equipment`
  - Typical concerns: scheduling, admin burden, equipment fit, service support, procurement.
  - Caution: no medical advice, diagnosis, treatment recommendation, patient-specific eligibility, or clinical claims.

- `automotive_service`
  - Typical concerns: repair timing, inspection, maintenance, warranty, estimate, scheduling.
  - Caution: no remote safety diagnosis, guaranteed repair cost, warranty interpretation, or legal/liability claims.

- `membership_or_subscription`
  - Typical concerns: value, renewal, cancellation, trial, account fit, usage.
  - Caution: no misleading renewal/cancellation statements; escalate billing disputes and cancellation requests to human policy.

- `retail_or_ecommerce_support_sales`
  - Typical concerns: product fit, shipping, returns, warranty, availability, upsell/cross-sell.
  - Caution: no false stock, delivery, refund, warranty, or price claims.

## 5. Campaign Playbook Contract Proposal

Module: `runtime/core/campaign_playbook_adapter.py`

Purpose: normalize a campaign's product facts, allowed claims, diagnostics, and appointment target into a contract consumed by contextual semantics and dialogue manager.

Suggested campaign playbook fields:

```python
{
    "campaign_id": "...",
    "schema_version": 1,
    "client_name": "...",
    "product_name": "...",
    "vertical_id": "...",
    "objective": "appointment_setting",
    "human_followup_owner": "...",
    "allowed_claims": [],
    "forbidden_claims": [],
    "pricing_or_plan_facts": [],
    "qualification_goals": [],
    "diagnostic_gaps": {},
    "review_or_appointment_target": "...",
    "handoff_owner": "...",
    "send_info_policy": {},
    "callback_policy": {},
    "right_person_policy": {},
    "escalation_triggers": [],
    "spoken_terms": {},
}
```

RouteSignal mapping:

- `client_name`: Northstar Workflow Labs.
- `product_name`: RouteSignal CRM.
- `vertical_id`: `b2b_saas`.
- `objective`: appointment-setting, not full sale closure.
- `human_followup_owner`: Northstar.
- `diagnostic_gaps`: callbacks, manual tracking, handoffs, routing, reminders, duplicates, visibility, right person.
- Universal pain mapping:
  - callbacks -> missed follow-up.
  - manual tracking -> manual work and follow-up tracking.
  - handoffs -> ownership confusion.
  - routing -> assignment delay.
  - reminders -> missed follow-up support.
  - duplicates -> duplicate work and ownership confusion.
  - visibility -> manager visibility gap.
  - right person -> authority or contact path.
- `review_or_appointment_target`: short workflow review with a human from Northstar.
- `pricing_or_plan_facts`: Starter and Growth facts only if the campaign allows them in the current checkpoint.
- `forbidden_claims`: guaranteed conversion/revenue/ROI, replaces every CRM, SOC 2 certified, payment/contract closure.

## 6. Validator Migration Plan

| Validator | Current classification | Keep as RouteSignal campaign regression? | Needs universal equivalent? | Vertical smoke test candidate? |
| --- | --- | --- | --- | --- |
| `validate_contextual_buyer_semantics_001.py` | Mixed | Yes | Yes | No |
| `validate_contextual_buyer_semantics_002_sequential_dialogue.py` | Mixed | Yes | Yes | No |
| `validate_contextual_buyer_semantics_003_memory_alignment.py` | Mixed | Yes | Yes | No |
| `validate_contextual_buyer_semantics_004_semantic_memory_invariants.py` | Mixed | Yes | Yes | No |
| `validate_contextual_buyer_semantics_005_outgoing_question_state.py` | Mixed | Yes | Yes | No |
| `validate_contextual_buyer_semantics_006_send_info_contact_capture.py` | Mostly universal with campaign examples | Yes | Yes | Yes |
| `validate_contextual_buyer_semantics_007_send_info_action_contract.py` | Mostly universal | Yes | Yes | Yes |
| `validate_contextual_buyer_semantics_008_contact_time_normalization.py` | Mostly universal | Yes | Yes | Yes |
| `validate_contextual_buyer_semantics_009_right_person_handoff.py` | Mostly universal with B2B/product-routing distinction | Yes | Yes | Yes |
| `validate_contextual_buyer_semantics_010_diagnostic_playbook.py` | RouteSignal-specific | Yes | No, create separate universal knowledge validator | B2B SaaS vertical only |

Future universal equivalents should use abstract pain dimensions instead of RouteSignal gaps. Example: `missed_follow_up`, `manual_work`, `ownership_confusion`, `visibility_gap`, `contact_path`, `authority_unclear`.

Future vertical smoke tests should avoid proving full campaign behavior. They should check that universal routes remain safe under each vertical profile: send-info, callback, right-person handoff, stop/refusal, regulated caution, and appointment capture.

## 7. Recommended Next Implementation Phases

### 4B1 - Universal Sales Knowledge Module

Add `runtime/core/universal_sales_knowledge.py`.

Minimum contents:

- sales stages
- buyer move families
- qualification dimensions
- generic pain dimensions
- objection families
- safe next-action policies
- call-control policy
- regulated vertical caution boundaries

Add a narrow validator proving the module has no RouteSignal/Northstar/product-specific facts.

### 4B2 - Vertical Adapter Skeletons

Add `runtime/core/vertical_sales_playbooks.py`.

Include required verticals:

- `b2b_saas`
- `insurance`
- `telecom`
- `home_services`
- `healthcare_admin_or_medical_equipment`
- `automotive_service`
- `membership_or_subscription`
- `retail_or_ecommerce_support_sales`

Keep adapters compact and deterministic. Do not add campaign scripts yet.

### 4B3 - Campaign Playbook Adapter

Add `runtime/core/campaign_playbook_adapter.py`.

Move RouteSignal-specific diagnostic playbook usage behind the adapter. `contextual_buyer_semantics.py` should consume an adapted campaign playbook, not import `sales_diagnostic_playbook.py` directly as universal truth.

### 4B4 - Cross-Vertical Smoke Tests

Add synthetic tests across the required verticals:

- permission to diagnostic
- no-pain handling
- pain to appointment bridge
- send-info capture
- callback scheduling
- wrong-person handoff
- stop/refusal handling
- regulated caution handling where applicable

No provider calls, no real data, no CRM/email/calendar writes.

### 4B5 - RouteSignal Regression After Adapter Migration

Re-run RouteSignal validators 001 through 010 and live-demo 014 after the adapter migration. The goal is behavior preservation with cleaner source boundaries, not a new live-demo behavior change.

## Main Risk

The biggest risk is implementing "universal sales knowledge" by adding more phrases and vertical examples into the current RouteSignal path. That would make the agent look broader while keeping the wrong dependency direction: universal semantics would still depend on one campaign's gap vocabulary.

The safer refactor is small and staged:

1. Universal primitives with no product facts.
2. Vertical defaults with no client facts.
3. Campaign adapter with RouteSignal as the first campaign.
4. Smoke tests for vertical safety.
5. RouteSignal regression to prove no live-demo behavior was lost.

