#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "LOCAL-QWEN-LORA-EVAL-QUALITY-GATE-001"
EVAL_RESULT_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "LOCAL-QWEN-LORA-EVAL-001"
    / "result.json"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def split_failures(split_name: str, metrics: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    case_count = int(metrics.get("case_count") or 0)
    if case_count <= 0:
        return [f"{split_name}.case_count must be positive"]
    for key in (
        "schema_valid_count",
        "verifier_pass_count",
        "compact_contract_valid_count",
        "strict_gold_semantic_match_count",
    ):
        value = int(metrics.get(key) or 0)
        if value != case_count:
            failures.append(f"{split_name}.{key} {value} != case_count {case_count}")
    for key in (
        "deprecated_label_count",
        "case_id_label_leak_count",
        "generic_action_count",
        "generic_sub_intent_count",
        "generic_act_count",
    ):
        value = int(metrics.get(key) or 0)
        if value != 0:
            failures.append(f"{split_name}.{key} must be 0, got {value}")
    return failures


def main() -> int:
    failures: list[str] = []
    if not EVAL_RESULT_PATH.is_file():
        failures.append(f"missing eval result: {EVAL_RESULT_PATH.relative_to(ROOT)}")
        result: dict[str, Any] = {}
    else:
        result = read_json(EVAL_RESULT_PATH)
    if result:
        if result.get("status") != "completed":
            failures.append(f"eval status must be completed, got {result.get('status')}")
        metrics = result.get("adapter_metrics") if isinstance(result.get("adapter_metrics"), dict) else {}
        for split_name in ("validation", "test"):
            split_metrics = metrics.get(split_name) if isinstance(metrics.get(split_name), dict) else {}
            failures.extend(split_failures(split_name, split_metrics))
        if result.get("quality_gate_passed") is not True:
            failures.append("quality_gate_passed must be true")
        if result.get("adapter_live_ready") is not True:
            failures.append("adapter_live_ready must be true")
        if result.get("adapter_quality_status") != "pass":
            failures.append(f"adapter_quality_status must be pass, got {result.get('adapter_quality_status')}")
    validation = {
        "experiment_id": EXPERIMENT_ID,
        "validated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "eval_result_path": str(EVAL_RESULT_PATH.relative_to(ROOT)).replace("\\", "/"),
        "adapter_quality_status": result.get("adapter_quality_status") if result else None,
        "adapter_live_ready": result.get("adapter_live_ready") if result else None,
        "quality_gate_passed": result.get("quality_gate_passed") if result else None,
        "failures": failures,
    }
    print(json.dumps(validation, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
