# HUMAN-SEMANTIC-REVIEW-PACKET-001 Index

Upload these files to ChatGPT or a human reviewer:

- `review_packet.md`: primary readable review packet.
- `review_packet.json`: full machine-readable packet.
- `review_packet.jsonl`: one sanitized reviewed turn per line.
- `redaction_report.json`: privacy and side-effect proof.

Conversations: 96
Turn records: 414

Vertical coverage:
- `automotive_service`: 10 conversations
- `b2b_saas`: 10 conversations
- `healthcare_admin_or_medical_equipment`: 10 conversations
- `home_services`: 10 conversations
- `insurance`: 10 conversations
- `membership_or_subscription`: 10 conversations
- `retail_or_ecommerce_support_sales`: 10 conversations
- `routesignal_live_demo`: 16 conversations
- `telecom`: 10 conversations

Edge buckets:
- `callback_timing`: 9 conversations
- `confusion`: 17 conversations
- `fallback_repair`: 11 conversations
- `long_conversation_state_drift`: 9 conversations
- `no_pain_current_issue_clear`: 10 conversations
- `not_relevant_no_need`: 9 conversations
- `pain_confirmed`: 10 conversations
- `permission_acknowledgement`: 9 conversations
- `possible_pain_ambiguity`: 9 conversations
- `regulated_caution`: 8 conversations
- `right_person_authority`: 9 conversations
- `routesignal_preservation`: 15 conversations
- `send_info`: 9 conversations
- `stop_refusal`: 9 conversations

Review priority:

1. Long mixed state-drift conversations.
2. Regulated caution turns.
3. Send-info and right-person contact capture.
4. Stop/refusal persistence.
5. Fallback repair and out-of-scope questions.
6. RouteSignal preservation cases where RouteSignal wording is allowed.
