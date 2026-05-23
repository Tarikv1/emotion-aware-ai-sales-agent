# UNIVERSAL-BUYER-MOVES-CROSS-CAMPAIGN-001

## Summary
Dry-run cross-campaign buyer-move matrix using existing turn builders and the universal policy frame.
Status: red_findings

## Matrix Size
- Campaigns: 5
- Buyer-move cases per campaign: 55
- Total turns evaluated: 275
- Recognition pass/fail: 275 / 0
- Response pass/fail: 266 / 9

## Pass/Fail Counts By Buyer-Move Category
- appointment_callback_send_info: pass=30 fail=0
- asr_repair: pass=16 fail=9
- confusion_challenge_repair: pass=30 fail=0
- direct_product_value_questions: pass=30 fail=0
- objections: pass=35 fail=0
- pain_tentative_pain: pass=25 fail=0
- permission_time_pressure: pass=15 fail=0
- scope_regulated_claim_boundaries: pass=25 fail=0
- social_conversation_management: pass=30 fail=0
- trust_identity_privacy_consent: pass=30 fail=0

## Top Failure Clusters
- asr_repair / repeated_full_menu: 8
- asr_repair / asr_garble_not_repaired: 1

## Top Recognition Failures

## Top Response-Shape Failures
- asr_repair / repeated_full_menu: 8
- asr_repair / asr_garble_not_repaired: 1

## Examples Of Strongest Failures
- routesignal_live_demo | asr_repair | repeal timings are usually pretty long | asr_garble_not_repaired | recognized=asr_garbled_or_low_confidence | response='I can answer that directly if you name the point: workflow, price, security, or callback timing.'
- synthetic-insurance-review | asr_repair | yeah that would be good | repeated_full_menu | recognized=permission_acknowledgement | response='The quick check is whether any of these areas is worth a short licensed coverage review: premium or budget, coverage fit, or renewal or timing. If not, I can stop here; which part should I check first?'
- synthetic-insurance-review | asr_repair | repair timings are usually pretty long | repeated_full_menu | recognized=pain_confirmed | response='The quick check is whether any of these areas is worth a short licensed coverage review: premium or budget, coverage fit, or renewal or timing. If not, I can stop here; which part should I check first?'
- synthetic-b2b-saas-operations | asr_repair | yeah that would be good | repeated_full_menu | recognized=permission_acknowledgement | response='The quick check is whether any of these areas is worth a short operations fit review: manual work, integration risk, or visibility gap. If not, I can stop here; which part should I check first?'
- synthetic-b2b-saas-operations | asr_repair | repair timings are usually pretty long | repeated_full_menu | recognized=pain_confirmed | response='The quick check is whether any of these areas is worth a short operations fit review: manual work, integration risk, or visibility gap. If not, I can stop here; which part should I check first?'
- synthetic-automotive-service-review | asr_repair | yeah that would be good | repeated_full_menu | recognized=permission_acknowledgement | response='The quick check is whether any of these areas is worth a short service advisor inspection review: vehicle issue, repair timing, or warranty or estimate. If not, I can stop here; which part should I check first?'
- synthetic-automotive-service-review | asr_repair | repair timings are usually pretty long | repeated_full_menu | recognized=pain_confirmed | response='The quick check is whether any of these areas is worth a short service advisor inspection review: vehicle issue, repair timing, or warranty or estimate. If not, I can stop here; which part should I check first?'
- synthetic-home-services-estimate | asr_repair | yeah that would be good | repeated_full_menu | recognized=permission_acknowledgement | response='The quick check is whether any of these areas is worth a short inspection or estimate review: service need, scheduling urgency, or estimate or property details. If not, I can stop here; which part should I check first?'
- synthetic-home-services-estimate | asr_repair | repair timings are usually pretty long | repeated_full_menu | recognized=pain_confirmed | response='The quick check is whether any of these areas is worth a short inspection or estimate review: service need, scheduling urgency, or estimate or property details. If not, I can stop here; which part should I check first?'

## Campaign-Specific Or Universal
Failures appearing in three or more campaigns are treated as likely universal-policy/runtime gaps.
- repeated_full_menu: 4 campaigns (synthetic-automotive-service-review, synthetic-b2b-saas-operations, synthetic-home-services-estimate, synthetic-insurance-review)

## Recommended Next Implementation Slice
Integrate universal challenge/direct-question response-shape constraints before campaign-specific fallback menus.

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
