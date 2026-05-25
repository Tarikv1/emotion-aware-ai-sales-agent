# OPENAI-LIVE-SALES-SKILL-FAILURE-AUDIT-001

- Status: `pass`
- Private findings: `6`
- Generated evidence findings: `0`
- Raw private transcript copied: `false`
- Side effects false: `true`

## Category Counts

```json
{
  "universal_sales_skill_defect": 6
}
```

## Sales Skill Failure Counts

```json
{
  "information_dump_without_momentum": 1,
  "missed_close_after_buying_signal": 1,
  "missed_recommendation_after_context": 3,
  "no_summary_of_known_buyer_context": 3,
  "repeated_safety_caveat": 4,
  "weak_choice_close": 3,
  "weak_opening_value": 1
}
```

## Sanitized Findings

```json
[
  {
    "agent_response_hash": "38e2f19668a9",
    "category": "universal_sales_skill_defect",
    "customer_transcript_hash": "bf6038066d44",
    "raw_private_transcript_copied": false,
    "sales_skill_failure_classes": [
      "weak_opening_value"
    ],
    "sanitized_buyer_signal_labels": [
      "no_private_phrase_exported"
    ],
    "source": "data/private/live-demo-003/raw-turns/browser-transcript/LIVE-DEMO-001-1ee53a37-c72e-41d7-87f6-472f4b7315fc-transcript.json",
    "turn_index": 1
  },
  {
    "agent_response_hash": "6d45ea8988b1",
    "category": "universal_sales_skill_defect",
    "customer_transcript_hash": "f4ecf1c11799",
    "raw_private_transcript_copied": false,
    "sales_skill_failure_classes": [
      "missed_recommendation_after_context",
      "no_summary_of_known_buyer_context",
      "repeated_safety_caveat",
      "weak_choice_close"
    ],
    "sanitized_buyer_signal_labels": [
      "buyer_asks_plus_sufficiency",
      "buyer_current_solution_or_no_fit_signal"
    ],
    "source": "data/private/live-demo-003/raw-turns/browser-transcript/LIVE-DEMO-001-1ee53a37-c72e-41d7-87f6-472f4b7315fc-transcript.json",
    "turn_index": 5
  },
  {
    "agent_response_hash": "6d45ea8988b1",
    "category": "universal_sales_skill_defect",
    "customer_transcript_hash": "38507e313579",
    "raw_private_transcript_copied": false,
    "sales_skill_failure_classes": [
      "repeated_safety_caveat"
    ],
    "sanitized_buyer_signal_labels": [
      "buyer_names_heavy_use"
    ],
    "source": "data/private/live-demo-003/raw-turns/browser-transcript/LIVE-DEMO-001-1ee53a37-c72e-41d7-87f6-472f4b7315fc-transcript.json",
    "turn_index": 6
  },
  {
    "agent_response_hash": "6d45ea8988b1",
    "category": "universal_sales_skill_defect",
    "customer_transcript_hash": "ddf55b31ce76",
    "raw_private_transcript_copied": false,
    "sales_skill_failure_classes": [
      "missed_close_after_buying_signal",
      "missed_recommendation_after_context",
      "no_summary_of_known_buyer_context",
      "repeated_safety_caveat",
      "weak_choice_close"
    ],
    "sanitized_buyer_signal_labels": [
      "buyer_agrees_pro_direction"
    ],
    "source": "data/private/live-demo-003/raw-turns/browser-transcript/LIVE-DEMO-001-1ee53a37-c72e-41d7-87f6-472f4b7315fc-transcript.json",
    "turn_index": 7
  },
  {
    "agent_response_hash": "4246f87c16c4",
    "category": "universal_sales_skill_defect",
    "customer_transcript_hash": "f5de61fcde17",
    "raw_private_transcript_copied": false,
    "sales_skill_failure_classes": [
      "information_dump_without_momentum"
    ],
    "sanitized_buyer_signal_labels": [
      "buyer_asks_price"
    ],
    "source": "data/private/live-demo-003/raw-turns/browser-transcript/LIVE-DEMO-001-1ee53a37-c72e-41d7-87f6-472f4b7315fc-transcript.json",
    "turn_index": 8
  },
  {
    "agent_response_hash": "6d45ea8988b1",
    "category": "universal_sales_skill_defect",
    "customer_transcript_hash": "7ba6a8d6f698",
    "raw_private_transcript_copied": false,
    "sales_skill_failure_classes": [
      "missed_recommendation_after_context",
      "no_summary_of_known_buyer_context",
      "repeated_safety_caveat",
      "weak_choice_close"
    ],
    "sanitized_buyer_signal_labels": [
      "buyer_asks_plus_sufficiency",
      "buyer_current_solution_or_no_fit_signal"
    ],
    "source": "data/private/live-demo-003/raw-turns/browser-transcript/LIVE-DEMO-001-1ee53a37-c72e-41d7-87f6-472f4b7315fc-transcript.json",
    "turn_index": 10
  }
]
```
