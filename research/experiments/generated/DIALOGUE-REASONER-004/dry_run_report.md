# DIALOGUE-REASONER-004 Async Enrichment

- Mode: `dry-run`
- Blocked reason: `dry-run-mode`
- Cases: `100`
- Guard batch: `30/30`
- Invocation gate batch: `30/30`
- Async queued before provider: `40/40`
- Deterministic response available before provider: `40/40`
- Provider cases completed: `0/40`
- Provider calls made: `false`
- Text sent to provider: `false`
- API key value logged: `false`
- Runtime route override allowed: `false`
- Customer response blocked on provider: `false`
- Opens PROD-102: `false`

## Boundary

- Deterministic response generation finishes before any provider enrichment result is needed.
- The provider may only enrich eligible reasoning cases with the DIALOGUE-REASONER-003 schema.
- The enrichment packet stores response fingerprints and counts, not customer-facing response text.
- Route labels and final response mutation stay blocked.

## Planned Async Enrichment

- `reason-product-route-signal-summary`: `queued`, prompt chars `2566`, response chars `208`
- `reason-product-what-do-you-do`: `queued`, prompt chars `2529`, response chars `208`
- `reason-product-what-does-it-do`: `queued`, prompt chars `2501`, response chars `208`
- `reason-product-inbound-demo`: `queued`, prompt chars `2528`, response chars `102`
- `reason-product-manager-visibility`: `queued`, prompt chars `2640`, response chars `208`
- `reason-product-ownership`: `queued`, prompt chars `2614`, response chars `208`
- `reason-workflow-included`: `queued`, prompt chars `2555`, response chars `155`
- `reason-workflow-steps`: `queued`, prompt chars `2559`, response chars `155`
- `reason-workflow-after-price`: `queued`, prompt chars `2750`, response chars `155`
- `reason-workflow-shared-inbox`: `queued`, prompt chars `2619`, response chars `155`
- `reason-workflow-slack`: `queued`, prompt chars `2632`, response chars `155`
- `reason-workflow-handoff-review`: `queued`, prompt chars `2529`, response chars `102`
- `reason-manual-spreadsheet`: `queued`, prompt chars `2627`, response chars `152`
- `reason-manual-current-process`: `queued`, prompt chars `2584`, response chars `152`
- `reason-manual-not-broken`: `queued`, prompt chars `2570`, response chars `152`
- `reason-manual-small-volume`: `queued`, prompt chars `2655`, response chars `152`
- `reason-manual-owner-routing`: `queued`, prompt chars `2574`, response chars `152`
- `reason-manual-enough`: `queued`, prompt chars `2603`, response chars `152`
- `reason-selected-handoffs-price`: `queued`, prompt chars `2685`, response chars `145`
- `reason-selected-callbacks-price`: `queued`, prompt chars `2706`, response chars `152`
- `reason-selected-routing-price`: `queued`, prompt chars `2695`, response chars `143`
- `reason-selected-handoff-delay`: `queued`, prompt chars `2674`, response chars `145`
- `reason-selected-callback-urgency`: `queued`, prompt chars `2701`, response chars `152`
- `reason-selected-owner-confusion`: `queued`, prompt chars `2691`, response chars `145`
- `reason-selected-manager-misses`: `queued`, prompt chars `2727`, response chars `156`
- `reason-selected-reminders`: `queued`, prompt chars `2702`, response chars `131`
- `reason-fit-situation`: `queued`, prompt chars `2504`, response chars `134`
- `reason-fit-relevant`: `queued`, prompt chars `2486`, response chars `134`
- `reason-fit-small-team`: `queued`, prompt chars `2507`, response chars `164`
- `reason-fit-low-volume`: `queued`, prompt chars `2582`, response chars `134`
- `reason-fit-current-crm`: `queued`, prompt chars `2599`, response chars `134`
- `reason-fit-team-process`: `queued`, prompt chars `2515`, response chars `134`
- `reason-effort-worth-time`: `queued`, prompt chars `2583`, response chars `100`
- `reason-effort-too-much`: `queued`, prompt chars `2593`, response chars `100`
- `reason-effort-busy`: `queued`, prompt chars `2617`, response chars `100`
- `reason-effort-switching`: `queued`, prompt chars `2572`, response chars `102`
- `reason-topic-shift-product`: `queued`, prompt chars `2742`, response chars `208`
- `reason-topic-shift-workflow`: `queued`, prompt chars `2729`, response chars `155`
- `reason-topic-shift-manual`: `queued`, prompt chars `2754`, response chars `152`
- `reason-topic-shift-fit`: `queued`, prompt chars `2658`, response chars `107`
