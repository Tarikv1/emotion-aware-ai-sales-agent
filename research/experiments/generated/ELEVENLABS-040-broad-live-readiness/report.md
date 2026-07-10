# ELEVENLABS-040 Broad Live Readiness Report

## Verdict

Broad live readiness is blocked and is not claimed.

The live Atlas configuration is structurally intact, but the unchanged ELEVENLABS-036 suite is not behaviorally stable. Prompt and active-KB hardening improved several targeted lanes, while repeated full and targeted runs continued to expose genuine state-routing failures. ElevenLabs provider labels were checked against raw traces with `scripts/validate_elevenlabs_036_live_test_traces.py`; provider passes were not treated as authoritative.

## Live State

- Agent: `agent_7801kt0g32zxf4f8x5zkykj7syty` (`web design`)
- Focused KB attachments: 17, unique and in manifest order
- Built-in `end_call`: 1
- Platform legacy system mirror: 1
- Custom/server duplicate `end_call`: 0
- Analysis criteria: 30
- Procedures: inactive
- Unrelated tools: unchanged
- Voice, LLM, first message, dynamic variables, phone configuration, and protected settings: preserved by guarded patch readbacks
- Outbound calls: none

## Passing Evidence

- Repo validators 030 through 039 passed after the final repo changes.
- Patch-utility safety validation passed.
- `git diff --check` passed.
- ELEVENLABS-039 invocation `suite_2601kx71hta1f5bb5605t6q5kc8j` passed provider and independent trace validation 4/4 after delivery-timing hardening.
- Targeted CRM, email-plus, visual, and scheduling lanes each produced three-pass provider runs during iteration.
- No dashboard test definition, success criterion, or Analysis criterion was changed to obtain a pass.

## Blocking Evidence

The last full ELEVENLABS-036 invocation before the final safety-boundary restoration, `suite_3101kx73txvzek1rffz8ayd2t57g`, had provider failures in scheduling, CRM, CTA fatigue, and legacy goodbye. Independent grading also found non-provider failures in email confirmation, future-price handling, and dashboard scope behavior. Only the same-turn email-confirmation-plus-goodbye conflict is eligible for the documented ELEVENLABS-039 precedence.

The next targeted CRM invocation `suite_8701kx740gd0etfvcv0gabqzg24y` failed two of three repeats:

- one run disclosed price before the buyer asked cost;
- one run omitted the required natural mockup next step after capability and cost were resolved.

These are product failures, not evaluator-only disagreements.

The final prompt fingerprint has a structural readback but no subsequent clean full-suite evidence. That missing final-fingerprint evaluation independently blocks a readiness claim.

## Architecture Finding

Multiple increasingly explicit prompt and KB locks did not stabilize the same capability-before-price transition. Under the current constraints, further wording changes would be uncontrolled prompt tuning. A credible next step requires permission to change a stronger control surface, such as the live LLM configuration or Procedures, followed by a fresh fixed-fingerprint evaluation. Both are currently prohibited.

## Evidence

- `readiness_contract.md`
- `final_live_readback_summary.json`
- `live_product_kb_patch_price-scope_result.json`
- `live_product_kb_patch_output-quality_result.json`
- `../ELEVENLABS-036-natural-sales-scenarios/readiness_frozen2_full_1_capture.json`
- `../ELEVENLABS-036-natural-sales-scenarios/readiness_frozen2_full_1_independent.json`
- `../ELEVENLABS-036-natural-sales-scenarios/readiness_candidate_crm_repeat3_capture.json`
- `../ELEVENLABS-036-natural-sales-scenarios/readiness_blocked_final_readback_2_run_plan.json`
- `../ELEVENLABS-039-end-call-edge-case-hardening/live_test_invocation_readiness_repeat_3_sanitized.json`
- `../ELEVENLABS-039-end-call-edge-case-hardening/independent_trace_validation_readiness_repeat_3.json`

No outbound calls were placed. Simulations were run only after the user explicitly authorized them.
