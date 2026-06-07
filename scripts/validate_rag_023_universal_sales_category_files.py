#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "RAG-023-universal-sales-category-files"
BASE = ROOT / "runtime" / "sales_knowledge" / "universal_sales_rag"
INDEX = BASE / "category_index.json"
CATEGORIES_DIR = BASE / "categories"
COMPILED = BASE / "compiled" / "universal_sales_core.md"
PROVIDER_KB = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "universal_sales_core.md"
CONTRACT = BASE / "layer_contract.json"
COMPILER = ROOT / "scripts" / "compile_universal_sales_rag.py"
DOC = ROOT / "docs" / "product" / "RAG_023_UNIVERSAL_SALES_CATEGORY_FILES.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"

EXPECTED_CATEGORIES = [
    "buyer_moves",
    "buyer_journey_jobs",
    "buyer_enablement_and_sensemaking",
    "stakeholder_mapping",
    "discovery_question_design",
    "qualification_evidence",
    "value_and_roi_framing",
    "objection_status_quo_and_competition",
    "trust_and_risk_repair",
    "proof_and_evidence_handling",
    "conversation_repair",
    "next_step_policy",
    "decision_and_paper_process",
    "negotiation_and_concession_policy",
    "disqualification_policy",
    "ethical_persuasion_boundaries",
    "motion_specific_playbooks",
    "vertical_general_playbooks",
    "post_sale_handoff",
    "success_failure_patterns",
    "call_quality_rubrics",
]

REQUIRED_CATEGORY_MARKERS = (
    "Layer: Universal Sales RAG",
    "Owns:",
    "Does Not Own:",
    "Retrieval Triggers:",
    "Operating Rules:",
    "Failure Modes:",
    "Campaign Overlay Handoff:",
)

BLOCKED_UNIVERSAL_FACT_MARKERS = (
    "Atlas Web Studio",
    "Mike's Kitchen",
    "$1,000",
    "$5,000",
    "$10-$30/month",
    "website_hosting_monthly_ballpark",
    "web design agent",
)


def fail(message: str) -> None:
    raise AssertionError(message)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"Missing JSON file: {path.relative_to(ROOT)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object.")
    return payload


def assert_text_markers(path: Path, markers: tuple[str, ...]) -> str:
    if not path.is_file():
        fail(f"Missing file: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        assert_condition(marker in text, f"{path.relative_to(ROOT)} missing marker: {marker}")
    return text


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    assert_condition(COMPILER.is_file(), f"Missing compiler: {COMPILER.relative_to(ROOT)}")
    contract = read_json(CONTRACT)
    assert_condition(contract.get("universal_sales_categories") == EXPECTED_CATEGORIES, "layer contract category list mismatch")

    index = read_json(INDEX)
    assert_condition(index.get("package_id") == CHECKPOINT_ID, "category index package_id mismatch")
    assert_condition(index.get("source_of_truth") == "category_files", "category index source_of_truth mismatch")
    categories = index.get("categories")
    assert_condition(isinstance(categories, list), "category index categories must be a list")
    ids = [item.get("id") for item in categories if isinstance(item, dict)]
    assert_condition(ids == EXPECTED_CATEGORIES, "category index order must match layer contract")

    for position, item in enumerate(categories, start=1):
        assert_condition(isinstance(item, dict), "category entry must be an object")
        category_id = item.get("id")
        path_value = item.get("path")
        assert_condition(category_id in EXPECTED_CATEGORIES, f"unexpected category id: {category_id}")
        assert_condition(isinstance(path_value, str) and path_value, f"{category_id} missing path")
        category_path = ROOT / path_value
        expected_prefix = f"{position:02d}_"
        assert_condition(category_path.name.startswith(expected_prefix), f"{category_id} path must preserve numeric order")
        text = assert_text_markers(category_path, REQUIRED_CATEGORY_MARKERS)
        assert_condition(f"Category ID: `{category_id}`" in text, f"{category_id} missing category id marker")
        assert_condition(item.get("title") in text, f"{category_id} missing title in source file")
        assert_condition(len(text) >= 700, f"{category_id} category file is too thin")
        for blocked in BLOCKED_UNIVERSAL_FACT_MARKERS:
            assert_condition(blocked not in text, f"{category_id} leaked campaign-specific marker: {blocked}")

    completed = subprocess.run(
        [sys.executable, str(COMPILER), "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)

    compiled_text = assert_text_markers(
        COMPILED,
        (
            "# Universal Sales Core Knowledge Base",
            "Package: `RAG-023-universal-sales-category-files`",
            "Compiled from category files by `scripts/compile_universal_sales_rag.py`.",
            "## Three-Layer Sales Knowledge Contract",
            "## Universal Sales Category Files",
            "### buyer_moves",
            "### call_quality_rubrics",
            "Universal sales guidance never creates campaign facts.",
        ),
    )
    provider_text = PROVIDER_KB.read_text(encoding="utf-8")
    assert_condition(provider_text == compiled_text, "provider universal_sales_core.md must match compiled output exactly")
    assert_condition(sha256_text(provider_text) == index.get("compiled_sha256"), "category index compiled_sha256 mismatch")
    for blocked in BLOCKED_UNIVERSAL_FACT_MARKERS:
        assert_condition(blocked not in compiled_text, f"compiled universal KB leaked campaign-specific marker: {blocked}")

    assert_text_markers(
        DOC,
        (
            "RAG-023 Universal Sales Category Files",
            "category files are the editable source",
            "compiled universal layer",
            "python scripts\\validate_rag_023_universal_sales_category_files.py",
        ),
    )
    assert_text_markers(
        CHECKPOINT_INDEX,
        (
            "Current RAG category-file checkpoint",
            "`RAG-023-universal-sales-category-files`",
        ),
    )
    assert_text_markers(
        COMMANDS,
        (
            "Compile the universal sales RAG category files",
            "python scripts\\compile_universal_sales_rag.py",
            "Validate the RAG-023 universal sales category files",
            "python scripts\\validate_rag_023_universal_sales_category_files.py",
        ),
    )
    assert_text_markers(
        METHODOLOGY_LOG,
        (
            "RAG-023 universal sales category files",
            "category files are now the editable source",
            "compiled universal layer",
        ),
    )

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "category_count": len(EXPECTED_CATEGORIES),
                "compiled_sha256": sha256_text(compiled_text),
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
