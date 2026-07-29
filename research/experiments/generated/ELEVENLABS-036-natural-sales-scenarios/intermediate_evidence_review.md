# ELEVENLABS-036 Intermediate Evidence Review

## Verdict

Preserve the recovered files as historical intermediate evidence. Do not treat
them as a new readiness result, a replacement for the final GPT-5.5 closeout,
or authoritative current-validator output.

The packet records failed, inconclusive, partial, and superseded iterations.
Keeping it avoids success-only evidence selection, but its limitations must
travel with it.

## Provenance

- Source checkout:
  `D:\Codex\active\emotion-aware-ai-sales-agent`
- Source checkout HEAD:
  `f90e0bbc36097daaf41e3d4d67e3ae80feabef7e`
- Source state: `142` untracked JSON files under this checkpoint folder and
  no tracked-file modifications.
- Review base:
  `5d564d5ce2a6d6293afb3d58662dc0c16ce195f6`
- Current validator blob:
  `2f327214f482fa8c3384e3288dbe3e3d6e3e93f0`
- Current test-definition blob:
  `6e1e075350dcc7dd17e238f95aea33c4a8f8da54`
- Review time: `2026-07-29T22:35:09Z`

The recovered JSON fields were not edited. Git's configured text normalization
applies when the files are added to the repository.

## Inventory

| Artifact type | Count |
| --- | ---: |
| LLM patch plan/request/result and pre/post snapshots | 5 |
| Capture | 30 |
| Replacement capture (`capture_v2`) | 1 |
| Stored independent result | 18 |
| Run plan | 30 |
| Run request | 29 |
| Run result | 29 |
| Total | 142 |

The files occupy `2,589,325` bytes in the source checkout before Git text
normalization. They represent `32` named families: one LLM patch family,
`30` capture-bearing run families, and one plan-only blocked readback family.

## Integrity Review

- All `142/142` files parse as JSON.
- All `31/31` stored capture payload hashes match the canonical sanitized
  payload.
- All `29` available plan/request pairs match after removing only their capture
  timestamp.
- All `29` available plan/result and result/capture lineages agree on selected
  counts, expected counts where present, invocation IDs, observed run counts,
  and provider statuses.
- All `18` capture/stored-independent pairs agree on invocation ID.
- No lineage-consistency violation was found.
- Every artifact that records `outbound_calls_made` records `false`: `91`
  artifacts report the field and none reports `true`.
- No API-key, bearer-token, JWT, private-key, AWS-key, GitHub-token, password,
  authorization, or secret field/pattern was found.
- The packet contains three synthetic email addresses already defined in the
  tracked ELEVENLABS-036 tests, prompt, or validator. No phone-like value or IP
  address was found.
- The LLM patch pre/post snapshots differ only in the requested LLM fields,
  expected provider version/update metadata, capture time/phase, and the
  LLM-sensitive preflight hash. The LLM-independent protected-state hash is
  unchanged.

Provider run results are mixed: `21` completed and `8` failed. A provider
`completed` result is not an independent behavioral pass.

## Current-Contract Revalidation

The current validator was run read-only against one preferred capture per
lineage, choosing `llm_gpt54_behavior1_full1_capture_v2.json` over its earlier
capture of the same invocation.

| Current independent status | Lineages |
| --- | ---: |
| Pass | 6 |
| Inconclusive | 2 |
| Fail | 22 |

Current-contract pass families:

- `llm_gpt54_behavior1_crm_repeat3`
- `llm_gpt55_behavior3_full1`
- `readiness_final3_email_plus_repeat3`
- `readiness_final6_crm_repeat3`
- `readiness_final6_scheduling_repeat3`
- `readiness_final6_visual_repeat3`

Current-contract inconclusive families:

- `llm_gpt54_behavior2_crm_repeat3`
- `readiness_final_crm_repeat3`

The recovered packet contains `18` stored independent-result files. Only `4`
are exactly reproducible as the same JSON object under the current validator.
Ten retain the same top-level status but differ in detail. Four change
top-level status under the current contract:

| Family | Stored status | Current-contract status |
| --- | --- | --- |
| `llm_gpt54_behavior1_crm_repeat3` | fail | pass |
| `llm_gpt55_behavior3_full1` | fail | pass |
| `readiness_final3_email_plus_repeat3` | fail | pass |
| `readiness_final_crm_repeat3` | fail | inconclusive |

Twelve capture-bearing families have no stored independent-result file.
Historical validator commit/version metadata is absent from the recovered
outputs, and the validator changed later in commit `535d357`. Therefore the
stored independent files are historical observations, not current
authoritative conclusions. Current revalidation is also a present-contract
view, not a retroactive claim that the historical validator was wrong.

Of the `31` captures, `29` exactly match the current tracked scenario and
success-condition text. These two do not:

- `llm_gpt54_behavior1_full1_capture.json` has four scenario/criterion
  mismatches; its later `capture_v2` for the same invocation matches the
  current definitions and is the preferred capture.
- `llm_gpt54mini_full1_capture.json` has four scenario/criterion mismatches and
  has no corrected replacement capture.

## Evidence Decision

The recovered artifacts are admitted only as a historical audit trail for the
iteration path. They do not alter the later tracked result in `report.md`:
final GPT-5.5 invocation `suite_2901kx7a8pkjfyw95retr4j4g5eg` remains the
superseding 10/10 provider and 10/10 independent deterministic closeout for the
covered ELEVENLABS-036 contract.

No product/runtime file, provider configuration, simulation, test definition,
Analysis criterion, outbound-call path, production state, or readiness claim
was changed during this review.
