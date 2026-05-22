from __future__ import annotations

from copy import deepcopy
from typing import Any


KNOWLEDGE_ID = "UNIVERSAL-SALES-KNOWLEDGE-001"
SCHEMA_VERSION = 1

_NO_SIDE_EFFECTS = {
    "provider_calls_made": False,
    "local_llm_calls_made": False,
    "sends_email": False,
    "creates_calendar_event": False,
    "writes_crm": False,
}


UNIVERSAL_SALES_KNOWLEDGE: dict[str, Any] = {
    "knowledge_id": KNOWLEDGE_ID,
    "schema_version": SCHEMA_VERSION,
    "sales_stages": {
        "opening": {
            "description": "Start the conversation, identify the caller role, and make the reason for outreach understandable without making a claim that needs product proof.",
            "allowed_next_actions": ["ask_permission", "clarify_purpose", "polite_close_if_refused"],
            "blocked_actions": ["diagnose_before_permission", "pressure_for_meeting", "state_unverified_claims"],
            "call_control_defaults": ["continue-call", "end-call"],
        },
        "permission": {
            "description": "Check whether the buyer has time and willingness to continue.",
            "allowed_next_actions": ["continue_to_discovery", "schedule_callback", "end_if_no_time_or_stop"],
            "blocked_actions": ["ignore_no", "skip_to_appointment", "continue_after_explicit_stop"],
            "call_control_defaults": ["continue-call", "schedule-and-end", "end-call"],
        },
        "discovery": {
            "description": "Ask a narrow diagnostic question to learn whether a relevant business issue exists.",
            "allowed_next_actions": ["ask_diagnostic", "clarify_question", "acknowledge_clear_issue", "acknowledge_confirmed_issue"],
            "blocked_actions": ["assume_pain", "ask_unrelated_diagnostic", "sell_without_context"],
            "call_control_defaults": ["continue-call"],
        },
        "qualification": {
            "description": "Confirm whether the issue, timing, authority, fit, and next contact path justify human follow-up.",
            "allowed_next_actions": ["ask_qualification_dimension", "summarize_evidence", "move_to_next_step_if_qualified"],
            "blocked_actions": ["claim_full_fit_without_evidence", "erase_prior_evidence", "overqualify_after_refusal"],
            "call_control_defaults": ["continue-call"],
        },
        "value_mapping": {
            "description": "Map confirmed buyer evidence to a general outcome principle while staying inside allowed campaign claims.",
            "allowed_next_actions": ["bridge_to_human_review", "offer_summary", "ask_next_relevant_question"],
            "blocked_actions": ["invent_roi", "invent_feature", "turn_no_pain_into_value_claim"],
            "call_control_defaults": ["continue-call"],
        },
        "objection_or_resistance": {
            "description": "Handle concern, hesitation, not-relevant language, timing resistance, or trust concerns without treating resistance as consent.",
            "allowed_next_actions": ["acknowledge_objection", "ask_one_clarifier", "offer_lower_pressure_next_step", "end_if_resistance_persists"],
            "blocked_actions": ["repeat_same_pitch", "pressure_after_refusal", "ignore_reason_given"],
            "call_control_defaults": ["continue-call", "end-call"],
        },
        "send_info": {
            "description": "When the buyer asks for written information, keep the lead state open and safely capture an email or callback path without pretending a meeting is confirmed.",
            "allowed_next_actions": ["request_email_or_callback_time", "capture_contact", "confirm_summary_note", "polite_close_if_contact_refused"],
            "blocked_actions": ["send_real_email", "invent_contact", "confirm_appointment_without_time"],
            "call_control_defaults": ["continue-call", "end-call"],
        },
        "callback_scheduling": {
            "description": "Capture a usable callback time when the buyer asks for later contact or provides a later time.",
            "allowed_next_actions": ["request_missing_time", "confirm_callback_time", "end_after_callback_confirmation"],
            "blocked_actions": ["confirm_without_time", "invent_calendar_event", "continue_selling_after_callback_confirmed"],
            "call_control_defaults": ["continue-call", "schedule-and-end"],
        },
        "appointment_setting": {
            "description": "After credible pain or buyer interest, ask for a human follow-up conversation and capture a concrete time if the buyer agrees.",
            "allowed_next_actions": ["ask_if_review_is_useful", "request_appointment_time", "confirm_appointment_time"],
            "blocked_actions": ["push_on_no_pain", "push_on_confusion", "confirm_without_buyer_time"],
            "call_control_defaults": ["continue-call", "schedule-and-end"],
        },
        "right_person_handoff": {
            "description": "If the speaker is not the right contact, capture the right person, team, or safe contact path, or end politely.",
            "allowed_next_actions": ["ask_for_right_person", "capture_right_person_contact", "offer_to_stop"],
            "blocked_actions": ["treat_contact_routing_as_product_pain", "pressure_wrong_person", "invent_target_contact"],
            "call_control_defaults": ["continue-call", "end-call"],
        },
        "refusal_or_stop": {
            "description": "Respect clear refusal, not-interested language, or do-not-contact requests.",
            "allowed_next_actions": ["acknowledge_refusal", "end_call", "record_terminal_state_locally"],
            "blocked_actions": ["continue_pitch", "ask_more_diagnostics", "request_appointment"],
            "call_control_defaults": ["end-call"],
        },
        "close_or_end": {
            "description": "Close the turn after a confirmed callback, appointment, explicit refusal, or safe no-fit outcome.",
            "allowed_next_actions": ["confirm_next_step", "say_goodbye", "stop_after_terminal_state"],
            "blocked_actions": ["restart_conversation", "add_new_pitch", "change_confirmed_next_step"],
            "call_control_defaults": ["schedule-and-end", "end-call"],
        },
    },
    "buyer_move_families": {
        "permission_acknowledgement": {
            "description": "The buyer grants permission to continue after a time or consent check.",
            "typical_contexts": ["after_permission_question", "after_call_purpose_check"],
            "safe_interpretation_rule": "Treat as permission only when it answers the agent's permission question.",
            "unsafe_interpretation_examples": ["Treating a generic yes as pain confirmation", "Treating permission as appointment consent"],
            "recommended_next_action": "continue_to_first_diagnostic",
        },
        "social_acknowledgement": {
            "description": "A polite acknowledgement that does not provide diagnostic, scheduling, or buying information.",
            "typical_contexts": ["after_intro", "after_explanation", "after_low_pressure_statement"],
            "safe_interpretation_rule": "Acknowledge briefly and ask the next relevant question.",
            "unsafe_interpretation_examples": ["Classifying social politeness as no-pain", "Classifying social politeness as consent"],
            "recommended_next_action": "ask_contextually_relevant_question",
        },
        "low_information_continue": {
            "description": "The buyer keeps the conversation open but does not answer the requested detail.",
            "typical_contexts": ["after_time_request", "after_contact_request", "after_diagnostic_question"],
            "safe_interpretation_rule": "Repeat or narrow the missing question once instead of guessing.",
            "unsafe_interpretation_examples": ["Inventing a time", "Treating vague agreement as scheduled"],
            "recommended_next_action": "request_missing_detail_again",
        },
        "current_issue_clear": {
            "description": "The buyer says the currently asked-about issue is not happening or is handled.",
            "typical_contexts": ["after_single_issue_diagnostic", "after_multi_issue_diagnostic_with_named_issue"],
            "safe_interpretation_rule": "Mark only the answered issue clear and ask about remaining relevant issues if no confirmed pain exists.",
            "unsafe_interpretation_examples": ["Erasing previously confirmed pain", "Treating a clear issue as pain"],
            "recommended_next_action": "ask_next_diagnostic_if_available",
        },
        "all_clear_or_no_pain": {
            "description": "The buyer says the relevant scope has no issue or is already handled.",
            "typical_contexts": ["after_multi_issue_diagnostic", "after_broad_relevance_check"],
            "safe_interpretation_rule": "Treat as no-pain for the asked scope unless the buyer also names a pain point.",
            "unsafe_interpretation_examples": ["Pushing for appointment anyway", "Repeating the same diagnostic"],
            "recommended_next_action": "ask_one_final_save_or_end_politely",
        },
        "pain_confirmed": {
            "description": "The buyer confirms a relevant problem, gap, friction, risk, delay, or cost.",
            "typical_contexts": ["after_diagnostic_question", "spontaneous_problem_statement"],
            "safe_interpretation_rule": "Store the confirmed issue and bridge to a human next step without overstating product claims.",
            "unsafe_interpretation_examples": ["Jumping to payment", "Inventing outcome guarantees"],
            "recommended_next_action": "bridge_to_human_follow_up_or_appointment",
        },
        "possible_pain_unclear": {
            "description": "The buyer gives partial, ambiguous, or qualified evidence that may indicate a problem.",
            "typical_contexts": ["hedged_answer", "mixed_answer", "uncertain_answer"],
            "safe_interpretation_rule": "Ask a short clarifier before treating the issue as confirmed.",
            "unsafe_interpretation_examples": ["Treating maybe as confirmed", "Ignoring the ambiguous evidence"],
            "recommended_next_action": "ask_clarifying_diagnostic",
        },
        "confusion_or_term_question": {
            "description": "The buyer does not understand the question, term, purpose, or next step.",
            "typical_contexts": ["what_do_you_mean", "not_clear", "purpose_question"],
            "safe_interpretation_rule": "Clarify in plain language and do not push an appointment until comprehension is restored.",
            "unsafe_interpretation_examples": ["Treating confusion as objection", "Treating confusion as no-pain"],
            "recommended_next_action": "clarify_previous_question",
        },
        "objection": {
            "description": "The buyer raises a reason not to continue, buy, trust, or prioritize the conversation.",
            "typical_contexts": ["price_concern", "current_process", "trust_concern", "too_busy"],
            "safe_interpretation_rule": "Address the objection family once and preserve the buyer's option to stop.",
            "unsafe_interpretation_examples": ["Arguing repeatedly", "Skipping acknowledgement"],
            "recommended_next_action": "acknowledge_and_choose_low_pressure_next_step",
        },
        "timing_deferral": {
            "description": "The buyer indicates the timing is bad without necessarily refusing future contact.",
            "typical_contexts": ["busy_now", "not_today", "try_later"],
            "safe_interpretation_rule": "Ask for a callback time if future contact remains acceptable.",
            "unsafe_interpretation_examples": ["Ending without asking for time", "Continuing the pitch after bad timing"],
            "recommended_next_action": "request_callback_time",
        },
        "send_info_request": {
            "description": "The buyer asks for written details, a summary, or information before deciding.",
            "typical_contexts": ["send_details", "email_me", "put_it_in_writing"],
            "safe_interpretation_rule": "Ask for an email or callback path and keep any appointment unconfirmed until time is given.",
            "unsafe_interpretation_examples": ["Pretending an appointment is booked", "Sending real email from runtime"],
            "recommended_next_action": "capture_send_info_contact",
        },
        "callback_request": {
            "description": "The buyer asks to be called later or gives a future callback window.",
            "typical_contexts": ["call_later", "tomorrow_time", "next_week_window"],
            "safe_interpretation_rule": "Capture the usable time; ask for missing day or time if ambiguous.",
            "unsafe_interpretation_examples": ["Scheduling without time", "Treating callback as no-interest"],
            "recommended_next_action": "capture_or_clarify_callback_time",
        },
        "appointment_acceptance": {
            "description": "The buyer indicates a human follow-up conversation would be useful.",
            "typical_contexts": ["after_review_offer", "after_human_follow_up_offer"],
            "safe_interpretation_rule": "Ask for a concrete time unless the buyer already gave one.",
            "unsafe_interpretation_examples": ["Ending before time capture", "Treating interest as confirmed schedule"],
            "recommended_next_action": "request_appointment_time",
        },
        "appointment_hesitation": {
            "description": "The buyer is not ready to book but has not refused.",
            "typical_contexts": ["need_to_think", "maybe", "send_info_first"],
            "safe_interpretation_rule": "Offer a lower-pressure written summary or callback path without forcing the appointment.",
            "unsafe_interpretation_examples": ["Dropping the lead immediately", "Pressuring after hesitation"],
            "recommended_next_action": "offer_summary_or_callback_path",
        },
        "appointment_time_given": {
            "description": "The buyer provides a usable time for a human follow-up conversation.",
            "typical_contexts": ["after_time_request", "spontaneous_time_offer"],
            "safe_interpretation_rule": "Confirm the time and end if the scheduling policy allows it.",
            "unsafe_interpretation_examples": ["Continuing diagnostics after confirmed time", "Changing the time"],
            "recommended_next_action": "confirm_time_and_schedule_end",
        },
        "wrong_person_or_authority_unclear": {
            "description": "The buyer indicates they are not the right owner or authority is elsewhere.",
            "typical_contexts": ["wrong_person", "another_team_handles_it", "manager_handles_it"],
            "safe_interpretation_rule": "Route toward the right person or close politely; do not treat contact routing as product pain.",
            "unsafe_interpretation_examples": ["Selecting a product gap from contact words", "Pushing the wrong person"],
            "recommended_next_action": "request_right_person_or_close",
        },
        "refusal_not_interested": {
            "description": "The buyer says they do not want the offer, do not need it, or are not interested.",
            "typical_contexts": ["not_interested", "not_relevant", "no_need"],
            "safe_interpretation_rule": "Acknowledge and end or ask at most one context-safe save question if the stage allows it.",
            "unsafe_interpretation_examples": ["Repeating diagnostics", "Ignoring stated lack of interest"],
            "recommended_next_action": "polite_close_or_one_save_question",
        },
        "stop_request": {
            "description": "The buyer explicitly asks the caller to stop, remove them, or not call again.",
            "typical_contexts": ["do_not_call", "remove_me", "stop"],
            "safe_interpretation_rule": "End immediately and preserve the terminal state.",
            "unsafe_interpretation_examples": ["Continuing the call", "Asking another diagnostic"],
            "recommended_next_action": "end_call",
        },
    },
    "qualification_dimensions": {
        "need_or_pain": {
            "purpose": "Determine whether a meaningful issue exists.",
            "positive_evidence_shape": ["specific friction", "repeated issue", "costly delay", "risk or lost opportunity"],
            "negative_evidence_shape": ["handled", "not happening", "not relevant", "all set"],
            "safe_next_action": "If positive, bridge to human next step; if negative, ask another relevant dimension or close.",
        },
        "urgency": {
            "purpose": "Understand whether the issue is current, recurring, or future-facing.",
            "positive_evidence_shape": ["happening now", "recent incident", "recurring problem", "deadline"],
            "negative_evidence_shape": ["rare", "not active", "future maybe", "no timeline"],
            "safe_next_action": "Match follow-up pressure to urgency and avoid overstating need.",
        },
        "authority_or_right_person": {
            "purpose": "Identify whether the speaker can evaluate, route, or schedule the next step.",
            "positive_evidence_shape": ["I handle it", "my team owns it", "named decision owner"],
            "negative_evidence_shape": ["wrong person", "another team handles it", "not my area"],
            "safe_next_action": "Route to the right person or capture a safe handoff target.",
        },
        "fit": {
            "purpose": "Check whether the buyer's environment and issue match the campaign's allowed scope.",
            "positive_evidence_shape": ["matching use case", "matching customer profile", "relevant workflow"],
            "negative_evidence_shape": ["outside scope", "different need", "not applicable"],
            "safe_next_action": "Proceed only inside campaign scope; otherwise close or route.",
        },
        "current_solution_or_status_quo": {
            "purpose": "Learn how the buyer currently handles the area being discussed.",
            "positive_evidence_shape": ["manual process", "workaround", "existing vendor issue", "inconsistent process"],
            "negative_evidence_shape": ["working solution", "stable process", "no gap"],
            "safe_next_action": "Do not attack the current solution; ask whether any gap remains.",
        },
        "budget_or_price_sensitivity": {
            "purpose": "Understand price concern without inventing pricing or financial outcomes.",
            "positive_evidence_shape": ["too expensive", "budget timing", "need price details"],
            "negative_evidence_shape": ["price not the issue", "budget already approved"],
            "safe_next_action": "Use only allowed campaign pricing facts or route to human follow-up.",
        },
        "timing": {
            "purpose": "Determine whether now, later, or no further contact is appropriate.",
            "positive_evidence_shape": ["specific callback time", "preferred date", "later window"],
            "negative_evidence_shape": ["bad timing with no future interest", "never", "do not call"],
            "safe_next_action": "Capture a usable time or end if the buyer refuses future contact.",
        },
        "contact_path": {
            "purpose": "Capture the safe route for written details, callback, or human follow-up.",
            "positive_evidence_shape": ["email", "phone path", "named team", "preferred callback time"],
            "negative_evidence_shape": ["no contact", "will not share", "not sure"],
            "safe_next_action": "Ask once for missing contact details, then close if refused.",
        },
        "compliance_or_risk_constraints": {
            "purpose": "Detect areas where advice, claims, data handling, or regulated decisions need human review.",
            "positive_evidence_shape": ["regulated request", "sensitive data", "contract term", "coverage or eligibility question"],
            "negative_evidence_shape": ["general scheduling or product overview only"],
            "safe_next_action": "Avoid advice or claims and escalate to a qualified human when needed.",
        },
    },
    "generic_pain_dimensions": {
        "missed_follow_up": {
            "definition": "A promised or expected follow-up does not happen on time.",
            "causal_story": "If follow-up depends on memory or unclear ownership, interested customers can wait and lose trust.",
            "example_customer_language_generic": ["we miss follow-ups", "people forget to respond", "things slip"],
            "what_counts_as_clear_or_no_pain": ["follow-up is handled", "nothing slips", "responses happen on time"],
            "possible_next_diagnostic_dimensions": ["ownership_confusion", "manual_work", "visibility_gap"],
            "appointment_bridge_principle": "Offer a human review of the actual follow-up path and where delays occur.",
        },
        "delay": {
            "definition": "The buyer's process takes too long or creates waiting time.",
            "causal_story": "Delays reduce trust and can cause customers to choose another option before the team acts.",
            "example_customer_language_generic": ["it takes too long", "we respond late", "customers wait"],
            "what_counts_as_clear_or_no_pain": ["speed is fine", "timing is handled", "no delays"],
            "possible_next_diagnostic_dimensions": ["missed_follow_up", "unclear_next_step", "manual_work"],
            "appointment_bridge_principle": "Review the slow step and whether a clearer process would help.",
        },
        "ownership_confusion": {
            "definition": "It is unclear who owns the next action or decision.",
            "causal_story": "When ownership is unclear, each person may think someone else is handling the next step.",
            "example_customer_language_generic": ["nobody knows who owns it", "it goes between teams", "the handoff gets unclear"],
            "what_counts_as_clear_or_no_pain": ["ownership is clear", "the right person always owns it", "handoffs are clean"],
            "possible_next_diagnostic_dimensions": ["unclear_next_step", "visibility_gap", "duplicate_work"],
            "appointment_bridge_principle": "Review the ownership path and where responsibility changes hands.",
        },
        "manual_work": {
            "definition": "The team relies on repeated manual entry, copying, reminders, or checking.",
            "causal_story": "Manual work creates inconsistency and makes the result depend on individual memory and effort.",
            "example_customer_language_generic": ["we track it manually", "we copy notes", "we use a spreadsheet"],
            "what_counts_as_clear_or_no_pain": ["manual work is not a problem", "tracking is handled", "the process is consistent"],
            "possible_next_diagnostic_dimensions": ["missed_follow_up", "cost_or_time_waste", "visibility_gap"],
            "appointment_bridge_principle": "Review which manual steps create risk or wasted time.",
        },
        "duplicate_work": {
            "definition": "Two or more people repeat work, create duplicate records, or act on the same item without coordination.",
            "causal_story": "Duplicate work can split ownership, waste time, and create inconsistent customer communication.",
            "example_customer_language_generic": ["two people do the same thing", "duplicates confuse us", "work gets repeated"],
            "what_counts_as_clear_or_no_pain": ["duplicates are handled", "no repeated work", "ownership is clear"],
            "possible_next_diagnostic_dimensions": ["ownership_confusion", "visibility_gap", "unclear_next_step"],
            "appointment_bridge_principle": "Review where duplicate work starts and how ownership is resolved.",
        },
        "visibility_gap": {
            "definition": "A manager or team member cannot see status, owner, next step, or risk quickly enough.",
            "causal_story": "When status is hidden, problems are discovered late and follow-up requires asking around.",
            "example_customer_language_generic": ["we cannot see status", "we ask around", "nobody has a clear view"],
            "what_counts_as_clear_or_no_pain": ["status is visible", "we can see what is happening", "visibility is fine"],
            "possible_next_diagnostic_dimensions": ["missed_follow_up", "ownership_confusion", "manual_work"],
            "appointment_bridge_principle": "Review what the team needs to see before an issue becomes late.",
        },
        "customer_experience_friction": {
            "definition": "The customer's path feels confusing, slow, repetitive, or low-trust.",
            "causal_story": "Friction before a human resolves the issue can reduce confidence even if the product or service is strong.",
            "example_customer_language_generic": ["customers get frustrated", "people have to repeat themselves", "the experience feels messy"],
            "what_counts_as_clear_or_no_pain": ["customers are not confused", "the experience is smooth", "no complaints"],
            "possible_next_diagnostic_dimensions": ["delay", "unclear_next_step", "trust_or_risk_concern"],
            "appointment_bridge_principle": "Review the customer path and the points that create confusion or delay.",
        },
        "trust_or_risk_concern": {
            "definition": "The buyer worries about trust, reliability, compliance, safety, privacy, or reputation.",
            "causal_story": "Trust and risk concerns slow decisions and require careful human handling when claims or regulated facts are involved.",
            "example_customer_language_generic": ["we worry about risk", "trust matters", "we need to be careful"],
            "what_counts_as_clear_or_no_pain": ["risk is handled", "no trust issue", "compliance is covered by our process"],
            "possible_next_diagnostic_dimensions": ["compliance_or_risk_constraints", "authority_or_right_person", "fit"],
            "appointment_bridge_principle": "Offer a human follow-up focused on constraints and allowed claims, not instant promises.",
        },
        "cost_or_time_waste": {
            "definition": "The process wastes staff time, operating cost, or effort.",
            "causal_story": "Repeated low-value work can make teams slower and more expensive even when no single incident looks severe.",
            "example_customer_language_generic": ["it wastes time", "it costs us effort", "people spend too long on it"],
            "what_counts_as_clear_or_no_pain": ["time cost is acceptable", "no waste", "it is efficient enough"],
            "possible_next_diagnostic_dimensions": ["manual_work", "duplicate_work", "delay"],
            "appointment_bridge_principle": "Review the work that repeats and whether it justifies a human next step.",
        },
        "unclear_next_step": {
            "definition": "The next action, owner, time, or decision is not clear.",
            "causal_story": "If the next step is ambiguous, the process can stall even when everyone agrees action is needed.",
            "example_customer_language_generic": ["not sure what happens next", "the next step is unclear", "it stalls"],
            "what_counts_as_clear_or_no_pain": ["next steps are clear", "everyone knows what to do", "nothing stalls"],
            "possible_next_diagnostic_dimensions": ["ownership_confusion", "visibility_gap", "delay"],
            "appointment_bridge_principle": "Review where the next step becomes unclear and who should own it.",
        },
    },
    "objection_families": {
        "no_need_or_all_set": {
            "interpretation": "The buyer says the relevant need is absent or already handled.",
            "safe_response_principle": "Acknowledge the answer and avoid pushing a meeting as if pain was confirmed.",
            "when_to_continue": "Only ask one next relevant diagnostic if the scope was narrow and the buyer has not refused.",
            "when_to_end": "End when the buyer clears the broader scope or repeats no-need language.",
            "escalation_or_handoff_rule": "No escalation unless the buyer asks for another contact path.",
        },
        "not_relevant": {
            "interpretation": "The buyer says the outreach does not apply to them or their organization.",
            "safe_response_principle": "Clarify scope once if early enough, then close politely.",
            "when_to_continue": "Only if a short scope question may reveal the right owner or relevant area.",
            "when_to_end": "End after repeated not-relevant language or late-stage resistance.",
            "escalation_or_handoff_rule": "Offer right-person handoff if the buyer identifies another owner.",
        },
        "not_interested": {
            "interpretation": "The buyer does not want to continue the sales conversation.",
            "safe_response_principle": "Respect the refusal and avoid repeating the pitch.",
            "when_to_continue": "Only if the buyer immediately volunteers another path such as written info or a callback.",
            "when_to_end": "End on clear not-interested language.",
            "escalation_or_handoff_rule": "Do not escalate unless the buyer requests it.",
        },
        "timing": {
            "interpretation": "The buyer's objection is about current availability or timing.",
            "safe_response_principle": "Ask for a concrete callback time if future contact is acceptable.",
            "when_to_continue": "Continue only to capture the time or contact path.",
            "when_to_end": "End after confirming a time or after future contact is refused.",
            "escalation_or_handoff_rule": "No escalation unless urgency or regulated issue is named.",
        },
        "price": {
            "interpretation": "The buyer raises cost, budget, or value concern.",
            "safe_response_principle": "Use only allowed campaign pricing facts and route detailed pricing to a human.",
            "when_to_continue": "Continue if the buyer wants allowed pricing context or a follow-up.",
            "when_to_end": "End if price concern closes the conversation.",
            "escalation_or_handoff_rule": "Escalate detailed quotes, discounts, contracts, or billing commitments to a human.",
        },
        "authority": {
            "interpretation": "The speaker cannot decide or another person owns the area.",
            "safe_response_principle": "Route to the right person instead of forcing the current speaker through qualification.",
            "when_to_continue": "Continue to capture a right person, team, or contact path.",
            "when_to_end": "End if the buyer will not provide a path or asks to stop.",
            "escalation_or_handoff_rule": "Use right-person handoff.",
        },
        "existing_vendor_or_process": {
            "interpretation": "The buyer already has a vendor, process, or internal method.",
            "safe_response_principle": "Do not attack the status quo; ask whether any gap remains.",
            "when_to_continue": "Continue if the buyer names a current gap or asks for comparison by a human.",
            "when_to_end": "End if the current process is working and no relevant gap remains.",
            "escalation_or_handoff_rule": "Escalate detailed comparisons or claims to a human.",
        },
        "trust": {
            "interpretation": "The buyer questions credibility, proof, or reliability.",
            "safe_response_principle": "Acknowledge and avoid unsupported proof claims.",
            "when_to_continue": "Continue if the buyer wants allowed information or a human explanation.",
            "when_to_end": "End if trust concern blocks further contact.",
            "escalation_or_handoff_rule": "Escalate proof, certification, or legal assurance questions to a human.",
        },
        "privacy_or_security": {
            "interpretation": "The buyer asks about privacy, security, data handling, or sensitive information.",
            "safe_response_principle": "Do not invent compliance posture; route to approved materials or a human.",
            "when_to_continue": "Continue only for allowed high-level process or contact capture.",
            "when_to_end": "End if the buyer declines follow-up.",
            "escalation_or_handoff_rule": "Escalate security, privacy, or compliance details to a qualified human.",
        },
        "complexity": {
            "interpretation": "The buyer is concerned the next step, setup, or change may be too complex.",
            "safe_response_principle": "Clarify the concern and avoid promising effort or implementation details without proof.",
            "when_to_continue": "Continue if a human review can safely assess complexity.",
            "when_to_end": "End if complexity concern makes the conversation not relevant.",
            "escalation_or_handoff_rule": "Escalate implementation or technical scope questions to a human.",
        },
        "send_info_first": {
            "interpretation": "The buyer wants information before committing to a meeting or callback.",
            "safe_response_principle": "Capture an email or callback path and keep the appointment unconfirmed.",
            "when_to_continue": "Continue to collect contact details or callback time.",
            "when_to_end": "End if contact is refused or after policy permits a safe close.",
            "escalation_or_handoff_rule": "No real email is sent by this local runtime.",
        },
        "stop_or_do_not_contact": {
            "interpretation": "The buyer asks to stop contact or be removed.",
            "safe_response_principle": "Acknowledge and end immediately.",
            "when_to_continue": "Do not continue.",
            "when_to_end": "Always end.",
            "escalation_or_handoff_rule": "Preserve terminal state and avoid further sales handling.",
        },
    },
    "safe_next_action_policies": {
        "ask_next_diagnostic_if_current_issue_clear": {
            "description": "If the buyer clears only the current issue, ask one remaining relevant diagnostic if no pain is confirmed.",
            "allowed_when": ["single_issue_clear", "remaining_relevant_dimensions_exist", "buyer_has_not_refused"],
            "blocked_when": ["all_scope_clear", "explicit_refusal", "confirmed_pain_already_requires_next_step"],
            "implementation_rule": "Track the cleared issue and do not ask it again in the same diagnostic cycle.",
        },
        "clarify_if_confused": {
            "description": "If the buyer is confused, explain the prior question in plain language.",
            "allowed_when": ["buyer_asks_meaning", "buyer_says_not_clear"],
            "blocked_when": ["buyer_explicitly_stops"],
            "implementation_rule": "Clarification must come before any appointment pressure.",
        },
        "do_not_push_appointment_on_confusion": {
            "description": "Confusion is not buying intent.",
            "allowed_when": ["confusion_detected"],
            "blocked_when": ["none"],
            "implementation_rule": "Clarify first; only revisit appointment after the buyer understands and confirms relevance.",
        },
        "do_not_push_appointment_on_no_pain": {
            "description": "No-pain answers should not be treated as appointment consent.",
            "allowed_when": ["current_scope_clear", "all_scope_clear"],
            "blocked_when": ["credible_pain_confirmed"],
            "implementation_rule": "Ask another diagnostic only if the cleared scope was narrow; otherwise close or ask one safe save question.",
        },
        "bridge_to_appointment_after_credible_pain_or_interest": {
            "description": "Use confirmed buyer evidence or expressed interest to offer a human next step.",
            "allowed_when": ["credible_pain_confirmed", "buyer_requests_human_follow_up"],
            "blocked_when": ["no_pain", "confusion", "explicit_refusal", "wrong_person_without_handoff"],
            "implementation_rule": "Bridge from the buyer's evidence, then ask for interest or time.",
        },
        "capture_send_info_contact_without_pretending_appointment": {
            "description": "Written-info requests should collect a contact path without marking a meeting confirmed.",
            "allowed_when": ["buyer_requests_information"],
            "blocked_when": ["buyer_refuses_contact", "explicit_stop"],
            "implementation_rule": "Ask for email or callback time and keep appointment confirmation false until time is provided.",
        },
        "capture_callback_time_before_schedule_and_end": {
            "description": "The call can schedule-and-end only after a usable time is captured.",
            "allowed_when": ["usable_callback_or_appointment_time_provided"],
            "blocked_when": ["vague_time", "no_time", "invalid_contact_only"],
            "implementation_rule": "Ask for missing day or time before confirmation.",
        },
        "route_wrong_person_toward_right_contact_or_polite_close": {
            "description": "Wrong-person signals should route to a handoff target, not product-pain qualification.",
            "allowed_when": ["speaker_not_right_person", "authority_unclear"],
            "blocked_when": ["explicit_stop"],
            "implementation_rule": "Ask for the right person/team/contact once, or close politely.",
        },
        "end_on_explicit_stop_request": {
            "description": "Stop requests are terminal.",
            "allowed_when": ["do_not_call", "remove_me", "stop_request"],
            "blocked_when": ["none"],
            "implementation_rule": "Set terminal call control and do not restart the call on later input.",
        },
        "preserve_buyer_agency": {
            "description": "The buyer's stated refusal, uncertainty, or preference controls the pressure level.",
            "allowed_when": ["all_stages"],
            "blocked_when": ["none"],
            "implementation_rule": "Offer choices only when useful; never make consent, pain, or timing up.",
        },
        "avoid_unverified_claims": {
            "description": "Only use claims allowed by the active campaign or verified source.",
            "allowed_when": ["all_stages"],
            "blocked_when": ["unknown_product_fact", "regulated_claim_without_approval"],
            "implementation_rule": "If a claim is not available, say a human can verify it rather than inventing it.",
        },
    },
    "call_control_policy": {
        "continue-call": {
            "allowed_when": ["permission_granted", "diagnostic_open", "clarification_needed", "contact_capture_needed"],
            "blocked_when": ["explicit_stop", "terminal_schedule_confirmed", "buyer_refuses_future_contact"],
            "examples_generic": ["ask the next diagnostic", "clarify the prior question", "request missing contact detail"],
            "side_effects_allowed_false_by_default": deepcopy(_NO_SIDE_EFFECTS),
        },
        "schedule-and-end": {
            "allowed_when": ["usable_callback_time_captured", "usable_appointment_time_captured"],
            "blocked_when": ["vague_time_only", "no_time_captured", "buyer_confused", "buyer_refused"],
            "examples_generic": ["confirm a callback time", "confirm a human follow-up time"],
            "side_effects_allowed_false_by_default": deepcopy(_NO_SIDE_EFFECTS),
        },
        "end-call": {
            "allowed_when": ["explicit_stop", "not_interested_terminal", "no_fit_close", "contact_refused"],
            "blocked_when": ["buyer_asked_question_and_no_answer_given", "usable_next_step_missing_but_buyer_still_engaged"],
            "examples_generic": ["respect a stop request", "close after no relevant issue", "close after contact refusal"],
            "side_effects_allowed_false_by_default": deepcopy(_NO_SIDE_EFFECTS),
        },
        "transfer-or-escalate": {
            "allowed_when": ["regulated_question", "human_authority_required", "approved_live_transfer_path_available"],
            "blocked_when": ["no_transfer_path", "buyer_explicitly_refuses", "runtime_not_configured_for_transfer"],
            "examples_generic": ["route a regulated advice question to a qualified human", "route contract details to a human"],
            "side_effects_allowed_false_by_default": deepcopy(_NO_SIDE_EFFECTS),
        },
    },
    "regulated_vertical_cautions": {
        "insurance": {
            "blocked_claims": ["coverage advice", "eligibility decision", "guaranteed savings", "policy interpretation"],
            "human_escalation_triggers": ["coverage question", "claim question", "eligibility question", "policy term dispute"],
            "safe_language_principle": "Stay at scheduling or general information level and route regulated questions to a licensed or qualified human.",
        },
        "healthcare_admin_or_medical_equipment": {
            "blocked_claims": ["medical advice", "diagnosis", "treatment recommendation", "patient-specific eligibility"],
            "human_escalation_triggers": ["clinical question", "patient-specific question", "equipment suitability question"],
            "safe_language_principle": "Avoid clinical judgment and route health-specific decisions to qualified staff.",
        },
        "financial_or_payment_sensitive": {
            "blocked_claims": ["investment advice", "guaranteed return", "credit decision", "payment commitment"],
            "human_escalation_triggers": ["financing terms", "billing dispute", "refund dispute", "payment collection"],
            "safe_language_principle": "Do not make financial promises or collect payment; route details to authorized humans.",
        },
        "legal_or_contract_sensitive": {
            "blocked_claims": ["legal advice", "contract interpretation", "enforceability claim", "binding commitment"],
            "human_escalation_triggers": ["contract term question", "cancellation dispute", "liability question"],
            "safe_language_principle": "Do not interpret legal terms; offer human review or approved written material.",
        },
        "telecom_contract_or_coverage": {
            "blocked_claims": ["guaranteed coverage", "guaranteed speed", "contract cancellation outcome", "unverified plan terms"],
            "human_escalation_triggers": ["coverage dispute", "contract term question", "cancellation or porting issue"],
            "safe_language_principle": "Use only allowed plan facts and route coverage or contract specifics to a human.",
        },
        "home_services_safety_or_estimate": {
            "blocked_claims": ["remote safety diagnosis", "guaranteed estimate", "code compliance claim", "emergency instruction"],
            "human_escalation_triggers": ["safety concern", "urgent damage", "permit or code question", "price estimate request"],
            "safe_language_principle": "Avoid diagnosing remotely; schedule qualified inspection or human review.",
        },
        "automotive_service_safety_or_warranty": {
            "blocked_claims": ["remote safety diagnosis", "guaranteed repair cost", "warranty interpretation", "roadworthiness claim"],
            "human_escalation_triggers": ["safety issue", "warranty dispute", "repair estimate", "drivability concern"],
            "safe_language_principle": "Route safety, warranty, and repair specifics to qualified service staff.",
        },
        "membership_or_subscription_cancellation": {
            "blocked_claims": ["misleading cancellation terms", "unverified renewal claim", "guaranteed refund", "binding account change"],
            "human_escalation_triggers": ["cancellation request", "billing dispute", "refund request", "account access issue"],
            "safe_language_principle": "Respect cancellation intent and route account-specific actions to authorized support.",
        },
        "retail_or_ecommerce_refund_warranty_availability": {
            "blocked_claims": ["false stock claim", "guaranteed delivery", "unverified refund", "warranty interpretation"],
            "human_escalation_triggers": ["refund dispute", "availability question", "warranty claim", "shipping dispute"],
            "safe_language_principle": "Use only verified order or product facts and escalate exceptions to human support.",
        },
    },
}


def _section(section_id: str) -> dict[str, Any]:
    return dict(UNIVERSAL_SALES_KNOWLEDGE.get(section_id) or {})


def _record(section_id: str, item_id: str | None) -> dict[str, Any]:
    if not item_id:
        return {}
    return deepcopy((_section(section_id)).get(item_id) or {})


def universal_knowledge_id() -> str:
    return str(UNIVERSAL_SALES_KNOWLEDGE["knowledge_id"])


def sales_stage(stage_id: str | None) -> dict[str, Any]:
    return _record("sales_stages", stage_id)


def buyer_move_family(move_id: str | None) -> dict[str, Any]:
    return _record("buyer_move_families", move_id)


def qualification_dimension(dimension_id: str | None) -> dict[str, Any]:
    return _record("qualification_dimensions", dimension_id)


def generic_pain_dimension(dimension_id: str | None) -> dict[str, Any]:
    return _record("generic_pain_dimensions", dimension_id)


def objection_family(objection_id: str | None) -> dict[str, Any]:
    return _record("objection_families", objection_id)


def safe_next_action_policy(policy_id: str | None) -> dict[str, Any]:
    return _record("safe_next_action_policies", policy_id)


def call_control_rule(call_control_id: str | None) -> dict[str, Any]:
    return _record("call_control_policy", call_control_id)


def regulated_caution(vertical_or_caution_id: str | None) -> dict[str, Any]:
    return _record("regulated_vertical_cautions", vertical_or_caution_id)


def all_sales_stage_ids() -> list[str]:
    return sorted(_section("sales_stages"))


def all_buyer_move_family_ids() -> list[str]:
    return sorted(_section("buyer_move_families"))


def all_qualification_dimension_ids() -> list[str]:
    return sorted(_section("qualification_dimensions"))


def all_generic_pain_dimension_ids() -> list[str]:
    return sorted(_section("generic_pain_dimensions"))


def all_objection_family_ids() -> list[str]:
    return sorted(_section("objection_families"))


def all_safe_next_action_policy_ids() -> list[str]:
    return sorted(_section("safe_next_action_policies"))


def all_call_control_ids() -> list[str]:
    return sorted(_section("call_control_policy"))


def all_regulated_caution_ids() -> list[str]:
    return sorted(_section("regulated_vertical_cautions"))


def _require_fields(failures: list[str], section_id: str, required_fields: set[str]) -> None:
    section = _section(section_id)
    if not section:
        failures.append(f"{section_id}: section is empty")
        return
    for item_id, record in section.items():
        if not isinstance(record, dict):
            failures.append(f"{section_id}.{item_id}: record must be a dict")
            continue
        for field in sorted(required_fields):
            value = record.get(field)
            if value is None or value == "" or value == [] or value == {}:
                failures.append(f"{section_id}.{item_id}.{field}: must be populated")


def validate_universal_sales_knowledge() -> dict[str, Any]:
    failures: list[str] = []
    required_top_level = {
        "knowledge_id",
        "schema_version",
        "sales_stages",
        "buyer_move_families",
        "qualification_dimensions",
        "generic_pain_dimensions",
        "objection_families",
        "safe_next_action_policies",
        "call_control_policy",
        "regulated_vertical_cautions",
    }
    missing = sorted(required_top_level - set(UNIVERSAL_SALES_KNOWLEDGE))
    if missing:
        failures.append(f"missing top-level fields: {missing}")
    if UNIVERSAL_SALES_KNOWLEDGE.get("knowledge_id") != KNOWLEDGE_ID:
        failures.append("knowledge_id mismatch")
    if UNIVERSAL_SALES_KNOWLEDGE.get("schema_version") != SCHEMA_VERSION:
        failures.append("schema_version mismatch")

    _require_fields(
        failures,
        "sales_stages",
        {"description", "allowed_next_actions", "blocked_actions", "call_control_defaults"},
    )
    _require_fields(
        failures,
        "buyer_move_families",
        {
            "description",
            "typical_contexts",
            "safe_interpretation_rule",
            "unsafe_interpretation_examples",
            "recommended_next_action",
        },
    )
    _require_fields(
        failures,
        "qualification_dimensions",
        {"purpose", "positive_evidence_shape", "negative_evidence_shape", "safe_next_action"},
    )
    _require_fields(
        failures,
        "generic_pain_dimensions",
        {
            "definition",
            "causal_story",
            "example_customer_language_generic",
            "what_counts_as_clear_or_no_pain",
            "possible_next_diagnostic_dimensions",
            "appointment_bridge_principle",
        },
    )
    _require_fields(
        failures,
        "objection_families",
        {"interpretation", "safe_response_principle", "when_to_continue", "when_to_end", "escalation_or_handoff_rule"},
    )
    _require_fields(
        failures,
        "safe_next_action_policies",
        {"description", "allowed_when", "blocked_when", "implementation_rule"},
    )
    _require_fields(
        failures,
        "call_control_policy",
        {"allowed_when", "blocked_when", "examples_generic", "side_effects_allowed_false_by_default"},
    )
    _require_fields(
        failures,
        "regulated_vertical_cautions",
        {"blocked_claims", "human_escalation_triggers", "safe_language_principle"},
    )

    for control_id, rule in _section("call_control_policy").items():
        side_effects = rule.get("side_effects_allowed_false_by_default") or {}
        for key, expected in _NO_SIDE_EFFECTS.items():
            if side_effects.get(key) is not expected:
                failures.append(f"call_control_policy.{control_id}.{key}: must be {expected}")

    return {
        "valid": not failures,
        "knowledge_id": universal_knowledge_id(),
        "schema_version": SCHEMA_VERSION,
        "failures": failures,
        "counts": {
            "sales_stages": len(all_sales_stage_ids()),
            "buyer_move_families": len(all_buyer_move_family_ids()),
            "qualification_dimensions": len(all_qualification_dimension_ids()),
            "generic_pain_dimensions": len(all_generic_pain_dimension_ids()),
            "objection_families": len(all_objection_family_ids()),
            "safe_next_action_policies": len(all_safe_next_action_policy_ids()),
            "call_control_rules": len(all_call_control_ids()),
            "regulated_vertical_cautions": len(all_regulated_caution_ids()),
        },
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
    }

