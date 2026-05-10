# PROD-041A Conditional Scenario Diversity Expansion

PROD-041A expands the offline conditional simulator before the PROD-041 human review checkpoint.

## Summary
- Call Count: `40`
- B2B Call Count: `24`
- B2C Call Count: `16`
- Scenario Label Count: `40`
- Domain Count: `27`
- B2B Domain Count: `19`
- B2C Domain Count: `8`
- Emotional Start State Count: `8`
- Objection Type Count: `34`
- Opening Style Count: `7`
- Terminal Outcome Type Count: `9`
- Safe Close Rate: `0.775`
- Non Sale Correctness Rate: `1.0`
- Hard Failure Rate: `0.0`
- Strategy Match Rate: `1.0`
- Emotion Handling Rate: `1.0`
- Hard Failure Count: `0`
- Payment Collection Count: `0`
- Unsupported Claim Count: `0`
- Leakage Finding Count: `0`

## Required Labels

`price_sensitive`, `manager_review`, `existing_provider`, `confused_fit`, `skeptical_proof`, `busy_now`, `send_info`, `contract_fear`, `payment_fear`, `security_review`, `bad_experience`, `needs_approval`, `hidden_objection`, `competitor_comparison`, `not_interested`, `hostile_rejection`, `callback_request`, `support_boundary`, `technical_integration`, `setup_timeline`, `multi_location_routing`, `low_fit`, `sale_ready`, `discovery_needed`, `insurance_price_fear`, `spouse_input`, `scam_card_fear`, `consumer_not_interested`, `consumer_callback`, `coverage_confusion`, `already_covered`, `consumer_bad_experience`, `written_info`, `consumer_hostile`, `cancellation_boundary`, `appointment_interest`, `sensitive_healthcare`, `home_service_comparison`, `reminder_plan`, `no_pressure_consumer`

## Review Surface

- Filter by B2B/B2C, domain, scenario label, emotion, strategy, objection, terminal outcome, and failure flag.
- Show selected opening plus unused opening variants.
- Show exact customer text and exact agent answer per turn.
- Show required strategy, detected strategies, terminal outcome validity, score flags, and failure taxonomy hits.

## Boundary

PROD-041A is local/offline only. It does not call providers, call an LLM, read private data, download datasets, store raw transcripts, copy transcript text, export transcript-derived commercial runtime prompts, start a server, collect payment, enable retrieval by default, enable composer hooks by default, change runtime behavior, or allow production runtime promotion.

The next checkpoint remains `PROD-041-conditional-simulation-review` for human review.

## Scenario Scores

| Scenario | Market | Domain | Emotion | Strategy Match | Emotion Handled | Terminal | Hard Failures |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `price_sensitive` | B2B | field-service software | skeptical | `true` | `true` | `callback_scheduled` | `0` |
| `manager_review` | B2B | logistics | curious | `true` | `true` | `manager_review_needed` | `0` |
| `existing_provider` | B2B | healthcare operations | calm | `true` | `true` | `callback_scheduled` | `0` |
| `confused_fit` | B2B | manufacturing | confused | `true` | `true` | `callback_scheduled` | `0` |
| `skeptical_proof` | B2B | financial services | skeptical | `true` | `true` | `written_info_requested` | `0` |
| `busy_now` | B2B | SaaS operations | rushed | `true` | `true` | `callback_scheduled` | `0` |
| `send_info` | B2B | education services | calm | `true` | `true` | `written_info_requested` | `0` |
| `contract_fear` | B2B | hospitality | anxious | `true` | `true` | `written_info_requested` | `0` |
| `payment_fear` | B2B | automotive services | distrustful | `true` | `true` | `handoff_required` | `0` |
| `security_review` | B2B | cybersecurity | skeptical | `true` | `true` | `handoff_required` | `0` |
| `bad_experience` | B2B | retail chain | irritated | `true` | `true` | `written_info_requested` | `0` |
| `needs_approval` | B2B | real estate | calm | `true` | `true` | `manager_review_needed` | `0` |
| `hidden_objection` | B2B | professional services | curious | `true` | `true` | `callback_scheduled` | `0` |
| `competitor_comparison` | B2B | marketing agency | skeptical | `true` | `true` | `written_info_requested` | `0` |
| `not_interested` | B2B | wholesale distribution | calm | `true` | `true` | `rejected` | `0` |
| `hostile_rejection` | B2B | telecom reseller | irritated | `true` | `true` | `do_not_contact` | `0` |
| `callback_request` | B2B | property management | rushed | `true` | `true` | `callback_scheduled` | `0` |
| `support_boundary` | B2B | B2B software | irritated | `true` | `true` | `support_boundary_ended` | `0` |
| `technical_integration` | B2B | manufacturing | curious | `true` | `true` | `handoff_required` | `0` |
| `setup_timeline` | B2B | healthcare operations | anxious | `true` | `true` | `callback_scheduled` | `0` |
| `multi_location_routing` | B2B | retail chain | calm | `true` | `true` | `accepted` | `0` |
| `low_fit` | B2B | construction | confused | `true` | `true` | `not_qualified` | `0` |
| `sale_ready` | B2B | field-service software | curious | `true` | `true` | `accepted` | `0` |
| `discovery_needed` | B2B | SaaS operations | calm | `true` | `true` | `callback_scheduled` | `0` |
| `insurance_price_fear` | B2C | insurance service | anxious | `true` | `true` | `written_info_requested` | `0` |
| `spouse_input` | B2C | home services | calm | `true` | `true` | `callback_scheduled` | `0` |
| `scam_card_fear` | B2C | consumer telecom | distrustful | `true` | `true` | `written_info_requested` | `0` |
| `consumer_not_interested` | B2C | retail membership | calm | `true` | `true` | `rejected` | `0` |
| `consumer_callback` | B2C | automotive service | rushed | `true` | `true` | `callback_scheduled` | `0` |
| `coverage_confusion` | B2C | insurance service | confused | `true` | `true` | `handoff_required` | `0` |
| `already_covered` | B2C | consumer telecom | calm | `true` | `true` | `rejected` | `0` |
| `consumer_bad_experience` | B2C | home services | irritated | `true` | `true` | `written_info_requested` | `0` |
| `written_info` | B2C | consumer wellness | skeptical | `true` | `true` | `written_info_requested` | `0` |
| `consumer_hostile` | B2C | retail membership | irritated | `true` | `true` | `do_not_contact` | `0` |
| `cancellation_boundary` | B2C | subscription service | irritated | `true` | `true` | `support_boundary_ended` | `0` |
| `appointment_interest` | B2C | healthcare scheduling | curious | `true` | `true` | `accepted` | `0` |
| `sensitive_healthcare` | B2C | healthcare scheduling | anxious | `true` | `true` | `handoff_required` | `0` |
| `home_service_comparison` | B2C | home services | skeptical | `true` | `true` | `rejected` | `0` |
| `reminder_plan` | B2C | automotive service | calm | `true` | `true` | `accepted` | `0` |
| `no_pressure_consumer` | B2C | consumer wellness | distrustful | `true` | `true` | `accepted` | `0` |
