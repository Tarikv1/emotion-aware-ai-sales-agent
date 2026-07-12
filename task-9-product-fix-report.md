# Task 9 Product Fix Report

## Status

Implemented the product fix revealed by canary suite `suite_8501kx9yxjmwfg4racwzgy19k1zd`.

No provider calls were made. The existing frozen 040 scenarios, success criteria, models, turns, and dynamic variables were not edited.

## Product Fix

- Added a global Atlas price-source lock to the prompt: use only approved Atlas package, add-on, and care values from Campaign Facts or the active pricing KB.
- Added the tested runtime mapping:
  - 3-5 page new site -> `{{website_basic_site_range}}`
  - compatible existing-site appointment request -> `$100-$250`
  - direct CRM/API add-on -> `$1,000-$2,500+`
  - new site plus standard integration -> `{{website_integration_heavy_range}}`
  - care -> `$79/$149/$249` only after ongoing-cost intent
  - portal/dashboard -> scope without a number
- Added output rules banning general-market, industry-average, and unsupported invented prices.
- Added output rule to avoid repeating the mockup CTA during live price follow-ups unless the buyer newly accepts the mockup.

## Patcher Fix

- Added guarded `--target-kb-doc NAME` subset support.
- Default target remains all 3 known KB docs.
- Empty, duplicate, and unknown target names fail closed.
- Subset plans preserve the exact prompt patch, dynamic-variable merge, protected state checks, and source evidence.
- Dry-run subset proof for `atlas_output_quality_rules.md` produced exactly 2 planned writes:
  - `update_kb_file::atlas_output_quality_rules.md`
  - `patch_agent::prompt_dynamic_variables`

## Validation

- Red tests observed before implementation:
  - 040 validator failed on missing price-source lock markers.
  - New patcher subset tests failed on missing subset APIs.
- Full offline validator chain passed: 040, 039, 038, 037, 036, 035, 034, 033, 032, 031, 030.
- 040 prompt word count: 1,895 validator words.
- 040 trace self-test passed.
- 040 runner tests passed: 32 tests.
- New patcher subset tests passed: 2 tests.
- `py_compile` passed for modified 040 scripts and related 040 runner/capture/trace test utilities.
- `git diff --check` passed.

## Concerns

- Historical untracked 040 live evidence artifacts remain in the worktree. They were not modified because this task forbids provider calls and did not ask to rewrite evidence.
- The 040 validator now treats recorded live evidence as historical when its embedded source commit differs from current `HEAD`, while still validating current offline request/source generation.
