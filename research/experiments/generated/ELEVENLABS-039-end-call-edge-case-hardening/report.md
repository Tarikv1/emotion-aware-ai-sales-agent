# ELEVENLABS-039 End-Call Edge-Case Hardening

- Agent: `agent_7801kt0g32zxf4f8x5zkykj7syty` / `web design`
- Status: `passed`
- KB count/order matches manifest: `17` / `true`
- Built-in `end_call` count: `1`
- Legacy platform mirror count: `1`
- Custom/server duplicate `end_call` count: `0`
- Procedures inactive: `true`
- Analysis criteria count: `30`
- Analysis IDs match repo: `true`
- Analysis max prompt length: `1790`
- Unrelated tool fingerprint preserved: `true`
- Voice preserved: `true`
- LLM preserved: `true`
- First message preserved: `true`
- Dynamic variables preserved: `true`
- Phone settings preserved: `true`
- Old monolithic KB attached: `false`
- Tests or Analysis docs attached as KB: `false`
- Simulations run: `false`
- Outbound calls made: `false`

## Old End Call Description

End the call only when the conversation is genuinely complete. Call this tool once when the buyer explicitly ends a completed conversation, gives a hard stop or do-not-call request, or a guarantee-only disqualification has reached its terminal conclusion. Before ending, answer any live direct question or unresolved concern, confirm any pending email destination, include by-the-end-of-day delivery timing after email confirmation, and confirm any agreed callback window. Use the tool's message field as the single final spoken line. Do not speak a separate farewell before invoking the tool. Do not end while email confirmation is pending, the buyer accepted the mockup but no email is known, or the buyer is still asking about price, process, capability, scope, or another unresolved concern. Do not call this tool more than once.

## New End Call Description

End the call only when the conversation is genuinely complete. Call this tool once when the buyer explicitly ends a completed conversation, gives a hard stop or do-not-call request, a completed gatekeeper callback or note outcome is reached, or a guarantee-only disqualification reaches its terminal conclusion. Before ending, answer any live direct question or unresolved concern, confirm any pending email destination, and confirm any agreed callback window. Exception: a hard stop or do-not-call request overrides pending email confirmation, callback, and every unfinished sales action; end immediately without confirming email or continuing the pitch. Include by-the-end-of-day delivery timing only when it has not already been stated, or when email confirmation and goodbye occur in the same buyer turn. Use the tool's message field as the single final spoken line. Do not speak a separate farewell before invoking the tool. Do not end while email confirmation is pending, the buyer accepted the mockup but no email is known, or the buyer is still asking about price, process, capability, scope, or another unresolved concern, except for the hard-stop/do-not-call override. Do not call this tool more than once.

## Edge-Case Results

- Hard-stop exception live: `true`
- Delivery-timing deduplication live: `true`
- Gatekeeper callback/note terminal live: `true`

## Updated KB Documents

- `atlas_close_and_followup_playbook.md`
- `atlas_output_quality_rules.md`

## KB Order

1. `universal_sales_core_summary.md`
2. `buyer_moves.md`
3. `value_and_roi_framing.md`
4. `objection_status_quo_and_competition.md`
5. `trust_and_risk_repair.md`
6. `conversation_repair.md`
7. `next_step_policy.md`
8. `disqualification_policy.md`
9. `ethical_persuasion_boundaries.md`
10. `call_quality_rubrics.md`
11. `atlas_offer_facts.md`
12. `atlas_value_mechanisms.md`
13. `atlas_vertical_playbooks.md`
14. `atlas_objection_playbook.md`
15. `atlas_price_scope_cost_drivers.md`
16. `atlas_close_and_followup_playbook.md`
17. `atlas_output_quality_rules.md`

## Failed MCP/API Actions

None.
