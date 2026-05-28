#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


EXPERIMENT_ID = "LOCAL-QWEN-MIXED-REPLAY-QUALITY-GATE-001"
EVAL_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LOCAL-QWEN-LORA-MIXED-REPLAY-EVAL-001" / "result.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def split_threshold_failures(split: str, metrics: dict[str, Any]) -> list[str]:
    count = int(metrics.get("case_count") or 0)
    failures: list[str] = []
    if count <= 0:
        return [f"{split}: empty or missing metrics"]
    thresholds = {
        "schema_valid_count": 1.0,
        "compact_contract_valid_count": 1.0,
        "verifier_pass_count": 0.98,
        "strict_gold_semantic_match_count": 0.85,
        "equivalence_match_count": 0.90,
    }
    for key, threshold in thresholds.items():
        ratio = int(metrics.get(key) or 0) / count
        if ratio < threshold:
            failures.append(f"{split}: {key} {ratio:.3f} below {threshold:.2f}")
    zero_keys = (
        "and_or_drift_count",
        "voice_writing_drift_count",
        "not_team_team_drift_count",
        "fake_side_effect_count",
        "internal_policy_language_count",
    )
    for key in zero_keys:
        if int(metrics.get(key) or 0) != 0:
            failures.append(f"{split}: {key} must be zero")
    if int(metrics.get("safety_pass_count") or 0) != count:
        failures.append(f"{split}: safety_pass_count must be 100%")
    return failures


def write_report(result: dict[str, Any]) -> None:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- status: {result.get('status')}",
        f"- quality_gate_passed: {str(result.get('quality_gate_passed')).lower()}",
        f"- adapter_live_ready: {str(result.get('adapter_live_ready')).lower()}",
        f"- live_wiring_allowed: {str(result.get('live_wiring_allowed')).lower()}",
        "",
        "## Failures",
        "",
        *(f"- {item}" for item in result.get("failures") or []),
        "",
        "## Metrics",
        "",
        json.dumps(result.get("metrics") or {}, indent=2, ensure_ascii=False),
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    eval_result = read_json(EVAL_RESULT_PATH)
    failures: list[str] = []
    if not eval_result:
        failures.append("missing mixed-replay eval result")
    if eval_result.get("status") != "completed":
        failures.append(f"eval status is not completed: {eval_result.get('status')}")
    failures.extend(split_threshold_failures("validation", eval_result.get("validation_metrics") or {}))
    failures.extend(split_threshold_failures("test", eval_result.get("test_metrics") or {}))
    if eval_result.get("live_wiring_allowed"):
        failures.append("live_wiring_allowed must remain false in this phase")
    quality_gate_passed = not failures and bool(eval_result.get("quality_gate_passed"))
    if bool(eval_result.get("quality_gate_passed")) != quality_gate_passed:
        failures.append("eval quality_gate_passed flag does not match validator recomputation")
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass" if quality_gate_passed else "fail",
        "quality_gate_passed": quality_gate_passed,
        "adapter_live_ready": bool(eval_result.get("adapter_live_ready")) and quality_gate_passed,
        "live_wiring_allowed": False,
        "failures": failures,
        "metrics": {
            "validation": eval_result.get("validation_metrics"),
            "test": eval_result.get("test_metrics"),
            "ood": eval_result.get("ood_metrics"),
        },
    }
    write_json(RESULT_PATH, result)
    write_report(result)
    print(json.dumps({"status": result["status"], "failures": failures}, indent=2))
    return 0 if quality_gate_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
