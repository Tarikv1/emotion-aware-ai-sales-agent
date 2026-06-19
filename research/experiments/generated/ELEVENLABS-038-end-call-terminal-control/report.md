# ELEVENLABS-038-end-call-terminal-control

- Target agent ID: `agent_7801kt0g32zxf4f8x5zkykj7syty`
- Target agent name: `web design`
- `end_call` already existed: `false`
- `end_call` added or updated: `true`
- Final `end_call` count: `1`
- Duplicate custom/server `end_call` removed: `false`
- Procedures inactive: `true`
- Prompt updated: `true`
- KB documents updated in place: `atlas_close_and_followup_playbook.md, atlas_output_quality_rules.md, atlas_price_scope_cost_drivers.md`
- Canonical KB attachments after patch: `17`
- Analysis updated through live agent config: `true`
- Analysis update limitation: Live platform_settings.evaluation.criteria was patched from the repo analysis config.
- Unrelated settings preserved: `true`
- Simulations run: `false`
- Outbound calls made: `false`

## Final End Call Description

End the call only when the conversation is genuinely complete. Call this tool once when the buyer explicitly ends a completed conversation, gives a hard stop or do-not-call request, or a guarantee-only disqualification has reached its terminal conclusion. Before ending, answer any live direct question or unresolved concern, confirm any pending email destination, include by-the-end-of-day delivery timing after email confirmation, and confirm any agreed callback window. Use the tool's message field as the single final spoken line. Do not speak a separate farewell before invoking the tool. Do not end while email confirmation is pending, the buyer accepted the mockup but no email is known, or the buyer is still asking about price, process, capability, scope, or another unresolved concern. Do not call this tool more than once.
