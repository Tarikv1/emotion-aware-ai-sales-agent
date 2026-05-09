# PROD-028 Synthetic Campaign Knowledge Grounding

PROD-028 creates a fictional but reality-patterned B2B CRM campaign so the local agent can answer concrete buyer questions with approved campaign facts instead of only asking discovery questions.

## Result

- Checkpoint id: `PROD-028-synthetic-campaign-knowledge-grounding`
- Reality-based source patterning: `true`
- Fictional product: `true`
- Same questions compared: `true`
- Question count: `12`
- Direct answer rate: `1.0`
- Factual correctness rate: `1.0`
- Price correctness rate: `1.0`
- Question overuse rate: `0.0`
- Baseline question overuse rate: `1.0`
- Safe unknown handling rate: `1.0`
- Unsupported claim count: `0`
- Payment collection count: `0`
- Provider calls made: `false`
- Runtime behavior changed: `false`
- Retrieval default enabled: `false`
- Composer hook default enabled: `false`
- Next checkpoint: `PROD-029-grounded-full-scenario-rerun`

## Outputs

- `research/experiments/generated/PROD-028-synthetic-campaign-knowledge-grounding/result.json`
- `research/experiments/generated/PROD-028-synthetic-campaign-knowledge-grounding/synthetic_campaign.json`
- `research/experiments/generated/PROD-028-synthetic-campaign-knowledge-grounding/report.md`
- `research/experiments/generated/PROD-028-synthetic-campaign-knowledge-grounding/grounded_answer_trace.html`

## Source Boundary

Public CRM and customer-operations pricing pages were used as inspiration only for realistic SaaS packaging patterns: per-seat tiers, free trials, annual billing, onboarding/migration fees, support/security tiers, add-ons, integrations, cancellation language, and specialist quote boundaries.

The fictional campaign does not copy real company wording, plan names, brand identity, customer claims, or sales copy. Source URLs and reuse labels are tracked in `docs/thesis/THESIS_REFERENCE_REGISTRY.md`.

## Synthetic Campaign

- Fictional client: `Northstar Workflow Labs`
- Fictional product: `RouteSignal CRM`
- Core product: B2B lead routing, callback ownership, reporting, handoff, and workflow visibility.
- Plans: `Starter`, `Growth`, and `Scale`
- Sales-call boundary: no payment collection, no revenue promises, no unsupported security/integration promises, and specialist handoff for security, procurement, or custom quote questions.

## Evaluation Shape

The checkpoint compares the current local guarded runtime default answer against a synthetic-campaign fact-grounded answer on the same `12` buyer questions. The questions cover pricing, plan differences, cancellation, setup time, integrations, role controls, discounts, eligibility, SSO/sandbox details, provider comparison, price objection, and forbidden revenue promises.

## Boundary

PROD-028 is a local evaluation artifact. It does not call providers, call an LLM, read private data, download datasets, collect payment, start a server, change runtime defaults, enable retrieval by default, or promote the synthetic product as a real client campaign.

## Commands

```powershell
python scripts\run_prod_028_synthetic_campaign_knowledge_grounding.py
python scripts\validate_prod_028_synthetic_campaign_knowledge_grounding.py
```
