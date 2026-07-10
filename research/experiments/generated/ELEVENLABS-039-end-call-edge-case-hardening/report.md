# ELEVENLABS-039-end-call-edge-case-hardening

- Target agent ID: `agent_7801kt0g32zxf4f8x5zkykj7syty`
- Target agent name: `web design`
- `end_call` already existed: `true`
- `end_call` added or updated: `true`
- Final `end_call` count: `1`
- Duplicate custom/server `end_call` removed: `false`
- Procedures inactive: `true`
- Prompt updated: `true`
- KB documents updated in place: `atlas_close_and_followup_playbook.md, atlas_offer_facts.md, atlas_output_quality_rules.md`
- Canonical KB attachments after patch: `17`
- Analysis updated through live agent config: `true`
- Analysis update limitation: Live platform_settings.evaluation.criteria was patched from the repo analysis config.
- Unrelated settings preserved: `true`
- Unrelated tool fingerprint preserved: `true`
- Provider patch utility simulations run: `false`
- Authorized dashboard simulations run after patch: `true` (`4` in the final batch)
- Final dashboard simulation result: `4/4 passed`
- Outbound calls made: `false`

## Final End Call Description

End the call only when the conversation is genuinely complete. Call this tool once when the buyer explicitly ends a completed conversation, gives a hard stop or do-not-call request, a completed gatekeeper callback or note outcome is reached, or a guarantee-only disqualification reaches its terminal conclusion. Before ending, answer any live direct question or unresolved concern, confirm any pending email destination, and confirm any agreed callback window. Exception: a hard stop or do-not-call request overrides pending email confirmation, callback, and every unfinished sales action; end immediately without confirming email or continuing the pitch. Include by-the-end-of-day delivery timing only when it has not already been stated, or when email confirmation and goodbye occur in the same buyer turn. Use the tool's message field as the single final spoken line. Do not speak a separate farewell before invoking the tool. Do not end while email confirmation is pending, the buyer accepted the mockup but no email is known, or the buyer is still asking about price, process, capability, scope, or another unresolved concern, except for the hard-stop/do-not-call override. Do not call this tool more than once.

## Dashboard Test Result

The initial browser batch passed `2/4`: hard-stop and gatekeeper-callback passed, while delivery-timing deduplication and gatekeeper-note termination failed. The prompt and active focused KB text were narrowed to remove the email-confirmation farewell conflict and make accepted gatekeeper-note handling literal and terminal.

The final clean browser batch passed `4/4`:

- `sim_039_hard_stop_overrides_pending_email`: `trun_6701kx5tnqcjeyhtg6nkcke6f9ha`
- `sim_039_delivery_timing_not_repeated`: `trun_4801kx5tnqchfv7amx388r1bresw`
- `sim_039_gatekeeper_callback_atomic_end_call`: `trun_6601kx5tnqckf918cgtr8nr4zyeg`
- `sim_039_gatekeeper_note_atomic_end_call`: `trun_4701kx5tnqcmer4rf9kn2whsm08p`

The final traces show one `end_call` per scenario, the expected tool-bound final message, no delivery-timing repetition, no email confirmation after a hard stop, and atomic gatekeeper callback/note termination. No outbound call ran. Procedures remained inactive. No unrelated dashboard draft was published.

## Provider Action Errors

No ElevenLabs MCP/API write failed. Local command quoting errors and stale browser element references occurred before provider requests or during dashboard navigation; they did not alter provider state.

## Final Validators

All requested validators exited `0`:

- `validate_elevenlabs_039_end_call_edge_case_hardening.py`: pass (`1641` prompt words, `30` criteria, `4` tests)
- `validate_elevenlabs_038_end_call_terminal_control.py`: pass (`1641` prompt words, `30` criteria, `7` tests)
- `validate_elevenlabs_037_confident_capability_control.py`: pass (`1641` prompt words, `30` criteria, `8` tests)
- `validate_elevenlabs_036_natural_sales_scenarios_tests.py`: pass (`10` tests)
- `validate_elevenlabs_034_human_phone_naturalness.py`: pass
- `validate_elevenlabs_033_email_confirmation_precision.py`: pass
- `validate_elevenlabs_032_final_runtime_polish.py`: pass
- `validate_elevenlabs_031_runtime_elite_hardening.py`: pass
- `validate_elevenlabs_030_live_transcript_failure_hardening.py`: pass
- `git diff --check`: pass; line-ending notices only
