# UNIVERSAL-BUYER-MOVES-CROSS-CAMPAIGN-001

## Summary
Dry-run cross-campaign buyer-move matrix using existing turn builders and the universal policy frame.
Status: pass

## Matrix Size
- Campaigns: 5
- Buyer-move cases per campaign: 55
- Total turns evaluated: 275
- Recognition pass/fail: 275 / 0
- Response pass/fail: 275 / 0

## Pass/Fail Counts By Buyer-Move Category
- appointment_callback_send_info: pass=30 fail=0
- asr_repair: pass=25 fail=0
- confusion_challenge_repair: pass=30 fail=0
- direct_product_value_questions: pass=30 fail=0
- objections: pass=35 fail=0
- pain_tentative_pain: pass=25 fail=0
- permission_time_pressure: pass=15 fail=0
- scope_regulated_claim_boundaries: pass=25 fail=0
- social_conversation_management: pass=30 fail=0
- trust_identity_privacy_consent: pass=30 fail=0

## Top Failure Clusters

## Top Recognition Failures

## Top Response-Shape Failures

## Examples Of Strongest Failures

## Campaign-Specific Or Universal
Failures appearing in three or more campaigns are treated as likely universal-policy/runtime gaps.

## Recommended Next Implementation Slice
No behavior slice recommended from this matrix; preserve current runtime and broaden only with live evidence.

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
