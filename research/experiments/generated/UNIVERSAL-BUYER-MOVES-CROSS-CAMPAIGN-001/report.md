# UNIVERSAL-BUYER-MOVES-CROSS-CAMPAIGN-001

## Summary
Dry-run cross-campaign buyer-move matrix using existing turn builders and the universal policy frame.
Status: red_findings

## Matrix Size
- Campaigns: 5
- Buyer-move cases per campaign: 55
- Total turns evaluated: 275
- Recognition pass/fail: 275 / 0
- Response pass/fail: 102 / 173

## Pass/Fail Counts By Buyer-Move Category
- appointment_callback_send_info: pass=30 fail=0
- asr_repair: pass=22 fail=3
- confusion_challenge_repair: pass=15 fail=15
- direct_product_value_questions: pass=5 fail=25
- objections: pass=0 fail=35
- pain_tentative_pain: pass=7 fail=18
- permission_time_pressure: pass=2 fail=13
- scope_regulated_claim_boundaries: pass=12 fail=13
- social_conversation_management: pass=0 fail=30
- trust_identity_privacy_consent: pass=9 fail=21

## Top Failure Clusters
- objections / repeated_full_menu: 52
- objections / no_acknowledgement: 35
- social_conversation_management / no_acknowledgement: 30
- direct_product_value_questions / no_acknowledgement: 25
- social_conversation_management / repeated_full_menu: 24
- permission_time_pressure / repeated_full_menu: 21
- trust_identity_privacy_consent / repeated_full_menu: 20
- direct_product_value_questions / repeated_full_menu: 18
- direct_product_value_questions / direct_question_not_answered: 18
- confusion_challenge_repair / no_acknowledgement: 15
- pain_tentative_pain / repeated_full_menu: 10
- scope_regulated_claim_boundaries / wrong_call_control: 10

## Top Recognition Failures

## Top Response-Shape Failures
- objections / repeated_full_menu: 52
- objections / no_acknowledgement: 35
- social_conversation_management / no_acknowledgement: 30
- direct_product_value_questions / no_acknowledgement: 25
- social_conversation_management / repeated_full_menu: 24
- permission_time_pressure / repeated_full_menu: 21
- trust_identity_privacy_consent / repeated_full_menu: 20
- direct_product_value_questions / repeated_full_menu: 18
- direct_product_value_questions / direct_question_not_answered: 18
- confusion_challenge_repair / no_acknowledgement: 15
- pain_tentative_pain / repeated_full_menu: 10
- scope_regulated_claim_boundaries / wrong_call_control: 10

## Examples Of Strongest Failures
- routesignal_live_demo | permission_time_pressure | yeah sure | repeated_full_menu | recognized=permission_acknowledgement | response='Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today?'
- routesignal_live_demo | pain_tentative_pain | premium is a problem | repeated_full_menu | recognized=pain_confirmed | response='If callback reminders for demo follow-up sit in a spreadsheet, they can slip. Which part is more familiar: manual tracking or missed callbacks?'
- routesignal_live_demo | pain_tentative_pain | repair timings are usually pretty long | repeated_full_menu | recognized=pain_confirmed | response='If callback reminders for demo follow-up sit in a spreadsheet, they can slip. Which part is more familiar: manual tracking or missed callbacks?'
- routesignal_live_demo | pain_tentative_pain | maybe coverage fit | internal_wording | recognized=tentative_gap_interest | response='I should not give coverage advice. I can route this to the approved qualified reviewer path.'
- routesignal_live_demo | direct_product_value_questions | what does your product do | no_acknowledgement | recognized=product_detail_question | response='RouteSignal CRM routes leads, captures follow-up tasks, and shows handoff status so inbound requests do not sit in a spreadsheet. Where does follow-up break first today: assignment, reminders, or missed replies?'
- routesignal_live_demo | direct_product_value_questions | what problem do you solve | repeated_full_menu, no_acknowledgement, direct_question_not_answered | recognized=what_problem_do_you_solve | response='If callback reminders for demo follow-up sit in a spreadsheet, they can slip. Which part is more familiar: manual tracking or missed callbacks?'
- routesignal_live_demo | direct_product_value_questions | what makes you different | repeated_full_menu, no_acknowledgement, direct_question_not_answered | recognized=what_makes_you_different | response='If callback reminders for demo follow-up sit in a spreadsheet, they can slip. Which part is more familiar: manual tracking or missed callbacks?'
- routesignal_live_demo | direct_product_value_questions | who is this for | no_acknowledgement | recognized=who_is_this_for | response='I only caught part of that. Please repeat the question in one sentence.'
- routesignal_live_demo | direct_product_value_questions | is this worth my time | no_acknowledgement | recognized=is_this_worth_my_time | response='The effort question is simple: would missed follow-up cost more time than a short review?'
- routesignal_live_demo | scope_regulated_claim_boundaries | so you cannot give me details | repeated_full_menu, direct_question_not_answered | recognized=scope_limit_question | response='If callback reminders for demo follow-up sit in a spreadsheet, they can slip. Which part is more familiar: manual tracking or missed callbacks?'

## Campaign-Specific Or Universal
Failures appearing in three or more campaigns are treated as likely universal-policy/runtime gaps.
- repeated_full_menu: 5 campaigns (routesignal_live_demo, synthetic-automotive-service-review, synthetic-b2b-saas-operations, synthetic-home-services-estimate, synthetic-insurance-review)
- internal_wording: 5 campaigns (routesignal_live_demo, synthetic-automotive-service-review, synthetic-b2b-saas-operations, synthetic-home-services-estimate, synthetic-insurance-review)
- no_acknowledgement: 5 campaigns (routesignal_live_demo, synthetic-automotive-service-review, synthetic-b2b-saas-operations, synthetic-home-services-estimate, synthetic-insurance-review)
- direct_question_not_answered: 5 campaigns (routesignal_live_demo, synthetic-automotive-service-review, synthetic-b2b-saas-operations, synthetic-home-services-estimate, synthetic-insurance-review)
- wrong_call_control: 5 campaigns (routesignal_live_demo, synthetic-automotive-service-review, synthetic-b2b-saas-operations, synthetic-home-services-estimate, synthetic-insurance-review)

## Recommended Next Implementation Slice
Integrate universal challenge/direct-question response-shape constraints before campaign-specific fallback menus.

## Runtime Behavior Changed
false

## Safety Boundary Summary
- provider_calls_made: False
- local_llm_calls_made: False
- sends_email: False
- creates_calendar_event: False
- writes_crm: False
- opens_prod_102: False
- customer_audio_uploaded_to_python_server: False
- customer_audio_uploaded_to_tts_provider: False
