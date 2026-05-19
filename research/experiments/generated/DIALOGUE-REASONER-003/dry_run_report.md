# DIALOGUE-REASONER-003 Hybrid Gate Evaluation

- Mode: `dry-run`
- Blocked reason: `dry-run-mode`
- Cases: `100`
- Guard batch: `30/30`
- Invocation gate batch: `30/30`
- Planned reasoning quality cases: `40`
- Provider calls made: `false`
- Text sent to provider: `false`
- API key value logged: `false`
- Runtime route override allowed: `false`
- Opens PROD-102: `false`

## Boundary

- Deterministic runtime owns dialogue act, buyer intent, topic, sales stage, response strategy, safety boundary, and call control.
- The provider may only return reasoning enrichment fields for allowed cases.
- Provider config comes from ignored local env, process env, or explicit non-secret flags.
- Live mode requires `--live` and `--consent-confirmed`.

## Planned Provider Reasoning Cases

- `reason-product-route-signal-summary`: allowed `true`, prompt chars `2566`
- `reason-product-what-do-you-do`: allowed `true`, prompt chars `2529`
- `reason-product-what-does-it-do`: allowed `true`, prompt chars `2501`
- `reason-product-inbound-demo`: allowed `true`, prompt chars `2528`
- `reason-product-manager-visibility`: allowed `true`, prompt chars `2640`
- `reason-product-ownership`: allowed `true`, prompt chars `2614`
- `reason-workflow-included`: allowed `true`, prompt chars `2555`
- `reason-workflow-steps`: allowed `true`, prompt chars `2559`
- `reason-workflow-after-price`: allowed `true`, prompt chars `2750`
- `reason-workflow-shared-inbox`: allowed `true`, prompt chars `2619`
- `reason-workflow-slack`: allowed `true`, prompt chars `2632`
- `reason-workflow-handoff-review`: allowed `true`, prompt chars `2529`
- `reason-manual-spreadsheet`: allowed `true`, prompt chars `2627`
- `reason-manual-current-process`: allowed `true`, prompt chars `2584`
- `reason-manual-not-broken`: allowed `true`, prompt chars `2570`
- `reason-manual-small-volume`: allowed `true`, prompt chars `2655`
- `reason-manual-owner-routing`: allowed `true`, prompt chars `2574`
- `reason-manual-enough`: allowed `true`, prompt chars `2603`
- `reason-selected-handoffs-price`: allowed `true`, prompt chars `2685`
- `reason-selected-callbacks-price`: allowed `true`, prompt chars `2706`
- `reason-selected-routing-price`: allowed `true`, prompt chars `2695`
- `reason-selected-handoff-delay`: allowed `true`, prompt chars `2674`
- `reason-selected-callback-urgency`: allowed `true`, prompt chars `2701`
- `reason-selected-owner-confusion`: allowed `true`, prompt chars `2691`
- `reason-selected-manager-misses`: allowed `true`, prompt chars `2727`
- `reason-selected-reminders`: allowed `true`, prompt chars `2702`
- `reason-fit-situation`: allowed `true`, prompt chars `2504`
- `reason-fit-relevant`: allowed `true`, prompt chars `2486`
- `reason-fit-small-team`: allowed `true`, prompt chars `2507`
- `reason-fit-low-volume`: allowed `true`, prompt chars `2582`
- `reason-fit-current-crm`: allowed `true`, prompt chars `2599`
- `reason-fit-team-process`: allowed `true`, prompt chars `2515`
- `reason-effort-worth-time`: allowed `true`, prompt chars `2583`
- `reason-effort-too-much`: allowed `true`, prompt chars `2593`
- `reason-effort-busy`: allowed `true`, prompt chars `2617`
- `reason-effort-switching`: allowed `true`, prompt chars `2572`
- `reason-topic-shift-product`: allowed `true`, prompt chars `2742`
- `reason-topic-shift-workflow`: allowed `true`, prompt chars `2729`
- `reason-topic-shift-manual`: allowed `true`, prompt chars `2754`
- `reason-topic-shift-fit`: allowed `true`, prompt chars `2658`
