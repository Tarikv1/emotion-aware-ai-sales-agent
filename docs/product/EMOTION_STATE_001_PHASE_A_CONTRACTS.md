# EMOTION-STATE-001 Partial Phase A Contracts

EMOTION-STATE-001 is an offline/prototype contract checkpoint. It establishes deterministic artifact and fail-closed interface evidence; it does not establish that all of Phase A is complete or authorize runtime use.

## Commands

Run and validate the frozen EXP-002 response/rating arithmetic:

```powershell
python scripts\run_exp_002_frozen_response_baseline.py
python scripts\validate_exp_002_frozen_response_baseline.py
```

Run and validate the Phase A contract checkpoint:

```powershell
python scripts\run_emotion_state_001_phase_a_contracts.py
python scripts\validate_emotion_state_001_phase_a_contracts.py
```

## Outputs

- Frozen response/rating evidence: `research/experiments/generated/EXP-002-frozen-response-baseline/`
- Phase A contract evidence: `research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/`

The canonical Phase A generated-artifact directory still contains exactly two files: `result.json` and `report.md`. Case inputs must remain under `research/experiments/cases/`. Project escape, parent traversal, private paths, output-root escape, and identical result/report destinations fail closed.

## Publication And Recovery Boundary

The runner holds an OS-level, non-blocking publication lock while it performs startup recovery and publication. Lock state, new-file stages, the transaction journal, previous-pair backups, and recovery scratch live under ignored `.tmp/`, not in the canonical generated-artifact directory. It stages and file-`fsync`s the new result and report, file-`fsync`s backups of the exact prior pair when one exists, persists the journal, replaces `result.json` first, and publishes `report.md` last.

The report is the logical commit record and contains exactly one result SHA-256 commit marker in the form `result.json sha256:<64-uppercase-SHA-256>`. A consumer must require `python scripts\validate_emotion_state_001_phase_a_contracts.py` to pass; reading either canonical file alone is not sufficient evidence of a committed pair.

At the next locked startup after a crash or interruption, recovery finalizes an exact new pair only when its recorded digests and report marker match. Otherwise it restores the exact previous pair from digest-verified backups, or restores the prior absence when no pair existed. If cleanup is interrupted after an exact new or previous pair is already canonical, a retry recognizes that pair and finishes cleanup. Corrupt or incomplete recovery evidence fails closed and is retained for diagnosis.

This protocol provides logical commit and crash recovery. It is not physical two-file atomicity, and file `fsync` does not make this a power-loss durability claim.

Controlled timeout regression coverage injects `subprocess.TimeoutExpired` at exactly six subprocess positions: two in the EXP-002 validator, one in the Phase A BRAIN section, and three in the Phase A checkpoint section. Every covered 60-second timeout returns exit `1` with the stable validator failure prefix, empty stderr, and no traceback. The coverage performs no provider, private-data, acoustic, runtime, customer-call, simulation, or production operation. Current-checkpoint hard stop: no ElevenLabs read or write occurred; neither an outbound call nor a customer call occurred; no simulation occurred; no source adaptation occurred; and no source-adaptation gate was opened.

## Contract Surfaces

- `exp_002_frozen_response_baseline`: frozen response/rating structure, score totals, recorded preferences, and aggregate arithmetic.
- `emotion_state_annotation_contracts`: reviewer-level annotation and dependency-safe split rules.
- `emotion_state_contracts`: strict turn evidence, audit, aggregate, correction, and perceived-customer-state interfaces.
- `emotion_pattern_contracts`: offline pattern-candidate, registry, approval-envelope, and fail-closed runtime-activation interfaces.
- `emotion_state_brain_extension`: a detached offline extension that cannot mutate or connect to BRAIN-002 v1.

## Determinism And Baseline Meaning

The six baseline fingerprints are SHA-256 content locks over the two frozen prompts, EXP-002 case file, frozen response/rating record, generated prompt packet, and evaluation rubric. A mismatch stops checkpoint generation. A matching fingerprint means only that those exact inputs did not drift; it does not improve evaluator provenance or create new semantic evidence.

Prompt-packet normalization proves deterministic rendering after the machine-specific source-case line is normalized. The separate Task 0 scorer reruns only frozen response/rating structure, totals, preferences, and aggregate arithmetic. Neither path regenerates responses or repeats semantic judgment. The frozen record does not establish evaluator type, identity or role, count, or procedure, so `evaluator_provenance_status` must remain `not_recorded`.

## Open Gates

- No public dataset is selected. Every selected dataset still needs an exact source/version, terms or license, access, local-file hash, label mapping, domain-limitation, split, and redistribution manifest.
- The Creative Analysis Engine repository URL and revision or authoritative archive date remain unverified. Phase B reuse scope, attribution wording, and separate approval remain undefined or pending. Author permission is attested, but license metadata is not used as permission authority. Source adaptation remains false.
- Live aggregate release remains blocked until a separately approved privacy-preserving unique-speaker cohort-release/dedup gate is designed, approved, satisfied, and validated. A small count of similar calls is not evidence of a stable population pattern.
- Public-dataset evaluation, private research, provider feasibility, Phase B reuse, and runtime activation remain blocked.

## Readiness Boundary

`phase_a_complete=false` remains the current readiness value. This checkpoint is limited to offline synthetic contract-artifact evidence. Acoustic implementation, private-data work, public-dataset evaluation, provider work, and runtime wiring or activation remain unstarted and blocked. It is not production readiness; it does not validate customer emotion, real-customer performance, PSTN, ASR, latency, provider feasibility, or runtime activation. It performs no provider operation, reads no private data, changes no runtime behavior, and leaves BRAIN-002 v1 unchanged.
