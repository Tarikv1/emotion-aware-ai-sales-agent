# UNIVERSAL-BUYER-MOVES-CROSS-CAMPAIGN-001

## Summary
Dry-run cross-campaign buyer-move matrix using existing turn builders and the universal policy frame.
Status: red_findings

## Matrix Size
- Campaigns: 5
- Buyer-move cases per campaign: 55
- Total turns evaluated: 275
- Recognition pass/fail: 275 / 0
- Response pass/fail: 231 / 44

## Pass/Fail Counts By Buyer-Move Category
- appointment_callback_send_info: pass=22 fail=8
- asr_repair: pass=14 fail=11
- confusion_challenge_repair: pass=30 fail=0
- direct_product_value_questions: pass=30 fail=0
- objections: pass=35 fail=0
- pain_tentative_pain: pass=25 fail=0
- permission_time_pressure: pass=15 fail=0
- scope_regulated_claim_boundaries: pass=25 fail=0
- social_conversation_management: pass=5 fail=25
- trust_identity_privacy_consent: pass=30 fail=0

## Top Failure Clusters
- social_conversation_management / no_acknowledgement: 25
- social_conversation_management / repeated_full_menu: 20
- appointment_callback_send_info / repeated_full_menu: 8
- asr_repair / repeated_full_menu: 8
- asr_repair / asr_garble_not_repaired: 3

## Top Recognition Failures

## Top Response-Shape Failures
- social_conversation_management / no_acknowledgement: 25
- social_conversation_management / repeated_full_menu: 20
- appointment_callback_send_info / repeated_full_menu: 8
- asr_repair / repeated_full_menu: 8
- asr_repair / asr_garble_not_repaired: 3

## Examples Of Strongest Failures
- routesignal_live_demo | social_conversation_management | slow down | no_acknowledgement | recognized=slow_down_or_speak_faster | response='I can answer that directly if you name the point: workflow, price, security, or callback timing.'
- routesignal_live_demo | social_conversation_management | I don't speak English well | no_acknowledgement | recognized=language_mismatch | response='I can answer that directly if you name the point: workflow, price, security, or callback timing.'
- routesignal_live_demo | social_conversation_management | that's not how you say my name | no_acknowledgement | recognized=pronunciation_or_name_correction | response='I can answer that directly if you name the point: workflow, price, security, or callback timing.'
- routesignal_live_demo | social_conversation_management | haha okay | no_acknowledgement | recognized=small_talk | response='I can answer that directly if you name the point: workflow, price, security, or callback timing.'
- routesignal_live_demo | social_conversation_management | you're annoying | no_acknowledgement | recognized=emotional_frustration | response='I can answer that directly if you name the point: workflow, price, security, or callback timing.'
- routesignal_live_demo | asr_repair | play a double be good | asr_garble_not_repaired | recognized=asr_garbled_or_low_confidence | response='I can answer that directly if you name the point: workflow, price, security, or callback timing.'
- routesignal_live_demo | asr_repair | yadav would be good | asr_garble_not_repaired | recognized=asr_garbled_or_low_confidence | response='I can answer that directly if you name the point: workflow, price, security, or callback timing.'
- routesignal_live_demo | asr_repair | repeal timings are usually pretty long | asr_garble_not_repaired | recognized=asr_garbled_or_low_confidence | response='I can answer that directly if you name the point: workflow, price, security, or callback timing.'
- synthetic-insurance-review | appointment_callback_send_info | can you send available times | repeated_full_menu | recognized=buyer_requests_available_times | response='The quick check is whether any of these areas is worth a short licensed coverage review: premium or budget, coverage fit, or renewal or timing. If not, I can stop here; which part should I check first?'
- synthetic-insurance-review | appointment_callback_send_info | I need email first | repeated_full_menu | recognized=buyer_wants_email_before_booking | response='The quick check is whether any of these areas is worth a short licensed coverage review: premium or budget, coverage fit, or renewal or timing. If not, I can stop here; which part should I check first?'

## Campaign-Specific Or Universal
Failures appearing in three or more campaigns are treated as likely universal-policy/runtime gaps.
- no_acknowledgement: 5 campaigns (routesignal_live_demo, synthetic-automotive-service-review, synthetic-b2b-saas-operations, synthetic-home-services-estimate, synthetic-insurance-review)
- repeated_full_menu: 4 campaigns (synthetic-automotive-service-review, synthetic-b2b-saas-operations, synthetic-home-services-estimate, synthetic-insurance-review)

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
