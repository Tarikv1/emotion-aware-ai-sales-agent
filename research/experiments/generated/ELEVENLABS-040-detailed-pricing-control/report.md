# ELEVENLABS-040 Detailed Pricing Control Report

## Status

Repo implementation and the guarded live Atlas product patch are complete at source commit `8b5f5521771c0b914c14c12ebbde9970de4c714e`.

Final behavioral verification is blocked by an external ElevenLabs simulation failure. Broad live readiness is not claimed.

## Product Changes

- Paid prices remain buyer-triggered and are not volunteered.
- The first price answer and later price, quote, review, or scoping follow-ups are price-only; mockup, email, and send CTAs stay locked.
- Three-plus-feature total-cost chains use only the `$4,000-$6,500` whole-project band, including later CRM questions.
- Direct CRM/API chains use only `$1,000-$2,500+`; the `$100-$250` request-form range is not introduced.
- Edit-definition questions do not unlock a second care-plan price.
- Portal/custom scope chains withhold numeric pricing and do not reopen the mockup.
- The independent trace validator now handles plural price/cost triggers, spoken range variants, negated fixed-quote wording, budget-fit equivalents, initial price CTAs, portal CTA leakage, and firm-quote/scoping follow-ups.

## Live Patch

- Agent: `agent_7801kt0g32zxf4f8x5zkykj7syty` (`web design`)
- Prompt word count: `1896`
- Provider writes: compact prompt plus the three already-active pricing/output KB documents
- Provider write result: passed
- Focused KB attachments: `17`, unique, manifest order preserved
- Analysis criteria: `30`, IDs and order preserved
- Built-in `end_call`: `1`
- Custom/server duplicate `end_call`: `0`
- Procedures: inactive
- Unrelated-tool fingerprint: identical before/after
- Outbound calls: none

KB order:

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

## Independent Evaluation

Pre-final source invocation `suite_8701kxbz5tktfh4tb0jfpvsmjdkt` was marked `10/10` passed by ElevenLabs but independently and manually graded `3/10` passed. Those seven failure classes were fixed in commit `8b5f552` and the live agent was repatched.

Post-final source invocation `suite_3101kxc0ccj6e25aajz927g0b5h1` did not produce gradeable conversations. All ten tests stopped after exactly three messages with:

- `Simulation did not complete successfully`
- `Unexpected error occurred`

Controlled single-test invocation `suite_2601kxc0p7w7fhhvqhma1339ke4e` reproduced the same failure after the same three-message boundary.

The signed-in dashboard confirms the 040 folder still contains exactly ten tests and that the inspected test still uses Gemini 2.5 Flash for simulated user and evaluation. No test definition was edited. The dashboard also displays an unpaid-invoice warning and a payment-failed modal.

## Verification

- `validate_elevenlabs_040_detailed_pricing_control.py`: pass
- Live patcher tests: `12/12` pass
- Live test runner tests: `44/44` pass
- Independent trace tests: `26/26` pass
- Evidence tests: `21/21` pass
- Validators 039, 038, 037, 036, 034, 033, 032, 031, and 030: pass
- `git diff --check`: pass
- GPT-5.5 focused product/parser re-review: pass, no blocking findings
- GPT-5.4 manual transcript audit: completed; matched the seven independently identified pre-final product failures

## Blocker And Next Gate

Resolve the ElevenLabs unpaid invoice or provider simulation-service error, then rerun the unchanged ten-test suite once. Capture that invocation and require both provider terminal completion and independent/manual transcript pass before claiming broad live readiness.

No outbound call was placed. Dashboard simulations were run as authorized. Test definitions, criteria, models, turns, and dynamic variables were not modified to manufacture a pass.
