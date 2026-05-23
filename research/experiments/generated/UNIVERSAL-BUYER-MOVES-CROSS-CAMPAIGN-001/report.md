# UNIVERSAL-BUYER-MOVES-CROSS-CAMPAIGN-001

## Summary
Dry-run cross-campaign buyer-move matrix using existing turn builders and the universal policy frame.
Status: red_findings

## Matrix Size
- Campaigns: 5
- Buyer-move cases per campaign: 55
- Total turns evaluated: 275
- Recognition pass/fail: 275 / 0
- Response pass/fail: 224 / 51

## Pass/Fail Counts By Buyer-Move Category
- appointment_callback_send_info: pass=30 fail=0
- asr_repair: pass=22 fail=3
- confusion_challenge_repair: pass=30 fail=0
- direct_product_value_questions: pass=30 fail=0
- objections: pass=35 fail=0
- pain_tentative_pain: pass=7 fail=18
- permission_time_pressure: pass=10 fail=5
- scope_regulated_claim_boundaries: pass=25 fail=0
- social_conversation_management: pass=5 fail=25
- trust_identity_privacy_consent: pass=30 fail=0

## Top Failure Clusters
- social_conversation_management / no_acknowledgement: 25
- social_conversation_management / repeated_full_menu: 24
- pain_tentative_pain / repeated_full_menu: 10
- pain_tentative_pain / internal_wording: 7
- permission_time_pressure / repeated_full_menu: 5
- asr_repair / asr_garble_not_repaired: 3
- pain_tentative_pain / false_pain: 1

## Top Recognition Failures

## Top Response-Shape Failures
- social_conversation_management / no_acknowledgement: 25
- social_conversation_management / repeated_full_menu: 24
- pain_tentative_pain / repeated_full_menu: 10
- pain_tentative_pain / internal_wording: 7
- permission_time_pressure / repeated_full_menu: 5
- asr_repair / asr_garble_not_repaired: 3
- pain_tentative_pain / false_pain: 1

## Examples Of Strongest Failures
- routesignal_live_demo | permission_time_pressure | yeah sure | repeated_full_menu | recognized=permission_acknowledgement | response='Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today?'
- routesignal_live_demo | pain_tentative_pain | premium is a problem | repeated_full_menu | recognized=pain_confirmed | response='If callback reminders for demo follow-up sit in a spreadsheet, they can slip. Which part is more familiar: manual tracking or missed callbacks?'
- routesignal_live_demo | pain_tentative_pain | repair timings are usually pretty long | repeated_full_menu | recognized=pain_confirmed | response='If callback reminders for demo follow-up sit in a spreadsheet, they can slip. Which part is more familiar: manual tracking or missed callbacks?'
- routesignal_live_demo | pain_tentative_pain | maybe coverage fit | internal_wording | recognized=tentative_gap_interest | response='I should not give coverage advice. I can route this to the approved qualified reviewer path.'
- routesignal_live_demo | social_conversation_management | slow down | repeated_full_menu, no_acknowledgement | recognized=slow_down_or_speak_faster | response='If callback reminders for demo follow-up sit in a spreadsheet, they can slip. Which part is more familiar: manual tracking or missed callbacks?'
- routesignal_live_demo | social_conversation_management | I don't speak English well | repeated_full_menu, no_acknowledgement | recognized=language_mismatch | response='If callback reminders for demo follow-up sit in a spreadsheet, they can slip. Which part is more familiar: manual tracking or missed callbacks?'
- routesignal_live_demo | social_conversation_management | that's not how you say my name | repeated_full_menu, no_acknowledgement | recognized=pronunciation_or_name_correction | response='If callback reminders for demo follow-up sit in a spreadsheet, they can slip. Which part is more familiar: manual tracking or missed callbacks?'
- routesignal_live_demo | social_conversation_management | haha okay | no_acknowledgement | recognized=small_talk | response='If inbound demo requests land in one inbox, missed follow-up can happen because everyone assumes someone else replied. Which part is harder today: seeing it, assigning the reply, or remembering the callback?'
- routesignal_live_demo | social_conversation_management | you're annoying | repeated_full_menu, no_acknowledgement | recognized=emotional_frustration | response='If callback reminders for demo follow-up sit in a spreadsheet, they can slip. Which part is more familiar: manual tracking or missed callbacks?'
- routesignal_live_demo | asr_repair | play a double be good | asr_garble_not_repaired | recognized=asr_garbled_or_low_confidence | response='No problem. We can leave it here.'

## Campaign-Specific Or Universal
Failures appearing in three or more campaigns are treated as likely universal-policy/runtime gaps.
- repeated_full_menu: 5 campaigns (routesignal_live_demo, synthetic-automotive-service-review, synthetic-b2b-saas-operations, synthetic-home-services-estimate, synthetic-insurance-review)
- internal_wording: 5 campaigns (routesignal_live_demo, synthetic-automotive-service-review, synthetic-b2b-saas-operations, synthetic-home-services-estimate, synthetic-insurance-review)
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
