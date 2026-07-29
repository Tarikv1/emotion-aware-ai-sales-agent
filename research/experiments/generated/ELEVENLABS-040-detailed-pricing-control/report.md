# ELEVENLABS-040 Detailed Pricing And Natural-Sales Readiness Report

## Verdict

The active Atlas configuration is ready to wrap the covered hosted text/simulation pricing and natural-sales phase. This is a scoped research/prototype closeout, not a broad live- or production-readiness claim and not a claim that every unchanged ElevenLabs dashboard evaluator is green.

The remaining dashboard discrepancies are evaluator/test-contract mismatches:

- The unchanged 036 CRM test expects a lighter handoff-price mention and a mockup next step. The active product intentionally withholds all paid prices until the buyer asks and suppresses mockup/email/send CTAs during capability and pricing turns.
- The unchanged 036 goodbye simulation collapsed acceptance, email, confirmation, thanks, and two goodbyes into one buyer utterance. The agent correctly used the same-turn atomic email-confirmed goodbye branch.
- The unchanged 036 future-pricing test still injects old dynamic-variable price values. The product and current live variables use the new pricing contract.

No dashboard test, criterion, model, turn limit, Analysis criterion, or test dynamic variable was edited to manufacture a pass.

## Product Result

- Paid prices are buyer-triggered; capability, scope, process, and next-step turns do not volunteer them.
- Existing-site request-form work uses `$100-$250` only after a price ask.
- Direct CRM/API integration uses `$1,000-$2,500+` only after a price ask.
- Multi-feature new-site scope uses one `$4,000-$6,500` whole-project band and one cost driver rather than adding feature ranges.
- Portal/custom scope does not echo speculative buyer numbers, invent a quote, or reopen the mockup.
- CRM capability follow-ups remain price-free and CTA-free until the buyer asks about cost.
- CRM scoping follow-ups request one missing input; a repetition complaint gets a narrowed unanswered point rather than the same sentence again.
- The guarantee-only terminal response is aligned between the compact prompt and close/follow-up KB.

## Live Patch

- Agent: `agent_7801kt0g32zxf4f8x5zkykj7syty` (`web design`)
- Implementation source commit: `5f779b714ef35bdf9c030e934a3436c8b04b5718`
- Latest guarded provider writes: compact prompt and `atlas_output_quality_rules.md`
- Latest provider write result: passed, `2/2` writes
- Focused KB attachments: `17`, unique, manifest order preserved
- Analysis criteria: `30`, IDs and order preserved
- Built-in `end_call`: `1`
- Platform legacy system mirror: `1` (accepted, not a custom duplicate)
- Custom/server duplicate `end_call`: `0`
- Procedures: inactive
- Unrelated-tool fingerprint: exact before/after equality
- Protected collateral hash: `b837f28d031624594f3ff7405d39ce281f30b535c3a0d18f241399478afdb9a6`
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

## Credit-Capped Verification

During the original readiness decision, no simulations were run after the user requested credit restraint; existing evidence was reconciled instead of rerunning full suites. On 2026-07-14, the user explicitly authorized closing the final fingerprint gap. Exactly one existing CRM canary ran with `repeat_count: 1`; no full suite or outbound call ran.

Post-final-write CRM canary:

- Scenario: `sim_040_direct_crm_integration_existing_site`
- Provider test: `test_0101kx9ddndtfawsgcrcjg72ycce`
- Invocation: `suite_7301kxf805wbecg8mc72j28zm39r`
- Test run: `trun_7001kxf805wvfz7b2xn7xnr7espd`
- Provider: pass
- Deterministic independent validation: pass
- Independent GPT-5.5 transcript adjudication: pass
- Manual finding: the agent progressed from general complexity factors to the buyer's missing CRM inputs, then used the supplied Salesforce/action/direction details without repeating the prior sentence or reopening a CTA
- Limitation: the simulated buyer used a near-repeat complexity follow-up, not an explicit "you already said that" complaint
- Subscription character delta: `563`; post-run remaining characters: `27,611`; overage: `$0`

040 evidence:

- Full suite `suite_0601kxewmfzbe05sr3e9q37kn49d`: provider `9/10`; manual review found real multi-feature, CRM CTA, and portal-number-echo defects.
- Multi-feature focus `suite_5901kxewzh87embrd44zh5sfgb9e`: provider pass, independent pass, manual pass after repair.
- CRM focus `suite_9601kxex7wk6f5cr5em179efjm4m`: provider pass, independent pass, manual pass after repetition-safe repair.
- Portal focus `suite_7601kxey0zq2fhrbr210wcr38xhk`: provider pass, independent pass, manual pass after proof/scope repair.

036 evidence:

- Full unchanged suite `suite_4801kxex9zs0ervt7hbgb6cn6pew`: provider `9/10`; manual review separated the invalid goodbye simulation and stale pricing inputs from real CRM CTA defects.
- Final CRM focus `suite_7101kxeym4vxe87abyrc0y9m44q3`: provider evaluator failed only because it demanded the stale handoff-price and mockup-next-step behavior. Manual/current-contract review passed: no unprompted price, no mockup/email/send CTA, one whole-project price after the buyer asked, no second handoff range, and no invented quote.

The product was judged from transcripts and the active contract, not from provider pass/fail labels alone.

## Structural Verification

All local validators passed after the latest live patch:

- ELEVENLABS validators `030`, `031`, `032`, `033`, `034`, `036`, `037`, `038`, `039`, and `040`
- `scripts.test_apply_elevenlabs_040_detailed_pricing_control`: `14/14`
- `scripts.test_validate_elevenlabs_040_live_test_traces`: `67/67`
- `git diff --check`

The committed product diff does not modify `runtime/providers/elevenlabs_agents/tests/` or `runtime/providers/elevenlabs_agents/analysis/`. The 040 package remains non-uploadable (`active_upload=false`) and does not broaden the active KB attachment set.

## Actions And Errors

- Provider writes: all succeeded; no failed MCP/API action.
- Local dry-run guard initially rejected `atlas_close_and_followup_playbook.md` as an unknown target. No provider request was sent. The allowlist was then extended by fixed document ID and covered by validators.
- Final GPT-5.5 review found an exact-repeat CRM loop. The product prompt and active output-quality KB were corrected and read back live without another simulation.
- Simulations did run during this development cycle; no outbound call was placed.
- No additional broad simulation is required for this wrap-up decision. Any future run should answer a new bounded evidence question, such as the still-untested explicit repetition-complaint branch or a separately governed PSTN/ASR/latency gate.
