# Sales Expert Feedback

## Purpose

Define how experienced salespeople can help train and improve the autonomous sales agent during development and testing.

This feedback loop is a product-learning mechanism, not a replacement for thesis evaluation.

## What Experts Should Review

Sales experts can review:

- generated agent responses
- selected persuasion strategies
- customer-state labels
- objection handling
- tone and pressure level
- whether the response would work in a real sales conversation

## Feedback Record Schema

Use one record per reviewed case.

```text
SalesExpertFeedbackRecord
  feedback_id
  reviewer_id
  reviewer_experience_note
  case_id
  conversation_context
  user_utterance
  detected_customer_state
  selected_strategy
  generated_response
  response_rating_1_to_5
  strategy_fit_1_to_5
  tone_fit_1_to_5
  would_use_in_real_call
  corrected_strategy
  rewritten_response
  objection_label
  risk_flags
  reviewer_notes
  created_at
```

## Rating Guidance

Use 1 to 5 scoring:

- 1: clearly bad or harmful
- 2: weak, awkward, or risky
- 3: acceptable but average
- 4: good and likely usable
- 5: excellent, natural, and sales-effective

## Feedback Types

### Rating

Experts score whether the response is usable.

### Correction

Experts rewrite the response or select a better strategy.

### Labeling

Experts label the customer's objection, mood, or buying stage.

### Risk Review

Experts flag behavior that is too aggressive, misleading, unnatural, or off-brand.

## How The Agent Learns From Feedback

Start with simple learning mechanisms:

1. Update prompts and strategy rules based on repeated failure patterns.
2. Store high-quality rewritten responses as examples.
3. Retrieve similar expert-approved examples for future cases.
4. Build a preference dataset from ratings and rewrites.
5. Consider fine-tuning only after the feedback dataset is large and clean enough.

## Guardrails

- Do not treat one expert's opinion as universal truth.
- Keep reviewer identity and experience notes separate from public thesis artifacts unless consent is explicit.
- Track whether feedback came from sales experts, general evaluators, or the project team.
- Do not use expert feedback to justify inflated product claims without testing.

## Near-Term Use

For the next product-oriented experiment, ask sales experts to review paired baseline responses and record:

- which response they prefer
- whether the strategy fits the customer state
- how they would rewrite the weaker response
- what objection or buying-stage label they see
