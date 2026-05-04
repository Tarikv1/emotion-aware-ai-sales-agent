# Adaptive Sales Agent Reasoning

Source inspiration: https://github.com/kyegomez/OpenMythos

Reuse label: adapted pattern.

This is a product-local reasoning workflow for the Emotion Aware AI Sales Agent. It is not an OpenMythos runtime dependency.

## Architecture Rule

Every use of this workflow must preserve:

```text
one reusable sales-agent core
  + configurable SalesCampaign profiles
  + explicit guardrails, consent, provider gates, and human escalation paths
```

The workflow can change how carefully the sales-agent core reviews a draft, but it must not create a separate campaign-specific agent or an unattended autonomous closer.

## Prelude

Before drafting or reviewing a sales response, gather only the necessary context:

- active SalesCampaign profile
- allowed product claims and do-not-claim list
- contact stage and channel
- latest user/customer message
- known consent and provider boundaries
- available source-backed proof
- escalation rules
- tone and brand constraints

Do not include unrelated transcripts, private files, secrets, API keys, or customer data that is not needed for the current response.

## Recurrent Review Loop

Each pass reviews the same draft against the stable campaign context.

Always-on checks:

- Does this use the reusable sales-agent core rather than a one-off agent?
- Does it stay inside the SalesCampaign profile?
- Are claims source-backed?
- Is the emotional read framed as uncertainty, not diagnosis?
- Are consent, privacy, and provider gates respected?
- Is there a clear human escalation path?

Routed checks:

- Objection handling: price, trust, timing, authority, need, or competitor.
- Emotion-aware tone: frustration, hesitation, curiosity, urgency, confusion, or disengagement.
- Claim safety: remove unsupported claims, guarantees, or overpromising.
- Compliance: avoid sensitive inference, manipulation, or hidden profiling.
- Channel fit: email, call script, chat, voicemail, or CRM note.

## Adaptive Depth

Use the smallest loop budget that matches the risk.

- Fast: low-risk internal draft or formatting pass.
- Standard: normal sales response, battle card, or campaign copy.
- Deep: claim-heavy, sensitive vertical, customer-facing automation, provider/API behavior, voice/audio, or thesis evaluation.
- Stop and ask Tarik: unclear consent, customer data exposure, legal/compliance uncertainty, publish/send action, or campaign architecture change.

## Halting Criteria

Stop the loop when:

- the draft fits the SalesCampaign profile
- unsupported claims are removed or sourced
- privacy/provider risks are addressed
- escalation is clear
- remaining limitations are documented
- the next step is a human review gate when external action is involved

## Coda

The final output should include:

- customer-facing draft or internal note
- source-backed claims used
- assumptions and missing data
- escalation or review gate
- verification or evaluation note when relevant

## Product Boundary

Do not add:

- OpenMythos package code
- PyTorch model code
- Hugging Face dataset downloads
- model weights or tokenizers
- autonomous send/publish/edit behavior
- hidden memory or unreviewed provider calls

If this workflow becomes executable later, implement it as project-local product tooling and keep customer setup simple.
