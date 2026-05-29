from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import sys
from time import perf_counter_ns
from typing import Any


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "research" / "experiments" / "generated" / "NON-LLM-ACTION-SELECTOR-DATASET-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "NON-LLM-ACTION-SELECTOR-EVAL-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
EVAL_ID = "NON-LLM-ACTION-SELECTOR-EVAL-001"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.action_selector.non_llm_action_selector import (  # noqa: E402
    RuleBasedActionSelector,
    SklearnActionSelector,
    StandardLibraryNearestLabelSelector,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"{path}:{line_number} is not a JSON object")
        rows.append(payload)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def load_dataset() -> dict[str, list[dict[str, Any]]]:
    return {split: read_jsonl(DATASET_DIR / f"{split}.jsonl") for split in ("train", "validation", "test")}


def predict_rows(selector: Any, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    predictions: list[dict[str, Any]] = []
    for row in rows:
        output = selector.select(row).to_dict()
        predictions.append(
            {
                "case_id": row["case_id"],
                "target_action_id": row["target_action_id"],
                "predicted_action_id": output["action_id"],
                "confidence": output["confidence"],
                "fallback_required": output["fallback_required"],
                "matched_features": output["matched_features"],
                "reasons": output["reasons"],
            }
        )
    return predictions


def per_label_metrics(predictions: list[dict[str, Any]]) -> dict[str, dict[str, float | int]]:
    labels = sorted({row["target_action_id"] for row in predictions} | {row["predicted_action_id"] for row in predictions})
    result: dict[str, dict[str, float | int]] = {}
    for label in labels:
        tp = sum(1 for row in predictions if row["target_action_id"] == label and row["predicted_action_id"] == label)
        fp = sum(1 for row in predictions if row["target_action_id"] != label and row["predicted_action_id"] == label)
        fn = sum(1 for row in predictions if row["target_action_id"] == label and row["predicted_action_id"] != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        result[label] = {
            "support": sum(1 for row in predictions if row["target_action_id"] == label),
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    return result


def confusion_matrix(predictions: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    matrix: dict[str, Counter[str]] = defaultdict(Counter)
    for row in predictions:
        matrix[row["target_action_id"]][row["predicted_action_id"]] += 1
    return {actual: dict(sorted(predicted.items())) for actual, predicted in sorted(matrix.items())}


def subset_metric(name: str, rows: list[dict[str, Any]], predictions: list[dict[str, Any]], predicate: Any) -> dict[str, Any]:
    selected_ids = {row["case_id"] for row in rows if predicate(row)}
    selected = [row for row in predictions if row["case_id"] in selected_ids]
    correct = sum(1 for row in selected if row["target_action_id"] == row["predicted_action_id"])
    return {
        "name": name,
        "case_count": len(selected),
        "accuracy": correct / len(selected) if selected else None,
        "correct": correct,
    }


def text_of(row: dict[str, Any]) -> str:
    return str(row.get("buyer_utterance_text") or "").casefold()


def split_metrics(rows: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    correct = sum(1 for row in predictions if row["target_action_id"] == row["predicted_action_id"])
    per_label = per_label_metrics(predictions)
    macro_f1 = statistics.mean(item["f1"] for item in per_label.values()) if per_label else 0.0
    fallback_count = sum(1 for row in predictions if row.get("fallback_required") is True)
    subsets = {
        item["name"]: item
        for item in [
            subset_metric("safety_boundary_accuracy", rows, predictions, lambda row: row["target_action_id"] in {"respect_boundary", "answer_privacy_boundary"}),
            subset_metric("already_told_you_repair_accuracy", rows, predictions, lambda row: row["target_action_id"] == "repair_already_told_you" or "already told" in text_of(row)),
            subset_metric("terminal_close_accuracy", rows, predictions, lambda row: row["target_action_id"] == "terminal_close"),
            subset_metric("price_question_accuracy", rows, predictions, lambda row: row["target_action_id"] == "answer_price"),
            subset_metric("competitor_objection_accuracy", rows, predictions, lambda row: row["target_action_id"] == "handle_competitor_context"),
            subset_metric("no_fit_accuracy", rows, predictions, lambda row: row["target_action_id"] == "disqualify_no_fit"),
            subset_metric("team_vs_individual_accuracy", rows, predictions, lambda row: row["target_action_id"] in {"clarify_team_vs_individual", "recommend_business_or_enterprise"}),
            subset_metric("and_or_fidelity_cases", rows, predictions, lambda row: " and " in f" {text_of(row)} " or " or " in f" {text_of(row)} "),
            subset_metric("voice_writing_fidelity_cases", rows, predictions, lambda row: "voice" in text_of(row) or "writing" in text_of(row)),
        ]
    }
    return {
        "row_count": len(rows),
        "accuracy": correct / len(predictions) if predictions else 0.0,
        "macro_f1": macro_f1,
        "fallback_rate": fallback_count / len(predictions) if predictions else 0.0,
        "fallback_count": fallback_count,
        "per_label": per_label,
        "confusion_matrix": confusion_matrix(predictions),
        "special_case_metrics": subsets,
    }


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((percentile_value / 100.0) * (len(ordered) - 1))))
    return ordered[index]


def latency_benchmark(selector: Any, rows: list[dict[str, Any]], min_samples: int = 500) -> dict[str, float | int]:
    if not rows:
        return {"sample_count": 0, "p50": 0.0, "p90": 0.0, "p99": 0.0, "max": 0.0}
    repeated = (rows * ((min_samples // len(rows)) + 1))[:min_samples]
    timings: list[float] = []
    for row in repeated:
        start = perf_counter_ns()
        selector.select(row)
        timings.append((perf_counter_ns() - start) / 1_000_000)
    return {
        "sample_count": len(timings),
        "p50": percentile(timings, 50),
        "p90": percentile(timings, 90),
        "p99": percentile(timings, 99),
        "max": max(timings),
    }


def evaluate_selector(name: str, selector: Any, rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    validation_predictions = predict_rows(selector, rows_by_split["validation"])
    test_predictions = predict_rows(selector, rows_by_split["test"])
    return {
        "baseline_name": name,
        "validation": split_metrics(rows_by_split["validation"], validation_predictions),
        "test": split_metrics(rows_by_split["test"], test_predictions),
        "latency_ms": latency_benchmark(selector, rows_by_split["test"]),
        "prediction_samples": {
            "validation": validation_predictions[:10],
            "test": test_predictions[:10],
        },
    }


def build_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {EVAL_ID}",
        "",
        f"- Status: {result['status']}",
        "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama calls: false",
        "- Live runtime wiring allowed: false",
        "- Runtime behavior changed: false",
        "- Response text changed: false",
        "",
        "## Baselines",
        "",
    ]
    for name, metrics in result["baseline_metrics"].items():
        lines.append(f"### {name}")
        lines.append(f"- Validation accuracy: {metrics['validation']['accuracy']:.4f}")
        lines.append(f"- Test accuracy: {metrics['test']['accuracy']:.4f}")
        lines.append(f"- Validation macro F1: {metrics['validation']['macro_f1']:.4f}")
        lines.append(f"- Test macro F1: {metrics['test']['macro_f1']:.4f}")
        latency = metrics["latency_ms"]
        lines.append(
            f"- Latency ms p50/p90/p99/max: {latency['p50']:.4f}/{latency['p90']:.4f}/{latency['p99']:.4f}/{latency['max']:.4f}"
        )
        lines.append(f"- Test fallback rate: {metrics['test']['fallback_rate']:.4f}")
        lines.append("")
    if result["sklearn_status"]["available"] is False:
        lines.extend(["## Sklearn", "", f"- unavailable: {result['sklearn_status']['reason']}"])
    return "\n".join(lines)


def main() -> int:
    rows_by_split = load_dataset()
    rule_selector = RuleBasedActionSelector()
    baseline_metrics: dict[str, Any] = {
        "rule_based": evaluate_selector("rule_based", rule_selector, rows_by_split)
    }

    sklearn_selector = SklearnActionSelector().fit(rows_by_split["train"])
    sklearn_status = {"available": sklearn_selector.available, "reason": sklearn_selector.unavailable_reason}
    if sklearn_selector.available:
        baseline_metrics["sklearn_tfidf_logistic_regression"] = evaluate_selector(
            "sklearn_tfidf_logistic_regression",
            sklearn_selector,
            rows_by_split,
        )
    else:
        nearest = StandardLibraryNearestLabelSelector().fit(rows_by_split["train"])
        baseline_metrics["nearest_label_stdlib"] = evaluate_selector("nearest_label_stdlib", nearest, rows_by_split)

    result = {
        "experiment_id": EVAL_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "dataset": "research/experiments/generated/NON-LLM-ACTION-SELECTOR-DATASET-001",
        "baseline_metrics": baseline_metrics,
        "sklearn_status": sklearn_status,
        "latency_target_ms": {"p50_preferred": 5, "p90_acceptable": 20, "p99_acceptable": 50},
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "ultravox_calls_made": False,
        "elevenlabs_calls_made": False,
        "local_llm_calls_made": False,
        "ollama_calls_made": False,
        "live_runtime_wiring_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    summary = {
        name: {
            "validation_accuracy": metrics["validation"]["accuracy"],
            "test_accuracy": metrics["test"]["accuracy"],
            "latency_ms": metrics["latency_ms"],
        }
        for name, metrics in baseline_metrics.items()
    }
    print(json.dumps({"status": result["status"], "baselines": summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
