# UNIVERSAL-SALES-CONVERSATION-KNOWLEDGE-001A

Status: pass
Failure count: 0

## Checks

- Module import and identity
- Required buyer moves, stages, response shapes, call controls, fact slots, ASR cases, and expanded 4E1A categories
- Material widening thresholds for buyer moves, response shapes, repair rules, and ASR repair cases
- Campaign-specific leakage outside the fixture matrix
- Response-shape required steps
- Call-control constraints
- ASR repair boundary
- Campaign fact slot responsibilities
- Expanded forbidden customer-facing patterns
- Declarative-only import and runtime response-generation boundaries
- Side-effect flags

## Counts

{
  "asr_cases": 19,
  "buyer_moves": 73,
  "call_controls": 9,
  "campaign_fact_slots": 20,
  "conversation_stages": 10,
  "forbidden_customer_patterns": 14,
  "repair_rules": 66,
  "response_shapes": 44
}

## Failures

- None

## Side Effects

{
  "creates_calendar_event": false,
  "live_tts_used": false,
  "local_llm_calls_made": false,
  "opens_prod_102": false,
  "private_transcript_content_copied": false,
  "provider_calls_made": false,
  "real_customer_data_used": false,
  "sends_email": false,
  "writes_crm": false
}
