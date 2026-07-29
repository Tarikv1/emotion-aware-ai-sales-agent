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

## Legacy Marker And Portal P1 Remediation

Restored these legacy output-quality markers as separate bullets without replacing the stronger adjacent rules:

- `In that lane, answer only the asked price issue: no mockup mention, mockup CTA, email ask, or renewed sales transition unless the buyer newly accepts or requests the mockup.`
- `Do not quote a fixed price or ceiling for portals, dashboards, APIs, accounts, databases, or custom business logic.`

The output rules now define `newly accepts or requests the mockup` as an explicit topic change to the mockup or an explicit send request. The stronger price-chain, multi-feature, care, and portal-chain rules remain present as additional bullets.

The compact parent-login response now starts exactly `A working parent login is custom. I can't give a real number...` and no longer compares portal work with the normal website range. The same prompt bullet prohibits standard-site ranges, package context, and mockup CTA during the portal price/scope chain.

Prompt count using the task validator's `len(re.findall(r"\b\S+\b", text))` method: `1895`. Earlier report counts based on a whitespace split were not the frozen validator's count and are superseded by this result.

Fresh requested validator results:

- `python scripts\validate_prod_040_callcenteren_conditional_customer_simulation.py` - exit `0`; `PROD-040 CallCenterEN conditional customer simulation validation passed.`
- `python scripts\validate_prod_039_customer_realism_simulator_hardening.py` - exit `0`; `PROD-039 customer realism simulator hardening validation passed.`
- `python scripts\validate_prod_038_local_demo_surface_review.py` - exit `0`; `PROD-038 local demo surface review validation passed.`
- `python scripts\validate_prod_037_local_interactive_trace_demo_surface.py` - exit `0`; `PROD-037 local interactive trace demo surface validation passed.`
- `python scripts\validate_prod_036_interactive_demo_readiness_review.py` - exit `0`; `PROD-036 interactive demo readiness review validation passed.`
- `python scripts\validate_prod_034_interactive_post_fix_review.py` - exit `0`; `PROD-034 interactive post-fix review validation passed.`
- `python scripts\validate_prod_033_interactive_simulator_termination_fix.py` - exit `0`; `PROD-033 interactive simulator termination fix validation passed.`
- `python scripts\validate_prod_032_interactive_simulation_review.py` - exit `0`; `PROD-032 interactive simulation review validation passed.`
- `python scripts\validate_prod_031_interactive_grounded_call_simulation.py` - exit `0`; `PROD-031 interactive grounded call simulation validation passed.`
- `python scripts\validate_prod_030_grounded_demo_review.py` - exit `0`; `PROD-030 grounded demo review validation passed.`
- Full requested chain exit: `0`.
- Pre-report `git diff --check` exit: `0`; only LF-to-CRLF working-copy warnings were printed.

An additional pre-commit run of `python scripts\validate_elevenlabs_040_detailed_pricing_control.py` passed its source marker and word-count stage, then exited `1` at its intentional clean-`HEAD` guard with `repo source files differ semantically from HEAD; refusing provider evidence`. It must be rerun after the source commit and is not recorded as passed here.

The requested chain rewrote six tracked `PROD-*` artifacts. Those runner side effects were restored to `HEAD`; no test, validator, runner, evidence, or provider file is included in this remediation.

After committing the source files, `python scripts\validate_elevenlabs_040_detailed_pricing_control.py` exited `0` with status `pass`, prompt word count `1895`, test count `10`, `active_manifest_changed: false`, and `procedures_changed: false`.

## Multi-Feature Same-Turn Price Gate Follow-Up

Live multi canary `suite_0001kxbns5v1f7yaj5cy1ffr5ttc` showed premature price disclosure after the buyer asked `What's the integrated option? I also need CRM, payments, service-area pages, and a blog.` The total-cost question arrived only on the next buyer turn.

The pricing and output-quality KBs now require both conditions in the current buyer turn before the three-or-more-feature whole-project price lock can disclose a price:

- a request for three or more functional or content features; and
- an explicit total price, cost, fee, how-much, range, ballpark, or budget ask.

A feature list, `What's the integrated option?`, `I also need ...`, capability question, or scope question alone now requires a simple-versus-integrated/custom explanation without dollars. When a later buyer turn explicitly asks total cost for the already-described scope, the answer is limited to the `$4,000-$6,500` whole-project band and one main driver, with no `$900-$1,500`, alternative bands, or add-on arithmetic.

The compact prompt was not edited; `git diff --exit-code HEAD -- runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md` exited `0` before validation.

Fresh requested validator results:

- `python scripts\validate_prod_040_callcenteren_conditional_customer_simulation.py` - exit `0`; `PROD-040 CallCenterEN conditional customer simulation validation passed.`
- `python scripts\validate_prod_039_customer_realism_simulator_hardening.py` - exit `0`; `PROD-039 customer realism simulator hardening validation passed.`
- `python scripts\validate_prod_038_local_demo_surface_review.py` - exit `0`; `PROD-038 local demo surface review validation passed.`
- `python scripts\validate_prod_037_local_interactive_trace_demo_surface.py` - exit `0`; `PROD-037 local interactive trace demo surface validation passed.`
- `python scripts\validate_prod_036_interactive_demo_readiness_review.py` - exit `0`; `PROD-036 interactive demo readiness review validation passed.`
- `python scripts\validate_prod_034_interactive_post_fix_review.py` - exit `0`; `PROD-034 interactive post-fix review validation passed.`
- `python scripts\validate_prod_033_interactive_simulator_termination_fix.py` - exit `0`; `PROD-033 interactive simulator termination fix validation passed.`
- `python scripts\validate_prod_032_interactive_simulation_review.py` - exit `0`; `PROD-032 interactive simulation review validation passed.`
- `python scripts\validate_prod_031_interactive_grounded_call_simulation.py` - exit `0`; `PROD-031 interactive grounded call simulation validation passed.`
- `python scripts\validate_prod_030_grounded_demo_review.py` - exit `0`; `PROD-030 grounded demo review validation passed.`
- Full requested chain exit: `0`.
- Pre-report `git diff --check` exit: `0`; only LF-to-CRLF working-copy warnings were printed.

The validators rewrote six tracked `PROD-*` artifacts. Those runner side effects were restored to `HEAD`; no prompt, test, validator, runner, evidence, provider, manifest, or tool file is included in this follow-up.

## Multi-Feature Whole-Project Lane Persistence Follow-Up

Live evidence `suite_1301kxbp8cmxe9dsdsejk45pp2kn` showed that, after correctly quoting the `$4,000-$6,500` new-site whole-project band, a later CRM and service-area-page question caused an incorrect switch to the `$1,000-$2,500+` direct CRM add-on range.

The pricing and output-quality KBs now keep later feature or scope questions about that same new-site project in the whole-project lane after the whole-project band has been quoted. They explicitly prohibit switching to or mentioning existing-site CRM/API, appointment-request, request-form, or per-page add-on ranges for that project.

A newly added CRM or service-area-page requirement is treated as a whole-project scope driver. Emma may explain that it moves or requires scope; a custom API receives no number. Individual add-on ranges remain available only for clearly separate compatible existing-site additions. The explicit changed-scope exception for a buyer who narrows the project to a simple appointment-request form plus an external or embedded payment link remains unchanged.

The compact prompt was not edited; the source-contract check and `git diff --exit-code HEAD -- runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md` both exited `0` before validation.

Fresh requested validator results:

- `python scripts\validate_prod_040_callcenteren_conditional_customer_simulation.py` - exit `0`; `PROD-040 CallCenterEN conditional customer simulation validation passed.`
- `python scripts\validate_prod_039_customer_realism_simulator_hardening.py` - exit `0`; `PROD-039 customer realism simulator hardening validation passed.`
- `python scripts\validate_prod_038_local_demo_surface_review.py` - exit `0`; `PROD-038 local demo surface review validation passed.`
- `python scripts\validate_prod_037_local_interactive_trace_demo_surface.py` - exit `0`; `PROD-037 local interactive trace demo surface validation passed.`
- `python scripts\validate_prod_036_interactive_demo_readiness_review.py` - exit `0`; `PROD-036 interactive demo readiness review validation passed.`
- `python scripts\validate_prod_034_interactive_post_fix_review.py` - exit `0`; `PROD-034 interactive post-fix review validation passed.`
- `python scripts\validate_prod_033_interactive_simulator_termination_fix.py` - exit `0`; `PROD-033 interactive simulator termination fix validation passed.`
- `python scripts\validate_prod_032_interactive_simulation_review.py` - exit `0`; `PROD-032 interactive simulation review validation passed.`
- `python scripts\validate_prod_031_interactive_grounded_call_simulation.py` - exit `0`; `PROD-031 interactive grounded call simulation validation passed.`
- `python scripts\validate_prod_030_grounded_demo_review.py` - exit `0`; `PROD-030 grounded demo review validation passed.`
- Full requested chain exit: `0`.
- Pre-report `git diff --check` exit: `0`; only LF-to-CRLF working-copy warnings were printed.

The validators rewrote five tracked `PROD-*` artifacts. Those runner side effects were restored to `HEAD`; no prompt, test, validator, runner, evidence, provider, manifest, or tool file is included in this follow-up.
