# EMOTION-STATE-001 Phase A Public-Dataset Contracts

EMOTION-STATE-001 is an offline, public-only checkpoint with `material-pending` and `complete` modes. The tracked inputs select exactly `crema-d-v1.0-audio-wav` and `ami-manual-annotations-v1.6.2`. The bounded complete state does not start dataset evaluation or authorize runtime use.

CREMA-D is controlled acoustic-sensitivity evidence only. AMI manual annotations are conversational-mechanics evidence only. Neither source supplies customer internal-emotion truth or mappings to hesitation, frustration, confusion, interest, or disengagement.

## Prepublication Validation

```powershell
python -m unittest scripts.test_emotion_state_001_open_dataset_gate scripts.test_emotion_state_001_closeout_hardening -v
python scripts\validate_emotion_state_001_phase_a_contracts.py --section prepublication --mode material-pending
python scripts\validate_emotion_state_001_phase_a_contracts.py --section materials
python scripts\validate_emotion_state_001_phase_a_contracts.py --section prepublication --mode complete
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

## Complete Input Evidence

Both manifests were accessed on `2026-07-17`. The complete tracked evidence is:

- CREMA-D: 7,446 selected files, 628,813,439 selected bytes, 7,446 included and 22,367 excluded quality entries; manifest SHA-256 `6E86F06358E4AD172C72BE1692CFF37291D9D5763DD7F6F5C7CE7405E7E01248`, hash-inventory SHA-256 `AD58D8165C683847DF246F923FF466722C7F628FE8D81679F618FA5EB3031C87`, quality-inventory SHA-256 `455D6A010855F209B4DC4C67F67E4222FAB81601861745B5B5E79E7942B92682`, source revision `f3b8611a309886568dfa957141775b2e05add04a`. The 7,442 WAV files are only one subset of the 7,446 selected inventory entries and are not advertised as the included inventory count.
- AMI: 2,074 selected files, 180,905,698 selected bytes, 2,074 included and 3,086 excluded quality entries; archive SHA-256 `B56E5BABB2496B8795DEEEDA7E71178D7FBC9963F94276CF2A3F4B56EBBC9F9D`, manifest SHA-256 `3904D4A3A9EDF53B06A65354E02FBE1BDD44361B5E196FC6DD4A3882C74911DE`, hash-inventory SHA-256 `CE7F837A2A44DFEE44691C4BA8B5B0D7766E46D6616986CF565A6300056DEAEE`, and quality-inventory SHA-256 `A376A6C0D5F89770525936299717F1595B743489B593DC4E5CE88AB08ACB22C9`.

`materials` validation requires the ignored local raw bytes. `checkpoint` validation reads the tracked evidence and canonical pair, so it can run in a clean clone; it validates what the captured complete run recorded but cannot re-prove raw-byte availability.

`phase_a_complete=true` is derived only for the scope `source_provenance_dataset_manifests_offline_contracts_and_cohort_release_gate_only`. It is not an accepted checkpoint until the deferred candidate passes independent readback and explicit acceptance.

## Hard Boundary

Dataset evaluation has not started. Source adaptation remains false. No private data, provider or ElevenLabs operation, outbound/customer call, simulation, runtime/prompt/KB/voice/LLM/phone/Procedure/dashboard change, or runtime activation occurred. Live aggregate release, public-dataset evaluation, Phase B, private research, provider feasibility, and runtime activation remain blocked. This checkpoint makes no production, customer, PSTN, ASR, latency, provider-feasibility, or internal-emotion claim.
