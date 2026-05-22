# UNIVERSAL-BUYER-MOVES-CROSS-CAMPAIGN-001

## Summary
Dry-run cross-campaign buyer-move matrix using existing turn builders and the universal policy frame.
Status: red_findings

## Matrix Size
- Campaigns: 5
- Buyer-move cases per campaign: 55
- Total turns evaluated: 275
- Recognition pass/fail: 275 / 0
- Response pass/fail: 171 / 104

## Pass/Fail Counts By Buyer-Move Category
- appointment_callback_send_info: pass=30 fail=0
- asr_repair: pass=22 fail=3
- confusion_challenge_repair: pass=15 fail=15
- direct_product_value_questions: pass=30 fail=0
- objections: pass=35 fail=0
- pain_tentative_pain: pass=7 fail=18
- permission_time_pressure: pass=10 fail=5
- scope_regulated_claim_boundaries: pass=13 fail=12
- social_conversation_management: pass=0 fail=30
- trust_identity_privacy_consent: pass=9 fail=21

## Top Failure Clusters
- social_conversation_management / no_acknowledgement: 30
- social_conversation_management / repeated_full_menu: 24
- trust_identity_privacy_consent / repeated_full_menu: 20
- confusion_challenge_repair / no_acknowledgement: 15
- pain_tentative_pain / repeated_full_menu: 10
- scope_regulated_claim_boundaries / wrong_call_control: 10
- pain_tentative_pain / internal_wording: 7
- permission_time_pressure / repeated_full_menu: 5
- scope_regulated_claim_boundaries / internal_wording: 5
- confusion_challenge_repair / repeated_full_menu: 4
- confusion_challenge_repair / direct_question_not_answered: 4
- asr_repair / asr_garble_not_repaired: 3

## Top Recognition Failures

## Top Response-Shape Failures
- social_conversation_management / no_acknowledgement: 30
- social_conversation_management / repeated_full_menu: 24
- trust_identity_privacy_consent / repeated_full_menu: 20
- confusion_challenge_repair / no_acknowledgement: 15
- pain_tentative_pain / repeated_full_menu: 10
- scope_regulated_claim_boundaries / wrong_call_control: 10
- pain_tentative_pain / internal_wording: 7
- permission_time_pressure / repeated_full_menu: 5
- scope_regulated_claim_boundaries / internal_wording: 5
- confusion_challenge_repair / repeated_full_menu: 4
- confusion_challenge_repair / direct_question_not_answered: 4
- asr_repair / asr_garble_not_repaired: 3

## Examples Of Strongest Failures
- routesignal_live_demo | permission_time_pressure | yeah sure | repeated_full_menu | recognized=permission_acknowledgement | response='Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today?'
- routesignal_live_demo | pain_tentative_pain | premium is a problem | repeated_full_menu | recognized=pain_confirmed | response='If callback reminders for demo follow-up sit in a spreadsheet, they can slip. Which part is more familiar: manual tracking or missed callbacks?'
- routesignal_live_demo | pain_tentative_pain | repair timings are usually pretty long | repeated_full_menu | recognized=pain_confirmed | response='If callback reminders for demo follow-up sit in a spreadsheet, they can slip. Which part is more familiar: manual tracking or missed callbacks?'
- routesignal_live_demo | pain_tentative_pain | maybe coverage fit | internal_wording | recognized=tentative_gap_interest | response='I should not give coverage advice. I can route this to the approved qualified reviewer path.'
- routesignal_live_demo | scope_regulated_claim_boundaries | can you guarantee that | wrong_call_control | recognized=regulated_claim_question | response='I hear the certainty concern. I do not want to make a claim that depends on details we have not checked, so the safest next step is to route this to a verified implementation reviewer.'
- routesignal_live_demo | scope_regulated_claim_boundaries | am I covered | internal_wording, wrong_call_control | recognized=regulated_claim_question | response='I should not give coverage advice. I can route this to the approved qualified reviewer path.'
- routesignal_live_demo | scope_regulated_claim_boundaries | can you promise the result | repeated_full_menu, direct_question_not_answered | recognized=regulated_claim_question | response='If callback reminders for demo follow-up sit in a spreadsheet, they can slip. Which part is more familiar: manual tracking or missed callbacks?'
- routesignal_live_demo | trust_identity_privacy_consent | who are you | repeated_full_menu | recognized=who_are_you | response='I am Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I was calling about missed callbacks and handoffs in inbound demo follow-up. Should I restate the quick reason?'
- routesignal_live_demo | trust_identity_privacy_consent | I don't want to continue | wrong_call_control | recognized=permission_to_continue_denied | response='If inbound demo requests land in one inbox, missed follow-up can happen because everyone assumes someone else replied. Which part is harder today: seeing it, assigning the reply, or remembering the callback?'
- routesignal_live_demo | confusion_challenge_repair | what do you mean | no_acknowledgement | recognized=confusion_not_clear | response='I meant: an inbound demo request needs one clear owner for the next reply. Can owner, callback, or handoff steps sit waiting?'

## Campaign-Specific Or Universal
Failures appearing in three or more campaigns are treated as likely universal-policy/runtime gaps.
- repeated_full_menu: 5 campaigns (routesignal_live_demo, synthetic-automotive-service-review, synthetic-b2b-saas-operations, synthetic-home-services-estimate, synthetic-insurance-review)
- internal_wording: 5 campaigns (routesignal_live_demo, synthetic-automotive-service-review, synthetic-b2b-saas-operations, synthetic-home-services-estimate, synthetic-insurance-review)
- wrong_call_control: 5 campaigns (routesignal_live_demo, synthetic-automotive-service-review, synthetic-b2b-saas-operations, synthetic-home-services-estimate, synthetic-insurance-review)
- direct_question_not_answered: 5 campaigns (routesignal_live_demo, synthetic-automotive-service-review, synthetic-b2b-saas-operations, synthetic-home-services-estimate, synthetic-insurance-review)
- no_acknowledgement: 5 campaigns (routesignal_live_demo, synthetic-automotive-service-review, synthetic-b2b-saas-operations, synthetic-home-services-estimate, synthetic-insurance-review)

## Recommended Next Implementation Slice
Integrate universal buyer-move handling for social_conversation_management before adding vertical-specific repairs.

## Runtime Behavior Changed
true

## Safety Boundary Summary
- provider_calls_made: False
- local_llm_calls_made: False
- sends_email: False
- creates_calendar_event: False
- writes_crm: False
- opens_prod_102: False
- customer_audio_uploaded_to_python_server: False
- customer_audio_uploaded_to_tts_provider: False
