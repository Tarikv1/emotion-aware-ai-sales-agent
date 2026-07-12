# Task 9 Full-Suite Product Hardening Report

## Scope

Edited only the owned product sources:

- `runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md`
- `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_price_scope_cost_drivers.md`
- `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_output_quality_rules.md`

Added this report:

- `.superpowers/sdd/task-9-full-suite-product-hardening-report.md`

No tests, criteria, validators, runners, provider settings, manifests, tools, or generated evidence were intentionally edited or staged.

## Product Changes

- Locked paid-price follow-up chains so range, scope-driver, budget, and new-versus-add-on questions stay in price mode with no mockup CTA, send offer, email ask, or sales pivot unless the buyer explicitly changes topic or asks to send the mockup.
- Locked multi-feature new-site total-cost answers to one `$4,000-$6,500` whole-project band and one main driver, with no `$900-$1,500`, alternative bands, or add-on arithmetic in that same answer.
- Locked portal, dashboard, account, database, custom API, permissions, and custom-logic price/scope chains to scoped, non-numeric answers with no standard range, unrelated package, ceiling, or mockup CTA.
- Locked care-plan follow-ups so scope questions do not unlock `$149` or `$249`; different care prices require a current-turn price/cost/fee/how-much question.
- Updated the compact prompt line exactly to `Other care prices require price/cost/fee questions.`

Prompt word count: `1900`.

## Verification Results

Fresh validator chain result:

- `python scripts\validate_prod_040_callcenteren_conditional_customer_simulation.py` - passed
- `python scripts\validate_prod_039_customer_realism_simulator_hardening.py` - passed
- `python scripts\validate_prod_038_local_demo_surface_review.py` - passed
- `python scripts\validate_prod_037_local_interactive_trace_demo_surface.py` - passed
- `python scripts\validate_prod_036_interactive_demo_readiness_review.py` - passed
- `python scripts\validate_prod_034_interactive_post_fix_review.py` - passed
- `python scripts\validate_prod_033_interactive_simulator_termination_fix.py` - passed
- `python scripts\validate_prod_032_interactive_simulation_review.py` - passed
- `python scripts\validate_prod_031_interactive_grounded_call_simulation.py` - passed
- `python scripts\validate_prod_030_grounded_demo_review.py` - passed
- Prompt word count check - `1900`
- `git diff --check` - passed; only line-ending warnings were printed

No provider, API, browser, Procedure, simulation, dashboard, or outbound-call work was performed beyond the local validators listed above.

## Self-Review

- Price-chain CTA lock: present in the prompt residue policy, pricing KB, and output quality rules. The KB includes the `$900` versus `$1,500` scope-driver example and blocks mockup invitations.
- Multi-feature whole-project lock: present in the prompt, pricing KB, and output quality rules. The first answer is constrained to `$4,000-$6,500` with one driver and no basic-site range or add-on math.
- Portal/custom-chain lock: present in the prompt, pricing KB, and output quality rules. The KB explicitly blocks numeric price, normal range, unrelated package, minimum, maximum, ceiling, and mockup CTA during the custom chain.
- Care follow-up lock: present in the prompt, pricing KB, and output quality rules. The exact compact prompt line is present, and the KB names the non-price follow-up examples that do not unlock `$149` or `$249`.
- Prompt size: verified at exactly `1900` words.
- Ownership: staged commit should include only the three product sources plus this report.

## Concerns

- Several listed validators run their local runners and rewrite tracked generated evidence while validating. To preserve the requested ownership boundary, those validator-mutated tracked generated files were restored after the successful chain and left out of the commit.
- Pre-existing dirty `research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/` files and untracked generated evidence were left untouched and uncommitted.
- The validators passed, but the brief's defects were manual-review defects not caught by the frozen suite before this patch, so the main confidence comes from direct policy diff review plus prompt word-count verification.

## Commit

Commit message: `Harden Atlas pricing chain product rules`

## Rejected Revision Remediation

The rejected revision compressed prompt text that the controller still treats as marker-bearing contract text. The prompt was restored to parent `a2eb6ab` for every line except the required care line:

- Parent: `Other care prices require cost questions.`
- Current: `Other care prices require price/cost/fee questions.`

The restored prompt is `1989` words. The earlier `1900` count above describes the rejected revision; retaining that compression would conflict with the remediation requirement to restore every other prompt line exactly to `a2eb6ab`.

Detailed full-suite hardening remains only in:

- `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_price_scope_cost_drivers.md`
- `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_output_quality_rules.md`

Fresh remediation validator results:

- `python scripts\validate_prod_040_callcenteren_conditional_customer_simulation.py` - `PROD-040 CallCenterEN conditional customer simulation validation passed.`
- `python scripts\validate_prod_039_customer_realism_simulator_hardening.py` - `PROD-039 customer realism simulator hardening validation passed.`
- `python scripts\validate_prod_038_local_demo_surface_review.py` - `PROD-038 local demo surface review validation passed.`
- `python scripts\validate_prod_037_local_interactive_trace_demo_surface.py` - `PROD-037 local interactive trace demo surface validation passed.`
- `python scripts\validate_prod_036_interactive_demo_readiness_review.py` - `PROD-036 interactive demo readiness review validation passed.`
- `python scripts\validate_prod_034_interactive_post_fix_review.py` - `PROD-034 interactive post-fix review validation passed.`
- `python scripts\validate_prod_033_interactive_simulator_termination_fix.py` - `PROD-033 interactive simulator termination fix validation passed.`
- `python scripts\validate_prod_032_interactive_simulation_review.py` - `PROD-032 interactive simulation review validation passed.`
- `python scripts\validate_prod_031_interactive_grounded_call_simulation.py` - `PROD-031 interactive grounded call simulation validation passed.`
- `python scripts\validate_prod_030_grounded_demo_review.py` - `PROD-030 grounded demo review validation passed.`
- Full chain exit: `0`.

The validators rewrote five tracked `PROD-*` generated artifacts while running. Those runner side effects were restored to `HEAD`; no validator, test, runner, criterion, or evidence change is included in this remediation.

Post-restoration `git diff --check` exited `0`; only working-copy LF-to-CRLF warnings were printed.
