# GENERIC-CAMPAIGN-SPOKEN-TEXT-QUALITY-001

- Status: `pass`
- Failure count: `0`
- Verticals tested: `b2b_saas, insurance, telecom, home_services, healthcare_admin_or_medical_equipment, automotive_service, membership_or_subscription, retail_or_ecommerce_support_sales`
- Scenarios covered: `callback_time_capture, current_gap_clear, fallback_repair, opening, pain_confirmed, permission_to_diagnostic, regulated_caution, right_person_handoff, send_info, stop_refusal`
- Spoken-text failures before patch: `528`
- RouteSignal preservation: `true`
- Provider calls made: `false`
- Local LLM calls made: `false`

## Spoken Quality Rules

- No RouteSignal leakage in final_response, tts_input_text, or provider-rendered dry-run text.
- No filler in stop/refusal, regulated caution, callback confirmation, send-info capture, or right-person capture.
- No more than one filler marker in any generic spoken response.
- No filler immediately before direct question words or after a diagnostic-list comma.
- Short generic responses under 30 words may not contain more than two SSML break tags.
- Break tags may not split role articles, owner roles, offer names, or email/callback-time phrases.
- Spoken text must not add scheduling, guarantees, product facts, or soften stop/refusal meaning.

## Failures

- None

## Scenario Samples

- `b2b_saas` `opening` `no_contextual_semantic`: Hi, this is Maya calling from Synthetic SaaS Operations about Operations Workflow Review. I am checking whether a short operations fit review is needed; do you have a minute?
- `b2b_saas` `permission_to_diagnostic` `permission_acknowledgement`: Thanks, I am checking manual work, integration risk, or visibility gap. Which one is causing trouble, if any?
- `b2b_saas` `current_gap_clear` `current_gap_clear`: Got it, manual work is clear. Should I check integration risk or visibility gap, or stop here?
- `b2b_saas` `pain_confirmed` `pain_confirmed`: Got it, that sounds like the part worth reviewing. The next step would be a short operations fit review; what time works for that review?
- `b2b_saas` `send_info` `send_info_affirmed_without_contact`: Sure. What email should I note for the summary, or what callback time should I use?
- `b2b_saas` `callback_time_capture` `callback_time_provided`: Confirmed. I will note that time for your operations fit review. Goodbye.
- `b2b_saas` `right_person_handoff` `wrong_person_or_wrong_department`: Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note?
- `b2b_saas` `stop_refusal` `stop_request`: Understood. I will stop here. Goodbye.
- `b2b_saas` `regulated_caution` `campaign_claim_boundary_caution`: I cannot verify that claim here. Exact integration, security, or setup fit needs verified material and review by an implementation specialist before I claim it. Is that the gap you want reviewed?
- `b2b_saas` `fallback_repair` `account_support_boundary`: I cannot help with account support on this call. If useful, an implementation specialist can follow up separately, or I can stop here.
- `insurance` `opening` `no_contextual_semantic`: Hi, this is Maya calling from Synthetic Insurance Agency about Policy Review Call. I am checking whether a short licensed coverage review is needed; do you have a minute?
- `insurance` `permission_to_diagnostic` `permission_acknowledgement`: Thanks, I am checking coverage fit, premium or budget, or renewal or timing. Which one is causing trouble, if any?
- `insurance` `current_gap_clear` `current_gap_clear`: Got it, coverage fit is clear. Should I check premium or budget or renewal or timing, or stop here?
- `insurance` `pain_confirmed` `pain_confirmed`: Got it, that sounds like the part worth reviewing. The next step would be a short licensed coverage review; what time works for that review?
- `insurance` `send_info` `send_info_affirmed_without_contact`: Sure. What email should I note for the summary, or what callback time should I use?
- `insurance` `callback_time_capture` `callback_time_provided`: Confirmed. I will note that time for your licensed coverage review. Goodbye.
- `insurance` `right_person_handoff` `wrong_person_or_wrong_department`: Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note?
- `insurance` `stop_refusal` `stop_request`: Understood. I will stop here. Goodbye.
- `insurance` `regulated_caution` `campaign_claim_boundary_caution`: I cannot promise coverage here. A licensed insurance specialist needs verified policy details before any coverage answer. Is coverage fit against policy details what you want reviewed?
- `insurance` `fallback_repair` `account_support_boundary`: I cannot handle claim support on this call. Please use the authorized support path; I can keep this to the review topic, or stop here.
- `telecom` `opening` `no_contextual_semantic`: Hi, this is Maya calling from Synthetic Telecom Provider about Plan Review Call. I am checking whether a short plan and coverage review is needed; do you have a minute?
- `telecom` `permission_to_diagnostic` `permission_acknowledgement`: Thanks, I am checking coverage or availability, plan fit, or contract or switching. Which one is causing trouble, if any?
- `telecom` `current_gap_clear` `current_gap_clear`: Got it, coverage or availability is clear. Should I check plan fit or contract or switching, or stop here?
- `telecom` `pain_confirmed` `pain_confirmed`: Got it, that sounds like the part worth reviewing. The next step would be a short plan and coverage review; what time works for that review?
- `telecom` `send_info` `send_info_affirmed_without_contact`: Sure. What email should I note for the summary, or what callback time should I use?
- `telecom` `callback_time_capture` `callback_time_provided`: Confirmed. I will note that time for your plan and coverage review. Goodbye.
- `telecom` `right_person_handoff` `wrong_person_or_wrong_department`: Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note?
- `telecom` `stop_refusal` `stop_request`: Understood. I will stop here. Goodbye.
- `telecom` `regulated_caution` `campaign_claim_boundary_caution`: I cannot promise service coverage here. A telecom plan specialist needs verified address, plan, and account details before any coverage answer. Is coverage and availability fit what you want reviewed?
- `telecom` `fallback_repair` `account_support_boundary`: I cannot change account plans on this call. Please use the authorized support path; I can keep this to the review topic, or stop here.
- `home_services` `opening` `no_contextual_semantic`: Hi, this is Maya calling from Synthetic Home Services about Service Estimate Call. I am checking whether a short service estimate review is needed; do you have a minute?
- `home_services` `permission_to_diagnostic` `permission_acknowledgement`: Thanks, I am checking service need, scheduling urgency, or estimate or property details. Which one is causing trouble, if any?
- `home_services` `current_gap_clear` `current_gap_clear`: Got it, service need is clear. Should I check scheduling urgency or estimate or property details, or stop here?
- `home_services` `pain_confirmed` `pain_confirmed`: Got it, that sounds like the part worth reviewing. The next step would be a short service estimate review; what time works for that review?
- `home_services` `send_info` `send_info_affirmed_without_contact`: Sure. What email should I note for the summary, or what callback time should I use?
- `home_services` `callback_time_capture` `callback_time_provided`: Confirmed. I will note that time for your service estimate review. Goodbye.
- `home_services` `right_person_handoff` `wrong_person_or_wrong_department`: Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note?
- `home_services` `stop_refusal` `stop_request`: Understood. I will stop here. Goodbye.
- `home_services` `regulated_caution` `campaign_claim_boundary_caution`: I cannot give an exact price without property details or inspection. A service advisor needs verified details before quoting. Is estimate details and property context what you want reviewed?
- `home_services` `fallback_repair` `account_support_boundary`: I cannot help with account support on this call. If useful, a service advisor can follow up separately, or I can stop here.
- `healthcare_admin_or_medical_equipment` `opening` `no_contextual_semantic`: Hi, this is Maya calling from Synthetic Healthcare Admin about Admin Equipment Review. I am checking whether a short specialist admin review is needed; do you have a minute?
- `healthcare_admin_or_medical_equipment` `permission_to_diagnostic` `permission_acknowledgement`: Thanks, I am checking admin workflow need, equipment or service fit, or specialist review needed. Which one is causing trouble, if any?
- `healthcare_admin_or_medical_equipment` `current_gap_clear` `current_gap_clear`: Got it, admin workflow need is clear. Should I check equipment or service fit or specialist review needed, or stop here?
- `healthcare_admin_or_medical_equipment` `pain_confirmed` `pain_confirmed`: Got it, that sounds like the part worth reviewing. The next step would be a short specialist admin review; what time works for that review?
- `healthcare_admin_or_medical_equipment` `send_info` `send_info_affirmed_without_contact`: Sure. What email should I note for the summary, or what callback time should I use?
- `healthcare_admin_or_medical_equipment` `callback_time_capture` `callback_time_provided`: Confirmed. I will note that time for your specialist admin review. Goodbye.
- `healthcare_admin_or_medical_equipment` `right_person_handoff` `wrong_person_or_wrong_department`: Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note?
- `healthcare_admin_or_medical_equipment` `stop_refusal` `stop_request`: Understood. I will stop here. Goodbye.
- `healthcare_admin_or_medical_equipment` `regulated_caution` `campaign_claim_boundary_caution`: I cannot promise an equipment or service outcome here. A specialist review coordinator needs verified admin and specialist details first. Is specialist review need what you want reviewed?
- `healthcare_admin_or_medical_equipment` `fallback_repair` `account_support_boundary`: I cannot help with account support on this call. If useful, a specialist review coordinator can follow up separately, or I can stop here.
- `automotive_service` `opening` `no_contextual_semantic`: Hi, this is Maya calling from Synthetic Automotive Service about Service Advisor Review. I am checking whether a short service advisor inspection review is needed; do you have a minute?
- `automotive_service` `permission_to_diagnostic` `permission_acknowledgement`: Thanks, I am checking vehicle issue, repair timing, or warranty or estimate. Which one is causing trouble, if any?
- `automotive_service` `current_gap_clear` `current_gap_clear`: Got it, vehicle issue is clear. Should I check repair timing or warranty or estimate, or stop here?
- `automotive_service` `pain_confirmed` `pain_confirmed`: Got it, that sounds like the part worth reviewing. The next step would be a short service advisor inspection review; what time works for that review?
- `automotive_service` `send_info` `send_info_affirmed_without_contact`: Sure. What email should I note for the summary, or what callback time should I use?
- `automotive_service` `callback_time_capture` `callback_time_provided`: Confirmed. I will note that time for your service advisor inspection review. Goodbye.
- `automotive_service` `right_person_handoff` `wrong_person_or_wrong_department`: Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note?
- `automotive_service` `stop_refusal` `stop_request`: Understood. I will stop here. Goodbye.
- `automotive_service` `regulated_caution` `campaign_claim_boundary_caution`: I cannot promise repair cost or warranty outcome here. A service advisor needs verified vehicle details or inspection first. Is warranty or estimate what you want reviewed?
- `automotive_service` `fallback_repair` `account_support_boundary`: I cannot check warranty support on this call. Please use the authorized support path; I can keep this to the review topic, or stop here.
- `membership_or_subscription` `opening` `no_contextual_semantic`: Hi, this is Maya calling from Synthetic Membership Services about Membership Plan Review. I am checking whether a short membership account review is needed; do you have a minute?
- `membership_or_subscription` `permission_to_diagnostic` `permission_acknowledgement`: Thanks, I am checking plan fit, renewal or cancellation, or usage or value. Which one is causing trouble, if any?
- `membership_or_subscription` `current_gap_clear` `current_gap_clear`: Got it, plan fit is clear. Should I check renewal or cancellation or usage or value, or stop here?
- `membership_or_subscription` `pain_confirmed` `pain_confirmed`: Got it, that sounds like the part worth reviewing. The next step would be a short membership account review; what time works for that review?
- `membership_or_subscription` `send_info` `send_info_affirmed_without_contact`: Sure. What email should I note for the summary, or what callback time should I use?
- `membership_or_subscription` `callback_time_capture` `callback_time_provided`: Confirmed. I will note that time for your membership account review. Goodbye.
- `membership_or_subscription` `right_person_handoff` `wrong_person_or_wrong_department`: Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note?
- `membership_or_subscription` `stop_refusal` `stop_request`: Understood. I will stop here. Goodbye.
- `membership_or_subscription` `regulated_caution` `campaign_claim_boundary_caution`: I cannot hide cancellation terms or make account-specific billing promises. A membership specialist should review the policy details transparently. Is renewal or cancellation terms what you want reviewed?
- `membership_or_subscription` `fallback_repair` `account_support_boundary`: I cannot cancel or change an account on this call. Please use authorized account support; I can stop here.
- `retail_or_ecommerce_support_sales` `opening` `no_contextual_semantic`: Hi, this is Maya calling from Synthetic Retail Support about Product Support Review. I am checking whether a short product support review is needed; do you have a minute?
- `retail_or_ecommerce_support_sales` `permission_to_diagnostic` `permission_acknowledgement`: Thanks, I am checking product fit, availability or delivery, or return or warranty. Which one is causing trouble, if any?
- `retail_or_ecommerce_support_sales` `current_gap_clear` `current_gap_clear`: Got it, product fit is clear. Should I check availability or delivery or return or warranty, or stop here?
- `retail_or_ecommerce_support_sales` `pain_confirmed` `pain_confirmed`: Got it, that sounds like the part worth reviewing. The next step would be a short product support review; what time works for that review?
- `retail_or_ecommerce_support_sales` `send_info` `send_info_affirmed_without_contact`: Sure. What email should I note for the summary, or what callback time should I use?
- `retail_or_ecommerce_support_sales` `callback_time_capture` `callback_time_provided`: Confirmed. I will note that time for your product support review. Goodbye.
- `retail_or_ecommerce_support_sales` `right_person_handoff` `wrong_person_or_wrong_department`: Understood, operations handles that. Who is the right person there, or what contact, email, or callback path should I note?
- `retail_or_ecommerce_support_sales` `stop_refusal` `stop_request`: Understood. I will stop here. Goodbye.
- `retail_or_ecommerce_support_sales` `regulated_caution` `campaign_claim_boundary_caution`: I cannot promise a refund, warranty, stock, or delivery outcome here. A support sales specialist needs verified policy and order details first. Is return or warranty policy what you want reviewed?
- `retail_or_ecommerce_support_sales` `fallback_repair` `account_support_boundary`: I cannot handle order support on this call. Please use the support team for order details; I can stop here.

## Patches Made

- Disabled visible filler and speech-imperfection insertion for non-RouteSignal generic campaign configs in runtime voice delivery.
- Kept generic campaigns eligible for provider rendering, pauses, and non-word prosody metadata while preventing filler words from entering spoken text.
- Left RouteSignal live-demo voice shaping unchanged by excluding known RouteSignal campaign IDs from the generic voice guard.
