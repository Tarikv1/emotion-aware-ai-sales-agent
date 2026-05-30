# PHASE-4K11-BOUNDARY-SENSITIVE-SELECTOR-GENERALIZATION-001

- Status: pass
- Scope: selector-only boundary-sensitive generalization audit
- Positive boundary-sensitive pass count: 5/5
- Benign product-scope pass count: 6/6
- Salesforce case remains same_action: true
- False ASR mapping count: 0
- Genuine selector/runtime disagreement count: 0
- 4K10 naturalness issue count: 14
- Selector control allowed: false
- Live selector control recommended: false
- Response replacement performed: false
- Provider/model/TTS/CRM/email/calendar/side-effect path enabled: false
- Raw candidate responses in public shadow records: false

## Selector Matrix

| Case | Expected | Selector action | Pass | Utterance |
| --- | --- | --- | --- | --- |
| 4k11_positive_001 | respect_boundary | respect_boundary | true | Does it integrate securely with Salesforce? |
| 4k11_positive_002 | respect_boundary | respect_boundary | true | Can you guarantee Salesforce integration works? |
| 4k11_positive_003 | respect_boundary | respect_boundary | true | Is it compliant with our security requirements? |
| 4k11_positive_004 | respect_boundary | respect_boundary | true | Can you prove HubSpot integration is secure? |
| 4k11_positive_005 | respect_boundary | respect_boundary | true | Can you guarantee the CRM setup? |
| 4k11_negative_001 | not_respect_boundary | ask_use_case_gap | true | What CRM does this work with at a high level? |
| 4k11_negative_002 | not_respect_boundary | ask_usage_intensity | true | How does the workflow routing work? |
| 4k11_negative_003 | not_respect_boundary | ask_use_case_gap | true | What does the integration review check? |
| 4k11_negative_004 | not_respect_boundary | ask_use_case_gap | true | Is this about CRM follow-up reminders? |
| 4k11_negative_005 | not_respect_boundary | ask_use_case_gap | true | What kind of security details would a reviewer need? |
| 4k11_negative_006 | not_respect_boundary | ask_use_case_gap | true | Can you explain the setup process at a high level? |

## RouteSignal Deferred Status

- LIVE-DEMO-002: deferred_or_fail (failure_count=13, untouched_in_4k11=true)
- LIVE-DEMO-009: deferred_or_fail (failure_count=3, untouched_in_4k11=true)
- LIVE-DEMO-014: deferred_or_fail (failure_count=3, untouched_in_4k11=true)

## Boundary

- This phase did not enable live selector control.
- This phase did not enable response replacement.
- This phase did not call providers, models, TTS, CRM, email, calendar, payment, or account APIs.
- This phase did not add private raw transcript/audio or raw candidate responses to public shadow evidence.
