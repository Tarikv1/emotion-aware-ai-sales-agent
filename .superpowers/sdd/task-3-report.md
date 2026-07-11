STATUS: DONE WITH CONCERNS

COMMIT:
- message: Gate Atlas paid pricing on buyer intent

FILES:
- runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md

WORD COUNT:
- validator-style before: 1900
- validator-style after: 1866
- raw whitespace count before: 1977
- raw whitespace count after: 1941

COMMANDS AND RESULTS:
- `npm run cli -- memory refresh --project emotion-aware-ai-sales-agent`
  - pass; local bootstrap refreshed project memory.
- `python -c "import scripts.validate_elevenlabs_040_detailed_pricing_control as v; v.validate_prompt_policy(); print('prompt policy: pass')"`
  - before edit: fail; missing 040 prompt markers.
  - after marker edit but before compression: fail; `compact prompt exceeds 1,900 words`.
  - final after compression: pass; `prompt policy: pass`.
- `python scripts/validate_elevenlabs_040_detailed_pricing_control.py`
  - fail; missing file `runtime/providers/elevenlabs_agents/tests/web_design_detailed_pricing_control_tests.json`.
- `python scripts/validate_elevenlabs_039_end_call_edge_case_hardening.py`
  - pass; prompt word count 1866.
- `python scripts/validate_elevenlabs_038_end_call_terminal_control.py`
  - pass; prompt word count 1866.
- `python scripts/validate_elevenlabs_037_confident_capability_control.py`
  - fail; missing existing cross-file markers including `Capability question examples`, `Scope question examples`, `Price question examples`, `Proof/experience question examples`, `Process-risk question examples`, and `"What's the catch?" is a process-risk question, not automatically a request for the full pricing menu.`
- `python scripts/validate_elevenlabs_036_natural_sales_scenarios_tests.py`
  - pass; 10 dry-run simulation tests validated, no live provider calls.
- `git diff --check`
  - pass with Git line-ending warning only; no diff-check errors.

SELF-REVIEW:
- Price intent gate: yes. Paid pricing now stays locked until explicit buyer price intent and blocks capability/mockup/process-risk leakage.
- One-range rule: yes. Prompt now says quote one relevant range and never read or stack the menu into a final quote.
- New-vs-existing classification: yes. Prompt now routes new work to a whole-project band, existing compatible sites to one add-on range, and asks when unclear.
- Custom scope: yes. Portals, dashboards, APIs, accounts, databases, complex payments, inventory sync, marketplaces, and custom logic require scoped pricing without a fixed price or ceiling.
- No stacking: yes. Prompt keeps the one-or-two add-on discussion cap and moves three or more additions back to a whole-project band.
- Word count: yes by validator logic; prompt is 1866 words after edit.

CONCERNS:
- The full 040 validator cannot pass in this worktree because the expected 040 tests file is absent, and the task explicitly forbids editing tests.
- 037 currently fails on missing capability/process-risk marker text outside this task's prompt-only scope; I did not modify those docs.
