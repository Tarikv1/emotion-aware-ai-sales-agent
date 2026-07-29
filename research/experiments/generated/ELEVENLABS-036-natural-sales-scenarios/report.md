# ELEVENLABS-036 Natural Sales Scenarios Test Creation

## Outcome

Created the `ELEVENLABS-036-natural-sales-scenarios` simulation test folder in ElevenLabs and created the 10 repo-side simulation tests from `runtime/providers/elevenlabs_agents/tests/web_design_natural_sales_scenarios_tests.json`.

- Folder ID: `tfld_9401ktwzqah2eknswj3p3z16acwc`
- Folder created: `true`
- Tests moved into folder: `10`
- Live provider calls made: `true`
- Simulations run: `false`
- Alpha routing/procedure fields used: `false`
- Atlas prompt changed: `false`
- Atlas KB changed: `false`
- Active upload manifest changed: `false`

## Created Tests

| Repo test ID | ElevenLabs test ID |
| --- | --- |
| `sim_036_email_confirmation_spoken_email_two_step` | `test_4201ktwzq7wpf589w4ypqbwwv6xk` |
| `sim_036_email_plus_free_question_confirmation` | `test_1301ktwzq879ex099m903r4f0gvt` |
| `sim_036_future_price_ballpark_no_overpricing` | `test_7101ktwzq8e5edm9bkmwe83tvcsw` |
| `sim_036_scheduling_simple_request_vs_live_integration` | `test_4601ktwzq8nyfcatm8a6mn58y7x6` |
| `sim_036_crm_payment_capability_before_price` | `test_4601ktwzq8xnfpbtry5qsepeprh3` |
| `sim_036_custom_dashboard_scoped_separately` | `test_9401ktwzq968e3bvmytqxg4exxc0` |
| `sim_036_free_mockup_visual_not_working_site` | `test_3301ktwzq9cnfzsa5dfjd9q61gq5` |
| `sim_036_next_step_questions_no_cta_fatigue` | `test_2001ktwzq9kbf92vdfttrgkvnr1x` |
| `sim_036_guarantee_required_clean_disqualify` | `test_7401ktwzq9txfkhs6ytstggj8k9y` |
| `sim_036_goodbye_take_care_no_loop` | `test_1901ktwzqa28f0mbk4rrt106d74d` |

## Evidence Files

- `dry_run_create_tests_plan.json`: preflight dry-run plan generated without provider calls.
- `dry_run_create_tests_requests.json`: preflight request payloads generated without provider calls.
- `live_create_tests_plan.json`: live creation response, including create-test calls and folder move result.
- `live_create_tests_requests.json`: exact request payloads generated from the repo test JSON.
- `live_create_tests_result.json`: compact provider result summary.
- `report.md`: this report.

## Boundaries

This was a test-definition creation run only. No simulations were started, no prompt or KB files were uploaded, no active Atlas upload manifest was changed, and no production-readiness claim is made.

## 2026-07-10 Product Hardening Run

The existing 10 tests were run inside ElevenLabs against the live Atlas agent. No outbound calls were placed. The test JSON, success criteria, models, turn limits, provider IDs, and folder placement were restored to and verified against their original repo definitions before the final runs.

Product-side changes only:

- compact prompt hardening for email confirmation, scheduling range framing, CRM capability-before-price, custom dashboard scoping, guarantee-only disqualification, CTA fatigue, and delivery-timing deduplication;
- built-in `end_call` policy hardening for guarantee-only conditions, confirmation-only turns, and timing deduplication;
- no KB attachment, Analysis, voice, LLM, first-message, dynamic-variable, phone, Procedure, or unrelated-tool changes.

Final unchanged full invocation: `suite_9901kx6ybykhf7kab8qezc6z2s24`.

- ElevenLabs result: 9 passed, 1 failed.
- Independently clean: email two-step, email plus process concern, future price, scheduling, CRM/payment, custom dashboard, visual-only mockup, CTA fatigue, and guarantee-only disqualification.
- Remaining label: `sim_036_goodbye_take_care_no_loop`.
- Conflict: its 036 criterion accepts only `Take care.` after the goodbye, while active ELEVENLABS-039 requires by-end-of-day timing when email confirmation and goodbye occur in the same buyer turn. The final trace followed 039 exactly. The 036 test was not edited and the product was not regressed to force a green label.

Key evidence:

- `live_test_invocation_unchanged_final_full_4_sanitized.json`
- `unchanged_final_full_4_run_plan.json`
- `unchanged_final_full_4_run_result.json`
- `live_test_invocation_unchanged_crm_capability_challenge_sanitized.json`
- `live_test_invocation_unchanged_scheduling_whole_site_range_sanitized.json`
- `live_test_invocation_unchanged_cta_priority_conflict_removed_sanitized.json`
- `live_test_invocation_unchanged_guarantee_original_wording_sanitized.json`
- `live_prompt_hardening_post_patch.json`
- `live_guarantee_tool_post_patch.json`
- `independent_review_final.json`

No production-readiness claim is made.

## 2026-07-11 Final GPT-5.5 Product Hardening Result

This section supersedes the earlier 9/10 blocked result above. The live Atlas product was changed; the ElevenLabs test definitions and Analysis criteria were not changed.

Final live configuration:

- Agent: `agent_7801kt0g32zxf4f8x5zkykj7syty` (`web design`)
- LLM: `gpt-5.5`
- Temperature: `0.1`
- Reasoning effort: `none`
- Provider-normalized thinking budget: `null`
- Prompt: exact repo match, 1,900 words
- Active KB: 17 unique documents in manifest order
- Analysis: 30 criteria in the original ID order
- Tools: one built-in `end_call`, zero custom/server duplicates, unrelated fingerprint preserved
- Procedures: inactive

Product changes:

- clarified CRM whole-project versus connection-only pricing;
- constrained the free visual to one static homepage concept, never a multi-screen flow;
- blocked calls to action while capability, scope, proof, or price follow-ups remain unresolved;
- separated simple appointment requests from live scheduling before discussing price;
- prohibited invented numeric portal minimums before scope;
- retained the 039 atomic terminal behavior for hard stops, timing deduplication, and gatekeeper outcomes.

Final unchanged 036 invocation: `suite_2901kx7a8pkjfyw95retr4j4g5eg`.

- ElevenLabs evaluator: 10/10 passed.
- Independent deterministic trace evaluation: 10/10 passed, complete coverage, no inconclusives.
- Final 039 regression invocation: `suite_1701kx7aeyhce7rsnpeajrnh8h2d`.
- 039 ElevenLabs evaluator: 4/4 passed.
- 039 independent deterministic trace evaluation: 4/4 passed.

Additional repeated stability evidence:

- Scheduling comparison on GPT-5.4: `suite_5001kx79b4hpe24rvmca9vh7zsh3`, 3/3 provider and independent pass.
- Visual-only scope on retained GPT-5.5: `suite_8001kx79rrmrexstrs3fvqn0qs7k`, 3/3 provider and independent pass.
- CRM plus dashboard on retained GPT-5.5: `suite_3001kx7a2q71e31vyew99gpgb8cd`, 6/6 provider and independent pass.

Final verification:

- Both independent trace validators exited 0.
- Repo validators 039, 038, 037, 036, 034, 033, 032, 031, and 030 exited 0.
- `git diff --check` exited 0.
- No outbound calls were placed.
- Simulations were run only inside ElevenLabs after explicit user authorization.

This supports broad simulation-backed live configuration readiness for the covered 036 and 039 behaviors. It does not prove PSTN audio, latency, interruption, ASR, or real-buyer performance because no outbound call was placed.

Final evidence:

- `llm_gpt55_behavior4_full1_capture.json`
- `llm_gpt55_behavior4_full1_independent.json`
- `gpt55_final_readback_run_plan.json`
- `gpt55_final_live_readback.json`
- `../ELEVENLABS-039-end-call-edge-case-hardening/gpt55_regression_capture.json`
- `../ELEVENLABS-039-end-call-edge-case-hardening/gpt55_regression_independent.json`

Failed non-provider action:

- The delegated GPT-5.4 Mini reviewer could not initialize because the local WASM agent package `@ruvector/rvagent-wasm` was missing. The orchestration path was abandoned and all conclusions were independently verified in the main task.

## 2026-07-29 Intermediate Evidence Recovery

A later repository audit found `142` untracked JSON artifacts from the
pre-closeout LLM and broad-readiness iteration path in a stale local `main`
checkout. They are now preserved as historical intermediate evidence to avoid
success-only evidence selection.

The packet is mixed and non-authoritative: it includes failed and incomplete
lineages, historical independent outputs that do not fully reproduce under the
current validator, and two captures that do not exactly match the current test
definition text. It does not change or weaken the final GPT-5.5 closeout above.

Review evidence:

- `intermediate_evidence_review.md`
- `intermediate_evidence_review.json`

No provider call, provider write, simulation, outbound call, runtime change,
test-definition change, Analysis-criterion change, or new readiness claim was
made during recovery.
