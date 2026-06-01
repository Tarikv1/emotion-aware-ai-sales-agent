#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PHASE-4N4A-ACTUAL-DATASET-USAGE-AUDIT-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILENAMES = [
    "result.json",
    "report.md",
    "00_dataset_usage_summary.md",
    "01_actual_dataset_inventory.md",
    "02_project_generated_dataset_inventory.md",
    "03_reference_only_sources.md",
    "04_easid_status_correction.md",
    "05_thesis_proposal_placeholder_correction.md",
    "06_metric_computation_status.md",
    "07_revised_thesis_data_section.md",
    "08_rq_to_dataset_evidence_mapping.md",
    "09_next_experiments_needed.md",
]

REQUIRED_CLASSIFICATIONS = [
    "actual_public_dataset_downloaded_extracted",
    "actual_public_dataset_partial_or_unverified",
    "project_generated_synthetic_sanitized_dataset",
    "project_generated_eval_case_pack",
    "reference_only_pattern_grounding",
    "planned_not_used",
    "thesis_schema_only",
    "proposal_placeholder_only",
    "product_source_bundle_claim_governance",
    "project_generated_eval_protocol",
    "provenance_audit_artifact",
]

FALSE_RESULT_FLAGS = [
    "easid_actual_dataset_used",
    "fabricated_results_present",
    "emotion_accuracy_computed",
    "human_likeness_scores_computed",
    "sales_effectiveness_scores_computed",
    "real_outbound_calls_enabled",
    "provider_calls_made",
    "elevenlabs_calls_made",
    "openai_api_calls_made",
    "model_calls_made",
    "tts_calls_made",
    "crm_calls_made",
    "email_calls_made",
    "calendar_calls_made",
    "payment_calls_made",
    "account_side_effects_made",
    "live_readiness_claimed",
]

REQUIRED_DATASET_MARKERS = [
    "MELD",
    "Persuasion for Good",
    "IEMOCAP",
    "EASID",
    "EXP-002 dataset-derived case pack",
    "LOCAL-QWEN-SFT-DATASET-001",
    "LOCAL-QWEN-BALANCED-SFT-DATASET-001",
    "NON-LLM-ACTION-SELECTOR-DATASET-001",
    "NON-LLM-ACTION-SELECTOR-DATA-SOURCES-001",
    "CallCenterEN",
    "Public OpenAI ChatGPT plan-fit fixture",
    "PHASE-4N3-WEBSITE-SALES-AGENT-EVALUATION-PROTOCOL-001",
    "PHASE-4N4-THESIS-EASID-ALIGNMENT-001",
]

PROJECT_GENERATED_MARKERS = [
    "LOCAL-QWEN-SFT-DATASET-001",
    "LOCAL-QWEN-BALANCED-SFT-DATASET-001",
    "NON-LLM-ACTION-SELECTOR-DATASET-001",
    "EXP-002 dataset-derived case pack",
    "PHASE-4N3-WEBSITE-SALES-AGENT-EVALUATION-PROTOCOL-001",
]

FORBIDDEN_RAW_PRIVATE_MARKERS = [
    "raw private transcript/audio included",
    "raw private transcript included: true",
    "raw private audio included: true",
    "raw private transcript copied",
    "private transcript excerpt",
    "private audio excerpt",
    "verbatim private transcript",
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(read_text(path))
    return payload if isinstance(payload, dict) else {}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def all_text() -> str:
    return "\n".join(read_text(OUT_DIR / filename) for filename in REQUIRED_FILENAMES)


def validate_required_files() -> None:
    missing = [filename for filename in REQUIRED_FILENAMES if not (OUT_DIR / filename).is_file()]
    require(not missing, f"missing required files: {', '.join(missing)}")


def validate_dataset_inventory() -> int:
    inventory_text = read_text(OUT_DIR / "01_actual_dataset_inventory.md")
    generated_text = read_text(OUT_DIR / "02_project_generated_dataset_inventory.md")
    reference_text = read_text(OUT_DIR / "03_reference_only_sources.md")
    combined = "\n".join([inventory_text, generated_text, reference_text, read_text(OUT_DIR / "04_easid_status_correction.md")])
    normalized = normalize(combined)

    missing_markers = [marker for marker in REQUIRED_DATASET_MARKERS if marker.lower() not in normalized]
    require(not missing_markers, f"dataset inventory missing markers: {', '.join(missing_markers)}")

    missing_classes = [item for item in REQUIRED_CLASSIFICATIONS if item not in normalized]
    require(not missing_classes, f"missing classifications: {', '.join(missing_classes)}")

    for marker in PROJECT_GENERATED_MARKERS:
        require(marker.lower() in normalize(generated_text), f"project-generated inventory missing {marker}")

    for source, classification in [
        ("MELD", "actual_public_dataset_downloaded_extracted"),
        ("Persuasion for Good", "actual_public_dataset_downloaded_extracted"),
        ("IEMOCAP", "actual_public_dataset_partial_or_unverified"),
    ]:
        pattern = rf"{re.escape(source)}[\s\S]{{0,800}}{classification}"
        require(re.search(pattern, combined, flags=re.IGNORECASE), f"{source} missing classification {classification}")

    return len(REQUIRED_DATASET_MARKERS)


def validate_easid_correction() -> None:
    text = read_text(OUT_DIR / "04_easid_status_correction.md")
    normalized = normalize(text)
    required = "easid is an operational schema/target data format introduced by the thesis, not a pre-existing external dataset used in the repo."
    require(required in normalized, "EASID schema-only correction sentence missing")
    forbidden = [
        "easid is an actual external dataset",
        "easid was downloaded",
        "pre-existing easid dataset used",
        "external easid corpus",
    ]
    leaked = [phrase for phrase in forbidden if phrase in normalized]
    require(not leaked, f"EASID described as actual external dataset: {', '.join(leaked)}")


def validate_placeholder_and_no_fabricated_metrics() -> None:
    text = all_text()
    normalized = normalize(text)
    require("proposal_placeholder_only" in normalized, "proposal placeholder classification missing")
    require("placeholder proposal metrics are not experimental results" in normalized, "placeholder metric correction missing")

    forbidden_number_patterns = [
        r"emotion detection accuracy\s*[:=]\s*\d",
        r"emotion accuracy\s*[:=]\s*\d",
        r"\bf1\s*[:=]\s*\d",
        r"human-likeness score\s*[:=]\s*\d",
        r"sales effectiveness\s*[:=]\s*\d",
        r"persuasion improvement\s*[:=]\s*\d",
    ]
    hits = [pattern for pattern in forbidden_number_patterns if re.search(pattern, normalized)]
    require(not hits, f"fabricated metric-like numbers found: {', '.join(hits)}")

    metric_table = read_text(OUT_DIR / "06_metric_computation_status.md")
    metric_norm = normalize(metric_table)
    for marker in [
        "| dataset/artifact | metric type | computed? | evidence path | notes |",
        "emotion detection accuracy/f1",
        "not computed",
        "qwen sft row/split counts",
        "elevenlabs manual sales effectiveness",
        "human-likeness scores",
    ]:
        require(marker.lower() in metric_norm, f"metric computation table missing marker: {marker}")


def validate_revised_thesis_section() -> None:
    text = read_text(OUT_DIR / "07_revised_thesis_data_section.md")
    normalized = normalize(text)
    required = [
        "the proposal introduced easid as a schema",
        "meld and persuasion for good",
        "iemocap was inspected/planned",
        "project-generated sanitized/synthetic datasets",
        "placeholder proposal metrics are not experimental results",
        "final thesis results must be computed from the defined evaluation protocol",
    ]
    missing = [marker for marker in required if marker in normalized and False]
    missing = [marker for marker in required if marker not in normalized]
    require(not missing, f"revised thesis data section missing: {', '.join(missing)}")


def validate_rq_mapping() -> None:
    text = read_text(OUT_DIR / "08_rq_to_dataset_evidence_mapping.md")
    normalized = normalize(text)
    missing = [f"rq{i}" for i in range(1, 8) if f"rq{i}" not in normalized]
    require(not missing, f"RQ mapping missing: {', '.join(missing)}")
    for marker in [
        "meld sentiment/emotion labels",
        "iemocap only pending verification",
        "easid schema",
        "generic elevenlabs baseline vs structured atlas package",
    ]:
        require(marker in normalized, f"RQ mapping missing marker: {marker}")


def validate_no_private_or_side_effect_claims() -> None:
    normalized = normalize(all_text())
    leaked_private = [marker for marker in FORBIDDEN_RAW_PRIVATE_MARKERS if marker in normalized]
    require(not leaked_private, f"raw private material marker present: {', '.join(leaked_private)}")

    forbidden_side_effect_claims = [
        "provider calls made: true",
        "elevenlabs calls made: true",
        "openai api calls made: true",
        "model calls made: true",
        "tts calls made: true",
        "crm calls made: true",
        "email calls made: true",
        "calendar calls made: true",
        "payment calls made: true",
        "account side effects made: true",
        "live readiness claimed: true",
        "real outbound calls enabled: true",
    ]
    leaked_claims = [claim for claim in forbidden_side_effect_claims if claim in normalized]
    require(not leaked_claims, f"unsafe side-effect claim present: {', '.join(leaked_claims)}")


def validate_result_json(dataset_inventory_count: int) -> None:
    result = read_json(OUT_DIR / "result.json")
    require(result.get("checkpoint_id") == CHECKPOINT_ID, "result.json checkpoint_id mismatch")
    require(result.get("status") == "pass", "result.json status must be pass")
    require(result.get("dataset_inventory_count") == dataset_inventory_count, "dataset_inventory_count mismatch")
    require(result.get("actual_public_dataset_count") == 2, "actual_public_dataset_count must be 2")
    require(result.get("project_generated_dataset_count") == 5, "project_generated_dataset_count must be 5")
    require(result.get("reference_only_source_count") == 2, "reference_only_source_count must be 2")
    require(result.get("easid_schema_defined") is True, "easid_schema_defined must be true")
    require(result.get("proposal_placeholder_metrics_detected") is True, "proposal_placeholder_metrics_detected must be true")
    require(result.get("thesis_data_section_ready") is True, "thesis_data_section_ready must be true")

    enabled = [flag for flag in FALSE_RESULT_FLAGS if result.get(flag) is not False]
    require(not enabled, f"unsafe or uncomputed result flags must be false: {', '.join(enabled)}")


def main() -> int:
    validate_required_files()
    dataset_inventory_count = validate_dataset_inventory()
    validate_easid_correction()
    validate_placeholder_and_no_fabricated_metrics()
    validate_revised_thesis_section()
    validate_rq_mapping()
    validate_no_private_or_side_effect_claims()
    validate_result_json(dataset_inventory_count)

    print(
        f"PASS {CHECKPOINT_ID}: {dataset_inventory_count} inventory entries, "
        "EASID schema-only, no fabricated metrics, side-effect flags false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
