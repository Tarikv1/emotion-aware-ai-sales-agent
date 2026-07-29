# EMOTION-STATE-001 Partial Phase A Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fail-closed, offline-only partial Phase A provenance and contract foundation for temporal customer-state research without adapting acoustic code, changing live sales behavior, or enabling runtime influence. Keep Phase A incomplete until both exact per-public-dataset manifests and the separately approved privacy-preserving unique-speaker cohort-release/dedup gate are designed, approved, satisfied, and validated.

**Architecture:** Add strict Python 3.11 contract modules for reviewer aggregation, customer-turn evidence, aggregate persistence, pattern artifacts, and a detached BRAIN extension. Exercise them through synthetic self-checks, one fixed case, one runner, and one standalone validator that produces checkpoint-scoped evidence. Keep BRAIN-002 v1, live entrypoints, dialogue reasoning, action selection, providers, and customer data untouched.

**Tech Stack:** Python 3.11 standard library, JSON fixtures/manifests, Markdown research and product documentation, standalone `scripts/validate_*.py` gates, Git.

## Global Constraints

- Implement only `EMOTION-STATE Phase A: Source Manifest, Dataset Manifests, And Contracts` from the approved design.
- The approved design is `docs/superpowers/specs/2026-07-14-emotion-state-layer-design.md`.
- The reviewed archive is `D:\Codex\z\creative-analysis-engine-dev.zip` with SHA-256 `E579B966E226F2AF6E4F8F8203C7189FEC94FB448EFC09B4B6640C10A398ECCC`.
- Author and supervisor permission is recorded as project-owner attestation dated `2026-07-14`; permission is not the remaining provenance blocker.
- The exact GitHub URL and source revision or archive date are unverified. Do not guess them.
- The observed repository license is also unverified, but Tarik's attested author permission is the reuse authority and license is not a permission blocker. Record the license if available; do not reopen the approved consent decision.
- Until the exact GitHub URL and source revision or archive date are recorded, the source manifest must set `adaptation_allowed` to `false`. Phase B also requires its own approval even after provenance is complete.
- Do not copy, translate, or adapt code from the archive in this plan.
- Do not add the Creative Analysis Engine or any of its dependencies as a runtime dependency.
- Use only Python standard-library functionality; do not add `numpy`, `librosa`, `scipy`, `soundfile`, `pydantic`, `pytest`, or a cryptography package.
- `CustomerTurnEvidenceV1`, `CustomerTurnAuditV1`, and `PerceivedCustomerStateV1` are memory-only contracts.
- `OperationalAggregateV1` keeps the approved exact field set and rejects cohorts below ten eligible calls. Its payload does not contain speaker IDs or a caller-supplied unique-speaker count.
- The approved unique-speaker suppression rule is not solved by call-scoped IDs: they cannot distinguish repeat callers across calls. Live aggregate release remains blocked until a separately approved privacy-preserving cohort-release/dedup design defines the identity source, repeat-caller semantics, ephemeral linkage retention and destruction, trust boundary, and audit. Do not invent or infer that proof in Phase A.
- `PatternCandidateV1.unique_speaker_count` is different: it may be derived only from approved research dependency-group IDs in public/synthetic or separately approved private research records; it is not a live caller identity or aggregate-release proof.
- No raw audio, raw private transcript, arbitrary transcript string, reusable speaker identity, individual emotional profile, provider payload, key, or secret may enter tracked output.
- Pseudonymous research data must not be described as anonymous.
- The acoustic lane remains offline; `runtime_approved` is always `false` in Phase A.
- BRAIN-002 v1 remains unchanged. Phase A adds a detached versioned extension and must not silently mutate current BRAIN fixtures or downstream consumers.
- Do not import the new contracts from `runtime/entrypoints/`, `runtime/core/dialogue_manager.py`, `runtime/core/contextual_buyer_semantics.py`, `runtime/action_selector/`, or provider code.
- Do not connect or write the detached offline BRAIN mapping into existing live affect or action-selector fields.
- No ElevenLabs or other provider read/write, no customer-audio upload, no outbound call, no live call, no live shadow telemetry, no runtime activation, and no sales-policy influence.
- No public dataset is selected in Phase A. Create the dataset-manifest contract, but create one dataset manifest only when an exact dataset is selected and its URL, version, terms, restrictions, and local hashes are verified.
- This is a partial Phase A foundation checkpoint: the approved per-public-dataset manifest requirement remains open because no dataset currently has complete verified provenance, and the privacy-preserving unique-speaker cohort-release/dedup gate remains undesigned and unapproved. Do not call all of Phase A complete until both subgates are designed, approved, satisfied, and validated.
- Acted, creative-expression, and other non-sales corpora may support offline thesis comparison only; they do not establish sales-domain or real-customer validity.
- The repository starts with a deterministic EXP-002 prompt-packet runner but no executable frozen-response scorer. Before any EMOTION-STATE task, Task 0 must add a deterministic scorer over the already recorded responses and rubric ratings of unrecorded evaluator provenance, recompute rating arithmetic, preferences, and aggregates, and record the result. It does not regenerate responses or rerun semantic judgment; evaluator type, identity or role, count, and procedure remain unrecorded.
- Existing `MELD`, `Persuasion for Good`, and local `IEMOCAP` provenance limitations remain unresolved. `MSP-Podcast` is not yet registered. Phase D remains blocked.
- Task 0 generated evidence belongs only under `research/experiments/generated/EXP-002-frozen-response-baseline/`; EMOTION-STATE generated evidence belongs only under `research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/`.
- Preserve the previous Universal Sales RAG roadmap item as parked, not completed; Tarik's approval reprioritizes the current checkpoint.
- Every task uses a red/green validator cycle and ends with a focused commit.
- This approved plan must be committed before execution. Task 0 is one prerequisite baseline commit; the seven numbered EMOTION-STATE task commits follow that clean, passing baseline.
- At plan approval, `python scripts\check_thesis_reference_registry.py` reports twenty failure locations covering twelve distinct unregistered URLs: eight unrelated URLs in committed Atlas/ElevenLabs documents, plus four emotion-state URLs repeated in the approved design and twice in this plan. Task 2 must register only the four distinct emotion-state URLs. Before Task 0, rerun the guard: any failing URL beyond those four is an external blocker that requires a separate cleanup or rebase; do not absorb the unrelated eight into this feature. Task 7 and the Definition of Done still require the repository-wide guard to exit `0` with no waiver.
- Merge, push, or integration into another branch is outside this plan and requires Tarik's later explicit direction.

## Scope Split

This plan stops at a partial Phase A foundation checkpoint because the remaining Phase A dataset-manifest and privacy-preserving unique-speaker cohort-release/dedup subgates, plus all later phases, have independent acceptance gates:

- Phase B needs a separate acoustic-feature plan after provenance is complete.
- Phase C needs a separate temporal tracker and monotonic policy-adapter plan.
- Phase D needs verified public-dataset manifests, preregistration, dependency-safe splits, power analysis, and a one-use lockbox.
- Phase E needs a separate private-data governance decision.
- Phase F permits documentation-only provider feasibility and authorized offline replay, not live wiring.
- Runtime activation requires a later security plan for real Ed25519 verification, trust-store custody, promotion ACLs, rollback, and live-boundary tests.

## Preflight

- [ ] Verify the isolated worktree, archive, frozen baseline, and repository governance precondition before Task 0.

```powershell
git status --short --branch
git rev-parse HEAD
Get-FileHash -Algorithm SHA256 D:\Codex\z\creative-analysis-engine-dev.zip
python scripts\validate_brain_002_runtime_state_schema.py
python scripts\validate_runtime_manifest.py
python scripts\validate_private_data_boundary.py
python scripts\check_thesis_reference_registry.py
python scripts\run_prompt_baseline.py --cases research\experiments\cases\exp-002-dataset-derived.json --out .tmp\emotion-state-001\EXP-002-prompt-packet.md
git diff --no-index --ignore-matching-lines="^- Source case file:" -- research\experiments\generated\EXP-002\EXP-002-prompt-packet.md .tmp\emotion-state-001\EXP-002-prompt-packet.md
$expected = [ordered]@{
  "packages/prompts/baseline-non-adaptive.txt" = "BB1FD1EAC0D4DE858BFDCE4A880BBF2C59C14A216489A1A85EF149F3E88D7FCA"
  "packages/prompts/baseline-adaptive.txt" = "EBD4106841987CA4A322C2B8B95A33ECFFC4238BB476DEC611A640D5B000EB42"
  "research/experiments/cases/exp-002-dataset-derived.json" = "882B94C0A31C41A94540941A254AC7E8119CADE9AAD9B071089E854917BDC7D6"
  "research/experiments/EXP-002-dataset-derived-baseline.md" = "D930C845AC912D44610B3CE263B55EA03BFFD7CAB8706C2BC95CB17045FF1316"
  "research/experiments/generated/EXP-002/EXP-002-prompt-packet.md" = "14017F985D54D2B46A338EA2EFA796B24202E3E5A3D3EB8223346CEA96E5CD09"
  "docs/thesis/EVALUATION_RUBRIC.md" = "39D3CF33E38A0C13ADEE178F3DB4174D4D8E3A42B1DE4C274BF96FFA36FFB416"
}
foreach ($path in $expected.Keys) {
  $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash
  if ($actual -ne $expected[$path]) { throw "Frozen baseline drift: $path" }
}
```

Expected:

```text
## codex/emotion-state-layer-design
E579B966E226F2AF6E4F8F8203C7189FEC94FB448EFC09B4B6640C10A398ECCC
BRAIN-002 runtime state schema validation passed.
Runtime manifest validation passed.
Private data boundary validation passed.
Frozen baseline hashes match the six values embedded above.
```

The exact wording of the runtime and privacy validators may differ; each must exit `0`. The thesis-reference guard may fail only on the four exact emotion-state design URLs listed in Task 2; any other failure blocks Task 0 pending a separately scoped cleanup or rebase. At preflight, the prompt command proves deterministic packet rendering only and the exact hashes freeze the recorded historical baseline. Task 0 then makes the frozen-response score arithmetic runnable and recorded. It still does not regenerate responses or rerun semantic judgment. Stop if the worktree is dirty or any hash differs; do not begin Task 1 until Task 0 passes and is committed.

## File Map

**Create:**

- `scripts/exp_002_frozen_response_baseline.py`: deterministic parser/scorer for the frozen historical EXP-002 responses and recorded ratings of unrecorded evaluator provenance.
- `scripts/run_exp_002_frozen_response_baseline.py`: record the deterministic frozen-response score result/report.
- `scripts/validate_exp_002_frozen_response_baseline.py`: rerun packet rendering and frozen-response scoring before EMOTION-STATE work.
- `research/experiments/generated/EXP-002-frozen-response-baseline/result.json`: machine-readable recorded baseline scorer output.
- `research/experiments/generated/EXP-002-frozen-response-baseline/report.md`: explicit runnable-baseline result and semantic-evaluation limitation.
- `runtime/contracts/emotion_state_contracts.py`: strict V1 turn, audit, aggregate, perceived-state, and event-identity contracts.
- `runtime/contracts/emotion_pattern_contracts.py`: canonical pattern content, digest, approval-shape, and fail-closed envelope contracts.
- `runtime/contracts/emotion_state_brain_extension.py`: detached offline BRAIN mapping; no packet mutation or live import.
- `research/sources/creative_analysis_engine/source_manifest.json`: immutable archive/source/adaptation ledger.
- `research/sources/creative_analysis_engine/source_notes.md`: human-readable provenance and collaboration boundary.
- `research/sources/emotion_state/dataset_manifest_contract.json`: required fields for later selected datasets.
- `research/sources/emotion_state/annotation_record_v1.schema.json`: exact reviewer-record fields and mutually exclusive abstention boundary.
- `research/sources/emotion_state/split_manifest_v1.schema.json`: dependency-disjoint partition and one-use lockbox contract.
- `scripts/emotion_state_annotation_contracts.py`: executable reviewer-record validation and deterministic three-reviewer aggregation.
- `docs/data/EMOTION_STATE_001_ANNOTATION_CODEBOOK.md`: reviewer fields, abstention, ambiguity, and consensus rules.
- `research/experiments/EMOTION-STATE-001-phase-a.md`: Phase A experiment/checkpoint note.
- `research/experiments/cases/emotion-state-001-phase-a-contracts.json`: fixed synthetic contract and baseline-fingerprint inputs.
- `scripts/emotion_state_phase_a_contracts.py`: checkpoint builder and report renderer.
- `scripts/run_emotion_state_001_phase_a_contracts.py`: project-path-safe runner.
- `scripts/validate_emotion_state_001_phase_a_contracts.py`: red/green contract validator.
- `docs/product/EMOTION_STATE_001_PHASE_A_CONTRACTS.md`: command, outputs, and readiness boundary.
- `research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/result.json`: generated machine-readable evidence.
- `research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/report.md`: generated human-readable evidence.

**Modify:**

- `docs/third-party-inspirations.md`: canonical Creative Analysis Engine attribution entry linked to the manifest.
- `docs/thesis/THESIS_REFERENCE_REGISTRY.md`: register the four external URLs introduced by the approved emotion-state design; do not fold unrelated registry debt into this feature.
- `docs/brain/BRAIN_002_RUNTIME_STATE_SCHEMA.md`: document the detached extension and unchanged v1 boundary.
- `docs/thesis/ROADMAP.md`: make Phase A current and park, rather than complete, the previous current checkpoint.
- `docs/thesis/DECISION_LOG.md`: record the Phase A/offline-only architecture decision as `DEC-021`.
- `docs/thesis/METHODOLOGY_LOG.md`: record the completed partial Phase A foundation evidence, `phase_a_complete=false`, both the open dataset-manifest and privacy-preserving unique-speaker cohort-release/dedup subgates, and other limitations.
- `docs/product/COMMANDS.md`: add runner and validator commands.
- `runtime/runtime_manifest.json`: register the three contract files as non-integrated contract surfaces.
- `scripts/validate_runtime_manifest.py`: require the three registered contract paths.
- `scripts/check_setup.py`: register new foundational files.
- `scripts/validate_check_setup.py`: require the matching setup-check IDs.
- `scripts/check_project_drift.py`: add the Phase A fixture/validator files to the drift inventory.
- `scripts/validate_project_drift_guard.py`: mirror the drift inventory additions.

**Must remain unchanged:**

- `runtime/contracts/brain_runtime_state_schema.py`
- `research/experiments/cases/brain-002-runtime-state-schema.json`
- `runtime/entrypoints/`
- `runtime/core/dialogue_manager.py`
- `runtime/core/contextual_buyer_semantics.py`
- `runtime/action_selector/`
- `runtime/providers/`
- `scripts/raw_audio_speech_features.py`
- all ElevenLabs prompt, KB, test, Analysis, voice, LLM, tool, phone, and Procedure files.

---

### Task 0: Make The Frozen EXP-002 Response Scorer Runnable Before EMOTION-STATE Work

This prerequisite satisfies the approved baseline ordering without pretending that historical responses or semantic ratings were regenerated or that the evaluator provenance is known. It reruns deterministic packet rendering, validates exact frozen inputs, parses all six recorded response pairs and rubric ratings of unrecorded evaluator provenance, recomputes totals/preferences/aggregate arithmetic, records the result, and hard-fails on drift. Task 1 may not begin until this task is green and committed.

**Files:**

- Create: `scripts/exp_002_frozen_response_baseline.py`
- Create: `scripts/run_exp_002_frozen_response_baseline.py`
- Create: `scripts/validate_exp_002_frozen_response_baseline.py`
- Create by runner: `research/experiments/generated/EXP-002-frozen-response-baseline/result.json`
- Create by runner: `research/experiments/generated/EXP-002-frozen-response-baseline/report.md`

**Interfaces:**

- Consumes only the six exact preflight-fingerprinted EXP-002 prompt, case, record, packet, and rubric files.
- Produces `build_frozen_baseline_result(root)`, `render_frozen_baseline_report(payload)`, `normalized_prompt_packet_digest(path)`, and `frozen_baseline_self_check(root)`.
- Recomputes score arithmetic and recorded preferences only. It does not regenerate a response or replace/repeat semantic evaluation, and it records `evaluator_provenance_status = not_recorded` rather than inferring a human or automated evaluator.

- [ ] **Step 1: Add the failing standalone validator**

```python
#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.exp_002_frozen_response_baseline import (
    build_frozen_baseline_result,
    frozen_baseline_self_check,
    normalized_prompt_packet_digest,
)

RUNNER = ROOT / "scripts" / "run_exp_002_frozen_response_baseline.py"
RESULT = ROOT / "research" / "experiments" / "generated" / "EXP-002-frozen-response-baseline" / "result.json"
REPORT = RESULT.with_name("report.md")
TRACKED_PACKET = ROOT / "research" / "experiments" / "generated" / "EXP-002" / "EXP-002-prompt-packet.md"
RENDERED_PACKET = ROOT / ".tmp" / "exp-002-frozen-response-baseline" / "EXP-002-prompt-packet.md"
EXPECTED_NORMALIZED_PROMPT_PACKET_SHA256 = "83DF6E5F7B3566754F7D09C78F5BBD3B013ABED328C01EF90BA68BCFF2C395FA"
EXPECTED_SUMMARY = {
    "case_count": 6,
    "response_count": 12,
    "adaptive_preferred_count": 6,
    "non_adaptive_preferred_count": 0,
    "tie_count": 0,
    "non_adaptive_average_total": 18.67,
    "adaptive_average_total": 23.67,
}


def main() -> int:
    try:
        if not RUNNER.exists():
            raise AssertionError("missing frozen-response baseline runner")
        completed = subprocess.run(
            [sys.executable, str(RUNNER)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stdout + completed.stderr)
        recorded = json.loads(RESULT.read_text(encoding="utf-8"))
        expected = build_frozen_baseline_result(ROOT)
        if recorded != expected:
            raise AssertionError("recorded frozen-response baseline differs from deterministic rebuild")
        if recorded["summary"] != EXPECTED_SUMMARY:
            raise AssertionError("frozen-response baseline summary drift")
        if recorded["response_generation_performed"] is not False:
            raise AssertionError("baseline must not claim response regeneration")
        if recorded["semantic_judgment_recomputed"] is not False:
            raise AssertionError("baseline must not claim semantic re-evaluation")
        if recorded["evaluator_provenance_status"] != "not_recorded":
            raise AssertionError("baseline evaluator provenance must remain explicitly unrecorded")
        if recorded["score_arithmetic_recomputed"] is not True:
            raise AssertionError("baseline score arithmetic was not recomputed")
        report = REPORT.read_text(encoding="utf-8")
        for marker in (
            "Frozen EXP-002 Response Baseline",
            "Score arithmetic recomputed: `True`",
            "Response generation performed: `False`",
            "Semantic judgment recomputed: `False`",
            "Evaluator provenance status: `not_recorded`",
        ):
            if marker not in report:
                raise AssertionError(f"baseline report missing marker: {marker}")
        rendered = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "run_prompt_baseline.py"),
                "--cases",
                str(ROOT / "research" / "experiments" / "cases" / "exp-002-dataset-derived.json"),
                "--out",
                str(RENDERED_PACKET),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
        if rendered.returncode != 0:
            raise AssertionError(rendered.stdout + rendered.stderr)
        if normalized_prompt_packet_digest(TRACKED_PACKET) != EXPECTED_NORMALIZED_PROMPT_PACKET_SHA256:
            raise AssertionError("tracked normalized prompt packet drift")
        if normalized_prompt_packet_digest(RENDERED_PACKET) != EXPECTED_NORMALIZED_PROMPT_PACKET_SHA256:
            raise AssertionError("rerendered normalized prompt packet drift")
        if frozen_baseline_self_check(ROOT) != "pass":
            raise AssertionError("frozen baseline self-check failed")
    except (AssertionError, KeyError, OSError, ValueError) as exc:
        print(f"EXP-002 frozen-response baseline validation failed: {exc}")
        return 1
    print("EXP-002 frozen-response baseline validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run the validator and prove the baseline red gate**

```powershell
python scripts\validate_exp_002_frozen_response_baseline.py
```

Expected: nonzero exit because the scorer and runner do not exist. Do not continue if it passes unexpectedly.

- [ ] **Step 3: Implement deterministic parsing and scoring of the frozen record**

```python
from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

EXPECTED_INPUT_FINGERPRINTS = {
    "packages/prompts/baseline-non-adaptive.txt": "BB1FD1EAC0D4DE858BFDCE4A880BBF2C59C14A216489A1A85EF149F3E88D7FCA",
    "packages/prompts/baseline-adaptive.txt": "EBD4106841987CA4A322C2B8B95A33ECFFC4238BB476DEC611A640D5B000EB42",
    "research/experiments/cases/exp-002-dataset-derived.json": "882B94C0A31C41A94540941A254AC7E8119CADE9AAD9B071089E854917BDC7D6",
    "research/experiments/EXP-002-dataset-derived-baseline.md": "D930C845AC912D44610B3CE263B55EA03BFFD7CAB8706C2BC95CB17045FF1316",
    "research/experiments/generated/EXP-002/EXP-002-prompt-packet.md": "14017F985D54D2B46A338EA2EFA796B24202E3E5A3D3EB8223346CEA96E5CD09",
    "docs/thesis/EVALUATION_RUBRIC.md": "39D3CF33E38A0C13ADEE178F3DB4174D4D8E3A42B1DE4C274BF96FFA36FFB416",
}
DIMENSIONS = (
    "Context fit",
    "Strategy coherence",
    "Emotional appropriateness",
    "Persuasive quality",
    "Human-likeness",
)
CASE_SECTION_PATTERN = re.compile(r"(?ms)^### (EXP-002-C\d{2})\n(.*?)(?=^### |\Z)")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def normalized_prompt_packet_digest(path: Path) -> str:
    text = path.read_bytes().decode("utf-8")
    normalized, count = re.subn(
        r"(?m)^- Source case file: `[^`\r\n]+`(?=\r?$)",
        "- Source case file: `<normalized>`",
        text,
    )
    if count != 1:
        raise ValueError(f"expected one source-case line in {path}")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest().upper()


def _extract_response(body: str, variant: str) -> str:
    match = re.search(
        rf"(?ms)^{re.escape(variant)} response:\s*\n`([^`\r\n]+)`",
        body,
    )
    if match is None or not match.group(1).strip():
        raise ValueError(f"missing frozen {variant} response")
    return match.group(1)


def _extract_scores(body: str, variant: str) -> dict[str, int]:
    match = re.search(
        rf"(?m)^- {re.escape(variant)}:\s*$\n(?P<lines>(?:  - [^\r\n]+\r?\n){{6}})",
        body,
    )
    if match is None:
        raise ValueError(f"missing {variant} score block")
    pairs = re.findall(r"(?m)^  - ([A-Za-z -]+): (\d+)$", match.group("lines"))
    scores = {label: int(value) for label, value in pairs}
    if len(pairs) != 6 or set(scores) != {*DIMENSIONS, "Total"}:
        raise ValueError(f"{variant} score fields mismatch")
    if any(not 1 <= scores[dimension] <= 5 for dimension in DIMENSIONS):
        raise ValueError(f"{variant} dimension score is outside 1..5")
    if scores["Total"] != sum(scores[dimension] for dimension in DIMENSIONS):
        raise ValueError(f"{variant} recorded total does not equal its dimensions")
    return scores


def parse_frozen_response_baseline(markdown: str, case_ids: list[str]) -> list[dict[str, Any]]:
    sections = CASE_SECTION_PATTERN.findall(markdown)
    if len(sections) != len(case_ids) or [case_id for case_id, _ in sections] != case_ids:
        raise ValueError("frozen response sections do not exactly match the case file")
    parsed: list[dict[str, Any]] = []
    for case_id, body in sections:
        non_adaptive_response = _extract_response(body, "Non-adaptive")
        adaptive_response = _extract_response(body, "Adaptive")
        non_adaptive_scores = _extract_scores(body, "Non-adaptive")
        adaptive_scores = _extract_scores(body, "Adaptive")
        preferred_match = re.search(r"(?m)^Preferred: (Adaptive|Non-adaptive|Tie)\s*$", body)
        if preferred_match is None or re.search(r"(?ms)^Why:\s*\n\s*\n\S", body) is None:
            raise ValueError(f"{case_id} lacks a recorded preference or rationale")
        computed_preference = (
            "Adaptive"
            if adaptive_scores["Total"] > non_adaptive_scores["Total"]
            else "Non-adaptive"
            if non_adaptive_scores["Total"] > adaptive_scores["Total"]
            else "Tie"
        )
        if preferred_match.group(1) != computed_preference:
            raise ValueError(f"{case_id} recorded preference disagrees with total scores")
        parsed.append({
            "case_id": case_id,
            "response_sha256": {
                "non_adaptive": hashlib.sha256(non_adaptive_response.encode("utf-8")).hexdigest().upper(),
                "adaptive": hashlib.sha256(adaptive_response.encode("utf-8")).hexdigest().upper(),
            },
            "scores": {
                "non_adaptive": non_adaptive_scores,
                "adaptive": adaptive_scores,
            },
            "preferred": computed_preference,
        })
    return parsed


def _average(total: int, count: int) -> float:
    value = (Decimal(total) / Decimal(count)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return float(value)


def build_frozen_baseline_result(root: Path) -> dict[str, Any]:
    actual_fingerprints = {
        relative_path: sha256_file(root / relative_path)
        for relative_path in EXPECTED_INPUT_FINGERPRINTS
    }
    if actual_fingerprints != EXPECTED_INPUT_FINGERPRINTS:
        raise ValueError("frozen EXP-002 baseline input drift")
    cases = json.loads((root / "research" / "experiments" / "cases" / "exp-002-dataset-derived.json").read_text(encoding="utf-8"))
    if not isinstance(cases, list) or len(cases) != 6:
        raise ValueError("EXP-002 case file must contain exactly six cases")
    case_ids = [case["case_id"] for case in cases]
    markdown = (root / "research" / "experiments" / "EXP-002-dataset-derived-baseline.md").read_text(encoding="utf-8")
    parsed = parse_frozen_response_baseline(markdown, case_ids)
    non_adaptive_total = sum(item["scores"]["non_adaptive"]["Total"] for item in parsed)
    adaptive_total = sum(item["scores"]["adaptive"]["Total"] for item in parsed)
    summary = {
        "case_count": len(parsed),
        "response_count": len(parsed) * 2,
        "adaptive_preferred_count": sum(item["preferred"] == "Adaptive" for item in parsed),
        "non_adaptive_preferred_count": sum(item["preferred"] == "Non-adaptive" for item in parsed),
        "tie_count": sum(item["preferred"] == "Tie" for item in parsed),
        "non_adaptive_average_total": _average(non_adaptive_total, len(parsed)),
        "adaptive_average_total": _average(adaptive_total, len(parsed)),
    }
    return {
        "checkpoint_id": "EXP-002-frozen-response-baseline",
        "schema_version": 1,
        "status": "frozen_response_score_arithmetic_runnable_and_recorded",
        "input_fingerprints": actual_fingerprints,
        "response_generation_performed": False,
        "semantic_judgment_recomputed": False,
        "evaluator_provenance_status": "not_recorded",
        "score_arithmetic_recomputed": True,
        "cases": parsed,
        "summary": summary,
    }


def render_frozen_baseline_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return "\n".join([
        "# Frozen EXP-002 Response Baseline",
        "",
        f"- Cases: `{summary['case_count']}`",
        f"- Responses: `{summary['response_count']}`",
        f"- Adaptive preferred: `{summary['adaptive_preferred_count']}`",
        f"- Non-adaptive average: `{summary['non_adaptive_average_total']}`",
        f"- Adaptive average: `{summary['adaptive_average_total']}`",
        f"- Score arithmetic recomputed: `{payload['score_arithmetic_recomputed']}`",
        f"- Response generation performed: `{payload['response_generation_performed']}`",
        f"- Semantic judgment recomputed: `{payload['semantic_judgment_recomputed']}`",
        f"- Evaluator provenance status: `{payload['evaluator_provenance_status']}`",
        "",
        "This is a deterministic rerun of frozen response/rating structure and arithmetic. It is not fresh response generation or fresh semantic evaluation. The frozen record does not establish evaluator type, identity or role, count, or procedure.",
        "",
    ])


def frozen_baseline_self_check(root: Path) -> str:
    payload = build_frozen_baseline_result(root)
    if payload["summary"] != {
        "case_count": 6,
        "response_count": 12,
        "adaptive_preferred_count": 6,
        "non_adaptive_preferred_count": 0,
        "tie_count": 0,
        "non_adaptive_average_total": 18.67,
        "adaptive_average_total": 23.67,
    }:
        raise AssertionError("frozen baseline summary mismatch")
    markdown_path = root / "research" / "experiments" / "EXP-002-dataset-derived-baseline.md"
    markdown = markdown_path.read_text(encoding="utf-8")
    case_ids = [item["case_id"] for item in payload["cases"]]
    tampered = markdown.replace("  - Total: 18", "  - Total: 19", 1)
    try:
        parse_frozen_response_baseline(tampered, case_ids)
    except ValueError:
        pass
    else:
        raise AssertionError("tampered frozen score unexpectedly passed")
    return "pass"
```

- [ ] **Step 4: Add the deterministic recorder**

```python
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.exp_002_frozen_response_baseline import (
    build_frozen_baseline_result,
    render_frozen_baseline_report,
)

OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / "EXP-002-frozen-response-baseline"
RESULT = OUTPUT_DIR / "result.json"
REPORT = OUTPUT_DIR / "report.md"


def main() -> int:
    payload = build_frozen_baseline_result(ROOT)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT.write_text(render_frozen_baseline_report(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run the complete baseline gate and inspect both outputs**

```powershell
python scripts\run_exp_002_frozen_response_baseline.py
python scripts\validate_exp_002_frozen_response_baseline.py
```

Expected: both commands exit `0`; the result reports six cases, twelve frozen responses, six adaptive preferences, averages `18.67` and `23.67`, `score_arithmetic_recomputed=true`, `response_generation_performed=false`, `semantic_judgment_recomputed=false`, and `evaluator_provenance_status="not_recorded"`. Read the generated result/report directly.

- [ ] **Step 6: Commit the passing baseline prerequisite before Task 1**

```powershell
git add scripts\exp_002_frozen_response_baseline.py scripts\run_exp_002_frozen_response_baseline.py scripts\validate_exp_002_frozen_response_baseline.py research\experiments\generated\EXP-002-frozen-response-baseline
git commit -m "Make frozen EXP-002 response scoring runnable"
```

Expected: clean worktree. Task 1 is blocked unless this commit exists and `python scripts\validate_exp_002_frozen_response_baseline.py` passes.

---

### Task 1: Add The Failing Phase A Validator

**Files:**

- Create: `scripts/validate_emotion_state_001_phase_a_contracts.py`
- Test: `scripts/validate_emotion_state_001_phase_a_contracts.py`

**Interfaces:**

- Consumes: the approved spec and exact file paths in this plan.
- Produces: `validate_source()`, `validate_contracts()`, `validate_patterns()`, `validate_brain_extension()`, `validate_checkpoint()`, and `main() -> int`.

- [ ] **Step 1: Create the complete section-selectable validator**

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SOURCE_MANIFEST = ROOT / "research" / "sources" / "creative_analysis_engine" / "source_manifest.json"
SOURCE_NOTES = SOURCE_MANIFEST.with_name("source_notes.md")
DATASET_CONTRACT = ROOT / "research" / "sources" / "emotion_state" / "dataset_manifest_contract.json"
ANNOTATION_SCHEMA = DATASET_CONTRACT.with_name("annotation_record_v1.schema.json")
SPLIT_SCHEMA = DATASET_CONTRACT.with_name("split_manifest_v1.schema.json")
CODEBOOK = ROOT / "docs" / "data" / "EMOTION_STATE_001_ANNOTATION_CODEBOOK.md"
THESIS_REFERENCE_REGISTRY = ROOT / "docs" / "thesis" / "THESIS_REFERENCE_REGISTRY.md"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "emotion-state-001-phase-a-contracts.json"
RUNNER = ROOT / "scripts" / "run_emotion_state_001_phase_a_contracts.py"
RESULT = ROOT / "research" / "experiments" / "generated" / "EMOTION-STATE-001-phase-a-contracts" / "result.json"
REPORT = RESULT.with_name("report.md")
EXPECTED_ARCHIVE_SHA256 = "E579B966E226F2AF6E4F8F8203C7189FEC94FB448EFC09B4B6640C10A398ECCC"
EXPECTED_BASELINE_FINGERPRINTS = {
    "packages/prompts/baseline-non-adaptive.txt": "BB1FD1EAC0D4DE858BFDCE4A880BBF2C59C14A216489A1A85EF149F3E88D7FCA",
    "packages/prompts/baseline-adaptive.txt": "EBD4106841987CA4A322C2B8B95A33ECFFC4238BB476DEC611A640D5B000EB42",
    "research/experiments/cases/exp-002-dataset-derived.json": "882B94C0A31C41A94540941A254AC7E8119CADE9AAD9B071089E854917BDC7D6",
    "research/experiments/EXP-002-dataset-derived-baseline.md": "D930C845AC912D44610B3CE263B55EA03BFFD7CAB8706C2BC95CB17045FF1316",
    "research/experiments/generated/EXP-002/EXP-002-prompt-packet.md": "14017F985D54D2B46A338EA2EFA796B24202E3E5A3D3EB8223346CEA96E5CD09",
    "docs/thesis/EVALUATION_RUBRIC.md": "39D3CF33E38A0C13ADEE178F3DB4174D4D8E3A42B1DE4C274BF96FFA36FFB416",
}
EXPECTED_NORMALIZED_PROMPT_PACKET_SHA256 = "83DF6E5F7B3566754F7D09C78F5BBD3B013ABED328C01EF90BA68BCFF2C395FA"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> Any:
    assert_condition(path.exists(), f"missing required file: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def require_text(path: Path, markers: list[str]) -> str:
    assert_condition(path.exists(), f"missing required file: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        assert_condition(marker in text, f"{path.relative_to(ROOT)} missing marker: {marker}")
    return text


def normalized_prompt_packet_digest(path: Path) -> str:
    text = path.read_bytes().decode("utf-8")
    normalized, replacement_count = re.subn(
        r"(?m)^- Source case file: `[^`\r\n]+`(?=\r?$)",
        "- Source case file: `<normalized>`",
        text,
    )
    assert_condition(replacement_count == 1, f"expected one source-case line in {path.relative_to(ROOT)}")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest().upper()


def validate_source() -> None:
    manifest = read_json(SOURCE_MANIFEST)
    assert_condition(manifest["manifest_id"] == "creative-analysis-engine-emotion-state-source-v1", manifest)
    assert_condition(manifest["archive_sha256"] == EXPECTED_ARCHIVE_SHA256, manifest)
    assert_condition(manifest["author"] == "Shehzeb Iftakhar", manifest)
    assert_condition(manifest["permission_attestation"]["status"] == "confirmed_by_project_owner", manifest)
    assert_condition(manifest["permission_attestation"]["date"] == "2026-07-14", manifest)
    assert_condition(
        manifest["permission_attestation"]["basis"]
        == "project-owner attestation of author and supervisor approval",
        manifest,
    )
    assert_condition(manifest["permission_attestation"]["credit_required"] is True, manifest)
    assert_condition(manifest["source_repository_url"] is None, manifest)
    assert_condition(manifest["source_repository_url_status"] == "unverified", manifest)
    assert_condition(manifest["source_revision"] is None, manifest)
    assert_condition(manifest["source_revision_status"] == "unverified", manifest)
    assert_condition(manifest["source_archive_date"] is None, manifest)
    assert_condition(manifest["source_archive_date_status"] == "unverified", manifest)
    assert_condition(manifest["observed_license_status"] == "unverified_not_relied_on_for_permission", manifest)
    assert_condition(manifest["copied_material"] == [], manifest)
    assert_condition(manifest["translated_material"] == [], manifest)
    assert_condition(manifest["adapted_material"] == [], manifest)
    assert_condition(manifest["independently_reimplemented_material"] == [], manifest)
    assert_condition(manifest["project_local_only"] is True, manifest)
    assert_condition(manifest["runtime_dependency_added"] is False, manifest)
    assert_condition(manifest["attribution"]["credit_name"] == "Shehzeb Iftakhar", manifest)
    assert_condition(manifest["attribution"]["phase_a_status"] == "recorded", manifest)
    assert_condition(manifest["attribution"]["phase_b_reuse_scope_status"] == "not_defined", manifest)
    assert_condition(manifest["attribution"]["phase_b_reuse_scope"] == [], manifest)
    assert_condition(manifest["attribution"]["phase_b_attribution_wording_status"] == "pending", manifest)
    assert_condition(manifest["attribution"]["phase_b_wording"] is None, manifest)
    assert_condition(manifest["phase_b_approval"]["status"] == "not_requested", manifest)
    assert_condition(manifest["phase_b_approval"]["approved"] is False, manifest)
    assert_condition(manifest["phase_b_approval"]["approval_reference"] is None, manifest)
    assert_condition(manifest["adaptation_blockers"] == [
        "source_repository_url_unverified",
        "source_revision_or_authoritative_archive_date_unverified",
        "phase_b_reuse_scope_not_defined",
        "phase_b_attribution_wording_pending",
        "phase_b_approval_not_granted",
    ], manifest)
    expected_reviewed_files = [
        {
            "path": "src/features/temporal/speech_prosody.py",
            "reuse_status": "inspiration_only",
            "phase_a_action": "reviewed_no_code_adapted",
        },
        {
            "path": "src/features/temporal/speech_turn_dynamics.py",
            "reuse_status": "inspiration_only",
            "phase_a_action": "reviewed_no_code_adapted",
        },
        {
            "path": "src/aggregation/speech_call_readiness.py",
            "reuse_status": "excluded_from_emotion_labels",
            "phase_a_action": "reviewed_no_code_adapted",
        },
    ]
    assert_condition(manifest["reviewed_files"] == expected_reviewed_files, manifest)
    if manifest["source_repository_url_status"] != "verified":
        assert_condition(manifest["source_repository_url"] is None, manifest)
        assert_condition(manifest["adaptation_allowed"] is False, manifest)
    if manifest["source_revision_status"] != "verified" and manifest["source_archive_date_status"] != "verified":
        assert_condition(manifest["source_revision"] is None, manifest)
        assert_condition(manifest["source_archive_date"] is None, manifest)
        assert_condition(manifest["adaptation_allowed"] is False, manifest)
    derived_adaptation_allowed = all([
        manifest["source_repository_url_status"] == "verified",
        manifest["source_revision_status"] == "verified" or manifest["source_archive_date_status"] == "verified",
        manifest["attribution"]["phase_b_reuse_scope_status"] == "approved",
        bool(manifest["attribution"]["phase_b_reuse_scope"]),
        manifest["attribution"]["phase_b_attribution_wording_status"] == "recorded",
        isinstance(manifest["attribution"]["phase_b_wording"], str) and bool(manifest["attribution"]["phase_b_wording"].strip()),
        manifest["phase_b_approval"]["status"] == "approved",
        manifest["phase_b_approval"]["approved"] is True,
        isinstance(manifest["phase_b_approval"]["approval_reference"], str) and bool(manifest["phase_b_approval"]["approval_reference"].strip()),
    ])
    assert_condition(manifest["adaptation_allowed"] is derived_adaptation_allowed, manifest)
    dataset_contract = read_json(DATASET_CONTRACT)
    assert_condition(dataset_contract["schema_id"] == "emotion-state-dataset-manifest-v1", dataset_contract)
    assert_condition(set(dataset_contract["required_fields"]) == {
        "dataset_id", "canonical_source_url", "release_or_version", "accessed_on",
        "terms_or_license", "access_restrictions", "local_file_hashes", "source_label",
        "source_labels", "project_label_mapping", "excluded_labels", "language", "domain",
        "domain_limitations", "permitted_research_lanes", "redistribution_status",
    }, dataset_contract)
    assert_condition(set(dataset_contract["allowed_source_labels"]) == {
        "public-only", "private-restricted", "mixed-source", "synthetic-only",
    }, dataset_contract)
    assert_condition(dataset_contract["selected_public_datasets"] == [], dataset_contract)
    assert_condition(dataset_contract["runtime_influence_allowed"] is False, dataset_contract)
    assert_condition(dataset_contract["domain_boundary"] == "acted_and_non_sales_corpora_support_offline_thesis_comparison_only", dataset_contract)
    annotation_schema = read_json(ANNOTATION_SCHEMA)
    from scripts.emotion_state_annotation_contracts import (
        ANNOTATION_FIELDS,
        DEPENDENCY_GROUP_FIELDS,
        NOT_INFERABLE_REASONS,
        OPERATIONAL_SIGNALS,
        SPLIT_MANIFEST_FIELDS,
        annotation_contract_self_check,
    )

    assert_condition(annotation_schema["schema_id"] == "emotion-state-annotation-record-v1", annotation_schema)
    assert_condition(set(annotation_schema["required_fields"]) == ANNOTATION_FIELDS, annotation_schema)
    assert_condition(set(annotation_schema["dependency_group_fields"]) == DEPENDENCY_GROUP_FIELDS, annotation_schema)
    assert_condition(set(annotation_schema["allowed_operational_signals"]) == OPERATIONAL_SIGNALS, annotation_schema)
    assert_condition(set(annotation_schema["allowed_evidence_classes"]) == {
        "direct_explicit", "observer_inference", "not_inferable",
    }, annotation_schema)
    assert_condition(set(annotation_schema["allowed_reviewer_confidence"]) == {
        "low", "medium", "high",
    }, annotation_schema)
    assert_condition(set(annotation_schema["allowed_not_inferable_reason_codes"]) == NOT_INFERABLE_REASONS, annotation_schema)
    assert_condition(annotation_schema["reviewers_per_turn"] == 3, annotation_schema)
    assert_condition(annotation_schema["valence_scale"] == [-2, -1, 0, 1, 2], annotation_schema)
    assert_condition(annotation_schema["activation_scale"] == [1, 2, 3, 4, 5], annotation_schema)
    assert_condition(annotation_schema["engagement_scale"] == [1, 2, 3, 4, 5], annotation_schema)
    assert_condition(annotation_schema["not_inferable_excludes_other_labels"] is True, annotation_schema)
    assert_condition(annotation_schema["unrestricted_transcript_quotes_allowed"] is False, annotation_schema)
    assert_condition(
        annotation_schema["explicit_statement_reference_format"]
        == "evidence:uuid:<canonical-lowercase-uuid-v4>",
        annotation_schema,
    )
    assert_condition(annotation_schema["runtime_influence_allowed"] is False, annotation_schema)
    split_schema = read_json(SPLIT_SCHEMA)
    assert_condition(split_schema["schema_id"] == "emotion-state-split-manifest-v1", split_schema)
    assert_condition(set(split_schema["required_fields"]) == SPLIT_MANIFEST_FIELDS, split_schema)
    assert_condition(set(split_schema["dependency_keys"]) == DEPENDENCY_GROUP_FIELDS, split_schema)
    assert_condition(split_schema["runtime_influence_allowed"] is False, split_schema)
    assert_condition(split_schema["training_discovery"]["case_ids"] == [], split_schema)
    assert_condition(split_schema["calibration"]["case_ids"] == [], split_schema)
    assert_condition(split_schema["balanced_diagnostic"]["case_ids"] == [], split_schema)
    assert_condition(split_schema["final_lockbox"]["open_count"] == 0, split_schema)
    assert_condition(split_schema["final_lockbox"]["case_ids"] == [], split_schema)
    for partition_name in ("training_discovery", "calibration", "balanced_diagnostic", "final_lockbox"):
        groups = split_schema[partition_name]["dependency_groups"]
        assert_condition(set(groups) == DEPENDENCY_GROUP_FIELDS, groups)
        assert_condition(all(identifiers == [] for identifiers in groups.values()), groups)
    require_text(SOURCE_NOTES, ["inspiration only", "source_repository_url_unverified", "No code was copied"])
    require_text(CODEBOOK, [
        "not_inferable", "ambiguous", "Krippendorff", "three independent reviewers",
        "practice set", "`none` means", "abstention-policy error", "redacted, nonreversible",
        "evidence:uuid:", "Retain reviewer-level disagreement", "Derive every split dependency summary",
    ])
    require_text(ROOT / "docs" / "third-party-inspirations.md", ["Creative Analysis Engine", "research/sources/creative_analysis_engine/source_manifest.json"])
    require_text(THESIS_REFERENCE_REGISTRY, [
        "https://sail.usc.edu/iemocap/",
        "https://ecs.utdallas.edu/research/researchlabs/msp-lab/MSP-Podcast.html",
        "https://onlinelibrary.wiley.com/doi/10.1111/j.1468-2958.2004.tb00738.x",
        "https://airc.nist.gov/airmf-resources/airmf/5-sec-core/",
    ])
    assert_condition(annotation_contract_self_check() == "pass", "annotation contract self-check failed")


def validate_contracts() -> None:
    case = read_json(CASE_PATH)
    assert_condition(case["checkpoint_id"] == "EMOTION-STATE-001-phase-a-contracts", case)
    assert_condition(case["source_label"] == "synthetic-only", case)
    assert_condition(case["selected_public_datasets"] == [], case)
    assert_condition(case["private_data_access_allowed"] is False, case)
    assert_condition(case["provider_operations_allowed"] is False, case)
    assert_condition(case["runtime_behavior_change_allowed"] is False, case)
    assert_condition(case["runtime_activation_allowed"] is False, case)
    assert_condition(case["baseline_fingerprints"] == EXPECTED_BASELINE_FINGERPRINTS, case)
    from runtime.contracts.emotion_state_contracts import contract_self_check

    assert_condition(contract_self_check() == "pass", "emotion-state contract self-check failed")


def validate_patterns() -> None:
    from runtime.contracts.emotion_pattern_contracts import pattern_contract_self_check

    assert_condition(pattern_contract_self_check() == "pass", "pattern contract self-check failed")


def validate_brain_extension() -> None:
    from runtime.contracts.emotion_state_brain_extension import brain_extension_self_check

    assert_condition(brain_extension_self_check() == "pass", "BRAIN extension self-check failed")
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_brain_002_runtime_state_schema.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert_condition(completed.returncode == 0, completed.stdout + completed.stderr)


def validate_checkpoint() -> None:
    assert_condition(RUNNER.exists(), f"missing runner: {RUNNER.relative_to(ROOT)}")
    baseline_gate = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_exp_002_frozen_response_baseline.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert_condition(baseline_gate.returncode == 0, baseline_gate.stdout + baseline_gate.stderr)
    from scripts.run_emotion_state_001_phase_a_contracts import (
        DEFAULT_CASE as RUNNER_DEFAULT_CASE,
        DEFAULT_OUTPUT_DIR as RUNNER_DEFAULT_OUTPUT_DIR,
        resolve_project_path,
    )

    assert_condition(
        resolve_project_path(str(RUNNER_DEFAULT_CASE), allowed_root=RUNNER_DEFAULT_CASE.parent)
        == RUNNER_DEFAULT_CASE.resolve(strict=False),
        "runner rejected its fixed case path",
    )
    for blocked_path in (
        ROOT.parent / "outside-result.json",
        ROOT / "runtime" / "overwrite-result.json",
        ROOT / "data" / "private" / "blocked-result.json",
    ):
        try:
            resolve_project_path(str(blocked_path), allowed_root=RUNNER_DEFAULT_OUTPUT_DIR)
        except ValueError:
            pass
        else:
            raise AssertionError(f"runner accepted blocked output path: {blocked_path}")
    completed = subprocess.run(
        [sys.executable, str(RUNNER)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert_condition(completed.returncode == 0, completed.stdout + completed.stderr)
    result = read_json(RESULT)
    report = require_text(REPORT, [
        "EMOTION-STATE-001", "offline", "all of Phase A is complete",
        "Per-public-dataset manifests remain open", "Live aggregate release remains blocked",
        "Runtime activation remains blocked",
    ])
    assert_condition(result["checkpoint_id"] == "EMOTION-STATE-001-phase-a-contracts", result)
    assert_condition(result["archive_sha256"] == EXPECTED_ARCHIVE_SHA256, result)
    assert_condition(
        result["status"] == "contract_artifact_validation_only_source_dataset_and_privacy_gates_open",
        result,
    )
    assert_condition(result["summary"]["provider_operations_performed_by_runner"] is False, result)
    assert_condition(result["summary"]["private_data_read_by_runner"] is False, result)
    assert_condition(result["summary"]["runtime_behavior_changed_by_runner"] is False, result)
    assert_condition(result["summary"]["code_adaptation_started"] is False, result)
    assert_condition(result["summary"]["runtime_activation_allowed"] is False, result)
    assert_condition(result["summary"]["source_adaptation_allowed"] is False, result)
    assert_condition(result["readiness_boundary"] == {
        "phase_a_contract_artifacts_built": True,
        "phase_a_complete": False,
        "full_repository_gate_claimed_by_this_artifact": False,
        "live_aggregate_release_unblocked": False,
        "phase_b_unblocked": False,
        "public_dataset_evaluation_unblocked": False,
        "private_research_unblocked": False,
        "provider_feasibility_unblocked": False,
        "runtime_activation_unblocked": False,
    }, result)
    expected_checks = {
        "exp_002_frozen_response_baseline",
        "emotion_state_annotation_contracts",
        "emotion_state_contracts",
        "emotion_pattern_contracts",
        "emotion_state_brain_extension",
    }
    assert_condition(set(result["summary"]["contract_checks"]) == expected_checks, result)
    assert_condition(set(result["summary"]["contract_checks"].values()) == {"pass"}, result)
    assert_condition(result["summary"]["contract_check_count"] == len(expected_checks), result)
    assert_condition(result["baseline_fingerprints"] == EXPECTED_BASELINE_FINGERPRINTS, result)
    assert_condition(all(
        isinstance(digest, str) and len(digest) == 64 and all(character in "0123456789ABCDEF" for character in digest)
        for digest in result["baseline_fingerprints"].values()
    ), result)
    assert_condition("production ready" not in report.lower(), "report overclaims readiness")
    rendered_packet = ROOT / ".tmp" / "emotion-state-001" / "EXP-002-prompt-packet.md"
    baseline_run = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_prompt_baseline.py"),
            "--cases",
            str(ROOT / "research" / "experiments" / "cases" / "exp-002-dataset-derived.json"),
            "--out",
            str(rendered_packet),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert_condition(baseline_run.returncode == 0, baseline_run.stdout + baseline_run.stderr)
    tracked_packet = ROOT / "research" / "experiments" / "generated" / "EXP-002" / "EXP-002-prompt-packet.md"
    assert_condition(
        normalized_prompt_packet_digest(tracked_packet) == EXPECTED_NORMALIZED_PROMPT_PACKET_SHA256,
        "tracked EXP-002 normalized prompt packet drifted from the frozen baseline",
    )
    assert_condition(
        normalized_prompt_packet_digest(rendered_packet) == EXPECTED_NORMALIZED_PROMPT_PACKET_SHA256,
        "EXP-002 normalized prompt packet drifted",
    )


SECTIONS: dict[str, Callable[[], None]] = {
    "source": validate_source,
    "contracts": validate_contracts,
    "patterns": validate_patterns,
    "brain": validate_brain_extension,
    "checkpoint": validate_checkpoint,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate EMOTION-STATE-001 Phase A contracts.")
    parser.add_argument("--section", choices=["all", *SECTIONS], default="all")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selected = SECTIONS.values() if args.section == "all" else [SECTIONS[args.section]]
    try:
        for validator in selected:
            validator()
    except (AssertionError, KeyError, ValueError) as exc:
        print(f"EMOTION-STATE-001 Phase A validation failed: {exc}")
        return 1
    print(f"EMOTION-STATE-001 Phase A validation passed: {args.section}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run the validator and prove the red gate**

```powershell
python scripts\validate_emotion_state_001_phase_a_contracts.py --section source
```

Expected: exit `1` with `missing required file: research\sources\creative_analysis_engine\source_manifest.json`. It must not fail with a syntax/import error.

- [ ] **Step 3: Commit the red gate**

```powershell
git add scripts\validate_emotion_state_001_phase_a_contracts.py
git commit -m "Add EMOTION-STATE Phase A red gate"
```

---

### Task 2: Establish Provenance, Reprioritization, And Annotation Rules

**Files:**

- Create: `research/sources/creative_analysis_engine/source_manifest.json`
- Create: `research/sources/creative_analysis_engine/source_notes.md`
- Create: `research/sources/emotion_state/dataset_manifest_contract.json`
- Create: `research/sources/emotion_state/annotation_record_v1.schema.json`
- Create: `research/sources/emotion_state/split_manifest_v1.schema.json`
- Create: `scripts/emotion_state_annotation_contracts.py`
- Create: `docs/data/EMOTION_STATE_001_ANNOTATION_CODEBOOK.md`
- Modify: `docs/third-party-inspirations.md`
- Modify: `docs/thesis/THESIS_REFERENCE_REGISTRY.md`
- Modify: `docs/thesis/ROADMAP.md:30-46`
- Test: `scripts/validate_emotion_state_001_phase_a_contracts.py::validate_source`

**Interfaces:**

- Consumes: archive metadata, user-attested permission, and approved label rules.
- Produces: immutable source ledger plus a fail-closed dataset and annotation boundary. Phase B consumes these only after the repository URL/revision gate is verified and a separate Phase B review is approved.

- [ ] **Step 1: Add the source manifest with the unresolved origin recorded honestly**

```json
{
  "manifest_id": "creative-analysis-engine-emotion-state-source-v1",
  "manifest_version": 1,
  "checked_on": "2026-07-14",
  "project_name": "Creative Analysis Engine",
  "author": "Shehzeb Iftakhar",
  "archive_filename": "creative-analysis-engine-dev.zip",
  "archive_sha256": "E579B966E226F2AF6E4F8F8203C7189FEC94FB448EFC09B4B6640C10A398ECCC",
  "source_repository_url": null,
  "source_repository_url_status": "unverified",
  "source_revision": null,
  "source_revision_status": "unverified",
  "source_archive_date": null,
  "source_archive_date_status": "unverified",
  "observed_license": null,
  "observed_license_status": "unverified_not_relied_on_for_permission",
  "permission_attestation": {
    "status": "confirmed_by_project_owner",
    "date": "2026-07-14",
    "basis": "project-owner attestation of author and supervisor approval",
    "credit_required": true
  },
  "attribution": {
    "credit_name": "Shehzeb Iftakhar",
    "project_name": "Creative Analysis Engine",
    "phase_a_status": "recorded",
    "phase_a_wording": "Creative Analysis Engine by Shehzeb Iftakhar, reviewed with author permission for the EMOTION-STATE thesis collaboration.",
    "phase_b_reuse_scope_status": "not_defined",
    "phase_b_reuse_scope": [],
    "phase_b_attribution_wording_status": "pending",
    "phase_b_wording": null
  },
  "phase_b_approval": {
    "status": "not_requested",
    "approved": false,
    "approval_reference": null
  },
  "reviewed_files": [
    {
      "path": "src/features/temporal/speech_prosody.py",
      "reuse_status": "inspiration_only",
      "phase_a_action": "reviewed_no_code_adapted"
    },
    {
      "path": "src/features/temporal/speech_turn_dynamics.py",
      "reuse_status": "inspiration_only",
      "phase_a_action": "reviewed_no_code_adapted"
    },
    {
      "path": "src/aggregation/speech_call_readiness.py",
      "reuse_status": "excluded_from_emotion_labels",
      "phase_a_action": "reviewed_no_code_adapted"
    }
  ],
  "copied_material": [],
  "translated_material": [],
  "adapted_material": [],
  "independently_reimplemented_material": [],
  "project_local_only": true,
  "runtime_dependency_added": false,
  "adaptation_allowed": false,
  "adaptation_blockers": [
    "source_repository_url_unverified",
    "source_revision_or_authoritative_archive_date_unverified",
    "phase_b_reuse_scope_not_defined",
    "phase_b_attribution_wording_pending",
    "phase_b_approval_not_granted"
  ]
}
```

When Tarik supplies the exact URL, update this immutable manifest through a new reviewed commit; do not rewrite history or infer the revision from the ZIP directory name.

- [ ] **Step 2: Add source notes and the canonical inspiration entry**

`source_notes.md` must state exactly:

```markdown
# Creative Analysis Engine Source Notes

- Current reuse label: `inspiration only`.
- Exact source status: `source_repository_url_unverified`.
- Permission basis: project-owner attestation of author and supervisor approval, dated `2026-07-14`.
- No code was copied, translated, adapted, or independently reimplemented in EMOTION-STATE Phase A.
- `speech_prosody.py` and `speech_turn_dynamics.py` were reviewed for future bounded adaptation.
- `speech_call_readiness.py` and `emotion_readiness_comparison_score` must not become customer-emotion labels.
- Phase B remains blocked by `source_repository_url_unverified`, `source_revision_or_authoritative_archive_date_unverified`, `phase_b_reuse_scope_not_defined`, `phase_b_attribution_wording_pending`, and `phase_b_approval_not_granted`. Record an observed license if available, but do not treat it as replacing or reopening the approved author-permission basis.
```

Add a `## Creative Analysis Engine / Shehzeb Iftakhar` entry to `docs/third-party-inspirations.md` using the existing entry shape: Source, observed license, checked date, reuse label, learned/adapted, copied material, affected files, runtime boundary, privacy notes, and follow-up. Link `research/sources/creative_analysis_engine/source_manifest.json`; state that the URL and license metadata are unverified, author permission is confirmed and is not a blocker, and no code was copied.

- [ ] **Step 2a: Register only the four references introduced by the approved design**

Update `docs/thesis/THESIS_REFERENCE_REGISTRY.md` using its existing source-entry shape:

- add `https://sail.usc.edu/iemocap/` as the exact IEMOCAP landing URL alongside the already registered IEMOCAP pages;
- add `https://ecs.utdallas.edu/research/researchlabs/msp-lab/MSP-Podcast.html` as an offline dataset candidate whose exact version, terms, restrictions, access conditions, and local hashes remain unverified; this does not select the dataset or satisfy the per-dataset manifest gate;
- add `https://onlinelibrary.wiley.com/doi/10.1111/j.1468-2958.2004.tb00738.x` as reliability-method guidance, not evidence that the planned labels are valid; and
- add `https://airc.nist.gov/airmf-resources/airmf/5-sec-core/` as AI-risk governance guidance, not proof of legal, ethical, or production readiness.

Do not register or edit the eight unrelated Atlas/ElevenLabs references in this task. The source-section validator must require these four exact URLs, and the repository-wide reference guard must be green before Task 7 can close.

- [ ] **Step 3: Add the dataset-manifest contract without speculative datasets**

```json
{
  "schema_id": "emotion-state-dataset-manifest-v1",
  "schema_version": 1,
  "required_fields": [
    "dataset_id",
    "canonical_source_url",
    "release_or_version",
    "accessed_on",
    "terms_or_license",
    "access_restrictions",
    "local_file_hashes",
    "source_label",
    "source_labels",
    "project_label_mapping",
    "excluded_labels",
    "language",
    "domain",
    "domain_limitations",
    "permitted_research_lanes",
    "redistribution_status"
  ],
  "allowed_source_labels": ["public-only", "private-restricted", "mixed-source", "synthetic-only"],
  "selected_public_datasets": [],
  "domain_boundary": "acted_and_non_sales_corpora_support_offline_thesis_comparison_only",
  "runtime_influence_allowed": false,
  "notes": "Create one immutable manifest per dataset only after exact source, version, terms, restrictions, and local hashes are verified."
}
```

- [ ] **Step 4: Add reviewer-record and split-manifest contracts without creating data records**

`annotation_record_v1.schema.json` is a project contract, not a populated annotation file:

```json
{
  "schema_id": "emotion-state-annotation-record-v1",
  "schema_version": 1,
  "record_scope": "one_reviewer_one_turn",
  "required_fields": [
    "annotation_record_id",
    "dataset_manifest_id",
    "turn_id",
    "dependency_group_ids",
    "reviewer_id",
    "reviewer_round",
    "valence",
    "activation",
    "engagement",
    "operational_signals",
    "reviewer_confidence",
    "not_inferable",
    "not_inferable_reason_code",
    "evidence_class",
    "explicit_statement_reference"
  ],
  "dependency_group_fields": ["speaker", "call_session", "dialogue_dyad", "source_corpus", "scripted_scenario"],
  "valence_scale": [-2, -1, 0, 1, 2],
  "activation_scale": [1, 2, 3, 4, 5],
  "engagement_scale": [1, 2, 3, 4, 5],
  "allowed_operational_signals": ["hesitation", "frustration", "confusion", "interest", "disengagement"],
  "allowed_evidence_classes": ["direct_explicit", "observer_inference", "not_inferable"],
  "allowed_reviewer_confidence": ["low", "medium", "high"],
  "allowed_not_inferable_reason_codes": ["unusable_audio", "insufficient_context", "contradictory_evidence", "other_codebook_reason"],
  "reviewers_per_turn": 3,
  "not_inferable_excludes_other_labels": true,
  "unrestricted_transcript_quotes_allowed": false,
  "explicit_statement_reference_format": "evidence:uuid:<canonical-lowercase-uuid-v4>",
  "runtime_influence_allowed": false
}
```

`split_manifest_v1.schema.json` freezes the later dependency boundary while containing no dataset or case allocation:

```json
{
  "schema_id": "emotion-state-split-manifest-v1",
  "schema_version": 1,
  "required_fields": [
    "manifest_id",
    "dataset_manifest_ids",
    "highest_dependency_unit",
    "dependency_keys",
    "training_discovery",
    "calibration",
    "balanced_diagnostic",
    "final_lockbox",
    "frozen_candidate_family_digest",
    "runtime_influence_allowed"
  ],
  "dependency_keys": ["speaker", "call_session", "dialogue_dyad", "source_corpus", "scripted_scenario"],
  "training_discovery": {
    "case_ids": [],
    "dependency_groups": {"speaker": [], "call_session": [], "dialogue_dyad": [], "source_corpus": [], "scripted_scenario": []}
  },
  "calibration": {
    "case_ids": [],
    "dependency_groups": {"speaker": [], "call_session": [], "dialogue_dyad": [], "source_corpus": [], "scripted_scenario": []},
    "prevalence_representative": true
  },
  "balanced_diagnostic": {
    "case_ids": [],
    "dependency_groups": {"speaker": [], "call_session": [], "dialogue_dyad": [], "source_corpus": [], "scripted_scenario": []},
    "calibration_claims_allowed": false
  },
  "final_lockbox": {
    "case_ids": [],
    "dependency_groups": {"speaker": [], "call_session": [], "dialogue_dyad": [], "source_corpus": [], "scripted_scenario": []},
    "prevalence_representative": true,
    "one_use_only": true,
    "open_count": 0
  },
  "frozen_candidate_family_digest": null,
  "runtime_influence_allowed": false,
  "notes": "This is an unpopulated Phase A contract. Selecting data or assigning cases requires a later reviewed phase."
}
```

A populated split manifest is valid only when `validate_split_manifest(payload, annotation_records)` receives the complete immutable three-reviewer records for every allocated case. The validator derives each case's speaker/call/dyad/corpus/scenario groups from those records, requires the stored partition summaries to match exactly, and then checks cross-partition leakage. Declared dependency summaries are never trusted by themselves.

- [ ] **Step 5: Implement executable reviewer validation and three-reviewer aggregation**

Create `scripts/emotion_state_annotation_contracts.py` with no I/O, provider, or model dependency:

```python
from __future__ import annotations

import re
from statistics import median
from typing import Any

ANNOTATION_FIELDS = frozenset({
    "annotation_record_id", "dataset_manifest_id", "turn_id", "dependency_group_ids",
    "reviewer_id", "reviewer_round", "valence", "activation", "engagement",
    "operational_signals", "reviewer_confidence", "not_inferable",
    "not_inferable_reason_code", "evidence_class", "explicit_statement_reference",
})
DEPENDENCY_GROUP_FIELDS = frozenset({
    "speaker", "call_session", "dialogue_dyad", "source_corpus", "scripted_scenario",
})
SPLIT_MANIFEST_FIELDS = frozenset({
    "manifest_id", "dataset_manifest_ids", "highest_dependency_unit", "dependency_keys",
    "training_discovery", "calibration", "balanced_diagnostic", "final_lockbox",
    "frozen_candidate_family_digest", "runtime_influence_allowed",
})
PARTITION_FIELDS = {
    "training_discovery": frozenset({"case_ids", "dependency_groups"}),
    "calibration": frozenset({"case_ids", "dependency_groups", "prevalence_representative"}),
    "balanced_diagnostic": frozenset({"case_ids", "dependency_groups", "calibration_claims_allowed"}),
    "final_lockbox": frozenset({"case_ids", "dependency_groups", "prevalence_representative", "one_use_only", "open_count"}),
}
OPERATIONAL_SIGNALS = frozenset({
    "hesitation", "frustration", "confusion", "interest", "disengagement",
})
NOT_INFERABLE_REASONS = frozenset({
    "unusable_audio", "insufficient_context", "contradictory_evidence", "other_codebook_reason",
})
OPAQUE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}$")
EVIDENCE_REFERENCE_PATTERN = re.compile(
    r"^evidence:uuid:[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


class AnnotationContractError(ValueError):
    pass


def _require_opaque_id(value: Any, field: str) -> None:
    if not isinstance(value, str) or OPAQUE_ID_PATTERN.fullmatch(value) is None:
        raise AnnotationContractError(f"{field} must be a bounded opaque identifier, not free text")


def _require_evidence_reference(value: Any, field: str) -> None:
    if not isinstance(value, str) or EVIDENCE_REFERENCE_PATTERN.fullmatch(value) is None:
        raise AnnotationContractError(
            f"{field} must be a typed content-independent evidence UUID, not transcript text"
        )


def validate_annotation_record(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise AnnotationContractError("annotation record must be an object")
    if set(payload) != ANNOTATION_FIELDS:
        raise AnnotationContractError("annotation record fields mismatch")
    for field in ("annotation_record_id", "dataset_manifest_id", "turn_id", "reviewer_id"):
        _require_opaque_id(payload[field], field)
    if type(payload["reviewer_round"]) is not int or payload["reviewer_round"] < 1:
        raise AnnotationContractError("reviewer_round must be a positive integer")
    groups = payload["dependency_group_ids"]
    if not isinstance(groups, dict) or set(groups) != DEPENDENCY_GROUP_FIELDS:
        raise AnnotationContractError("dependency_group_ids fields mismatch")
    if groups["speaker"] is None or groups["source_corpus"] is None:
        raise AnnotationContractError("speaker and source_corpus dependency groups are required")
    for field, value in groups.items():
        if value is not None:
            _require_opaque_id(value, f"dependency_group_ids.{field}")
    signals = payload["operational_signals"]
    if not isinstance(signals, list) or any(not isinstance(signal, str) for signal in signals):
        raise AnnotationContractError("operational_signals must be a string list")
    if len(signals) != len(set(signals)):
        raise AnnotationContractError("operational_signals must be a unique list")
    if any(signal not in OPERATIONAL_SIGNALS for signal in signals):
        raise AnnotationContractError("operational_signals contains an unknown label")
    if payload["reviewer_confidence"] not in {"low", "medium", "high"}:
        raise AnnotationContractError("reviewer_confidence is invalid")
    if type(payload["not_inferable"]) is not bool:
        raise AnnotationContractError("not_inferable must be boolean")

    dimensions = (payload["valence"], payload["activation"], payload["engagement"])
    if payload["not_inferable"]:
        if dimensions != (None, None, None) or signals:
            raise AnnotationContractError("not_inferable excludes dimensional and operational labels")
        if payload["not_inferable_reason_code"] not in NOT_INFERABLE_REASONS:
            raise AnnotationContractError("not_inferable requires an enumerated reason")
        if payload["evidence_class"] != "not_inferable" or payload["explicit_statement_reference"] is not None:
            raise AnnotationContractError("not_inferable evidence fields are inconsistent")
        return payload

    if type(payload["valence"]) is not int or payload["valence"] not in {-2, -1, 0, 1, 2}:
        raise AnnotationContractError("valence must use the frozen five-point ordinal scale")
    for field in ("activation", "engagement"):
        if type(payload[field]) is not int or payload[field] not in {1, 2, 3, 4, 5}:
            raise AnnotationContractError(f"{field} must use the frozen five-point ordinal scale")
    if payload["not_inferable_reason_code"] is not None:
        raise AnnotationContractError("inferable records cannot carry an abstention reason")
    if payload["evidence_class"] not in {"direct_explicit", "observer_inference"}:
        raise AnnotationContractError("inferable evidence_class is invalid")
    reference = payload["explicit_statement_reference"]
    if payload["evidence_class"] == "direct_explicit":
        _require_evidence_reference(reference, "explicit_statement_reference")
    elif reference is not None:
        raise AnnotationContractError("observer inference cannot carry an explicit-statement reference")
    return payload


def _require_unique_opaque_list(value: Any, field: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise AnnotationContractError(f"{field} must be a list")
    for item in value:
        _require_opaque_id(item, field)
    if len(value) != len(set(value)):
        raise AnnotationContractError(f"{field} must be unique")
    return value


def validate_split_manifest(
    payload: dict[str, Any],
    annotation_records: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != SPLIT_MANIFEST_FIELDS:
        raise AnnotationContractError("split manifest fields mismatch")
    _require_opaque_id(payload["manifest_id"], "manifest_id")
    _require_unique_opaque_list(payload["dataset_manifest_ids"], "dataset_manifest_ids", allow_empty=False)
    if payload["runtime_influence_allowed"] is not False:
        raise AnnotationContractError("split manifests cannot influence runtime")
    if (
        not isinstance(payload["dependency_keys"], list)
        or set(payload["dependency_keys"]) != DEPENDENCY_GROUP_FIELDS
        or len(payload["dependency_keys"]) != len(DEPENDENCY_GROUP_FIELDS)
    ):
        raise AnnotationContractError("dependency_keys must contain the frozen dependency dimensions")
    if payload["highest_dependency_unit"] not in DEPENDENCY_GROUP_FIELDS:
        raise AnnotationContractError("highest_dependency_unit is invalid")
    digest = payload["frozen_candidate_family_digest"]
    if not isinstance(digest, str) or re.fullmatch(r"[0-9A-F]{64}", digest) is None:
        raise AnnotationContractError("frozen_candidate_family_digest must be an uppercase SHA-256")

    if not isinstance(annotation_records, list) or not annotation_records:
        raise AnnotationContractError("split validation requires immutable reviewer records")
    records_by_turn: dict[str, list[dict[str, Any]]] = {}
    for record in annotation_records:
        validated = validate_annotation_record(record)
        records_by_turn.setdefault(validated["turn_id"], []).append(validated)
    case_dependencies: dict[str, dict[str, str | None]] = {}
    case_dataset_manifest_ids: set[str] = set()
    for turn_id, records in records_by_turn.items():
        aggregate_three_reviewer_labels(records)
        case_dependencies[turn_id] = dict(records[0]["dependency_group_ids"])
        case_dataset_manifest_ids.add(records[0]["dataset_manifest_id"])

    if set(payload["dataset_manifest_ids"]) != case_dataset_manifest_ids:
        raise AnnotationContractError("split dataset manifests do not match the supplied reviewer records")

    manifest_case_ids: set[str] = set()
    seen_cases: set[str] = set()
    seen_groups = {key: set() for key in DEPENDENCY_GROUP_FIELDS}
    for partition_name, expected_fields in PARTITION_FIELDS.items():
        partition = payload[partition_name]
        if not isinstance(partition, dict) or set(partition) != expected_fields:
            raise AnnotationContractError(f"{partition_name} fields mismatch")
        case_ids = _require_unique_opaque_list(partition["case_ids"], f"{partition_name}.case_ids")
        if any(case_id not in case_dependencies for case_id in case_ids):
            raise AnnotationContractError(f"{partition_name} references a case without reviewer records")
        overlap = seen_cases & set(case_ids)
        if overlap:
            raise AnnotationContractError(f"case leakage across partitions: {sorted(overlap)}")
        seen_cases.update(case_ids)
        manifest_case_ids.update(case_ids)
        groups = partition["dependency_groups"]
        if not isinstance(groups, dict) or set(groups) != DEPENDENCY_GROUP_FIELDS:
            raise AnnotationContractError(f"{partition_name}.dependency_groups fields mismatch")
        derived_groups = {
            dependency_key: sorted({
                case_dependencies[case_id][dependency_key]
                for case_id in case_ids
                if case_dependencies[case_id][dependency_key] is not None
            })
            for dependency_key in DEPENDENCY_GROUP_FIELDS
        }
        if groups != derived_groups:
            raise AnnotationContractError(
                f"{partition_name}.dependency_groups do not match immutable reviewer records"
            )
        for dependency_key, identifiers in groups.items():
            identifiers = _require_unique_opaque_list(
                identifiers,
                f"{partition_name}.dependency_groups.{dependency_key}",
            )
            dependency_overlap = seen_groups[dependency_key] & set(identifiers)
            if dependency_overlap:
                raise AnnotationContractError(
                    f"{dependency_key} leakage across partitions: {sorted(dependency_overlap)}"
                )
            seen_groups[dependency_key].update(identifiers)
        if case_ids and not groups[payload["highest_dependency_unit"]]:
            raise AnnotationContractError(f"{partition_name} lacks its highest dependency groups")

    if manifest_case_ids != set(case_dependencies):
        raise AnnotationContractError("split cases must exactly match the supplied reviewer records")

    if payload["calibration"]["prevalence_representative"] is not True:
        raise AnnotationContractError("calibration must preserve prevalence")
    if payload["balanced_diagnostic"]["calibration_claims_allowed"] is not False:
        raise AnnotationContractError("balanced diagnostic data cannot support calibration claims")
    lockbox = payload["final_lockbox"]
    if lockbox["prevalence_representative"] is not True or lockbox["one_use_only"] is not True:
        raise AnnotationContractError("final lockbox controls are invalid")
    if type(lockbox["open_count"]) is not int or lockbox["open_count"] not in {0, 1}:
        raise AnnotationContractError("final lockbox may be opened at most once")
    return payload


def _empty_consensus(turn_id: str, status: str, not_inferable_count: int) -> dict[str, Any]:
    return {
        "turn_id": turn_id,
        "label_status": status,
        "valence": None,
        "activation": None,
        "engagement": None,
        "operational_signals": [],
        "none_selected": False,
        "reviewer_count": 3,
        "not_inferable_count": not_inferable_count,
    }


def aggregate_three_reviewer_labels(records: list[dict[str, Any]]) -> dict[str, Any]:
    if len(records) != 3:
        raise AnnotationContractError("exactly three reviewer records are required")
    validated = [validate_annotation_record(record) for record in records]
    for field in ("dataset_manifest_id", "turn_id", "reviewer_round"):
        if len({record[field] for record in validated}) != 1:
            raise AnnotationContractError(f"review records disagree on {field}")
    if any(record["dependency_group_ids"] != validated[0]["dependency_group_ids"] for record in validated[1:]):
        raise AnnotationContractError("review records disagree on dependency_group_ids")
    if len({record["reviewer_id"] for record in validated}) != 3:
        raise AnnotationContractError("reviewers must be distinct")
    if len({record["annotation_record_id"] for record in validated}) != 3:
        raise AnnotationContractError("annotation records must be distinct")

    turn_id = validated[0]["turn_id"]
    not_inferable = [record for record in validated if record["not_inferable"]]
    inferable = [record for record in validated if not record["not_inferable"]]
    if len(not_inferable) >= 2:
        return _empty_consensus(turn_id, "not_inferable", len(not_inferable))
    if len(not_inferable) == 1:
        first, second = inferable
        first_labels = (
            first["valence"], first["activation"], first["engagement"],
            frozenset(first["operational_signals"]),
        )
        second_labels = (
            second["valence"], second["activation"], second["engagement"],
            frozenset(second["operational_signals"]),
        )
        if first_labels != second_labels:
            return _empty_consensus(turn_id, "ambiguous", 1)

    consensus_signals = sorted(
        signal
        for signal in OPERATIONAL_SIGNALS
        if sum(signal in record["operational_signals"] for record in inferable) >= 2
    )
    return {
        "turn_id": turn_id,
        "label_status": "consensus",
        "valence": int(median(record["valence"] for record in inferable)),
        "activation": int(median(record["activation"] for record in inferable)),
        "engagement": int(median(record["engagement"] for record in inferable)),
        "operational_signals": consensus_signals,
        "none_selected": not consensus_signals,
        "reviewer_count": 3,
        "not_inferable_count": len(not_inferable),
    }


def _expect_annotation_error(callback: Any) -> None:
    try:
        callback()
    except AnnotationContractError:
        return
    raise AssertionError("expected AnnotationContractError")


def _fixture_record(record_id: str, reviewer_id: str) -> dict[str, Any]:
    return {
        "annotation_record_id": record_id,
        "dataset_manifest_id": "synthetic-fixture-manifest-v1",
        "turn_id": "turn-fixture-1",
        "dependency_group_ids": {
            "speaker": "speaker-fixture-1",
            "call_session": "call-fixture-1",
            "dialogue_dyad": None,
            "source_corpus": "synthetic-fixture-corpus",
            "scripted_scenario": "scenario-fixture-1",
        },
        "reviewer_id": reviewer_id,
        "reviewer_round": 1,
        "valence": 0,
        "activation": 3,
        "engagement": 2,
        "operational_signals": ["confusion"],
        "reviewer_confidence": "medium",
        "not_inferable": False,
        "not_inferable_reason_code": None,
        "evidence_class": "observer_inference",
        "explicit_statement_reference": None,
    }


def _not_inferable(record: dict[str, Any]) -> dict[str, Any]:
    return dict(
        record,
        valence=None,
        activation=None,
        engagement=None,
        operational_signals=[],
        not_inferable=True,
        not_inferable_reason_code="insufficient_context",
        evidence_class="not_inferable",
        explicit_statement_reference=None,
    )


def annotation_contract_self_check() -> str:
    first = _fixture_record("annotation-1", "reviewer-1")
    second = _fixture_record("annotation-2", "reviewer-2")
    third = dict(
        _fixture_record("annotation-3", "reviewer-3"),
        valence=1,
        activation=4,
        engagement=3,
        operational_signals=["confusion", "interest"],
    )
    consensus = aggregate_three_reviewer_labels([first, second, third])
    assert consensus["label_status"] == "consensus"
    assert consensus["valence"] == 0
    assert consensus["operational_signals"] == ["confusion"]

    two_abstain = aggregate_three_reviewer_labels([first, _not_inferable(second), _not_inferable(third)])
    assert two_abstain["label_status"] == "not_inferable"

    one_abstains_agree = aggregate_three_reviewer_labels([first, second, _not_inferable(third)])
    assert one_abstains_agree["label_status"] == "consensus"
    assert type(one_abstains_agree["valence"]) is int
    one_abstains_disagree = aggregate_three_reviewer_labels([
        first,
        dict(second, valence=-1),
        _not_inferable(third),
    ])
    assert one_abstains_disagree["label_status"] == "ambiguous"

    _expect_annotation_error(lambda: validate_annotation_record(dict(_not_inferable(first), valence=0)))
    _expect_annotation_error(lambda: validate_annotation_record(dict(
        first,
        evidence_class="direct_explicit",
        explicit_statement_reference="raw transcript sentence",
    )))
    for transcript_like_reference in (
        "I-am-confused-about-price",
        "I_am_confused_about_price",
        "I%20am%20confused",
        "Ich-bin-verwirrt-wegen-des-Preises",
    ):
        _expect_annotation_error(lambda reference=transcript_like_reference: validate_annotation_record(dict(
            first,
            evidence_class="direct_explicit",
            explicit_statement_reference=reference,
        )))
    validate_annotation_record(dict(
        first,
        evidence_class="direct_explicit",
        explicit_statement_reference="evidence:uuid:11111111-1111-4111-8111-111111111111",
    ))
    _expect_annotation_error(lambda: aggregate_three_reviewer_labels([
        first,
        dict(second, reviewer_id="reviewer-1"),
        third,
    ]))
    _expect_annotation_error(lambda: aggregate_three_reviewer_labels([
        first,
        dict(second, dependency_group_ids=dict(second["dependency_group_ids"], speaker="speaker-fixture-2")),
        third,
    ]))

    def dependency_groups(suffix: str) -> dict[str, list[str]]:
        return {key: [f"{key}-{suffix}"] for key in DEPENDENCY_GROUP_FIELDS}

    def records_for_case(case_id: str, suffix: str) -> list[dict[str, Any]]:
        groups = {key: f"{key}-{suffix}" for key in DEPENDENCY_GROUP_FIELDS}
        return [
            dict(
                _fixture_record(f"annotation-{suffix}-{index}", f"reviewer-{index}"),
                turn_id=case_id,
                dependency_group_ids=groups,
            )
            for index in range(1, 4)
        ]

    split_records = [
        record
        for case_id, suffix in (
            ("case-training-1", "training"),
            ("case-calibration-1", "calibration"),
            ("case-diagnostic-1", "diagnostic"),
            ("case-lockbox-1", "lockbox"),
        )
        for record in records_for_case(case_id, suffix)
    ]

    split = {
        "manifest_id": "split-fixture-v1",
        "dataset_manifest_ids": ["synthetic-fixture-manifest-v1"],
        "highest_dependency_unit": "speaker",
        "dependency_keys": sorted(DEPENDENCY_GROUP_FIELDS),
        "training_discovery": {
            "case_ids": ["case-training-1"],
            "dependency_groups": dependency_groups("training"),
        },
        "calibration": {
            "case_ids": ["case-calibration-1"],
            "dependency_groups": dependency_groups("calibration"),
            "prevalence_representative": True,
        },
        "balanced_diagnostic": {
            "case_ids": ["case-diagnostic-1"],
            "dependency_groups": dependency_groups("diagnostic"),
            "calibration_claims_allowed": False,
        },
        "final_lockbox": {
            "case_ids": ["case-lockbox-1"],
            "dependency_groups": dependency_groups("lockbox"),
            "prevalence_representative": True,
            "one_use_only": True,
            "open_count": 0,
        },
        "frozen_candidate_family_digest": "A" * 64,
        "runtime_influence_allowed": False,
    }
    validate_split_manifest(split, split_records)
    leaky_groups = dict(split["calibration"]["dependency_groups"], speaker=["speaker-training"])
    _expect_annotation_error(lambda: validate_split_manifest(dict(
        split,
        calibration=dict(split["calibration"], dependency_groups=leaky_groups),
    ), split_records))
    fabricated_distinct_speaker_records = [
        dict(
            record,
            dependency_group_ids=dict(record["dependency_group_ids"], speaker="speaker-training"),
        )
        if record["turn_id"] == "case-calibration-1"
        else record
        for record in split_records
    ]
    _expect_annotation_error(lambda: validate_split_manifest(
        split,
        fabricated_distinct_speaker_records,
    ))
    _expect_annotation_error(lambda: validate_split_manifest(dict(
        split,
        calibration=dict(split["calibration"], case_ids=["case-training-1"]),
    ), split_records))
    _expect_annotation_error(lambda: validate_split_manifest(dict(
        split,
        final_lockbox=dict(split["final_lockbox"], open_count=2),
    ), split_records))
    _expect_annotation_error(lambda: validate_split_manifest(split, split_records[:-1]))
    return "pass"
```

- [ ] **Step 6: Write the annotation codebook from the approved rules**

The codebook must contain these exact sections and rules:

```markdown
## Evidence Available To Reviewers

- Give each trained reviewer the customer audio turn, its transcript, and one or two preceding turns only when needed for context.
- Use three independent reviewers per labelled turn.
- Before accepted annotation, every reviewer completes a codebook-calibration practice set excluded from discovery and evaluation.
- Any codebook change invalidates prior calibration for new labels; rerun the practice set before accepting more labels.
- Do not ask customers for emotional self-report. Record only unsolicited direct statements already present in approved evidence.

## Evidence Hidden From Reviewers

- Hide model predictions, provider/LLM evaluator labels, conversion or appointment outcomes, future turns, and every other reviewer's labels.

## Label Fields

- Freeze valence to `-2..2`; freeze activation and engagement to `1..5`; do not change these scales without a reviewed schema version.
- Treat hesitation, frustration, confusion, interest, and disengagement as separate binary operational signals.
- Use only the enumerated reviewer-confidence values and `not_inferable` reason codes in `annotation_record_v1.schema.json`.
- `none` means all operational signals are negative. It is distinct from `not_inferable` and is never a reviewer-selected signal.
- Record direct explicit evidence as `evidence_class = direct_explicit` plus a redacted, nonreversible `evidence:uuid:<canonical-lowercase-uuid-v4>` reference issued independently of the statement text; never copy or encode the statement text in an identifier. The UUID may point only to a separately validated redacted evidence record in an approved research store.

## `not_inferable` And `ambiguous`

- `not_inferable` is mutually exclusive with dimensional and operational labels and requires an enumerated reason.
- Two or more `not_inferable` ratings produce `label_status = not_inferable`.
- One `not_inferable` rating is missing evidence; the other two reviewers must agree on every dimensional and operational label or the result is `ambiguous`.
- Unusable audio, insufficient context, or unresolved disagreement produces `ambiguous`; never force consensus.
- Retain reviewer-level disagreement records; do not overwrite them with the aggregate label.

## Consensus Rules

- Operational consensus-positive requires two of three reviewers.
- Dimensional consensus is the median of valid ordinal ratings.
- `not_inferable` and `ambiguous` turns are excluded from positive/negative supervised-label denominators but retained in end-to-end eligibility, abstention, and coverage metrics.
- Model non-abstention on a `not_inferable` reference turn is an abstention-policy error.

## Agreement Metrics

- Use ordinal Krippendorff's alpha for valence, activation, and engagement.
- Use nominal Krippendorff's alpha separately for each binary operational signal.
- Report speaker-clustered confidence intervals and per-label prevalence; do not pool disagreement into a favorable score.
- Derive every split dependency summary from the complete immutable three-reviewer records for its cases; reject missing records, mismatched summaries, and cross-partition speaker/call/dyad/corpus/scenario overlap.

## Privacy Boundary

- Do not persist unrestricted transcript quotes, raw customer audio, reusable customer identity, provider payloads, or secrets in tracked annotation artifacts.
- Pseudonymous dependency-group IDs are research-only and must remain consistent across the three records for one turn.
```

- [ ] **Step 7: Reprioritize the roadmap without erasing the previous work**

Replace the current-checkpoint line with:

```markdown
- [ ] Current: implement the `EMOTION-STATE-001` partial Phase A provenance and offline contract foundation checkpoint. Keep `phase_a_complete=false` until both exact per-public-dataset manifests and the separately approved privacy-preserving unique-speaker cohort-release/dedup gate are designed, approved, satisfied, and validated. No acoustic code adaptation, private-data ingestion, provider work, runtime wiring, or live customer use is authorized.
```

Move the prior Universal Sales RAG current item into the next-checkpoint list as:

```markdown
- [ ] Parked by Tarik's `2026-07-14` reprioritization: design the first full Universal Sales RAG source skeleton from the accepted layer contract. This work is not completed or rejected.
```

- [ ] **Step 8: Run the source section green**

```powershell
python scripts\validate_emotion_state_001_phase_a_contracts.py --section source
```

Expected: `EMOTION-STATE-001 Phase A validation passed: source`.

- [ ] **Step 9: Commit provenance and annotation rules**

```powershell
git add research\sources\creative_analysis_engine research\sources\emotion_state scripts\emotion_state_annotation_contracts.py docs\data\EMOTION_STATE_001_ANNOTATION_CODEBOOK.md docs\third-party-inspirations.md docs\thesis\THESIS_REFERENCE_REGISTRY.md docs\thesis\ROADMAP.md
git commit -m "Add EMOTION-STATE provenance and annotation gates"
```

---

### Task 3: Implement Strict Turn, Audit, Aggregate, And State Contracts

**Files:**

- Create: `runtime/contracts/emotion_state_contracts.py`
- Create: `research/experiments/cases/emotion-state-001-phase-a-contracts.json`
- Test: `scripts/validate_emotion_state_001_phase_a_contracts.py::validate_contracts`

**Interfaces:**

- Produces: `EventWatermarkV1`, `validate_opaque_reference()`, `validate_evidence_reference()`, `validate_decision_reference()`, `validate_customer_turn_evidence(payload)`, `validate_customer_turn_audit(payload)`, `validate_operational_aggregate(payload)`, `validate_perceived_customer_state(payload)`, `validate_event_identity(payload, *, watermark) -> EventWatermarkV1`, `serialize_default_live_record(contract_name, payload)`, and `contract_self_check()`.
- Consumed later by: Phase B offline feature adapter, Phase C tracker, and the Phase A checkpoint builder.
- Initialize an empty `EventWatermarkV1` with `last_turn_sequence=-1`, empty tuple maps, and an empty `frozenset`; the validator rejects mutable or internally inconsistent watermarks.
- `serialize_default_live_record()` is exercised only as a contract-shape fixture in Phase A and has no runtime caller. It cannot prove unique humans from call-scoped IDs and does not authorize aggregate release; the separate privacy gate in Global Constraints remains mandatory.

- [ ] **Step 1: Create the contract module with exact field sets and fail-closed persistence**

```python
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

TURN_EVIDENCE_FIELDS = frozenset({
    "call_session_id", "campaign_profile_id", "campaign_profile_version", "turn_id",
    "turn_sequence", "event_id", "input_revision", "event_timestamp",
    "call_scoped_speaker_id", "start_time_ms", "end_time_ms", "audio_quality_status",
    "audio_quality_reasons", "acoustic_features", "acoustic_feature_confidence",
    "transcript_signals", "explicit_customer_statements", "dialogue_context_refs",
    "speaker_baseline_status", "extraction_status", "source_timestamps", "persistence_allowed",
})
TURN_AUDIT_FIELDS = frozenset({
    "ephemeral_audit_session_id", "turn_sequence", "audio_analysis_status",
    "audio_quality_bucket", "enumerated_signal_types", "abstained",
    "abstention_reason_codes", "processing_latency_ms", "evidence_policy_version",
    "runtime_approved", "contains_raw_audio", "contains_raw_transcript",
})
OPERATIONAL_AGGREGATE_FIELDS = frozenset({
    "aggregation_window", "eligible_call_count", "audio_analysis_availability_rate",
    "audio_quality_bucket_counts", "abstention_rate", "processing_latency_percentiles",
    "evidence_policy_version_counts", "contains_call_level_rows", "contains_raw_audio",
    "contains_raw_transcript", "contains_signal_labels",
})
PERCEIVED_STATE_FIELDS = frozenset({
    "call_session_id", "campaign_profile_id", "campaign_profile_version", "turn_id",
    "turn_sequence", "valence_estimate", "activation_estimate", "engagement_estimate",
    "operational_signals", "confidence_by_signal", "selected_policy_signal",
    "selected_signal_confidence_bucket", "overall_evidence_quality", "trajectory",
    "evidence_refs", "signal_provenance_by_modality", "allowed_policy_effects",
    "blocked_policy_effects", "abstained", "abstention_reasons", "evidence_policy_version",
    "runtime_approved",
})
FORBIDDEN_BODY_KEYS = frozenset({
    "raw_audio", "audio_bytes", "raw_transcript", "transcript_text", "customer_name",
    "customer_phone", "customer_email", "speaker_embedding", "voiceprint", "provider_payload",
    "api_key", "secret", "hidden_reasoning",
})
FORBIDDEN_KEY_FRAGMENTS = (
    "raw_audio", "audio_bytes", "raw_transcript", "transcript_text", "speaker_embedding",
    "voiceprint", "provider_payload", "api_key", "access_token", "auth_token", "password",
    "secret", "private_key", "hidden_reasoning",
)
REFERENCE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}$")
EVIDENCE_REFERENCE_PATTERN = re.compile(
    r"^evidence:uuid:[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
DECISION_REFERENCE_PATTERN = re.compile(
    r"^decision:uuid:[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
BASE_OPERATIONAL_SIGNALS = frozenset({
    "hesitation", "frustration", "confusion", "interest", "disengagement",
})
STATE_OPERATIONAL_SIGNALS = BASE_OPERATIONAL_SIGNALS | frozenset({
    "possible_hesitation", "possible_frustration", "possible_confusion",
    "possible_interest", "possible_disengagement", "none",
})
ALLOWED_POLICY_EFFECTS = frozenset({
    "preserve", "soften", "shorten", "clarify", "acknowledge", "handoff", "stop", "abstain",
})
REQUIRED_BLOCKED_POLICY_EFFECTS = frozenset({
    "expand_action_set", "increase_persuasion_intensity", "create_new_close",
    "override_refusal", "override_do_not_call", "rewrite_protected_text",
    "exploit_vulnerability", "voice_only_emotional_appeal", "unsupported_claim",
    "automatic_close_or_payment",
})
AUDIO_QUALITY_STATUSES = frozenset({"usable", "degraded", "unusable", "unavailable"})
AUDIO_QUALITY_REASON_CODES = frozenset({
    "phase_a_no_audio", "low_signal", "clipping", "noise", "too_short",
    "missing_audio", "unsupported_format", "contradictory_evidence",
})
EXTRACTION_STATUSES = frozenset({"offline_fixture_only", "complete", "partial", "abstained", "failed", "unavailable"})
SPEAKER_BASELINE_STATUSES = frozenset({"not_started", "collecting", "available", "unusable"})
ABSTENTION_REASON_CODES = frozenset({
    "phase_a_no_audio", "insufficient_evidence", "contradictory_evidence",
    "low_audio_quality", "missing_input", "stale_input",
})
EVIDENCE_QUALITY_VALUES = frozenset({"text_only", "acoustic_only", "multimodal", "insufficient", "low_quality"})
TRAJECTORY_VALUES = frozenset({"stable", "improving", "worsening", "insufficient_history", "contradictory"})
AGGREGATION_WINDOW_FIELDS = frozenset({"window_start_date", "window_end_date", "timezone"})
EVIDENCE_POLICY_VERSION_PATTERN = re.compile(r"^emotion-state-evidence-v[1-9][0-9]*$")
EXPLICIT_STATEMENT_FIELDS = frozenset({
    "evidence_class", "redacted_reference_id", "operational_signal",
})


class EmotionStateContractError(ValueError):
    pass


@dataclass(frozen=True)
class EventWatermarkV1:
    expected_session_id: str
    expected_campaign_profile_id: str
    expected_campaign_profile_version: str
    last_turn_sequence: int
    turn_sequence_by_id: tuple[tuple[str, int], ...]
    turn_id_by_sequence: tuple[tuple[int, str], ...]
    last_input_revision_by_turn: tuple[tuple[str, int], ...]
    seen_event_ids: frozenset[str]


def _find_forbidden_paths(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower()
            child_path = f"{path}.{key}"
            if normalized in FORBIDDEN_BODY_KEYS or any(fragment in normalized for fragment in FORBIDDEN_KEY_FRAGMENTS):
                found.append(child_path)
            found.extend(_find_forbidden_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_find_forbidden_paths(child, f"{path}[{index}]"))
    return found


def _key_is_forbidden(key: Any) -> bool:
    normalized = str(key).lower()
    return normalized in FORBIDDEN_BODY_KEYS or any(fragment in normalized for fragment in FORBIDDEN_KEY_FRAGMENTS)


def _require_fields(payload: dict[str, Any], required: frozenset[str], contract: str) -> None:
    if not isinstance(payload, dict):
        raise EmotionStateContractError(f"{contract} must be an object")
    missing = sorted(required - set(payload))
    if missing:
        raise EmotionStateContractError(f"{contract} missing fields: {missing}")
    forbidden: list[str] = []
    for key, value in payload.items():
        if key not in required and _key_is_forbidden(key):
            forbidden.append(f"$.{key}")
        forbidden.extend(_find_forbidden_paths(value, f"$.{key}"))
    if forbidden:
        raise EmotionStateContractError(f"{contract} contains forbidden fields: {forbidden}")
    unknown = sorted(set(payload) - required)
    if unknown:
        raise EmotionStateContractError(f"{contract} unknown fields: {unknown}")


def validate_opaque_reference(value: Any, field: str) -> None:
    if not isinstance(value, str) or REFERENCE_ID_PATTERN.fullmatch(value) is None:
        raise EmotionStateContractError(f"{field} must be a bounded opaque reference, not free text")


def validate_evidence_reference(value: Any, field: str) -> None:
    if not isinstance(value, str) or EVIDENCE_REFERENCE_PATTERN.fullmatch(value) is None:
        raise EmotionStateContractError(
            f"{field} must be a typed content-independent evidence UUID, not transcript text"
        )


def validate_decision_reference(value: Any, field: str) -> None:
    if not isinstance(value, str) or DECISION_REFERENCE_PATTERN.fullmatch(value) is None:
        raise EmotionStateContractError(
            f"{field} must be a typed content-independent decision UUID, not free text"
        )


def _validate_event_watermark(
    watermark: EventWatermarkV1,
) -> tuple[dict[str, int], dict[int, str], dict[str, int]]:
    if not isinstance(watermark, EventWatermarkV1):
        raise EmotionStateContractError("event watermark type is invalid")
    for field, value in (
        ("expected_session_id", watermark.expected_session_id),
        ("expected_campaign_profile_id", watermark.expected_campaign_profile_id),
        ("expected_campaign_profile_version", watermark.expected_campaign_profile_version),
    ):
        validate_opaque_reference(value, f"watermark.{field}")
    if type(watermark.last_turn_sequence) is not int or watermark.last_turn_sequence < -1:
        raise EmotionStateContractError("event watermark last_turn_sequence is invalid")
    tuple_fields = (
        watermark.turn_sequence_by_id,
        watermark.turn_id_by_sequence,
        watermark.last_input_revision_by_turn,
    )
    if any(type(value) is not tuple for value in tuple_fields) or type(watermark.seen_event_ids) is not frozenset:
        raise EmotionStateContractError("event watermark collections must be immutable")
    if any(type(pair) is not tuple or len(pair) != 2 for value in tuple_fields for pair in value):
        raise EmotionStateContractError("event watermark entries are invalid")
    sequence_by_id = dict(watermark.turn_sequence_by_id)
    id_by_sequence = dict(watermark.turn_id_by_sequence)
    revision_by_turn = dict(watermark.last_input_revision_by_turn)
    if any(len(mapping) != len(source) for mapping, source in (
        (sequence_by_id, watermark.turn_sequence_by_id),
        (id_by_sequence, watermark.turn_id_by_sequence),
        (revision_by_turn, watermark.last_input_revision_by_turn),
    )):
        raise EmotionStateContractError("event watermark contains duplicate map keys")
    for turn_id, sequence in sequence_by_id.items():
        validate_opaque_reference(turn_id, "watermark.turn_id")
        if type(sequence) is not int or sequence < 0:
            raise EmotionStateContractError("event watermark turn sequence is invalid")
    for sequence, turn_id in id_by_sequence.items():
        if type(sequence) is not int or sequence < 0:
            raise EmotionStateContractError("event watermark reverse turn sequence is invalid")
        validate_opaque_reference(turn_id, "watermark.reverse_turn_id")
    for turn_id, revision in revision_by_turn.items():
        validate_opaque_reference(turn_id, "watermark.revision_turn_id")
        if type(revision) is not int or revision < 0:
            raise EmotionStateContractError("event watermark revision is invalid")
    for event_id in watermark.seen_event_ids:
        validate_opaque_reference(event_id, "watermark.seen_event_id")
    if {sequence: turn_id for turn_id, sequence in sequence_by_id.items()} != id_by_sequence:
        raise EmotionStateContractError("event watermark turn maps are inconsistent")
    if set(revision_by_turn) != set(sequence_by_id):
        raise EmotionStateContractError("event watermark revision map is inconsistent")
    expected_last_sequence = max(id_by_sequence, default=-1)
    if watermark.last_turn_sequence != expected_last_sequence:
        raise EmotionStateContractError("event watermark last_turn_sequence is inconsistent")
    return sequence_by_id, id_by_sequence, revision_by_turn


def _require_reference_list(value: Any, field: str) -> None:
    if not isinstance(value, list):
        raise EmotionStateContractError(f"{field} must contain typed evidence UUID references, not free text")
    for reference in value:
        validate_evidence_reference(reference, field)
    if len(value) != len(set(value)):
        raise EmotionStateContractError(f"{field} must contain unique references")


def _require_enum_list(value: Any, allowed: frozenset[str], field: str) -> None:
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) or item not in allowed for item in value)
        or len(value) != len(set(value))
    ):
        raise EmotionStateContractError(f"{field} contains an unknown value")


def _require_numeric_map(value: Any, field: str, *, minimum: float | None = None, maximum: float | None = None) -> None:
    if not isinstance(value, dict):
        raise EmotionStateContractError(f"{field} must be an object of scalar values")
    for key, number in value.items():
        validate_opaque_reference(key, f"{field} key")
        if type(number) not in {int, float} or not math.isfinite(number):
            raise EmotionStateContractError(f"{field}.{key} must be a finite scalar")
        if minimum is not None and number < minimum:
            raise EmotionStateContractError(f"{field}.{key} is below its minimum")
        if maximum is not None and number > maximum:
            raise EmotionStateContractError(f"{field}.{key} is above its maximum")


def _require_rate(value: Any, field: str) -> None:
    if type(value) not in {int, float} or not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise EmotionStateContractError(f"{field} must be a finite rate in [0, 1]")


def _require_count_map(value: Any, field: str, *, expected_total: int) -> None:
    if not isinstance(value, dict) or not value:
        raise EmotionStateContractError(f"{field} must be a nonempty count object")
    total = 0
    for key, count in value.items():
        validate_opaque_reference(key, f"{field} key")
        if type(count) is not int or count < 0:
            raise EmotionStateContractError(f"{field}.{key} must be a nonnegative integer")
        total += count
    if total != expected_total:
        raise EmotionStateContractError(f"{field} must sum to eligible_call_count")


def _validate_aggregation_window(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != AGGREGATION_WINDOW_FIELDS:
        raise EmotionStateContractError("aggregation_window fields mismatch")
    if value["timezone"] != "UTC":
        raise EmotionStateContractError("aggregation_window timezone must be UTC")
    try:
        start = date.fromisoformat(value["window_start_date"])
        end = date.fromisoformat(value["window_end_date"])
    except (TypeError, ValueError) as exc:
        raise EmotionStateContractError("aggregation_window dates must use YYYY-MM-DD") from exc
    if end < start:
        raise EmotionStateContractError("aggregation_window end precedes start")


def _validate_explicit_statements(value: Any) -> None:
    if not isinstance(value, list):
        raise EmotionStateContractError("explicit_customer_statements must be a list")
    for statement in value:
        if not isinstance(statement, dict) or set(statement) != EXPLICIT_STATEMENT_FIELDS:
            raise EmotionStateContractError("explicit statement fields mismatch")
        if statement["evidence_class"] != "direct_explicit":
            raise EmotionStateContractError("explicit statement evidence class mismatch")
        if statement["operational_signal"] not in BASE_OPERATIONAL_SIGNALS:
            raise EmotionStateContractError("explicit statement signal is invalid")
        _require_reference_list([statement["redacted_reference_id"]], "redacted_reference_id")


def _require_false(payload: dict[str, Any], fields: tuple[str, ...], contract: str) -> None:
    for field in fields:
        if payload.get(field) is not False:
            raise EmotionStateContractError(f"{contract}.{field} must be false")


def validate_customer_turn_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    _require_fields(payload, TURN_EVIDENCE_FIELDS, "CustomerTurnEvidenceV1")
    _require_false(payload, ("persistence_allowed",), "CustomerTurnEvidenceV1")
    if type(payload["turn_sequence"]) is not int or payload["turn_sequence"] < 0:
        raise EmotionStateContractError("turn_sequence must be a nonnegative integer")
    if type(payload["input_revision"]) is not int or payload["input_revision"] < 0:
        raise EmotionStateContractError("input_revision must be a nonnegative integer")
    for field in (
        "call_session_id", "campaign_profile_id", "campaign_profile_version", "turn_id", "event_id",
        "call_scoped_speaker_id", "audio_quality_status", "speaker_baseline_status", "extraction_status",
    ):
        validate_opaque_reference(payload[field], field)
    if not payload["call_scoped_speaker_id"].startswith(f"{payload['call_session_id']}:"):
        raise EmotionStateContractError("call_scoped_speaker_id must be bound to the current call session")
    if type(payload["start_time_ms"]) is not int or type(payload["end_time_ms"]) is not int:
        raise EmotionStateContractError("turn timestamps must be integers")
    if payload["start_time_ms"] < 0 or payload["end_time_ms"] <= payload["start_time_ms"]:
        raise EmotionStateContractError("turn timestamp range is invalid")
    try:
        event_timestamp = datetime.fromisoformat(payload["event_timestamp"].replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise EmotionStateContractError("event_timestamp must be ISO-8601") from exc
    if event_timestamp.tzinfo is None:
        raise EmotionStateContractError("event_timestamp must include a timezone")
    if payload["audio_quality_status"] not in AUDIO_QUALITY_STATUSES:
        raise EmotionStateContractError("audio_quality_status is invalid")
    _require_enum_list(payload["audio_quality_reasons"], AUDIO_QUALITY_REASON_CODES, "audio_quality_reasons")
    if payload["speaker_baseline_status"] not in SPEAKER_BASELINE_STATUSES:
        raise EmotionStateContractError("speaker_baseline_status is invalid")
    if payload["extraction_status"] not in EXTRACTION_STATUSES:
        raise EmotionStateContractError("extraction_status is invalid")
    _require_numeric_map(payload["acoustic_features"], "acoustic_features")
    _require_numeric_map(payload["acoustic_feature_confidence"], "acoustic_feature_confidence", minimum=0.0, maximum=1.0)
    _require_numeric_map(payload["source_timestamps"], "source_timestamps", minimum=0.0)
    _require_enum_list(payload["transcript_signals"], STATE_OPERATIONAL_SIGNALS, "transcript_signals")
    _validate_explicit_statements(payload["explicit_customer_statements"])
    _require_reference_list(payload["dialogue_context_refs"], "dialogue_context_refs")
    return payload


def validate_customer_turn_audit(payload: dict[str, Any]) -> dict[str, Any]:
    _require_fields(payload, TURN_AUDIT_FIELDS, "CustomerTurnAuditV1")
    unknown = sorted(set(payload) - TURN_AUDIT_FIELDS)
    if unknown:
        raise EmotionStateContractError(f"CustomerTurnAuditV1 unknown fields: {unknown}")
    _require_false(payload, ("runtime_approved", "contains_raw_audio", "contains_raw_transcript"), "CustomerTurnAuditV1")
    validate_opaque_reference(payload["ephemeral_audit_session_id"], "ephemeral_audit_session_id")
    validate_opaque_reference(payload["evidence_policy_version"], "evidence_policy_version")
    if EVIDENCE_POLICY_VERSION_PATTERN.fullmatch(payload["evidence_policy_version"]) is None:
        raise EmotionStateContractError("audit evidence_policy_version is invalid")
    if type(payload["turn_sequence"]) is not int or payload["turn_sequence"] < 0:
        raise EmotionStateContractError("audit turn_sequence must be a nonnegative integer")
    if payload["audio_analysis_status"] not in {"unavailable", "complete", "partial", "failed", "abstained"}:
        raise EmotionStateContractError("audio_analysis_status is invalid")
    if payload["audio_quality_bucket"] not in AUDIO_QUALITY_STATUSES:
        raise EmotionStateContractError("audio_quality_bucket is invalid")
    _require_enum_list(payload["enumerated_signal_types"], STATE_OPERATIONAL_SIGNALS, "enumerated_signal_types")
    _require_enum_list(payload["abstention_reason_codes"], ABSTENTION_REASON_CODES, "abstention_reason_codes")
    if type(payload["abstained"]) is not bool:
        raise EmotionStateContractError("abstained must be boolean")
    if payload["abstained"] != bool(payload["abstention_reason_codes"]):
        raise EmotionStateContractError("audit abstention flag and reasons are inconsistent")
    if type(payload["processing_latency_ms"]) is not int or payload["processing_latency_ms"] < 0:
        raise EmotionStateContractError("processing_latency_ms must be a nonnegative integer")
    return payload


def validate_operational_aggregate(payload: dict[str, Any]) -> dict[str, Any]:
    _require_fields(payload, OPERATIONAL_AGGREGATE_FIELDS, "OperationalAggregateV1")
    unknown = sorted(set(payload) - OPERATIONAL_AGGREGATE_FIELDS)
    if unknown:
        raise EmotionStateContractError(f"OperationalAggregateV1 unknown fields: {unknown}")
    if type(payload["eligible_call_count"]) is not int or payload["eligible_call_count"] < 10:
        raise EmotionStateContractError("OperationalAggregateV1 requires at least ten eligible calls")
    _require_false(
        payload,
        ("contains_call_level_rows", "contains_raw_audio", "contains_raw_transcript", "contains_signal_labels"),
        "OperationalAggregateV1",
    )
    _validate_aggregation_window(payload["aggregation_window"])
    _require_rate(payload["audio_analysis_availability_rate"], "audio_analysis_availability_rate")
    _require_rate(payload["abstention_rate"], "abstention_rate")
    quality_counts = payload["audio_quality_bucket_counts"]
    if not isinstance(quality_counts, dict) or set(quality_counts) - AUDIO_QUALITY_STATUSES:
        raise EmotionStateContractError("audio_quality_bucket_counts contains an unknown cohort bucket")
    _require_count_map(quality_counts, "audio_quality_bucket_counts", expected_total=payload["eligible_call_count"])
    percentiles = payload["processing_latency_percentiles"]
    if not isinstance(percentiles, dict) or set(percentiles) != {"p50", "p95"}:
        raise EmotionStateContractError("processing_latency_percentiles must contain p50 and p95 only")
    _require_numeric_map(percentiles, "processing_latency_percentiles", minimum=0.0)
    if percentiles["p95"] < percentiles["p50"]:
        raise EmotionStateContractError("processing latency percentiles are non-monotonic")
    policy_counts = payload["evidence_policy_version_counts"]
    if not isinstance(policy_counts, dict) or any(
        not isinstance(version, str) or EVIDENCE_POLICY_VERSION_PATTERN.fullmatch(version) is None
        for version in policy_counts
    ):
        raise EmotionStateContractError("evidence_policy_version_counts contains a non-version identifier")
    _require_count_map(
        policy_counts,
        "evidence_policy_version_counts",
        expected_total=payload["eligible_call_count"],
    )
    return payload


def validate_perceived_customer_state(payload: dict[str, Any]) -> dict[str, Any]:
    _require_fields(payload, PERCEIVED_STATE_FIELDS, "PerceivedCustomerStateV1")
    _require_false(payload, ("runtime_approved",), "PerceivedCustomerStateV1")
    for field in ("call_session_id", "campaign_profile_id", "campaign_profile_version", "turn_id", "evidence_policy_version"):
        validate_opaque_reference(payload[field], field)
    if EVIDENCE_POLICY_VERSION_PATTERN.fullmatch(payload["evidence_policy_version"]) is None:
        raise EmotionStateContractError("state evidence_policy_version is invalid")
    if type(payload["turn_sequence"]) is not int or payload["turn_sequence"] < 0:
        raise EmotionStateContractError("state turn_sequence must be a nonnegative integer")
    if payload["valence_estimate"] != "not_inferable" and (
        type(payload["valence_estimate"]) is not int or payload["valence_estimate"] not in {-2, -1, 0, 1, 2}
    ):
        raise EmotionStateContractError("valence_estimate is invalid")
    for field in ("activation_estimate", "engagement_estimate"):
        if payload[field] != "not_inferable" and (
            type(payload[field]) is not int or payload[field] not in {1, 2, 3, 4, 5}
        ):
            raise EmotionStateContractError(f"{field} is invalid")
    if payload["selected_signal_confidence_bucket"] not in {"low", "medium", "high"}:
        raise EmotionStateContractError("invalid selected_signal_confidence_bucket")
    _require_enum_list(payload["operational_signals"], STATE_OPERATIONAL_SIGNALS, "operational_signals")
    if "none" in payload["operational_signals"] and payload["operational_signals"] != ["none"]:
        raise EmotionStateContractError("none cannot coexist with operational signals")
    _require_numeric_map(payload["confidence_by_signal"], "confidence_by_signal", minimum=0.0, maximum=1.0)
    signal_keys = set(payload["operational_signals"]) - {"none"}
    if set(payload["confidence_by_signal"]) != signal_keys:
        raise EmotionStateContractError("confidence_by_signal must match operational_signals")
    if payload["selected_policy_signal"] not in STATE_OPERATIONAL_SIGNALS:
        raise EmotionStateContractError("selected_policy_signal is invalid")
    if payload["overall_evidence_quality"] not in EVIDENCE_QUALITY_VALUES:
        raise EmotionStateContractError("overall_evidence_quality is invalid")
    if payload["trajectory"] not in TRAJECTORY_VALUES:
        raise EmotionStateContractError("trajectory is invalid")
    _require_enum_list(payload["allowed_policy_effects"], ALLOWED_POLICY_EFFECTS, "allowed_policy_effects")
    _require_enum_list(payload["blocked_policy_effects"], REQUIRED_BLOCKED_POLICY_EFFECTS, "blocked_policy_effects")
    if set(payload["blocked_policy_effects"]) != REQUIRED_BLOCKED_POLICY_EFFECTS:
        raise EmotionStateContractError("blocked_policy_effects must contain every monotonic safety block")
    _require_reference_list(payload["evidence_refs"], "evidence_refs")
    if len(payload["evidence_refs"]) != len(set(payload["evidence_refs"])):
        raise EmotionStateContractError("evidence_refs must be unique")
    provenance = payload["signal_provenance_by_modality"]
    if not isinstance(provenance, dict) or set(provenance) != signal_keys:
        raise EmotionStateContractError("modality provenance must cover every operational signal")
    provenance_ref_union: set[str] = set()
    for signal, modality_refs in provenance.items():
        if not isinstance(modality_refs, dict) or not set(modality_refs).issubset({"text", "acoustic", "dialogue"}):
            raise EmotionStateContractError(f"invalid modality provenance for {signal}")
        signal_ref_union: set[str] = set()
        for modality, references in modality_refs.items():
            _require_reference_list(references, f"signal_provenance_by_modality.{signal}.{modality}")
            signal_ref_union.update(references)
        if not signal_ref_union:
            raise EmotionStateContractError(f"signal {signal} has no evidence provenance")
        provenance_ref_union.update(signal_ref_union)
    if provenance_ref_union != set(payload["evidence_refs"]):
        raise EmotionStateContractError("evidence_refs must equal the signal provenance reference union")
    _require_enum_list(payload["abstention_reasons"], ABSTENTION_REASON_CODES, "abstention_reasons")
    if type(payload["abstained"]) is not bool:
        raise EmotionStateContractError("abstained must be boolean")
    if payload["abstained"]:
        if not payload["abstention_reasons"] or payload["selected_policy_signal"] != "none":
            raise EmotionStateContractError("abstained state must select none and provide a reason")
        if payload["allowed_policy_effects"] != ["preserve"]:
            raise EmotionStateContractError("abstained acoustic state must preserve the text-only policy without a delta")
    else:
        if payload["abstention_reasons"]:
            raise EmotionStateContractError("non-abstained state cannot carry abstention reasons")
        if payload["selected_policy_signal"] not in signal_keys:
            raise EmotionStateContractError("selected policy signal lacks state evidence")
    return payload


def validate_event_identity(
    payload: dict[str, Any],
    *,
    watermark: EventWatermarkV1,
) -> EventWatermarkV1:
    validate_customer_turn_evidence(payload)
    sequence_by_id, id_by_sequence, revision_by_turn = _validate_event_watermark(watermark)
    if payload["call_session_id"] != watermark.expected_session_id:
        raise EmotionStateContractError("cross-session event")
    if payload["campaign_profile_id"] != watermark.expected_campaign_profile_id:
        raise EmotionStateContractError("cross-campaign event")
    if payload["campaign_profile_version"] != watermark.expected_campaign_profile_version:
        raise EmotionStateContractError("stale or wrong campaign profile version")
    if payload["event_id"] in watermark.seen_event_ids:
        raise EmotionStateContractError("duplicate event")
    turn_sequence = payload["turn_sequence"]
    turn_id = payload["turn_id"]
    input_revision = payload["input_revision"]
    if turn_id in sequence_by_id and sequence_by_id[turn_id] != turn_sequence:
        raise EmotionStateContractError("turn_id rebound to another sequence")
    if turn_sequence in id_by_sequence and id_by_sequence[turn_sequence] != turn_id:
        raise EmotionStateContractError("turn_sequence rebound to another turn_id")
    if turn_sequence < watermark.last_turn_sequence:
        raise EmotionStateContractError("stale or non-monotonic turn")
    if turn_id in sequence_by_id:
        if turn_sequence != watermark.last_turn_sequence:
            raise EmotionStateContractError("correction targets a closed turn")
        if input_revision <= revision_by_turn[turn_id]:
            raise EmotionStateContractError("stale input revision")
    else:
        if turn_sequence <= watermark.last_turn_sequence:
            raise EmotionStateContractError("new turn is not monotonic")
        if input_revision != 0:
            raise EmotionStateContractError("new turn must begin at input revision zero")
        sequence_by_id[turn_id] = turn_sequence
        id_by_sequence[turn_sequence] = turn_id
    revision_by_turn[turn_id] = input_revision
    return EventWatermarkV1(
        expected_session_id=watermark.expected_session_id,
        expected_campaign_profile_id=watermark.expected_campaign_profile_id,
        expected_campaign_profile_version=watermark.expected_campaign_profile_version,
        last_turn_sequence=max(watermark.last_turn_sequence, turn_sequence),
        turn_sequence_by_id=tuple(sorted(sequence_by_id.items())),
        turn_id_by_sequence=tuple(sorted(id_by_sequence.items())),
        last_input_revision_by_turn=tuple(sorted(revision_by_turn.items())),
        seen_event_ids=watermark.seen_event_ids | {payload["event_id"]},
    )


def serialize_default_live_record(contract_name: str, payload: dict[str, Any]) -> str:
    if contract_name != "OperationalAggregateV1":
        raise EmotionStateContractError(f"{contract_name} is not default-persistable")
    validate_operational_aggregate(payload)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))
```

Append these deterministic fixtures and self-check:

```python
def _expect_contract_error(callback: Any) -> None:
    try:
        callback()
    except EmotionStateContractError:
        return
    raise AssertionError("expected EmotionStateContractError")


def contract_self_check() -> str:
    evidence = {
        "call_session_id": "session-fixture-1",
        "campaign_profile_id": "emotion-state-phase-a-fixture",
        "campaign_profile_version": "fixture-v1",
        "turn_id": "turn-1",
        "turn_sequence": 1,
        "event_id": "event-1",
        "input_revision": 0,
        "event_timestamp": "2026-07-14T00:00:00Z",
        "call_scoped_speaker_id": "session-fixture-1:speaker-1",
        "start_time_ms": 0,
        "end_time_ms": 1000,
        "audio_quality_status": "unavailable",
        "audio_quality_reasons": ["phase_a_no_audio"],
        "acoustic_features": {},
        "acoustic_feature_confidence": {},
        "transcript_signals": ["possible_confusion"],
        "explicit_customer_statements": [{
            "evidence_class": "direct_explicit",
            "redacted_reference_id": "evidence:uuid:22222222-2222-4222-8222-222222222222",
            "operational_signal": "confusion",
        }],
        "dialogue_context_refs": ["evidence:uuid:11111111-1111-4111-8111-111111111111"],
        "speaker_baseline_status": "not_started",
        "extraction_status": "offline_fixture_only",
        "source_timestamps": {},
        "persistence_allowed": False,
    }
    audit = {
        "ephemeral_audit_session_id": "audit-fixture-1",
        "turn_sequence": 1,
        "audio_analysis_status": "unavailable",
        "audio_quality_bucket": "unavailable",
        "enumerated_signal_types": ["possible_confusion"],
        "abstained": True,
        "abstention_reason_codes": ["phase_a_no_audio"],
        "processing_latency_ms": 0,
        "evidence_policy_version": "emotion-state-evidence-v1",
        "runtime_approved": False,
        "contains_raw_audio": False,
        "contains_raw_transcript": False,
    }
    aggregate = {
        "aggregation_window": {
            "window_start_date": "2026-07-01",
            "window_end_date": "2026-07-14",
            "timezone": "UTC",
        },
        "eligible_call_count": 10,
        "audio_analysis_availability_rate": 0.0,
        "audio_quality_bucket_counts": {"unavailable": 10},
        "abstention_rate": 1.0,
        "processing_latency_percentiles": {"p50": 0, "p95": 0},
        "evidence_policy_version_counts": {"emotion-state-evidence-v1": 10},
        "contains_call_level_rows": False,
        "contains_raw_audio": False,
        "contains_raw_transcript": False,
        "contains_signal_labels": False,
    }
    state = {
        "call_session_id": "session-fixture-1",
        "campaign_profile_id": "emotion-state-phase-a-fixture",
        "campaign_profile_version": "fixture-v1",
        "turn_id": "turn-1",
        "turn_sequence": 1,
        "valence_estimate": "not_inferable",
        "activation_estimate": "not_inferable",
        "engagement_estimate": "not_inferable",
        "operational_signals": ["possible_confusion"],
        "confidence_by_signal": {"possible_confusion": 0.6},
        "selected_policy_signal": "possible_confusion",
        "selected_signal_confidence_bucket": "medium",
        "overall_evidence_quality": "text_only",
        "trajectory": "insufficient_history",
        "evidence_refs": ["evidence:uuid:11111111-1111-4111-8111-111111111111"],
        "signal_provenance_by_modality": {
            "possible_confusion": {
                "text": ["evidence:uuid:11111111-1111-4111-8111-111111111111"],
                "acoustic": [],
            },
        },
        "allowed_policy_effects": ["preserve", "clarify", "soften"],
        "blocked_policy_effects": [
            "expand_action_set", "increase_persuasion_intensity", "create_new_close",
            "override_refusal", "override_do_not_call", "rewrite_protected_text",
            "exploit_vulnerability", "voice_only_emotional_appeal", "unsupported_claim",
            "automatic_close_or_payment",
        ],
        "abstained": False,
        "abstention_reasons": [],
        "evidence_policy_version": "emotion-state-evidence-v1",
        "runtime_approved": False,
    }
    validate_customer_turn_evidence(evidence)
    validate_customer_turn_audit(audit)
    validate_operational_aggregate(aggregate)
    validate_perceived_customer_state(state)
    abstained_state = dict(
        state,
        valence_estimate="not_inferable",
        activation_estimate="not_inferable",
        engagement_estimate="not_inferable",
        operational_signals=["none"],
        confidence_by_signal={},
        selected_policy_signal="none",
        selected_signal_confidence_bucket="low",
        overall_evidence_quality="insufficient",
        evidence_refs=[],
        signal_provenance_by_modality={},
        allowed_policy_effects=["preserve"],
        abstained=True,
        abstention_reasons=["insufficient_evidence"],
    )
    validate_perceived_customer_state(abstained_state)
    initial_watermark = EventWatermarkV1(
        expected_session_id="session-fixture-1",
        expected_campaign_profile_id="emotion-state-phase-a-fixture",
        expected_campaign_profile_version="fixture-v1",
        last_turn_sequence=-1,
        turn_sequence_by_id=(),
        turn_id_by_sequence=(),
        last_input_revision_by_turn=(),
        seen_event_ids=frozenset(),
    )
    first_watermark = validate_event_identity(evidence, watermark=initial_watermark)
    corrected = dict(evidence, event_id="event-2", input_revision=1)
    corrected_watermark = validate_event_identity(corrected, watermark=first_watermark)
    assert initial_watermark.turn_sequence_by_id == ()
    assert corrected_watermark.last_input_revision_by_turn == (("turn-1", 1),)
    assert json.loads(serialize_default_live_record("OperationalAggregateV1", aggregate)) == aggregate
    _expect_contract_error(lambda: validate_customer_turn_evidence(dict(evidence, raw_transcript="blocked")))
    _expect_contract_error(lambda: validate_customer_turn_evidence(dict(evidence, acoustic_features={"provider_payload": {}})))
    _expect_contract_error(lambda: validate_customer_turn_evidence(dict(evidence, dialogue_context_refs=["raw transcript sentence"])))
    for transcript_like_reference in (
        "I-am-confused-about-price",
        "I_am_confused_about_price",
        "I%20am%20confused",
        "Ich-bin-verwirrt-wegen-des-Preises",
    ):
        _expect_contract_error(lambda reference=transcript_like_reference: validate_customer_turn_evidence(dict(
            evidence,
            dialogue_context_refs=[reference],
        )))
    _expect_contract_error(lambda: validate_customer_turn_evidence(dict(evidence, event_timestamp="2026-07-14T00:00:00")))
    _expect_contract_error(lambda: validate_customer_turn_evidence(dict(evidence, call_scoped_speaker_id="reusable-speaker-1")))
    _expect_contract_error(lambda: validate_customer_turn_audit(dict(audit, reviewer_notes="blocked")))
    _expect_contract_error(lambda: validate_customer_turn_audit(dict(audit, enumerated_signal_types=["raw transcript sentence"])))
    _expect_contract_error(lambda: validate_operational_aggregate(dict(aggregate, eligible_call_count=9)))
    _expect_contract_error(lambda: validate_operational_aggregate(dict(aggregate, eligible_unique_speaker_count=10)))
    _expect_contract_error(lambda: validate_operational_aggregate(dict(
        aggregate,
        audio_quality_bucket_counts={"call-fixture-1": 10},
    )))
    _expect_contract_error(lambda: validate_operational_aggregate(dict(
        aggregate,
        aggregation_window="session-fixture-1",
    )))
    _expect_contract_error(lambda: validate_operational_aggregate(dict(
        aggregate,
        evidence_policy_version_counts={"call-fixture-1": 10},
    )))
    _expect_contract_error(lambda: serialize_default_live_record("CustomerTurnEvidenceV1", evidence))
    _expect_contract_error(lambda: validate_event_identity(evidence, watermark=first_watermark))
    _expect_contract_error(lambda: validate_event_identity(
        dict(
            evidence,
            event_id="event-cross-session",
            call_session_id="another-session",
            call_scoped_speaker_id="another-session:speaker-1",
        ),
        watermark=initial_watermark,
    ))
    _expect_contract_error(lambda: validate_event_identity(
        dict(evidence, event_id="event-stale-revision"),
        watermark=first_watermark,
    ))
    _expect_contract_error(lambda: validate_event_identity(
        dict(evidence, event_id="event-wrong-campaign", campaign_profile_version="fixture-v2"),
        watermark=initial_watermark,
    ))
    _expect_contract_error(lambda: validate_event_identity(
        dict(evidence, event_id="event-stale-turn", turn_id="turn-stale", turn_sequence=0),
        watermark=first_watermark,
    ))
    _expect_contract_error(lambda: validate_event_identity(
        dict(evidence, event_id="event-sequence-rebound", turn_id="turn-2"),
        watermark=first_watermark,
    ))
    _expect_contract_error(lambda: validate_event_identity(
        dict(evidence, event_id="event-id-rebound", turn_sequence=2),
        watermark=first_watermark,
    ))
    _expect_contract_error(lambda: validate_event_identity(
        evidence,
        watermark=EventWatermarkV1(
            expected_session_id="session-fixture-1",
            expected_campaign_profile_id="emotion-state-phase-a-fixture",
            expected_campaign_profile_version="fixture-v1",
            last_turn_sequence=0,
            turn_sequence_by_id=(),
            turn_id_by_sequence=(),
            last_input_revision_by_turn=(),
            seen_event_ids=frozenset(),
        ),
    ))
    _expect_contract_error(lambda: validate_perceived_customer_state(dict(state, runtime_approved=True)))
    _expect_contract_error(lambda: validate_perceived_customer_state(dict(
        state,
        operational_signals=["possible_confusion", "none"],
    )))
    _expect_contract_error(lambda: validate_perceived_customer_state(dict(state, abstained=True)))
    _expect_contract_error(lambda: validate_perceived_customer_state(dict(
        abstained_state,
        allowed_policy_effects=["preserve", "soften"],
    )))
    _expect_contract_error(lambda: validate_perceived_customer_state(dict(
        state,
        blocked_policy_effects=["expand_action_set"],
    )))
    return "pass"
```

- [ ] **Step 2: Add the fixed case file**

The JSON must contain:

```json
{
  "checkpoint_id": "EMOTION-STATE-001-phase-a-contracts",
  "schema_version": 1,
  "source_label": "synthetic-only",
  "campaign_profile_id": "emotion-state-phase-a-fixture",
  "campaign_profile_version": "fixture-v1",
  "selected_public_datasets": [],
  "private_data_access_allowed": false,
  "provider_operations_allowed": false,
  "runtime_behavior_change_allowed": false,
  "runtime_activation_allowed": false,
  "baseline_fingerprints": {
    "packages/prompts/baseline-non-adaptive.txt": "BB1FD1EAC0D4DE858BFDCE4A880BBF2C59C14A216489A1A85EF149F3E88D7FCA",
    "packages/prompts/baseline-adaptive.txt": "EBD4106841987CA4A322C2B8B95A33ECFFC4238BB476DEC611A640D5B000EB42",
    "research/experiments/cases/exp-002-dataset-derived.json": "882B94C0A31C41A94540941A254AC7E8119CADE9AAD9B071089E854917BDC7D6",
    "research/experiments/EXP-002-dataset-derived-baseline.md": "D930C845AC912D44610B3CE263B55EA03BFFD7CAB8706C2BC95CB17045FF1316",
    "research/experiments/generated/EXP-002/EXP-002-prompt-packet.md": "14017F985D54D2B46A338EA2EFA796B24202E3E5A3D3EB8223346CEA96E5CD09",
    "docs/thesis/EVALUATION_RUBRIC.md": "39D3CF33E38A0C13ADEE178F3DB4174D4D8E3A42B1DE4C274BF96FFA36FFB416"
  }
}
```

- [ ] **Step 3: Run the contract section green**

```powershell
python scripts\validate_emotion_state_001_phase_a_contracts.py --section contracts
```

Expected: `EMOTION-STATE-001 Phase A validation passed: contracts`.

- [ ] **Step 4: Commit the base contracts**

```powershell
git add runtime\contracts\emotion_state_contracts.py research\experiments\cases\emotion-state-001-phase-a-contracts.json
git commit -m "Add EMOTION-STATE offline data contracts"
```

---

### Task 4: Implement Pattern Integrity Without Pretending Approval Authenticity

**Files:**

- Create: `runtime/contracts/emotion_pattern_contracts.py`
- Test: `scripts/validate_emotion_state_001_phase_a_contracts.py::validate_patterns`

**Interfaces:**

- Produces: `canonical_json_bytes()`, `content_digest()`, `approval_record_digest()`, `envelope_digest()`, `validate_pattern_candidate()`, `validate_pattern_content()`, `validate_detached_approval_shape()`, `validate_envelope_integrity()`, `authorize_runtime()`, and `pattern_contract_self_check()`.
- Does not produce: a real signature verifier, trust-store loader, promotion writer, or runtime-approved package.
- `PatternCandidateV1` validation is a Phase A structural/count-floor guard only. A later research runner must recompute speaker and turn counts from immutable labelled records and enforce no more than two qualifying turns per speaker; self-reported counts are never promotion evidence.

- [ ] **Step 1: Implement canonical digests and structural validation**

```python
from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from runtime.contracts.emotion_state_contracts import ALLOWED_POLICY_EFFECTS, REQUIRED_BLOCKED_POLICY_EFFECTS

PATTERN_CANDIDATE_FIELDS = frozenset({
    "candidate_id", "hypothesis", "feature_definition", "target_operational_signal",
    "discovery_dataset_version", "unique_speaker_count", "independent_turn_count",
    "annotation_agreement", "status", "runtime_influence_allowed",
})
FEATURE_DEFINITION_FIELDS = frozenset({
    "relationship", "direction", "null_comparator", "minimum_observed_effect",
    "eligible_turn_definition", "search_budget", "tested_hypothesis_count",
    "max_qualifying_turns_per_speaker",
})
ANNOTATION_AGREEMENT_FIELDS = frozenset({
    "metric", "point_estimate", "lower_95_ci", "upper_95_ci", "status",
})
PATTERN_CONTENT_FIELDS = frozenset({
    "pattern_version", "source_snapshot_hashes", "feature_schema_version", "label_schema_version",
    "speaker_split_manifest_hash", "text_only_baseline", "acoustic_only_result", "multimodal_result",
    "calibration_result", "confidence_intervals", "slice_results", "known_limits",
    "allowed_runtime_effects", "blocked_runtime_effects", "rollback_version", "minimum_engine_version",
    "maximum_engine_version", "compatible_evidence_schema_versions", "compatible_state_schema_versions",
    "registry_sequence",
})
APPROVAL_FIELDS = frozenset({
    "approval_stage", "candidate_content_digest", "decision", "reviewer_id", "decision_timestamp",
    "approved_constraints", "evidence_artifact_digests", "signing_key_id", "signature_algorithm",
    "approval_record_digest", "approval_signature",
})
ENVELOPE_FIELDS = frozenset({
    "pattern_content", "candidate_content_digest", "shadow_authorization", "shadow_report_digest",
    "runtime_activation_approval", "envelope_digest",
})


class PatternContractError(ValueError):
    pass


class RuntimeActivationBlocked(PatternContractError):
    pass


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest().upper()


def content_digest(pattern_content: dict[str, Any]) -> str:
    validate_pattern_content(pattern_content)
    return _sha256(pattern_content)


def approval_record_digest(approval: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in approval.items() if key not in {"approval_record_digest", "approval_signature"}}
    return _sha256(unsigned)


def envelope_digest(envelope: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in envelope.items() if key != "envelope_digest"}
    return _sha256(unsigned)


def _require_exact(payload: dict[str, Any], fields: frozenset[str], label: str) -> None:
    if not isinstance(payload, dict):
        raise PatternContractError(f"{label} must be an object")
    if set(payload) != fields:
        raise PatternContractError(f"{label} fields mismatch")


def _require_sha256(value: Any, label: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789ABCDEF" for character in value)
    ):
        raise PatternContractError(f"{label} must be an uppercase SHA-256 digest")


def _require_nonempty_string(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise PatternContractError(f"{label} must be a nonempty string")


def validate_pattern_candidate(payload: dict[str, Any]) -> dict[str, Any]:
    _require_exact(payload, PATTERN_CANDIDATE_FIELDS, "PatternCandidateV1")
    for field in ("candidate_id", "hypothesis", "target_operational_signal", "discovery_dataset_version"):
        _require_nonempty_string(payload[field], field)
    if payload["status"] != "candidate_hypothesis_only":
        raise PatternContractError("PatternCandidateV1 must remain a hypothesis")
    if payload["runtime_influence_allowed"] is not False:
        raise PatternContractError("PatternCandidateV1 cannot influence runtime")
    if type(payload["unique_speaker_count"]) is not int or payload["unique_speaker_count"] < 5:
        raise PatternContractError("PatternCandidateV1 requires at least five unique speakers")
    if type(payload["independent_turn_count"]) is not int or payload["independent_turn_count"] < 10:
        raise PatternContractError("PatternCandidateV1 requires at least ten independently labelled turns")
    if payload["target_operational_signal"] not in {
        "hesitation", "frustration", "confusion", "interest", "disengagement"
    }:
        raise PatternContractError("PatternCandidateV1 target signal is invalid")
    feature = payload["feature_definition"]
    if not isinstance(feature, dict):
        raise PatternContractError("feature_definition must be an object")
    _require_exact(feature, FEATURE_DEFINITION_FIELDS, "PatternCandidateV1.feature_definition")
    for field in ("relationship", "null_comparator", "eligible_turn_definition"):
        _require_nonempty_string(feature[field], f"feature_definition.{field}")
    if feature["direction"] not in {"increase", "decrease", "nonmonotonic"}:
        raise PatternContractError("feature_definition.direction is invalid")
    if (
        type(feature["minimum_observed_effect"]) not in {int, float}
        or not math.isfinite(feature["minimum_observed_effect"])
    ):
        raise PatternContractError("feature_definition.minimum_observed_effect must be finite numeric")
    if type(feature["search_budget"]) is not int or feature["search_budget"] < 1:
        raise PatternContractError("feature_definition.search_budget must be positive")
    if (
        type(feature["tested_hypothesis_count"]) is not int
        or not 1 <= feature["tested_hypothesis_count"] <= feature["search_budget"]
    ):
        raise PatternContractError("feature_definition.tested_hypothesis_count is outside the frozen budget")
    if feature["max_qualifying_turns_per_speaker"] != 2:
        raise PatternContractError("candidate discovery permits at most two qualifying turns per speaker")
    agreement = payload["annotation_agreement"]
    if not isinstance(agreement, dict):
        raise PatternContractError("annotation_agreement must be an object")
    _require_exact(agreement, ANNOTATION_AGREEMENT_FIELDS, "PatternCandidateV1.annotation_agreement")
    if agreement["metric"] != "nominal_krippendorff_alpha":
        raise PatternContractError("candidate annotation agreement metric is invalid")
    if agreement["status"] == "not_evaluated_in_phase_a":
        if any(agreement[field] is not None for field in ("point_estimate", "lower_95_ci", "upper_95_ci")):
            raise PatternContractError("unevaluated annotation agreement cannot carry estimates")
    elif agreement["status"] == "estimated":
        values = [agreement[field] for field in ("point_estimate", "lower_95_ci", "upper_95_ci")]
        if any(type(value) not in {int, float} or not -1.0 <= value <= 1.0 for value in values):
            raise PatternContractError("annotation agreement estimates are invalid")
        if not agreement["lower_95_ci"] <= agreement["point_estimate"] <= agreement["upper_95_ci"]:
            raise PatternContractError("annotation agreement interval is invalid")
    else:
        raise PatternContractError("annotation agreement status is invalid")
    return payload


def validate_pattern_content(payload: dict[str, Any]) -> dict[str, Any]:
    _require_exact(payload, PATTERN_CONTENT_FIELDS, "PatternPackageContentV1")
    for field in (
        "pattern_version", "feature_schema_version", "label_schema_version", "rollback_version",
        "minimum_engine_version", "maximum_engine_version",
    ):
        _require_nonempty_string(payload[field], field)
    hashes = payload["source_snapshot_hashes"]
    if not isinstance(hashes, list) or not hashes or any(not isinstance(digest, str) for digest in hashes) or len(hashes) != len(set(hashes)):
        raise PatternContractError("source_snapshot_hashes must be a nonempty unique list")
    for digest in hashes:
        _require_sha256(digest, "source_snapshot_hash")
    _require_sha256(payload["speaker_split_manifest_hash"], "speaker_split_manifest_hash")
    if payload["compatible_evidence_schema_versions"] != ["CustomerTurnEvidenceV1"]:
        raise PatternContractError("evidence schema compatibility is invalid for Phase A")
    if payload["compatible_state_schema_versions"] != ["PerceivedCustomerStateV1"]:
        raise PatternContractError("state schema compatibility is invalid for Phase A")
    for field in (
        "text_only_baseline", "acoustic_only_result", "multimodal_result", "calibration_result",
        "confidence_intervals", "slice_results",
    ):
        if not isinstance(payload[field], dict):
            raise PatternContractError(f"{field} must be an object")
    if (
        not isinstance(payload["known_limits"], list)
        or not payload["known_limits"]
        or any(not isinstance(limit, str) or not limit.strip() for limit in payload["known_limits"])
    ):
        raise PatternContractError("known_limits must be a nonempty list")
    if not isinstance(payload["registry_sequence"], int) or payload["registry_sequence"] < 1:
        raise PatternContractError("registry_sequence must be a positive integer")
    allowed = payload["allowed_runtime_effects"]
    blocked = payload["blocked_runtime_effects"]
    if not isinstance(allowed, list) or any(not isinstance(item, str) for item in allowed) or len(allowed) != len(set(allowed)) or set(allowed) - ALLOWED_POLICY_EFFECTS:
        raise PatternContractError("pattern content contains an invalid or expanding runtime effect")
    if not isinstance(blocked, list) or any(not isinstance(item, str) for item in blocked) or len(blocked) != len(set(blocked)):
        raise PatternContractError("blocked_runtime_effects must be a unique list")
    if set(blocked) != REQUIRED_BLOCKED_POLICY_EFFECTS:
        raise PatternContractError("pattern content must preserve every blocked runtime effect")
    if set(allowed) & set(blocked):
        raise PatternContractError("allowed and blocked runtime effects overlap")
    return payload


def validate_detached_approval_shape(payload: dict[str, Any], expected_stage: str) -> dict[str, Any]:
    _require_exact(payload, APPROVAL_FIELDS, "DetachedPatternApprovalV1")
    if payload["approval_stage"] != expected_stage:
        raise PatternContractError("approval stage mismatch")
    if payload["signature_algorithm"] != "Ed25519":
        raise PatternContractError("signature algorithm must be Ed25519")
    _require_sha256(payload["candidate_content_digest"], "candidate_content_digest")
    if not isinstance(payload["evidence_artifact_digests"], list):
        raise PatternContractError("evidence_artifact_digests must be a list")
    for digest in payload["evidence_artifact_digests"]:
        _require_sha256(digest, "evidence_artifact_digest")
    for field in ("decision", "reviewer_id", "decision_timestamp", "signing_key_id", "approval_signature"):
        _require_nonempty_string(payload[field], field)
    if not isinstance(payload["approved_constraints"], list) or not payload["approved_constraints"] or any(
        not isinstance(constraint, str) or not constraint.strip() for constraint in payload["approved_constraints"]
    ):
        raise PatternContractError("approved_constraints must be a nonempty string list")
    _require_sha256(payload["approval_record_digest"], "approval_record_digest")
    if approval_record_digest(payload) != payload["approval_record_digest"]:
        raise PatternContractError("approval record digest mismatch")
    return payload


def validate_envelope_integrity(payload: dict[str, Any]) -> dict[str, Any]:
    _require_exact(payload, ENVELOPE_FIELDS, "ApprovedPatternEnvelopeV1")
    content = validate_pattern_content(payload["pattern_content"])
    _require_sha256(payload["candidate_content_digest"], "candidate_content_digest")
    _require_sha256(payload["shadow_report_digest"], "shadow_report_digest")
    _require_sha256(payload["envelope_digest"], "envelope_digest")
    if content_digest(content) != payload["candidate_content_digest"]:
        raise PatternContractError("candidate content digest mismatch")
    shadow = validate_detached_approval_shape(payload["shadow_authorization"], "shadow_authorization")
    runtime = validate_detached_approval_shape(payload["runtime_activation_approval"], "runtime_activation")
    if shadow["candidate_content_digest"] != payload["candidate_content_digest"]:
        raise PatternContractError("shadow authorization targets another candidate")
    if runtime["candidate_content_digest"] != payload["candidate_content_digest"]:
        raise PatternContractError("runtime approval targets another candidate")
    if payload["shadow_report_digest"] not in runtime["evidence_artifact_digests"]:
        raise PatternContractError("runtime approval does not bind the shadow report")
    if envelope_digest(payload) != payload["envelope_digest"]:
        raise PatternContractError("envelope digest mismatch")
    return payload


def authorize_runtime(payload: dict[str, Any]) -> None:
    validate_envelope_integrity(payload)
    raise RuntimeActivationBlocked(
        "EMOTION-STATE-001 Phase A has no signature verifier, trust store, promotion ACL, or runtime activation path"
    )
```

Append this deterministic structural self-check. Its signature strings are explicitly invalid test fixtures and cannot authorize runtime use:

```python
def _expect_pattern_error(callback: Any) -> None:
    try:
        callback()
    except PatternContractError:
        return
    raise AssertionError("expected PatternContractError")


def _fixture_approval(stage: str, candidate_digest: str, evidence_digests: list[str]) -> dict[str, Any]:
    approval = {
        "approval_stage": stage,
        "candidate_content_digest": candidate_digest,
        "decision": "approved_for_structural_fixture_only",
        "reviewer_id": "fixture-reviewer-not-authorized",
        "decision_timestamp": "2026-07-14T00:00:00Z",
        "approved_constraints": ["runtime_activation_blocked"],
        "evidence_artifact_digests": evidence_digests,
        "signing_key_id": "fixture-key-not-trusted",
        "signature_algorithm": "Ed25519",
    }
    approval["approval_record_digest"] = approval_record_digest(approval)
    approval["approval_signature"] = "test-fixture-not-a-valid-signature"
    return approval


def pattern_contract_self_check() -> str:
    candidate = {
        "candidate_id": "fixture-candidate-1",
        "hypothesis": "fixture relationship for structural validation only",
        "feature_definition": {
            "relationship": "synthetic structural relationship",
            "direction": "increase",
            "null_comparator": "no_association",
            "minimum_observed_effect": 0.0,
            "eligible_turn_definition": "synthetic_fixture_turns_only",
            "search_budget": 1,
            "tested_hypothesis_count": 1,
            "max_qualifying_turns_per_speaker": 2,
        },
        "target_operational_signal": "confusion",
        "discovery_dataset_version": "synthetic-fixture-v1",
        "unique_speaker_count": 5,
        "independent_turn_count": 10,
        "annotation_agreement": {
            "metric": "nominal_krippendorff_alpha",
            "point_estimate": None,
            "lower_95_ci": None,
            "upper_95_ci": None,
            "status": "not_evaluated_in_phase_a",
        },
        "status": "candidate_hypothesis_only",
        "runtime_influence_allowed": False,
    }
    validate_pattern_candidate(candidate)
    _expect_pattern_error(lambda: validate_pattern_candidate(dict(candidate, unique_speaker_count=4)))
    _expect_pattern_error(lambda: validate_pattern_candidate(dict(candidate, runtime_influence_allowed=True)))
    _expect_pattern_error(lambda: validate_pattern_candidate(dict(
        candidate,
        feature_definition=dict(candidate["feature_definition"], max_qualifying_turns_per_speaker=3),
    )))
    _expect_pattern_error(lambda: validate_pattern_candidate(dict(
        candidate,
        feature_definition=dict(candidate["feature_definition"], minimum_observed_effect=float("inf")),
    )))

    content = {
        "pattern_version": "fixture-pattern-v1",
        "source_snapshot_hashes": ["A" * 64],
        "feature_schema_version": "feature-v1",
        "label_schema_version": "label-v1",
        "speaker_split_manifest_hash": "B" * 64,
        "text_only_baseline": {"macro_f1": 0.50},
        "acoustic_only_result": {"macro_f1": 0.40},
        "multimodal_result": {"macro_f1": 0.56},
        "calibration_result": {"brier": 0.18},
        "confidence_intervals": {"macro_f1_lift": [0.01, 0.11]},
        "slice_results": {},
        "known_limits": ["synthetic_fixture_only"],
        "allowed_runtime_effects": ["preserve", "soften", "clarify", "abstain"],
        "blocked_runtime_effects": sorted(REQUIRED_BLOCKED_POLICY_EFFECTS),
        "rollback_version": "text-only",
        "minimum_engine_version": "1",
        "maximum_engine_version": "1",
        "compatible_evidence_schema_versions": ["CustomerTurnEvidenceV1"],
        "compatible_state_schema_versions": ["PerceivedCustomerStateV1"],
        "registry_sequence": 1,
    }
    candidate_digest = content_digest(content)
    shadow_report_digest = "C" * 64
    shadow = _fixture_approval("shadow_authorization", candidate_digest, [])
    runtime = _fixture_approval("runtime_activation", candidate_digest, [shadow_report_digest])
    envelope = {
        "pattern_content": content,
        "candidate_content_digest": candidate_digest,
        "shadow_authorization": shadow,
        "shadow_report_digest": shadow_report_digest,
        "runtime_activation_approval": runtime,
    }
    envelope["envelope_digest"] = envelope_digest(envelope)
    validate_envelope_integrity(envelope)
    assert candidate_digest == content_digest(json.loads(canonical_json_bytes(content)))

    tampered_content = json.loads(canonical_json_bytes(envelope))
    tampered_content["pattern_content"]["registry_sequence"] = 2
    _expect_pattern_error(lambda: validate_envelope_integrity(tampered_content))

    tampered_approval = json.loads(canonical_json_bytes(envelope))
    tampered_approval["runtime_activation_approval"]["reviewer_id"] = "forged-reviewer"
    _expect_pattern_error(lambda: validate_envelope_integrity(tampered_approval))

    unbound_runtime = _fixture_approval("runtime_activation", candidate_digest, [])
    unbound_envelope = dict(envelope, runtime_activation_approval=unbound_runtime)
    unbound_envelope["envelope_digest"] = envelope_digest(unbound_envelope)
    _expect_pattern_error(lambda: validate_envelope_integrity(unbound_envelope))
    _expect_pattern_error(lambda: validate_pattern_content(dict(
        content,
        allowed_runtime_effects=["increase_persuasion_intensity"],
    )))
    _expect_pattern_error(lambda: validate_pattern_content(dict(
        content,
        blocked_runtime_effects=["expand_action_set"],
    )))
    _expect_pattern_error(lambda: validate_pattern_content(dict(
        content,
        source_snapshot_hashes=["a" * 64],
    )))
    _expect_pattern_error(lambda: authorize_runtime(envelope))
    return "pass"
```

- [ ] **Step 2: Run the pattern section green**

```powershell
python scripts\validate_emotion_state_001_phase_a_contracts.py --section patterns
```

Expected: `EMOTION-STATE-001 Phase A validation passed: patterns`.

- [ ] **Step 3: Commit pattern integrity contracts**

```powershell
git add runtime\contracts\emotion_pattern_contracts.py
git commit -m "Add fail-closed EMOTION-STATE pattern contracts"
```

---

### Task 5: Add A Detached Offline BRAIN Extension

**Files:**

- Create: `runtime/contracts/emotion_state_brain_extension.py`
- Modify: `docs/brain/BRAIN_002_RUNTIME_STATE_SCHEMA.md`
- Test: `scripts/validate_emotion_state_001_phase_a_contracts.py::validate_brain_extension`
- Regression: `scripts/validate_brain_002_runtime_state_schema.py`

**Interfaces:**

- Consumes: validated `PerceivedCustomerStateV1` and an immutable `decision:uuid:<canonical-lowercase-uuid-v4>` text-only decision reference issued independently of decision text.
- Produces: `build_offline_brain_extension(state, text_only_policy_decision_ref)` and `brain_extension_self_check()`.
- Explicitly does not modify a BRAIN-002 packet.

- [ ] **Step 1: Implement the detached mapping and hard runtime block**

```python
from __future__ import annotations

from copy import deepcopy
from typing import Any

from runtime.contracts.emotion_state_contracts import (
    EmotionStateContractError,
    REQUIRED_BLOCKED_POLICY_EFFECTS,
    validate_decision_reference,
    validate_perceived_customer_state,
)

EXTENSION_SCHEMA_VERSION = "emotion-state-brain-extension-v1"


class BrainExtensionBlocked(ValueError):
    pass


def build_offline_brain_extension(
    state: dict[str, Any],
    text_only_policy_decision_ref: str,
) -> dict[str, Any]:
    try:
        validate_perceived_customer_state(state)
    except EmotionStateContractError as exc:
        raise BrainExtensionBlocked("invalid PerceivedCustomerStateV1") from exc
    try:
        validate_decision_reference(text_only_policy_decision_ref, "text_only_policy_decision_ref")
    except EmotionStateContractError as exc:
        raise BrainExtensionBlocked("invalid text-only policy decision reference") from exc
    if set(state["blocked_policy_effects"]) != REQUIRED_BLOCKED_POLICY_EFFECTS:
        raise BrainExtensionBlocked("monotonic blocked effects are incomplete")
    return {
        "schema_version": EXTENSION_SCHEMA_VERSION,
        "buyer_state_patch": {
            "emotional_signal": state["selected_policy_signal"],
            "emotion_confidence": state["selected_signal_confidence_bucket"],
            "evidence_refs": list(state["evidence_refs"]),
        },
        "state_evidence_by_modality": deepcopy(state["signal_provenance_by_modality"]),
        "allowed_policy_effects": list(state["allowed_policy_effects"]),
        "blocked_policy_effects": list(state["blocked_policy_effects"]),
        "text_only_policy_decision_ref": text_only_policy_decision_ref,
        "runtime_connection_allowed": False,
        "runtime_approved": False,
    }


def apply_extension_to_brain_packet(packet: dict[str, Any], extension: dict[str, Any]) -> None:
    del packet, extension
    raise BrainExtensionBlocked("BRAIN-002 v1 mutation and runtime connection are blocked under EMOTION-STATE-001")
```

Append this self-check:

```python
def _expect_brain_block(callback: Any) -> None:
    try:
        callback()
    except BrainExtensionBlocked:
        return
    raise AssertionError("expected BrainExtensionBlocked")


def brain_extension_self_check() -> str:
    state = {
        "call_session_id": "session-fixture-1",
        "campaign_profile_id": "emotion-state-phase-a-fixture",
        "campaign_profile_version": "fixture-v1",
        "turn_id": "turn-1",
        "turn_sequence": 1,
        "valence_estimate": "not_inferable",
        "activation_estimate": "not_inferable",
        "engagement_estimate": "not_inferable",
        "operational_signals": ["possible_confusion"],
        "confidence_by_signal": {"possible_confusion": 0.6},
        "selected_policy_signal": "possible_confusion",
        "selected_signal_confidence_bucket": "medium",
        "overall_evidence_quality": "text_only",
        "trajectory": "insufficient_history",
        "evidence_refs": ["evidence:uuid:11111111-1111-4111-8111-111111111111"],
        "signal_provenance_by_modality": {
            "possible_confusion": {
                "text": ["evidence:uuid:11111111-1111-4111-8111-111111111111"],
                "acoustic": [],
            },
        },
        "allowed_policy_effects": ["preserve", "clarify", "soften"],
        "blocked_policy_effects": sorted(REQUIRED_BLOCKED_POLICY_EFFECTS),
        "abstained": False,
        "abstention_reasons": [],
        "evidence_policy_version": "emotion-state-evidence-v1",
        "runtime_approved": False,
    }
    decision_ref = "decision:uuid:33333333-3333-4333-8333-333333333333"
    extension = build_offline_brain_extension(state, decision_ref)
    assert set({
        "state_evidence_by_modality", "allowed_policy_effects", "blocked_policy_effects",
        "text_only_policy_decision_ref",
    }).issubset(extension)
    assert extension["runtime_connection_allowed"] is False
    assert extension["runtime_approved"] is False
    extension["state_evidence_by_modality"]["possible_confusion"]["text"].append(
        "evidence:uuid:44444444-4444-4444-8444-444444444444"
    )
    assert len(state["signal_provenance_by_modality"]["possible_confusion"]["text"]) == 1
    incomplete = dict(state, blocked_policy_effects=["expand_action_set"])
    _expect_brain_block(lambda: build_offline_brain_extension(incomplete, decision_ref))
    _expect_brain_block(lambda: build_offline_brain_extension(state, " "))
    _expect_brain_block(lambda: build_offline_brain_extension(state, "raw decision sentence"))
    _expect_brain_block(lambda: build_offline_brain_extension(state, "x" * 161))
    _expect_brain_block(lambda: build_offline_brain_extension(state, None))
    _expect_brain_block(lambda: apply_extension_to_brain_packet({}, extension))
    return "pass"
```

- [ ] **Step 2: Document the extension without changing BRAIN-002 v1**

Add a section to `docs/brain/BRAIN_002_RUNTIME_STATE_SCHEMA.md` stating:

```markdown
## EMOTION-STATE Detached Extension

`emotion-state-brain-extension-v1` is an offline contract only. It carries `state_evidence_by_modality`, `allowed_policy_effects`, `blocked_policy_effects`, and `text_only_policy_decision_ref` alongside a proposed mapping to the existing three buyer-state fields.

It does not mutate `brain-runtime-state-v1`, enter a live trace, feed the action selector, alter a response, or authorize acoustic influence. A later versioned BRAIN migration and runtime-activation checkpoint are required before connection.
```

- [ ] **Step 3: Run the new and old validators**

```powershell
python scripts\validate_emotion_state_001_phase_a_contracts.py --section brain
python scripts\validate_brain_002_runtime_state_schema.py
```

Expected: both commands exit `0`; the existing BRAIN-002 generated payload remains `brain-runtime-state-v1`.

- [ ] **Step 4: Commit the detached extension**

```powershell
git add runtime\contracts\emotion_state_brain_extension.py docs\brain\BRAIN_002_RUNTIME_STATE_SCHEMA.md
git commit -m "Add offline EMOTION-STATE BRAIN extension"
```

---

### Task 6: Build The Phase A Checkpoint And Evidence

**Files:**

- Create: `scripts/emotion_state_phase_a_contracts.py`
- Create: `scripts/run_emotion_state_001_phase_a_contracts.py`
- Create: `research/experiments/EMOTION-STATE-001-phase-a.md`
- Create: `docs/product/EMOTION_STATE_001_PHASE_A_CONTRACTS.md`
- Create by runner: `research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/result.json`
- Create by runner: `research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/report.md`
- Modify: `docs/product/COMMANDS.md`
- Test: `scripts/validate_emotion_state_001_phase_a_contracts.py::validate_checkpoint`

**Interfaces:**

- Consumes: fixed case, source manifest, contract self-checks, and hashes of the frozen baseline artifacts.
- Produces: `build_phase_a_payload(case_path, root)`, `render_phase_a_report(payload)`, and a deterministic result/report pair.

- [ ] **Step 1: Implement the checkpoint builder**

```python
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.contracts.emotion_pattern_contracts import pattern_contract_self_check
from runtime.contracts.emotion_state_brain_extension import brain_extension_self_check
from runtime.contracts.emotion_state_contracts import contract_self_check
from scripts.exp_002_frozen_response_baseline import frozen_baseline_self_check
from scripts.emotion_state_annotation_contracts import annotation_contract_self_check

EXPECTED_BASELINE_FINGERPRINTS = {
    "packages/prompts/baseline-non-adaptive.txt": "BB1FD1EAC0D4DE858BFDCE4A880BBF2C59C14A216489A1A85EF149F3E88D7FCA",
    "packages/prompts/baseline-adaptive.txt": "EBD4106841987CA4A322C2B8B95A33ECFFC4238BB476DEC611A640D5B000EB42",
    "research/experiments/cases/exp-002-dataset-derived.json": "882B94C0A31C41A94540941A254AC7E8119CADE9AAD9B071089E854917BDC7D6",
    "research/experiments/EXP-002-dataset-derived-baseline.md": "D930C845AC912D44610B3CE263B55EA03BFFD7CAB8706C2BC95CB17045FF1316",
    "research/experiments/generated/EXP-002/EXP-002-prompt-packet.md": "14017F985D54D2B46A338EA2EFA796B24202E3E5A3D3EB8223346CEA96E5CD09",
    "docs/thesis/EVALUATION_RUBRIC.md": "39D3CF33E38A0C13ADEE178F3DB4174D4D8E3A42B1DE4C274BF96FFA36FFB416",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def validate_phase_a_case(case: dict[str, Any]) -> None:
    expected = {
        "checkpoint_id": "EMOTION-STATE-001-phase-a-contracts",
        "schema_version": 1,
        "source_label": "synthetic-only",
        "selected_public_datasets": [],
        "private_data_access_allowed": False,
        "provider_operations_allowed": False,
        "runtime_behavior_change_allowed": False,
        "runtime_activation_allowed": False,
        "baseline_fingerprints": EXPECTED_BASELINE_FINGERPRINTS,
    }
    mismatched = {key: case.get(key) for key, value in expected.items() if case.get(key) != value}
    if mismatched:
        raise ValueError(f"invalid Phase A case boundary: {mismatched}")


def build_phase_a_payload(case_path: Path, *, root: Path) -> dict[str, Any]:
    case = read_json(case_path)
    validate_phase_a_case(case)
    manifest_path = root / "research" / "sources" / "creative_analysis_engine" / "source_manifest.json"
    manifest = read_json(manifest_path)
    material_fields = (
        "copied_material", "translated_material", "adapted_material", "independently_reimplemented_material",
    )
    code_adaptation_started = any(manifest[field] for field in material_fields)
    baseline = {
        relative_path: sha256_file(root / relative_path)
        for relative_path in case["baseline_fingerprints"]
    }
    if baseline != case["baseline_fingerprints"]:
        raise ValueError("frozen baseline fingerprint drift")
    checks = {
        "exp_002_frozen_response_baseline": frozen_baseline_self_check(root),
        "emotion_state_annotation_contracts": annotation_contract_self_check(),
        "emotion_state_contracts": contract_self_check(),
        "emotion_pattern_contracts": pattern_contract_self_check(),
        "emotion_state_brain_extension": brain_extension_self_check(),
    }
    return {
        "checkpoint_id": "EMOTION-STATE-001-phase-a-contracts",
        "schema_version": 1,
        "status": "contract_artifact_validation_only_source_dataset_and_privacy_gates_open",
        "summary": {
            "contract_check_count": len(checks),
            "contract_checks": checks,
            "baseline_fingerprint_count": len(baseline),
            "selected_public_dataset_count": len(case["selected_public_datasets"]),
            "source_repository_url_status": manifest["source_repository_url_status"],
            "source_adaptation_allowed": manifest["adaptation_allowed"],
            "code_adaptation_started": code_adaptation_started,
            "provider_operations_performed_by_runner": False,
            "private_data_read_by_runner": False,
            "runtime_behavior_changed_by_runner": False,
            "runtime_activation_allowed": False,
        },
        "archive_sha256": manifest["archive_sha256"],
        "baseline_fingerprints": baseline,
        "readiness_boundary": {
            "phase_a_contract_artifacts_built": True,
            "phase_a_complete": False,
            "full_repository_gate_claimed_by_this_artifact": False,
            "live_aggregate_release_unblocked": False,
            "phase_b_unblocked": False,
            "public_dataset_evaluation_unblocked": False,
            "private_research_unblocked": False,
            "provider_feasibility_unblocked": False,
            "runtime_activation_unblocked": False,
        },
    }


def render_phase_a_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return "\n".join([
        "# EMOTION-STATE-001 Phase A Contract Report",
        "",
        "This artifact validates offline contract artifacts only; it does not claim that the full repository gate or all of Phase A is complete.",
        "",
        f"- Contract checks: `{summary['contract_check_count']}`",
        f"- Baseline fingerprints: `{summary['baseline_fingerprint_count']}`",
        f"- Selected public datasets: `{summary['selected_public_dataset_count']}`",
        f"- Source URL status: `{summary['source_repository_url_status']}`",
        f"- Code adaptation started: `{summary['code_adaptation_started']}`",
        f"- Provider operations performed by this runner: `{summary['provider_operations_performed_by_runner']}`",
        f"- Private data read by this runner: `{summary['private_data_read_by_runner']}`",
        f"- Runtime behavior changed by this runner: `{summary['runtime_behavior_changed_by_runner']}`",
        "",
        "Source adaptation remains blocked by the source URL, revision or authoritative archive date, Phase B reuse scope, Phase B attribution wording, and separate Phase B approval.",
        "Per-public-dataset manifests remain open. Acted and non-sales corpora can support offline thesis comparison only. Runtime activation remains blocked.",
        "Live aggregate release remains blocked until a separately approved privacy-preserving unique-speaker cohort-release and dedup gate exists.",
        "",
        "This is not production readiness, real-customer validation, PSTN/ASR/latency validation, or proof of internal customer emotion.",
        "",
    ])
```

- [ ] **Step 2: Implement the project-path-safe runner**

Create the runner with this complete implementation:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.emotion_state_phase_a_contracts import build_phase_a_payload, render_phase_a_report

DEFAULT_CASE = ROOT / "research" / "experiments" / "cases" / "emotion-state-001-phase-a-contracts.json"
DEFAULT_OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / "EMOTION-STATE-001-phase-a-contracts"
DEFAULT_RESULT = DEFAULT_OUTPUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "report.md"
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build EMOTION-STATE-001 Phase A contract evidence.")
    parser.add_argument("--case", default=str(DEFAULT_CASE))
    parser.add_argument("--out", default=str(DEFAULT_RESULT))
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT))
    return parser.parse_args()


def _contains_private_path(path: Path) -> bool:
    parts = tuple(part.lower() for part in path.parts)
    return any(
        parts[index:index + len(private_parts)] == private_parts
        for private_parts in PRIVATE_PATH_PARTS
        for index in range(0, len(parts) - len(private_parts) + 1)
    )


def resolve_project_path(path_value: str, *, allowed_root: Path) -> Path:
    candidate = Path(path_value)
    resolved = (candidate if candidate.is_absolute() else ROOT / candidate).resolve(strict=False)
    try:
        resolved.relative_to(ROOT.resolve(strict=False))
    except ValueError as exc:
        raise ValueError(f"path must stay inside project root: {path_value}") from exc
    if _contains_private_path(resolved):
        raise ValueError(f"private path is blocked: {path_value}")
    try:
        resolved.relative_to(allowed_root.resolve(strict=False))
    except ValueError as exc:
        raise ValueError(f"path is outside its allowed artifact root: {path_value}") from exc
    return resolved


def main() -> int:
    args = parse_args()
    case_path = resolve_project_path(args.case, allowed_root=DEFAULT_CASE.parent)
    result_path = resolve_project_path(args.out, allowed_root=DEFAULT_OUTPUT_DIR)
    report_path = resolve_project_path(args.report_out, allowed_root=DEFAULT_OUTPUT_DIR)
    if result_path == report_path:
        raise ValueError("result and report paths must be distinct")
    payload = build_phase_a_payload(case_path, root=ROOT)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report_path.write_text(render_phase_a_report(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Add the experiment note and product doc**

The experiment note must follow `research/experiments/EXPERIMENT_TEMPLATE.md` and record:

```markdown
Status: Pending full repository gate
Source Label: `synthetic-only`
Decision: Pending
Editable scope: provenance and contract files only
Fixed constraints: no code adaptation, no private data, no provider, no live aggregate release, no runtime influence
Result: contract artifacts generated; acceptance waits for Task 7. Per-public-dataset manifests and the privacy-preserving unique-speaker cohort-release/dedup design remain open, so this cannot complete all of Phase A.
```

The product doc must list the four baseline/checkpoint runner and validator commands, both exact output folders, contract names, baseline-fingerprint meaning, unresolved source/dataset blockers, the open privacy-preserving unique-speaker cohort-release/dedup gate, and the offline/prototype readiness boundary. State that prompt-packet normalization proves deterministic rendering, while the separate Task 0 scorer reruns only frozen response/rating structure, totals, preferences, and aggregate arithmetic. Neither path regenerates responses or repeats semantic judgment, and the frozen record's evaluator provenance must remain `not_recorded`.

- [ ] **Step 4: Add commands and generate evidence**

Add to `docs/product/COMMANDS.md`:

```powershell
python scripts\run_exp_002_frozen_response_baseline.py
python scripts\validate_exp_002_frozen_response_baseline.py
python scripts\run_emotion_state_001_phase_a_contracts.py
python scripts\validate_emotion_state_001_phase_a_contracts.py
```

Then run:

```powershell
python scripts\run_emotion_state_001_phase_a_contracts.py
python scripts\validate_emotion_state_001_phase_a_contracts.py --section checkpoint
```

Expected: result/report are written only under `research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/`, and checkpoint validation passes.

- [ ] **Step 5: Commit the checkpoint evidence**

```powershell
git add scripts\emotion_state_phase_a_contracts.py scripts\run_emotion_state_001_phase_a_contracts.py research\experiments\EMOTION-STATE-001-phase-a.md research\experiments\generated\EMOTION-STATE-001-phase-a-contracts docs\product\EMOTION_STATE_001_PHASE_A_CONTRACTS.md docs\product\COMMANDS.md
git commit -m "Build EMOTION-STATE Phase A checkpoint"
```

---

### Task 7: Register The Contract Surfaces And Run The Full Gate

**Files:**

- Modify: `runtime/runtime_manifest.json`
- Modify: `scripts/validate_runtime_manifest.py`
- Modify: `scripts/check_setup.py`
- Modify: `scripts/validate_check_setup.py`
- Modify: `scripts/check_project_drift.py`
- Modify: `scripts/validate_project_drift_guard.py`
- Modify: `docs/thesis/DECISION_LOG.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`
- Modify: `research/experiments/EMOTION-STATE-001-phase-a.md`
- Test: all focused and repository policy validators below.

**Interfaces:**

- Consumes: every Phase A artifact.
- Produces: discoverable runtime-contract inventory, setup/drift coverage, and thesis traceability.

- [ ] **Step 1: Register the three non-integrated contract files**

Add three runtime-manifest entries with these exact paths and roles:

```json
{
  "path": "runtime/contracts/emotion_state_contracts.py",
  "path_type": "file",
  "tier": "core-runtime-contract",
  "runtime_role": "Offline-only EMOTION-STATE V1 evidence, audit, aggregate, perceived-state, persistence, and event-identity contracts; not imported by live runtime.",
  "behavior_surface": ["contract validation only", "no live runtime import", "no provider behavior"]
}
```

```json
{
  "path": "runtime/contracts/emotion_pattern_contracts.py",
  "path_type": "file",
  "tier": "core-runtime-contract",
  "runtime_role": "Offline-only EMOTION-STATE pattern serialization and digest contracts with runtime activation hard-blocked.",
  "behavior_surface": ["artifact integrity only", "no signature authenticity claim", "no runtime activation"]
}
```

```json
{
  "path": "runtime/contracts/emotion_state_brain_extension.py",
  "path_type": "file",
  "tier": "core-runtime-contract",
  "runtime_role": "Detached offline BRAIN extension carrying modality provenance and monotonic policy bounds without mutating BRAIN-002 v1.",
  "behavior_surface": ["offline mapping only", "BRAIN-002 v1 unchanged", "runtime connection blocked"]
}
```

Add the three paths to `REQUIRED_RUNTIME_PATHS` in `scripts/validate_runtime_manifest.py`, update `runtime/runtime_manifest.json.updated_on` to `2026-07-14`, and run `python scripts\validate_runtime_manifest.py`.

- [ ] **Step 2: Register setup and drift coverage symmetrically**

Add these exact tuples to `REQUIRED_FILES` in `scripts/check_setup.py`:

```python
PHASE_A_REQUIRED_FILES = [
    ("file.scripts_exp_002_frozen_response_baseline", "scripts/exp_002_frozen_response_baseline.py", "Frozen EXP-002 response scorer"),
    ("file.scripts_run_exp_002_frozen_response_baseline", "scripts/run_exp_002_frozen_response_baseline.py", "Frozen EXP-002 response scorer runner"),
    ("file.scripts_validate_exp_002_frozen_response_baseline", "scripts/validate_exp_002_frozen_response_baseline.py", "Frozen EXP-002 response scorer validator"),
    ("file.runtime_contracts_emotion_state_contracts", "runtime/contracts/emotion_state_contracts.py", "EMOTION-STATE evidence and persistence contracts"),
    ("file.runtime_contracts_emotion_pattern_contracts", "runtime/contracts/emotion_pattern_contracts.py", "EMOTION-STATE pattern integrity contracts"),
    ("file.runtime_contracts_emotion_state_brain_extension", "runtime/contracts/emotion_state_brain_extension.py", "Detached EMOTION-STATE BRAIN extension"),
    ("file.scripts_emotion_state_annotation_contracts", "scripts/emotion_state_annotation_contracts.py", "EMOTION-STATE reviewer aggregation contracts"),
    ("file.scripts_emotion_state_phase_a_contracts", "scripts/emotion_state_phase_a_contracts.py", "EMOTION-STATE Phase A checkpoint builder"),
    ("file.scripts_run_emotion_state_001_phase_a_contracts", "scripts/run_emotion_state_001_phase_a_contracts.py", "EMOTION-STATE Phase A checkpoint runner"),
    ("file.scripts_validate_emotion_state_001_phase_a_contracts", "scripts/validate_emotion_state_001_phase_a_contracts.py", "EMOTION-STATE Phase A validator"),
    ("file.research_case_emotion_state_001_phase_a_contracts", "research/experiments/cases/emotion-state-001-phase-a-contracts.json", "EMOTION-STATE Phase A fixed case"),
    ("file.research_experiment_emotion_state_001_phase_a", "research/experiments/EMOTION-STATE-001-phase-a.md", "EMOTION-STATE Phase A experiment note"),
    ("file.docs_product_emotion_state_001_phase_a_contracts", "docs/product/EMOTION_STATE_001_PHASE_A_CONTRACTS.md", "EMOTION-STATE Phase A product contract"),
    ("file.docs_data_emotion_state_001_annotation_codebook", "docs/data/EMOTION_STATE_001_ANNOTATION_CODEBOOK.md", "EMOTION-STATE annotation codebook"),
    ("file.research_source_creative_analysis_engine_manifest", "research/sources/creative_analysis_engine/source_manifest.json", "Creative Analysis Engine source manifest"),
    ("file.research_source_creative_analysis_engine_notes", "research/sources/creative_analysis_engine/source_notes.md", "Creative Analysis Engine source notes"),
    ("file.research_source_emotion_state_dataset_manifest_contract", "research/sources/emotion_state/dataset_manifest_contract.json", "EMOTION-STATE dataset-manifest contract"),
    ("file.research_source_emotion_state_annotation_record_schema", "research/sources/emotion_state/annotation_record_v1.schema.json", "EMOTION-STATE annotation-record schema"),
    ("file.research_source_emotion_state_split_manifest_schema", "research/sources/emotion_state/split_manifest_v1.schema.json", "EMOTION-STATE split-manifest schema"),
]
```

Insert the tuple entries (not the `PHASE_A_REQUIRED_FILES` variable) into the existing `REQUIRED_FILES` list. Add each first element to the matching required-ID set in `scripts/validate_check_setup.py`. Add each second element to both `scripts/check_project_drift.py` and `scripts/validate_project_drift_guard.py`; keep the two drift lists identical.

- [ ] **Step 3: Add the thesis decisions without overstating evidence**

Append `DEC-021` to `docs/thesis/DECISION_LOG.md`:

```markdown
### DEC-021 - Start customer-state work with an offline provenance and contract foundation

- Date: 2026-07-14
- Status: accepted
- Decision: implement EMOTION-STATE-001 as separate gated phases, beginning with source provenance, annotation rules, strict contracts, and a detached BRAIN extension.
- Why: acoustic cues are ambiguous, current affect fields can influence sales selection, BRAIN-002 v1 cannot enforce modality provenance or monotonic de-escalation, and public/private data provenance is incomplete.
- Consequences: no acoustic code adaptation, private-data ingestion, provider work, live wiring, runtime activation, or customer-state claim is authorized by Phase A.
```

Append a methodology entry that lists the files and validator evidence, records the verified archive hash, states the URL/revision blockers, records that author permission is confirmed and license metadata is not being used as permission authority, notes that Task 0 fingerprinted the baseline and reran frozen score arithmetic without regenerating responses or repeating semantic judgment, explicitly records `evaluator_provenance_status = not_recorded` because evaluator type, identity or role, count, and procedure are absent from the frozen evidence, records `phase_a_complete=false` until both exact per-public-dataset manifests and the separately approved privacy-preserving unique-speaker cohort-release/dedup gate are designed, approved, satisfied, and validated, and repeats the no-provider/no-private/no-runtime boundary.

- [ ] **Step 4: Run focused validation**

```powershell
python scripts\validate_exp_002_frozen_response_baseline.py
python scripts\validate_emotion_state_001_phase_a_contracts.py
python scripts\validate_brain_002_runtime_state_schema.py
python scripts\validate_product_agent_output_contract.py
python scripts\validate_runtime_manifest.py
python scripts\validate_private_data_boundary.py
python scripts\validate_self_contained_project_policy.py
```

Expected: all commands exit `0`. Inspect the Phase A result/report directly; do not infer success from validator labels alone.

- [ ] **Step 5: Run repository governance validation**

```powershell
python scripts\validate_check_setup.py
python scripts\validate_project_drift_guard.py
python scripts\check_thesis_reference_registry.py
python scripts\check_thesis_update_gate.py
python scripts\validate_context_reading_policy.py
git diff --check
```

Expected: all Python commands exit `0`; `git diff --check` prints nothing. Do not baseline, waive, or subtract pre-existing reference-registry failures. If the unrelated Atlas/ElevenLabs registry debt still exists, stop and report Task 7 as blocked rather than editing it under this feature.

- [ ] **Step 6: Verify forbidden imports and change scope**

```powershell
rg -n "emotion_state_(contracts|brain_extension)|emotion_pattern_contracts" runtime\entrypoints runtime\core runtime\action_selector runtime\providers
rg -n "^(from|import) (numpy|librosa|scipy|soundfile|pydantic|pytest)(\.| |$)" runtime\contracts\emotion_state_contracts.py runtime\contracts\emotion_pattern_contracts.py runtime\contracts\emotion_state_brain_extension.py scripts\exp_002_frozen_response_baseline.py scripts\run_exp_002_frozen_response_baseline.py scripts\validate_exp_002_frozen_response_baseline.py scripts\emotion_state_annotation_contracts.py scripts\emotion_state_phase_a_contracts.py scripts\run_emotion_state_001_phase_a_contracts.py scripts\validate_emotion_state_001_phase_a_contracts.py
git diff HEAD~7 --name-only | rg --pcre2 "(^|/)(requirements[^/]*\.txt|pyproject\.toml|setup\.py|setup\.cfg|Pipfile|poetry\.lock|uv\.lock|package(-lock)?\.json)$"
git diff HEAD~7 --name-only
git status --short --branch
```

Expected: all three `rg` commands have no matches. The diff contains only files named in this plan and no provider/ElevenLabs or dependency-metadata file. Because `rg` returns exit `1` for no matches, run these as inspection commands rather than a chained success condition.

- [ ] **Step 7: Commit the completed partial Phase A foundation checkpoint**

Only after Steps 4-6 pass, update the experiment note to:

```markdown
Status: Completed - partial Phase A contract foundation checkpoint
Decision: Keep contract foundation; per-public-dataset manifest and privacy-preserving unique-speaker cohort-release/dedup subgates remain open
Result: all Task 7 validators passed; generated result/report remain artifact-only evidence and do not claim the full gate themselves
```

Record the exact commands and exit results in the experiment note. Do not change `readiness_boundary.phase_a_complete=false` in the generated result.

```powershell
git add runtime\runtime_manifest.json scripts\validate_runtime_manifest.py scripts\check_setup.py scripts\validate_check_setup.py scripts\check_project_drift.py scripts\validate_project_drift_guard.py docs\thesis\DECISION_LOG.md docs\thesis\METHODOLOGY_LOG.md research\experiments\EMOTION-STATE-001-phase-a.md
git commit -m "Register EMOTION-STATE Phase A foundation"
```

- [ ] **Step 8: Perform final readback**

```powershell
git status --short --branch
git log --oneline -8
git diff HEAD~8..HEAD --name-only
python scripts\validate_emotion_state_001_phase_a_contracts.py
```

Expected: clean branch, one focused baseline-prerequisite commit plus seven focused Phase A commits, only planned files changed, and the Phase A validator passes. Report the remaining blockers exactly: source repository URL, source revision or authoritative archive date, Phase B reuse scope, Phase B attribution wording, separate Phase B approval, per-public-dataset manifests and provenance, privacy-preserving unique-speaker cohort release/dedup, private-data approval, provider feasibility, real signature/trust-store implementation, and runtime activation.

## Definition Of Done

The partial Phase A foundation checkpoint is complete only when:

- Task 0's frozen EXP-002 response scorer and prompt renderer rerun deterministically from the fixed fingerprints, while the evidence states that responses and semantic judgments were not regenerated and that evaluator provenance is `not_recorded`;
- provenance and attribution exist, unresolved URL/revision fields remain explicitly blocked, and unverified license metadata is recorded without reopening author permission;
- no source code has been adapted;
- four customer-state contracts, pattern integrity contracts, and the detached BRAIN extension validate;
- the contract-only persistence self-check accepts only the approved exact `OperationalAggregateV1` shape with at least ten eligible calls and no speaker IDs; no live aggregate release is authorized until the separate unique-speaker cohort-release/dedup gate is designed, approved, satisfied, and validated;
- BRAIN-002 v1 and all live runtime surfaces remain unchanged;
- baseline, source, contract, pattern, BRAIN, checkpoint, privacy, runtime-manifest, setup, drift, thesis-reference (with no baseline waiver), thesis-update, and context-policy gates pass;
- generated evidence states `runtime_activation_allowed=false` and makes no production, customer, PSTN, ASR, latency, or true-emotion claim;
- the worktree is clean after the final commit.

Passing this plan leaves Phase A incomplete until both the per-public-dataset manifest subgate and the separately approved privacy-preserving unique-speaker cohort-release/dedup gate are designed, approved, satisfied, and validated. It authorizes only a separate Phase B planning/review decision; it does not authorize acoustic implementation automatically, merge this branch, or push it.
