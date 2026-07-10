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
