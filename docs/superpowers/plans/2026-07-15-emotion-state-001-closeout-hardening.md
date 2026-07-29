# EMOTION-STATE-001 Closeout Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the three non-blocking review findings on the offline EMOTION-STATE-001 Phase A checkpoint without opening any later research, data, provider, or runtime gate.

**Architecture:** Keep `result.json` and `report.md` as the only canonical evidence files. Publish staged and fsynced bytes from the project-local ignored `.tmp/` area, persist a recovery journal plus exact previous-pair backups before replacing either canonical file, replace `result.json` first, and replace a result-hash-bearing `report.md` last as the logical commit marker. Normalize validator timeouts only at the existing top-level controlled-failure boundaries, then correct the stale design status and describe the new recovery boundary honestly.

**Tech Stack:** Python 3.11 standard library (`hashlib`, `json`, `os`, `tempfile`, `unittest`, `unittest.mock`, `uuid`), Markdown, Git.

## Global Constraints

- Work only in `D:\Codex\active\emotion-aware-ai-sales-agent\.worktrees\emotion-state-layer-design` on `codex/emotion-state-layer-design`.
- The checkpoint remains offline and partial: `phase_a_complete=false` must remain exact.
- Do not select a dataset, adapt source code/text/configuration, read private data, contact a provider, run calls, run simulations, change dashboard tests, enable Procedures, wire a runtime consumer, activate behavior, add a dependency, push, merge, or rewrite history.
- Do not make any ElevenLabs read or write.
- Keep the canonical generated directory limited to `result.json` and `report.md`; all transaction state belongs under ignored `.tmp/emotion-state-001-phase-a-publication/`.
- Do not claim physical two-file atomicity, power-loss durability, production readiness, customer-emotion truth, real-customer performance, PSTN/ASR/latency validation, provider feasibility, or runtime activation.
- Preserve the current `result.json` bytes if the payload is unchanged. `report.md` may change only to add the result-hash commit marker.
- Use TDD for Tasks 1 and 2: add the regression first, run it and capture the intended RED, make the minimum production change, then rerun GREEN.
- Preserve all existing tests and evaluators. Use only deterministic offline tests and mocked fault injection.
- Each task gets its own commit and independent review. Fix all Critical and Important review findings before advancing; record Minor findings.

---

### Task 1: Recoverable result/report publication

**Files:**
- Modify: `scripts/emotion_state_phase_a_contracts.py`
- Modify: `scripts/run_emotion_state_001_phase_a_contracts.py`
- Modify: `scripts/validate_emotion_state_001_phase_a_contracts.py`
- Create: `scripts/test_emotion_state_001_closeout_hardening.py`
- Regenerate: `research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/report.md`

**Interfaces:**
- Consumes: the existing deterministic `build_phase_a_payload(case_path, root=ROOT)` payload and fixed canonical paths.
- Produces: `render_phase_a_report(payload, *, result_sha256: str) -> str`, `publish_evidence_pair(...) -> None`, and `recover_incomplete_publication(...) -> str` where the recovery result is one of `"none"`, `"committed"`, or `"restored"`.
- Produces: a report line exactly matching ``- Publication commit marker: `result.json sha256:<64 uppercase hex characters>` ``.

- [ ] **Step 1: Add failing publication tests**

Create `PublicationRecoveryTests` in `scripts/test_emotion_state_001_closeout_hardening.py` with real temporary files under `.tmp/`. The tests must assert:

```python
class PublicationRecoveryTests(unittest.TestCase):
    def test_successful_publication_uses_report_as_commit_marker(self):
        # Publish a payload into a temporary canonical directory.
        # Assert result/report are the only canonical files.
        # Assert the marker digest equals SHA-256 of the exact result bytes.
        # Assert no transaction journal remains.

    def test_second_replace_failure_restores_previous_pair(self):
        # Seed an old result/report pair.
        # Patch only os.replace and fail the report-target replacement once.
        # Assert EvidencePublicationError, exact old bytes restored, and no journal.

    def test_hard_interrupt_after_result_replace_is_recovered_next_run(self):
        # Let the real result replacement finish, then raise KeyboardInterrupt.
        # Assert a journal and backups remain.
        # Call recover_incomplete_publication and assert exact old pair restored.

    def test_hard_interrupt_after_report_replace_finalizes_committed_pair(self):
        # Let both real replacements finish, then raise KeyboardInterrupt.
        # Recovery must recognize exact new hashes, retain the new pair, and clean state.

    def test_corrupt_backup_fails_closed_and_retains_recovery_evidence(self):
        # Interrupt after the first replacement, corrupt a recorded backup, and recover.
        # Assert EvidencePublicationError and that the journal is retained.

    def test_mismatched_report_marker_is_rejected(self):
        # Call the pure pair-verification helper on a result/report hash mismatch.
        # Assert a bounded validation failure.
```

Run:

```powershell
python -m unittest scripts.test_emotion_state_001_closeout_hardening.PublicationRecoveryTests -v
```

Expected RED: import/signature/behavior failures because publication journaling, recovery, and the report marker do not exist yet. The failure must not come from a syntax error or bad fixture.

- [ ] **Step 2: Add the report commit marker**

Change `render_phase_a_report` to require keyword-only `result_sha256`. Reject values that are not exactly 64 uppercase hexadecimal characters. Add this exact line near the other evidence counts:

```python
f"- Publication commit marker: `result.json sha256:{result_sha256}`",
```

The digest is computed from the exact staged `result.json` bytes after platform newline translation, not from an LF-only in-memory string.

- [ ] **Step 3: Implement durable journaled publication**

In the runner, add `EvidencePublicationError(RuntimeError)` and these behaviors:

```python
DEFAULT_RECOVERY_DIR = ROOT / ".tmp" / "emotion-state-001-phase-a-publication"
JOURNAL_NAME = "transaction.json"
TRANSACTION_SCHEMA_VERSION = 1
```

Implementation contract:

1. `recover_incomplete_publication` runs before a new payload is built.
2. A transaction uses a lowercase 32-character UUID transaction id. Stage names are derived from that validated id; journal-controlled arbitrary paths are forbidden.
3. Stage the new result using text mode with normal platform newline translation, flush, and `os.fsync`; hash its actual bytes. Render the report with that digest, then stage/fsync/hash the report.
4. If a previous canonical pair exists, require both files, back up both exact byte sequences under the recovery directory, flush/fsync them, and record both digests. A legacy pre-marker pair may be backed up for the one-time migration. A partial pre-existing pair fails closed.
5. Persist and fsync `transaction.json` with schema version, transaction id, previous-pair presence/digests, and new-pair digests before either canonical replacement. Create it exclusively so a concurrent publisher cannot overwrite an active transaction.
6. `os.replace` the staged result first and staged report last. The report is the logical commit marker.
7. Verify both final byte hashes and the report marker, then delete only the current transaction's journal, stages, and backups.
8. If an `OSError` occurs after the journal is durable, invoke recovery immediately and raise a bounded `EvidencePublicationError`; do not emit a traceback from `main()`.
9. If the process is interrupted after only the result replacement, the next recovery rebuilds restore stages from the preserved backups, atomically restores both prior files, verifies their exact digests, and then cleans transaction state.
10. If both canonical files match the recorded new hashes, recovery treats publication as committed and only cleans transaction state.
11. Missing or corrupt required backups, malformed journal fields, unknown schema versions, unsafe transaction ids, or a failed restore retain the journal/evidence and fail closed.
12. Do not catch `BaseException`; a simulated `KeyboardInterrupt` must leave durable recovery state for the next run.

- [ ] **Step 4: Make checkpoint validation require a committed pair**

After the runner succeeds, read the exact result bytes, parse the JSON, compute its uppercase SHA-256, and require the entire report to equal:

```python
render_phase_a_report(result, result_sha256=result_sha256)
```

Keep all existing marker/readiness assertions. This makes an old report plus new result fail closed.

- [ ] **Step 5: Verify GREEN and byte boundaries**

Run:

```powershell
python -m unittest scripts.test_emotion_state_001_closeout_hardening.PublicationRecoveryTests -v
python scripts\run_emotion_state_001_phase_a_contracts.py
python scripts\validate_emotion_state_001_phase_a_contracts.py --section checkpoint
python -c "from pathlib import Path; import hashlib; p=Path('research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/result.json'); print(hashlib.sha256(p.read_bytes()).hexdigest().upper())"
git diff --check
```

Expected GREEN: all publication tests pass; checkpoint passes; canonical directory has exactly two files; result digest remains `8A499F9A5CD3365AC98595A67250921C5E6A000E4218CDF3079E86071E57A618`; report contains the same digest as its commit marker.

- [ ] **Step 6: Commit**

```powershell
git add scripts\emotion_state_phase_a_contracts.py scripts\run_emotion_state_001_phase_a_contracts.py scripts\validate_emotion_state_001_phase_a_contracts.py scripts\test_emotion_state_001_closeout_hardening.py research\experiments\generated\EMOTION-STATE-001-phase-a-contracts\report.md
git commit -m "Harden EMOTION-STATE evidence publication"
```

### Task 2: Controlled validator timeout failures

**Files:**
- Modify: `scripts/test_emotion_state_001_closeout_hardening.py`
- Modify: `scripts/validate_exp_002_frozen_response_baseline.py`
- Modify: `scripts/validate_emotion_state_001_phase_a_contracts.py`

**Interfaces:**
- Consumes: the existing two validator `main() -> int` functions and six `subprocess.run(..., timeout=60)` call sites.
- Produces: the existing validator failure prefixes, return code `1`, no stderr traceback, no retries, and no timeout increase.

- [ ] **Step 1: Add six failing timeout-injection tests**

Add `ValidatorTimeoutTests` using `unittest.mock.patch`, `io.StringIO`, and `redirect_stdout`/`redirect_stderr`. Cover the two EXP call positions, the BRAIN section call, and the three checkpoint call positions. Earlier calls use `subprocess.CompletedProcess(..., returncode=0, stdout="", stderr="")`; the selected call raises `subprocess.TimeoutExpired(["stable-test-label"], 60)`.

Each test must assert:

```python
self.assertEqual(exit_code, 1)
self.assertIn(expected_prefix, stdout.getvalue())
self.assertIn("timed out after 60 seconds", stdout.getvalue())
self.assertEqual(stderr.getvalue(), "")
self.assertNotIn("Traceback", stdout.getvalue() + stderr.getvalue())
```

Run:

```powershell
python -m unittest scripts.test_emotion_state_001_closeout_hardening.ValidatorTimeoutTests -v
```

Expected RED: all selected timeouts escape the controlled paths as `TimeoutExpired` errors.

- [ ] **Step 2: Normalize only TimeoutExpired**

Add `subprocess.TimeoutExpired` to each validator's existing top-level caught exception tuple. Do not add retries, change 60-second limits, catch broad `Exception`, or add a new abstraction.

Expected controlled prefixes remain exact:

```text
EXP-002 frozen-response baseline validation failed:
EMOTION-STATE-001 Phase A validation failed:
```

- [ ] **Step 3: Verify GREEN**

Run:

```powershell
python -m unittest scripts.test_emotion_state_001_closeout_hardening.ValidatorTimeoutTests -v
python scripts\validate_exp_002_frozen_response_baseline.py
python scripts\validate_emotion_state_001_phase_a_contracts.py
git diff --check
```

Expected GREEN: six injected timeout cases return `1` with bounded stdout and empty stderr; both normal validators pass.

- [ ] **Step 4: Commit**

```powershell
git add scripts\test_emotion_state_001_closeout_hardening.py scripts\validate_exp_002_frozen_response_baseline.py scripts\validate_emotion_state_001_phase_a_contracts.py
git commit -m "Normalize EMOTION-STATE validator timeouts"
```

### Task 3: Truthful current status and recovery documentation

**Files:**
- Modify: `docs/superpowers/specs/2026-07-14-emotion-state-layer-design.md:5`
- Modify: `docs/product/EMOTION_STATE_001_PHASE_A_CONTRACTS.md`
- Modify: `research/experiments/EMOTION-STATE-001-phase-a.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`

**Interfaces:**
- Consumes: the reviewed design, completed offline partial contract checkpoint, new publication protocol, and timeout test evidence.
- Produces: current status language with every later gate still closed.

- [ ] **Step 1: Correct the stale status line**

Replace line 5 with exactly:

```md
Status: reviewed and approved design; offline partial Phase A contract foundation implemented; `phase_a_complete=false`; acoustic implementation, private-data work, provider work, and runtime activation remain unstarted and blocked
```

- [ ] **Step 2: Document the publication boundary accurately**

State that:

- the canonical directory still contains only `result.json` and `report.md`;
- the runner stages/fsyncs under ignored `.tmp/`, journals and backs up the prior pair, replaces result first, and publishes report last with the exact result SHA-256 commit marker;
- startup recovery either finalizes an exact committed new pair or restores the exact previous pair;
- consumers must require the validator to pass;
- this is logical commit/recovery, not physical two-file atomicity or a power-loss durability claim.

Record the timeout regression coverage and preserve every readiness disclaimer and `phase_a_complete=false`.

- [ ] **Step 3: Verify documentation and governance**

Run:

```powershell
python scripts\read_relevant.py find --path docs/superpowers/specs/2026-07-14-emotion-state-layer-design.md --query "offline partial Phase A contract foundation implemented" --context 2
python scripts\read_relevant.py find --path docs/product/EMOTION_STATE_001_PHASE_A_CONTRACTS.md --query "commit marker" --context 4
python scripts\validate_context_reading_policy.py
python scripts\check_thesis_update_gate.py
python scripts\validate_emotion_state_001_phase_a_contracts.py
git diff --check
```

Expected: all commands exit `0`; no wording opens Phase B, provider, private-data, acoustic, or runtime gates.

- [ ] **Step 4: Commit**

```powershell
git add docs\superpowers\specs\2026-07-14-emotion-state-layer-design.md docs\product\EMOTION_STATE_001_PHASE_A_CONTRACTS.md research\experiments\EMOTION-STATE-001-phase-a.md docs\thesis\METHODOLOGY_LOG.md
git commit -m "Close EMOTION-STATE checkpoint documentation gaps"
```

### Final offline verification and review

- [ ] Run the whole closeout test file, both focused validators, BRAIN/runtime/setup/drift/thesis/reference/context gates, JSON parsing, Python compilation, exact generated-artifact inventory, immutable BRAIN-002/frozen hashes, forbidden-path diff scan, `git diff --check`, and clean Git-state checks.
- [ ] Generate a merge-base-to-HEAD review package and obtain a fresh whole-branch code review.
- [ ] Fix and re-review all Critical or Important findings. Record any remaining Minor findings.
- [ ] Preserve the branch/worktree. Do not push or merge.
