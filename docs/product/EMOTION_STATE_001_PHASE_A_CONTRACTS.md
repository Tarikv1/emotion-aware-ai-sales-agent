# EMOTION-STATE-001 Material-Pending Phase A Contracts

EMOTION-STATE-001 is an offline, public-only material-pending checkpoint. It selects exactly `crema-d-v1.0-audio-wav` and `ami-manual-annotations-v1.6.2`, but it does not authorize or start dataset download or evaluation. `phase_a_complete=false`.

CREMA-D is controlled acoustic-sensitivity evidence only. AMI manual annotations are conversational-mechanics evidence only. Neither source supplies customer internal-emotion truth or mappings to hesitation, frustration, confusion, interest, or disengagement.

## Prepublication Validation

```powershell
python -m unittest scripts.test_emotion_state_001_open_dataset_gate scripts.test_emotion_state_001_closeout_hardening -v
python scripts\validate_emotion_state_001_phase_a_contracts.py --section prepublication --mode material-pending
```

Prepublication validation reads no canonical result/report pair and never invokes the Phase A runner. Candidate and accepted-checkpoint readback are also pure readback paths and never invoke the runner.

## Deferred Publication Transaction

The controller-only material-pending transaction is:

```powershell
$receipt = '.tmp\emotion-state-001-phase-a-publication\material-pending-receipt.json'
python scripts\run_emotion_state_001_phase_a_contracts.py --mode material-pending --defer-acceptance --receipt $receipt
try {
    python scripts\validate_emotion_state_001_phase_a_contracts.py --section candidate --receipt $receipt
    if ($LASTEXITCODE -ne 0) { throw 'Pending candidate readback failed' }
    python -m unittest scripts.test_emotion_state_001_open_dataset_gate scripts.test_emotion_state_001_closeout_hardening -v
    if ($LASTEXITCODE -ne 0) { throw 'Pending candidate tests failed' }
    python scripts\run_emotion_state_001_phase_a_contracts.py --accept-receipt $receipt
    if ($LASTEXITCODE -ne 0) { throw 'Pending candidate acceptance failed' }
}
catch {
    if (Test-Path $receipt) {
        python scripts\run_emotion_state_001_phase_a_contracts.py --reject-receipt $receipt
        if ($LASTEXITCODE -ne 0) { throw 'Pending candidate rejection/restoration failed' }
    }
    throw
}
```

The normal deferred `material-pending` CLI uses the fixed project-local root `data/public/emotion-state`; invocation authority remains external, and only an explicitly authorized controller may run that defer transaction. Each authorized defer transaction performs exactly two metadata-only, non-recursive absence-check cycles—before publication-lock acquisition and immediately before staging—limited to root `exists()`, conditional root `is_dir()`, and exact-child `exists()` for `crema-d-v1.0` and `ami-manual-annotations-v1.6.2`; it performs no listing, content read, hash, download, create, or write. Injected synthetic roots remain available for tests, while accept and reject do not access the material root. The implementer did not run the real defer transaction or modify the canonical pair; `phase_a_complete=false` remains the boundary.

## Publication And Recovery Boundary

The runner uses the accepted verification prepare, persistent-lock, finalize, and active-lease validation APIs. The candidate transaction retains a durable `awaiting_acceptance` journal, byte-exact previous-pair backups, and an exact ignored receipt under `.tmp/emotion-state-001-phase-a-publication/`. The receipt contains only its schema version, transaction ID, mode, candidate digests, and prior-pair presence/digests; it contains no timestamp or absolute path.

Publication replaces `result.json` first and `report.md` last. Candidate readback requires the live receipt/journal and exact candidate digests. Acceptance revalidates those invariants, durably records `accepted`, then cleans transaction state. Any pre-acceptance failure or explicit rejection restores the byte-identical previous pair. Startup recovery treats `awaiting_acceptance` as rejected; only a valid durable `accepted` state may retain the candidate and finish interrupted cleanup.

The canonical directory remains exactly:

- `research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/result.json`
- `research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/report.md`

No third canonical file is allowed. The protocol is logical commit and crash recovery, not physical two-file atomicity or a power-loss durability claim.

## Material-Pending Payload

The deterministic payload records the exact selected IDs, Creative Analysis Engine source pin, passing public-dataset/split-v2/cohort contract checks, blocker codes, six frozen baseline fingerprints, and normalized verification evidence. It records no invented local hashes, manifest counts, speaker evidence, or dataset material evidence.

The exact blockers are:

- `dataset_download_not_authorized`
- `selected_dataset_manifests_not_verified`

The completion scope is `source_provenance_dataset_selection_and_offline_contracts_only_material_verification_pending`. Every later readiness flag remains false.

## Contract Surfaces

- `emotion_state_public_dataset_contracts`: frozen CREMA-D and AMI public-source profiles and offline material rules.
- `emotion_state_split_manifest_v2_contracts`: dependency-aware, quarantine-first synthetic split design.
- `emotion_state_cohort_release_contracts`: synthetic discovery, unique-speaker, suppression, replacement, and confirmatory-floor design.
- `emotion_state_phase_a_verification_evidence`: byte-bound Git/input inventory, dependency closure, guarded command ledger, and deterministic verification digests.
- `emotion_state_annotation_contracts`, `emotion_state_contracts`, `emotion_pattern_contracts`, and `emotion_state_brain_extension`: offline reviewer, evidence, pattern, and detached BRAIN-extension contracts.

## Hard Boundary

Download and evaluation have not started. Source adaptation remains false. No private data, provider or ElevenLabs operation, outbound/customer call, simulation, runtime/prompt/KB/voice/LLM/phone/Procedure/dashboard change, or runtime activation occurred. This checkpoint makes no production, customer, PSTN, ASR, latency, provider-feasibility, or internal-emotion claim.
