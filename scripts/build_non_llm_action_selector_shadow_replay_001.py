from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "research" / "experiments" / "generated" / "NON-LLM-ACTION-SELECTOR-DATASET-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "NON-LLM-ACTION-SELECTOR-SHADOW-REPLAY-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
REPLAY_PATH = OUT_DIR / "replay.jsonl"
EXPERIMENT_ID = "NON-LLM-ACTION-SELECTOR-SHADOW-REPLAY-001"
DEFAULT_CAMPAIGN_ID = "public-openai-chatgpt-plans"


ACTION_CATEGORY = {
    "answer_price": "price",
    "handle_price_objection": "price_objection",
    "handle_competitor_context": "competitor_context",
    "answer_source_or_affiliation": "source_affiliation",
    "answer_privacy_boundary": "privacy",
    "answer_signup_path": "signup",
    "answer_plan_change": "plan_change",
    "ask_use_case_gap": "use_case",
    "ask_usage_intensity": "usage_intensity",
    "clarify_team_vs_individual": "team_vs_individual",
    "recommend_business_or_enterprise": "team_vs_individual",
    "repair_already_told_you": "already_told_you",
    "repair_asr_uncertainty": "asr_uncertainty",
    "terminal_close": "terminal_close",
    "disqualify_no_fit": "no_fit",
    "respect_boundary": "boundary",
    "avoid_repetition_rephrase": "already_told_you",
    "repair_buyer_correction": "team_vs_individual",
}

REQUIRED_DIVERSITY = (
    "price",
    "price_objection",
    "competitor_context",
    "source_affiliation",
    "privacy",
    "signup",
    "plan_change",
    "use_case",
    "usage_intensity",
    "team_vs_individual",
    "already_told_you",
    "asr_uncertainty",
    "terminal_close",
    "no_fit",
    "boundary",
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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def context_summary(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "known_use_case": context.get("known_use_case") or [],
        "known_tools": context.get("known_tools") or [],
        "known_plan_interest": context.get("known_plan_interest") or "",
        "known_team_status": context.get("known_team_status") or "",
        "buyer_emotion": context.get("buyer_emotion") or "",
        "buyer_confusion_level": context.get("buyer_confusion_level") or "",
        "buyer_skepticism_level": context.get("buyer_skepticism_level") or "",
        "buyer_engagement_level": context.get("buyer_engagement_level") or "",
        "safety_boundary_detected": context.get("safety_boundary_detected") is True,
        "compact_target": context.get("compact_target") if isinstance(context.get("compact_target"), dict) else {},
        "benchmark_category": context.get("benchmark_category") or "",
    }


def replay_row(source_row: dict[str, Any], split: str, index: int) -> dict[str, Any]:
    expected_action_id = str(source_row.get("target_action_id") or "")
    context = source_row.get("context") if isinstance(source_row.get("context"), dict) else {}
    return {
        "replay_case_id": f"shadow_replay::{split}::{index:03d}",
        "source_file": str(source_row.get("source_file") or rel(DATASET_DIR / f"{split}.jsonl")),
        "source_case_id": str(source_row.get("source_case_id") or source_row.get("case_id") or ""),
        "campaign_id": str(context.get("campaign_id") or DEFAULT_CAMPAIGN_ID),
        "buyer_utterance_text": str(source_row.get("buyer_utterance_text") or ""),
        "context": context_summary(context),
        "expected_action_id": expected_action_id,
        "existing_runtime_action_id": str(source_row.get("existing_runtime_action_id") or ""),
        "existing_runtime_response_text_available": bool(source_row.get("existing_runtime_response_text_available") is True),
        "sanitized": True,
        "raw_private_data": False,
        "category": ACTION_CATEGORY.get(expected_action_id, "other"),
        "notes": "Replay row derived from committed 4K0 sanitized/synthetic validation/test action-selector dataset.",
    }


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split in ("validation", "test"):
        for index, source_row in enumerate(read_jsonl(DATASET_DIR / f"{split}.jsonl"), start=1):
            rows.append(replay_row(source_row, split, index))
    return rows


def validate_replay(rows: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    if len(rows) < 100:
        failures.append(f"fewer than 100 replay rows: {len(rows)}")
    categories = Counter(row["category"] for row in rows)
    missing = sorted(category for category in REQUIRED_DIVERSITY if categories.get(category, 0) == 0)
    if missing:
        failures.append(f"missing required diversity categories: {missing}")
    for index, row in enumerate(rows, start=1):
        label = f"replay[{index}]"
        if row.get("sanitized") is not True:
            failures.append(f"{label}.sanitized must be true")
        if row.get("raw_private_data") is not False:
            failures.append(f"{label}.raw_private_data must be false")
        source_file = str(row.get("source_file") or "").replace("\\", "/").casefold()
        if "data/private" in source_file or "private-restricted" in source_file:
            failures.append(f"{label}.source_file references private data")
    return failures


def build_result(rows: list[dict[str, Any]]) -> dict[str, Any]:
    failures = validate_replay(rows)
    categories = Counter(row["category"] for row in rows)
    action_counts = Counter(row["expected_action_id"] for row in rows)
    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "replay_case_count": len(rows),
        "target_replay_case_count": 100,
        "target_met": len(rows) >= 100,
        "source_splits": ["validation", "test"],
        "source_dataset": "research/experiments/generated/NON-LLM-ACTION-SELECTOR-DATASET-001",
        "category_counts": dict(sorted(categories.items())),
        "expected_action_counts": dict(sorted(action_counts.items())),
        "runtime_action_available_count": sum(1 for row in rows if row.get("existing_runtime_action_id")),
        "existing_runtime_response_text_available_count": sum(1 for row in rows if row.get("existing_runtime_response_text_available") is True),
        "sanitized": True,
        "raw_private_data": False,
        "audio_data_used": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "ultravox_calls_made": False,
        "elevenlabs_calls_made": False,
        "local_llm_calls_made": False,
        "ollama_calls_made": False,
        "side_effects_allowed": False,
        "buyer_facing_text_generated": False,
        "live_runtime_wiring_allowed": False,
        "should_not_change_runtime": True,
        "response_text_changed": False,
        "runtime_behavior_changed": False,
        "failures": failures,
    }


def build_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Replay cases: {result['replay_case_count']}",
        f"- Target met: {str(result['target_met']).lower()}",
        f"- Runtime action available count: {result['runtime_action_available_count']}",
        "- Sanitized only: true",
        "- Raw private data/audio used: false",
        "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama calls: false",
        "- Live runtime wiring allowed: false",
        "- Runtime behavior changed: false",
        "- Response text changed: false",
        "",
        "## Category Counts",
        "",
    ]
    for category, count in result["category_counts"].items():
        lines.append(f"- {category}: {count}")
    lines.extend(["", "## Expected Action Counts", ""])
    for action_id, count in result["expected_action_counts"].items():
        lines.append(f"- {action_id}: {count}")
    if result["failures"]:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in result["failures"])
    return "\n".join(lines)


def main() -> int:
    rows = build_rows()
    result = build_result(rows)
    write_jsonl(REPLAY_PATH, rows)
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(json.dumps({"status": result["status"], "replay_case_count": result["replay_case_count"]}, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
