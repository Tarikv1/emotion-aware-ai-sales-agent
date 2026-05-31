# Tool Contracts: Future Read-Only Tools

Purpose: plan future ElevenLabs server/MCP/client tool contracts without configuring any tool in 4M0.

All tools below have `configure_now: false`. No tool may send email, book calendar events, write CRM, take payment, change account state, submit contact-sales forms, or claim that an external action happened.

## plan_fit_verifier

- ElevenLabs tool type recommendation: server_tool
- configure_now: false
- Description: Verify a proposed plan recommendation against buyer context and claim boundaries.
- When to call: Future phase only, before a high-confidence recommendation when buyer context is complex.
- When not to call: Do not call in 4M0; do not call for email, booking, CRM, payment, account, or sales submission requests.
- System prompt orchestration note: If unavailable, use KB plan-fit rules and ask one clarifying question.
- Safe fallback if unavailable: Recommend the lightest source-bounded plan or route official review.
- Side-effect policy: Read-only. No account, CRM, email, calendar, payment, or contact-sales side effects.

Parameter schema:

```json
{
  "properties": {
    "buyer_context": {
      "description": "Short non-private summary of buyer use case.",
      "type": "string"
    },
    "proposed_plan": {
      "enum": [
        "Free",
        "Go",
        "Plus",
        "Pro",
        "Business",
        "Enterprise",
        "API boundary",
        "No fit"
      ],
      "type": "string"
    },
    "proposed_reason": {
      "description": "One-sentence reason the agent wants to say.",
      "type": "string"
    }
  },
  "required": [
    "buyer_context",
    "proposed_plan",
    "proposed_reason"
  ],
  "type": "object"
}
```

Output schema:

```json
{
  "properties": {
    "allowed": {
      "type": "boolean"
    },
    "risk_flags": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "safe_plan": {
      "type": "string"
    },
    "spoken_guidance": {
      "type": "string"
    }
  },
  "required": [
    "allowed",
    "safe_plan",
    "spoken_guidance",
    "risk_flags"
  ],
  "type": "object"
}
```

## source_claim_checker

- ElevenLabs tool type recommendation: server_tool or MCP_tool
- configure_now: false
- Description: Classify proposed claims using 4L5 precision categories.
- When to call: Future phase only, before saying exact pricing, model, limits, privacy, security, or Go feature claims.
- When not to call: Do not call in 4M0; do not use as a live browser or source refresh tool.
- System prompt orchestration note: If claim is not stable, choose caveat or official route.
- Safe fallback if unavailable: Say the safe high-level version and route exact details to official pages.
- Side-effect policy: Read-only classification. No network refresh, account, CRM, email, calendar, payment, or contact-sales side effects.

Parameter schema:

```json
{
  "properties": {
    "claim_context": {
      "description": "Optional short context for why the claim is needed.",
      "type": "string"
    },
    "claim_text": {
      "description": "Draft buyer-facing claim to classify.",
      "type": "string"
    }
  },
  "required": [
    "claim_text"
  ],
  "type": "object"
}
```

Output schema:

```json
{
  "properties": {
    "allowed_spoken_version": {
      "type": "string"
    },
    "claim_precision_category": {
      "enum": [
        "stable_source_claim",
        "current_terms_claim_requires_caveat",
        "source_conflict_or_ambiguous",
        "unsupported_do_not_say",
        "official_route_only"
      ],
      "type": "string"
    },
    "official_route_required": {
      "type": "boolean"
    },
    "required_caveat": {
      "type": "string"
    }
  },
  "required": [
    "claim_precision_category",
    "allowed_spoken_version",
    "required_caveat",
    "official_route_required"
  ],
  "type": "object"
}
```

## side_effect_guard

- ElevenLabs tool type recommendation: server_tool
- configure_now: false
- Description: Block email, calendar, CRM, payment, account, purchase, or contact-sales actions and return safe spoken alternative.
- When to call: Future phase only, before responding to action requests.
- When not to call: Do not call in 4M0; do not use to perform the action.
- System prompt orchestration note: If blocked, state that no tool is enabled and provide manual official route.
- Safe fallback if unavailable: Refuse the side effect and provide the manual official route.
- Side-effect policy: Read-only. It must never send, book, write, charge, submit, or change account state.

Parameter schema:

```json
{
  "properties": {
    "buyer_context": {
      "description": "Short context, without private raw transcript.",
      "type": "string"
    },
    "requested_action": {
      "description": "User-requested action.",
      "type": "string"
    }
  },
  "required": [
    "requested_action"
  ],
  "type": "object"
}
```

Output schema:

```json
{
  "properties": {
    "blocked": {
      "type": "boolean"
    },
    "reason": {
      "type": "string"
    },
    "safe_spoken_alternative": {
      "type": "string"
    }
  },
  "required": [
    "blocked",
    "reason",
    "safe_spoken_alternative"
  ],
  "type": "object"
}
```

## conversation_state_summarizer

- ElevenLabs tool type recommendation: server_tool or client_tool
- configure_now: false
- Description: Summarize buyer context without storing private raw transcripts in public evidence.
- When to call: Future phase only, after multiple turns when context preservation is needed.
- When not to call: Do not call in 4M0; do not store private raw transcripts or audio.
- System prompt orchestration note: Use summary to avoid repeated-question loops.
- Safe fallback if unavailable: Use the visible conversation context and ask one clarifying question.
- Side-effect policy: Read-only summary. No external send, storage of raw private transcript, CRM, email, calendar, payment, or account side effects.

Parameter schema:

```json
{
  "properties": {
    "known_plan_context": {
      "description": "Known plan-fit facts from the conversation.",
      "type": "string"
    },
    "recent_turn_summary": {
      "description": "Short local summary, not raw transcript.",
      "type": "string"
    }
  },
  "required": [
    "recent_turn_summary"
  ],
  "type": "object"
}
```

Output schema:

```json
{
  "properties": {
    "buyer_type": {
      "type": "string"
    },
    "known_constraints": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "next_best_question": {
      "type": "string"
    },
    "usage_intensity": {
      "type": "string"
    }
  },
  "required": [
    "buyer_type",
    "usage_intensity",
    "known_constraints",
    "next_best_question"
  ],
  "type": "object"
}
```
