# Task 9 Legacy Evidence Fixture Report

## Scope

- Worktree: `D:\Codex\active\emotion-aware-ai-sales-agent\.worktrees\atlas-detailed-pricing-control`
- Owned files:
  - `scripts/test_validate_elevenlabs_040_evidence.py`
  - `.superpowers/sdd/task-9-legacy-evidence-fixture-report.md`

## Root Cause

Seven legacy-evidence tests were still reading the mutable live 040 evidence bundle. After the plan-only evidence refresh replaced that bundle with current `git_blob` evidence, those tests stopped exercising the historical allowlisted artifact and started failing for unrelated current-state reasons.

## Fixture Design

- Added a pinned legacy fixture for source commit `1e8af8510b072d5fe08501af7229abac5208bdf8`.
- Pinned the exact legacy tuples in test-owned constants instead of deriving them from the production allowlist:
  - `update_kb_file::atlas_price_scope_cost_drivers.md`
    - path: `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_price_scope_cost_drivers.md`
    - SHA-256: `df6f06af92ad57ca5679b848c909f56cc34905fc78fa3a3fd888861913cbfd54`
    - length: `14394`
    - mode: `legacy_git_blob_old_fields`
  - `update_kb_file::atlas_output_quality_rules.md`
    - path: `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_output_quality_rules.md`
    - SHA-256: `5f6f68f5ec26640a55658d374c5729bfdc23d10745a4c194ed245d4aa486425e`
    - length: `19064`
    - mode: `legacy_worktree_line_endings`
- Built the synthetic evidence bundle for the care-follow-up three-write subset only.
- Replaced legacy test dependence on `copy_current_live_evidence()` and direct `validator.LIVE_EVIDENCE_DIR` reads with a temp evidence dir plus a temp historical worktree.
- Reconstructed the legacy output worktree bytes deterministically from the historical Git blob plus a pinned LF-only line-number map. The helper asserts the exact pinned hash/length before validation and asserts CRLF normalization returns the historical blob.
- Added a legacy validator shim that:
  - emulates `rev-parse HEAD` as the pinned source commit,
  - keeps Git blob reads on real repository history,
  - redirects `validator.ROOT / source_path` reads to the temp historical worktree.

## Legacy Test Coverage

- Positive coverage:
  - legacy line-ending fixture passes and reports `legacy_worktree_line_endings`
  - legacy price old-field fixture passes and remains outside the line-ending subset
- Tamper coverage keeps the intended failure reasons:
  - allowlist mismatch on upload length tamper
  - allowlist mismatch on tuple SHA tamper
  - current-HEAD blob mismatch for output KB
  - current-HEAD blob mismatch for price KB
  - binary source content on legacy output blob
- Current/live `git_blob` evidence tests remain separate and unchanged in purpose.

## Verification

- `python scripts/test_validate_elevenlabs_040_evidence.py`
  - Result: pass
  - Detail: `Ran 21 tests in 19.614s`, `OK`
- `python scripts/validate_elevenlabs_040_detailed_pricing_control.py`
  - Result: pass
  - Detail:
    - `status: pass`
    - `live_evidence_validation.status: validated_current_source_commit`
    - `live_evidence_validation.source_evidence_commit: 2f35710403a08cd6866ee5388f07214e14767fca`
    - `live_evidence_validation.source_evidence_mode: git_blob`
    - `legacy_allowlisted_request_ids: []`
    - `legacy_worktree_line_endings_request_ids: []`
- `python scripts/test_apply_elevenlabs_040_detailed_pricing_control.py`
  - Result: pass
  - Detail: `Ran 12 tests in 2.759s`, `OK`
- `git diff --check`
  - Result: pass
  - Note: Git printed an LF/CRLF normalization warning for `scripts/test_validate_elevenlabs_040_evidence.py`, but no whitespace errors were reported.

## Self-Review

- Boundary check: only the owned evidence test file and this report were edited.
- Semantics check: production validator behavior was not changed; the tests now isolate historical legacy state entirely on the test side.
- Determinism check: the fixture uses a pinned commit, pinned tuples, pinned LF-only line map, and temp directories only.
- Failure-mode check: each tamper test still fails for the intended validator reason instead of relying on mutable live evidence drift.

## Concerns

- The current live 040 evidence bundle in this worktree now validates as current `git_blob` evidence, not legacy evidence. That is expected and is the exact drift this task had to isolate away from the legacy tests.
- The worktree still contains unrelated modified and untracked generated evidence files under `research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/`. They were left untouched and must not be staged with this task.

## Commit

- Commit hash: `32fc390f1f755bcab6b4bec0b621261628dfd3fd`
