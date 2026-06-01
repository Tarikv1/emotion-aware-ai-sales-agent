# Campaign Adapter Rendering Spec

## Purpose

The renderer turns a validated campaign adapter into a provider-shell package. It does not create campaign facts. It combines universal sales rules, adapter facts, capability boundaries, and campaign-specific KB content.

## Inputs

- universal sales system prompt
- universal sales principles KB
- universal buyer state and emotion KB
- universal objection handling KB
- universal persuasion strategy KB
- universal capability and side-effect policy
- campaign adapter JSON

## Outputs

### ElevenLabs System Prompt

Render a single buyer-facing system prompt that includes:

- truthful identity fields
- campaign goal
- approved opening logic
- qualification and discovery rules
- pricing behavior
- forbidden claims
- capability boundaries
- stop-request handling
- no fake guarantees
- no fake authority
- no pressure after refusal
- no bracketed/internal labels

The prompt must not include internal test language, schema implementation notes, adapter validation notes, private data, unrelated campaign knowledge, or fake actions.

### KB Files

Render uploadable KB files from:

- product facts
- approved claims
- proof points
- buyer personas
- pain-to-value mappings
- objection playbooks
- close paths
- capability and side-effect policy

Each KB file must identify whether it is uploadable knowledge, test-only reference, or do-not-upload material.

### Test Cases

Render test cases from:

- universal test matrix
- campaign-specific objections
- campaign-specific close paths
- pricing policy
- forbidden claims
- unavailable actions
- stop-request policy

Each test case should define expected behavior, pass/fail criteria, and relevant EASID fields.

### Upload Manifest

Render a manifest with:

- filename
- purpose
- upload mode
- source layer
- buyer-facing or internal-only
- side effects enabled flag
- required human review flag

### EASID Logging Fields

Render EASID field requirements for:

- campaign_id
- agent_variant
- buyer_persona
- buyer_state_label
- emotion_label
- objection_type
- persuasion_strategy
- sales_stage
- recommended_next_action
- micro_close_attempted
- micro_close_outcome
- outcome_label
- hard_failure_flags
- safety_flags
- privacy_redaction_status

## Rendering Rules

1. Universal rules apply first.
2. Campaign adapter facts fill only campaign-specific slots.
3. Forbidden claims override approved claims.
4. Unavailable actions override close paths.
5. Stop-request policy overrides persuasion.
6. Missing pricing policy blocks rendering.
7. Missing target customer blocks rendering.
8. Missing conversion goal blocks rendering.
9. Missing stop-request policy blocks rendering.
10. No provider upload, runtime change, or side effect is part of rendering.

## Failure Behavior

If validation returns any blocker, the renderer must output a validation report only. It must not output an uploadable prompt package.
