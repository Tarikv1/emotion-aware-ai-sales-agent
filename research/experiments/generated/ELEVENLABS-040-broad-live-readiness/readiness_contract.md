# Atlas Broad Live Readiness Contract

## Scope

This contract governs readiness evidence for Atlas agent `agent_7801kt0g32zxf4f8x5zkykj7syty` without outbound calls, dashboard-test edits, Procedure enablement, or KB broadening.

## Contract Precedence

When two unchanged checkpoint tests specify different behavior for the same buyer turn, the newer and more specific checkpoint owns that overlap.

ELEVENLABS-039 therefore supersedes ELEVENLABS-036 only for a buyer turn that contains both explicit email confirmation and goodbye:

- confirmation plus goodbye in the same buyer turn: the atomic `end_call` message includes by-end-of-day timing and `Take care.`;
- delivery timing stated in an earlier agent turn, followed by a later goodbye or terminal thanks: the atomic `end_call` message is exactly `Take care.`;
- confirmation without goodbye: state by-end-of-day timing only, with no farewell or `end_call`.

The unchanged `sim_036_goodbye_take_care_no_loop` evaluator may label the first case as failed because its older criterion accepts only `Take care.`. That provider label is not waived silently: every such trace must independently prove exact compliance with the 039 rule. The 036 test definition and success criterion remain unchanged.

## Required Gates

Broad live readiness requires all of the following on one final prompt/tool fingerprint:

The final fingerprint artifact must bind every invocation below to one readback and record the compact prompt SHA-256, `end_call` description SHA-256, full tool summary, ordered KB IDs, Analysis criterion IDs/count/content SHA-256, unrelated-tool fingerprint, protected-settings fingerprint, and invocation IDs.

1. Repo validators 030 through 039 and `git diff --check` pass.
2. All 10 live 036 test definitions exactly match the repo.
3. All four live 039 test definitions exactly match the repo.
4. Two unchanged full 036 invocations show no failure except `sim_036_goodbye_take_care_no_loop` classified as `allowed_legacy_contract_conflict`, and that classification is allowed only when its saved trace shows same-turn explicit email confirmation plus goodbye and exact 039 tool reason/message. Any other failure, or that test failing for another reason, blocks readiness.
5. Two unchanged full 039 invocations pass provider and independent trace validation 4/4.
6. Three-repeat targeted stability runs pass for email-plus-process concern, visual-only mockup, scheduling scope, same-turn confirmation plus goodbye, prior delivery timing then goodbye, confirmation without goodbye, and forced post-goodbye/no-loop behavior.
7. Every saved trace receives independent review; provider labels are evidence, not authority.
8. The live readback has exactly 17 focused KB attachments in manifest order, one built-in `end_call`, no custom/server duplicate, 30 Analysis criteria, inactive Procedures, and an unchanged unrelated-tool fingerprint.
9. Voice, LLM, first message, dynamic variables, phone configuration, and unrelated settings are unchanged.
10. No outbound calls are placed and no broad-readiness claim is made while a product failure remains. `allowed_legacy_contract_conflict` is a versioned evaluator conflict only after the independent trace proves the exact newer behavior; every other behavioral failure is a product failure.

## Claim Rule

Broad live readiness may be claimed only when every gate above is evidenced. A conflicting legacy provider label is acceptable only when the saved trace passes the explicit newer contract and no product behavior is being excused.
