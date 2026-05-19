# DIALOGUE-REASONER-001 Structured Runtime Reasoner

- Mode: `baseline`
- Cases: `30/30`
- Provider calls made: `false`
- Text sent to provider: `false`
- Live-demo response behavior changed: `false`
- Opens PROD-102: `false`

## Coverage

- dialogue_acts: `agent_open, ambiguous_negative, asr_fragment, callback_request, callback_time, caller_identity_question, effort_objection, fit_question, integration_question, low_information_acknowledgement, manual_tracking_objection, opening_greeting, plan_question, previous_question_clarification, price_question, product_question, recommendation_request, security_question, selected_gap, specialist_request, timing_objection, topic_shift, unknown, workflow_question`
- buyer_intents: `acknowledge_continue, ask_for_recommendation, change_topic, clarify_prior_question, compare_manual_process, confirm_callback_time, defer_timing, evaluate_effort, evaluate_fit, identify_caller, name_workflow_gap, off_topic_or_unclear, reject_or_decline_unclear, repair_asr, request_human, schedule_callback, small_talk_start, start_call, understand_plan_value, understand_price, understand_product, understand_workflow, verify_integration, verify_security`
- sales_stages: `boundary, discovery, objection_handling, opening, qualification, repair, scheduling, value_mapping`
- response_strategies: `answer_identity_then_offer_reason, answer_then_diagnose, ask_for_callback_time, avoid_unnecessary_handoff, clarify_prior_question, clarify_rejection_target, confirm_schedule_and_end, diagnose_before_recommendation, guarded_boundary, map_gap_to_value, open_with_permission, proactive_guided_selling, refocus_to_sales_call, repeat_request`
- safety_boundaries: `agency_preservation_boundary, asr_quality_boundary, human_handoff_boundary, integration_claim_boundary, none, security_claim_boundary`

## Cases

- `agent-open-starts-sales-call`: `pass` -> agent_open / qualification / open_with_permission
- `greeting-opens-like-sales-call`: `pass` -> opening_greeting / qualification / open_with_permission
- `caller-identity-recall-after-opener`: `pass` -> caller_identity_question / caller_identity / answer_identity_then_offer_reason
- `clarify-previous-question-qualification`: `pass` -> previous_question_clarification / qualification / clarify_prior_question
- `clarify-previous-question-price`: `pass` -> previous_question_clarification / price / clarify_prior_question
- `bare-no-after-opener`: `pass` -> ambiguous_negative / qualification / clarify_rejection_target
- `no-time-needs-callback-time`: `pass` -> callback_request / timing / ask_for_callback_time
- `callback-time-confirms-and-ends`: `pass` -> callback_time / timing / confirm_schedule_and_end
- `direct-price-question`: `pass` -> price_question / price / answer_then_diagnose
- `low-info-after-price`: `pass` -> low_information_acknowledgement / price / proactive_guided_selling
- `growth-plan-value`: `pass` -> plan_question / growth_plan / answer_then_diagnose
- `starter-plan-fit`: `pass` -> fit_question / starter_plan / answer_then_diagnose
- `product-explanation`: `pass` -> product_question / product_details / answer_then_diagnose
- `workflow-scope`: `pass` -> workflow_question / workflow_scope / answer_then_diagnose
- `manual-tracking-objection`: `pass` -> manual_tracking_objection / manual_tracking / answer_then_diagnose
- `handoffs-selected-after-price`: `pass` -> selected_gap / handoffs / map_gap_to_value
- `callbacks-selected-after-price`: `pass` -> selected_gap / callbacks / map_gap_to_value
- `fit-question`: `pass` -> fit_question / fit / answer_then_diagnose
- `timing-objection`: `pass` -> timing_objection / timing / answer_then_diagnose
- `effort-worth-objection`: `pass` -> effort_objection / effort / answer_then_diagnose
- `salesforce-integration-boundary`: `pass` -> integration_question / integration / guarded_boundary
- `security-boundary`: `pass` -> security_question / security / guarded_boundary
- `specialist-not-needed-for-basics`: `pass` -> specialist_request / handoff_boundary / avoid_unnecessary_handoff
- `topic-shift-price-to-product`: `pass` -> topic_shift / product_details / answer_then_diagnose
- `topic-shift-price-to-workflow`: `pass` -> topic_shift / workflow_scope / answer_then_diagnose
- `repeat-price-without-loop`: `pass` -> price_question / price / proactive_guided_selling
- `generic-followup-after-qualification`: `pass` -> low_information_acknowledgement / qualification / proactive_guided_selling
- `asr-fragment-repair`: `pass` -> asr_fragment / asr_quality / repeat_request
- `off-topic-unclear-turn`: `pass` -> unknown / unknown / refocus_to_sales_call
- `recommendation-request-preserves-agency`: `pass` -> recommendation_request / price / diagnose_before_recommendation
