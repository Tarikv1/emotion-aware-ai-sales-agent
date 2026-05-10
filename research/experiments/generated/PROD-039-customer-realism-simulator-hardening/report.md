# PROD-039 Customer Realism Simulator Hardening

PROD-039 keeps the same fixed calls and rewrites only simulated customer phrasing so the dialogue sounds less like evaluation labels and more like hesitant, busy, skeptical, confused, or rejecting buyers.

## Experiment Discipline

- Hypothesis: more natural customer phrasing improves reviewability without changing agent answers, decisions, safety flags, or terminal outcomes.
- Fixed cases: same `8` calls and `14` turns from PROD-037.
- Editable surface: `customer_simulator_response_phrasing`.
- Decision: `keep-for-demo-surface-rerun`.

## Result

- Checkpoint id: `PROD-039-customer-realism-simulator-hardening`
- Source checkpoint: `PROD-038-local-demo-surface-review`
- Trace source checkpoint: `PROD-037-local-interactive-trace-demo-surface`
- Customer realism gate passed: `true`
- Customer response changed count: `14`
- Customer opening changed count: `8`
- Agent answer changed count: `0`
- Decision snapshot changed count: `0`
- Terminal outcome changed count: `0`
- Safety flag changed count: `0`
- Baseline unrealistic phrase hits: `11`
- Hardened unrealistic phrase hits: `0`
- Naturalness feature count: `29`
- Same cases rerun: `true`
- One editable surface: `customer_simulator_response_phrasing`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`
- Next build recommendation: `customer_realism_demo_surface_rerun`
- Next checkpoint: `PROD-040-customer-realism-demo-surface-rerun`

## Naturalness Features

budget-reservation, compressed-summary-request, conditional-acceptance, conditional-future-review, conditional-interest, direct-price-question, do-not-call-boundary, existing-provider-friction, firm-stop-request, hedging, internal-stakeholder-friction, low-commitment, low-patience, mild-interest, mild-reluctance, partial-understanding, plain-rejection, plain-spoken-question, practicality-boundary, product-fit-check, purchase-boundary, realistic-next-step, redirect-request, skeptical-friction, stakeholder-fit, stakeholder-friction, support-boundary, time-pressure, written-proof-request

## Boundary

PROD-039 does not call providers, call an LLM, read private data, download datasets, start a server, collect payment, enable retrieval by default, enable composer hooks by default, change runtime behavior, unblock voice playback, unblock public demo polish, or allow production runtime promotion.
