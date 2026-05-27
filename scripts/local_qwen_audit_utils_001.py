#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = ROOT / "research" / "experiments" / "generated"

LABEL_FIELDS = ("act", "sub", "action", "strategy", "buyer", "intent", "rel", "neg")
CORE_FIELDS = ("act", "sub", "action", "strategy")
PLAN_FIELDS = ("facts", "preserve", "avoid")
WEIGHT_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt")

SIDE_EFFECT_FALSE_KEYS = (
    "local_model_calls_made",
    "provider_calls_made",
    "openai_api_calls_made",
    "live_tts_calls_made",
    "provider_side_effects_made",
    "model_download_attempted",
    "model_redownloaded",
    "model_weights_committed",
    "runtime_behavior_changed",
    "response_text_changed",
    "raw_private_transcript_included",
    "raw_private_transcript_copied_to_public_evidence",
    "case_text_stored_in_evidence",
    "adapter_files_committed",
)

GROUP_ORDER = (
    "current_tool_ai",
    "personal_not_team",
    "plan_explanation",
    "price_or_price_objection",
    "upgrade_midcycle",
    "terminal_acceptance",
    "safety_boundary",
    "use_case_coding_voice_writing_research",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"{rel(path)} line {line_number} must contain a JSON object")
        rows.append(payload)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def listify(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def string_list(value: Any) -> list[str]:
    return [str(item) for item in listify(value) if isinstance(item, str)]


def normalized(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): normalized(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    if value is None:
        return ""
    return value


def signature_to_dict(signature: tuple[tuple[str, Any], ...]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field, value in signature:
        if isinstance(value, tuple):
            result[field] = list(value)
        else:
            result[field] = value
    return result


def compact_target(row: dict[str, Any]) -> dict[str, Any]:
    target = row.get("target_compact_json")
    return target if isinstance(target, dict) else {}


def compact_prediction(case: dict[str, Any]) -> dict[str, Any]:
    output = case.get("compact_planner_output")
    return output if isinstance(output, dict) else {}


def label_signature(payload: dict[str, Any], fields: tuple[str, ...] = LABEL_FIELDS) -> tuple[tuple[str, Any], ...]:
    return tuple((field, normalized(payload.get(field))) for field in fields)


def response_plan_signature(payload: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    return (
        ("action", normalized(payload.get("action"))),
        ("strategy", normalized(payload.get("strategy"))),
        ("facts", normalized(payload.get("facts"))),
        ("preserve", normalized(payload.get("preserve"))),
        ("avoid", normalized(payload.get("avoid"))),
        ("say_style", say_style(str(payload.get("say") or ""))),
    )


def compact_public_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "act": payload.get("act"),
        "sub": payload.get("sub"),
        "action": payload.get("action"),
        "strategy": payload.get("strategy"),
        "buyer": payload.get("buyer"),
        "intent": payload.get("intent"),
        "rel": payload.get("rel"),
        "neg": payload.get("neg"),
        "update": normalized(payload.get("update")),
        "facts": list(normalized(payload.get("facts")) or []),
        "preserve": list(normalized(payload.get("preserve")) or []),
        "avoid": list(normalized(payload.get("avoid")) or []),
        "say_style": say_style(str(payload.get("say") or "")),
    }


def extract_input_context(row: dict[str, Any]) -> dict[str, Any]:
    prompt = str(row.get("prompt") or "")
    marker = "Input context:\n"
    if marker not in prompt:
        return {}
    raw = prompt.rsplit(marker, 1)[1].strip()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def row_private_text_for_grouping(row: dict[str, Any]) -> str:
    context = extract_input_context(row)
    parts = [
        row.get("case_id"),
        row.get("category"),
        row.get("source_type"),
        row.get("sanitized_buyer_text"),
        context.get("normalized_transcript") if isinstance(context, dict) else None,
    ]
    target = compact_target(row)
    parts.extend(target.get(field) for field in CORE_FIELDS)
    parts.extend(string_list(target.get("obj")))
    parts.extend(string_list(target.get("preserve")))
    parts.extend(string_list(target.get("avoid")))
    return " ".join(str(item) for item in parts if item).lower()


def semantic_groups(row: dict[str, Any]) -> list[str]:
    text = row_private_text_for_grouping(row)
    target = compact_target(row)
    groups: list[str] = []
    if any(token in text for token in ("chatgpt", "claude", "other ai", "competitor", "current tool")):
        groups.append("current_tool_ai")
    if any(token in text for token in ("not a team", "by myself", "personal", "individual")) or target.get("sub") in {
        "not_team_personal_use",
        "personal_use",
    }:
        groups.append("personal_not_team")
    if any(token in text for token in ("plan category", "what is this", "plans", "subscription", "model vs subscription")) or target.get("sub") in {
        "plan_category_explanation",
        "model_vs_subscription_question",
        "plus_sufficiency_question",
    }:
        groups.append("plan_explanation")
    if any(token in text for token in ("price", "cost", "expensive", "plus price")) or target.get("act") in {
        "price_objection",
        "price_question",
    }:
        groups.append("price_or_price_objection")
    if any(token in text for token in ("upgrade", "midcycle", "middle of the month", "later upgrade")) or target.get("sub") == "midcycle_upgrade_question":
        groups.append("upgrade_midcycle")
    if any(token in text for token in ("terminal", "thanks", "sounds right", "that is all")) or target.get("act") == "terminal_acceptance":
        groups.append("terminal_acceptance")
    if target.get("act") in {"safety_boundary", "negative_control", "no_fit"} or any(
        token in text
        for token in (
            "no crm",
            "no calendar",
            "transcript",
            "policy",
            "privacy",
            "unsupported",
            "do not store",
            "raw url",
            "tts",
            "side effect",
            "rules",
        )
    ):
        groups.append("safety_boundary")
    if any(token in text for token in ("coding", "voice", "writing", "research", "file upload", "files")) or str(target.get("sub") or "").startswith("coding_"):
        groups.append("use_case_coding_voice_writing_research")
    return [group for group in GROUP_ORDER if group in groups]


def say_style(text: str) -> str:
    lowered = " ".join(text.lower().split())
    markers: list[str] = []
    if "?" in text:
        markers.append("asks_question")
    if lowered.startswith(("understood", "got it", "i hear")):
        markers.append("acknowledges_buyer")
    if "cannot" in lowered or "can't" in lowered or "no " in lowered:
        markers.append("boundary_language")
    if "next step" in lowered or "plan-fit" in lowered or "plan fit" in lowered:
        markers.append("next_step_plan_fit")
    if "recommend" in lowered:
        markers.append("recommendation_language")
    if "free" in lowered and "plus" in lowered:
        markers.append("plan_list_language")
    if "close" in lowered or "thanks" in lowered:
        markers.append("terminal_language")
    return "+".join(markers) if markers else "plain_statement"


def counter_records(counter: Counter[Any], *, limit: int | None = None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for key, count in counter.most_common(limit):
        if isinstance(key, tuple) and key and isinstance(key[0], tuple):
            value: Any = signature_to_dict(key)
        elif isinstance(key, tuple):
            value = list(key)
        else:
            value = key
        records.append({"value": value, "count": count})
    return records


def group_signature_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    label_counter: Counter[tuple[tuple[str, Any], ...]] = Counter()
    action_strategy_counter: Counter[tuple[tuple[str, Any], ...]] = Counter()
    response_counter: Counter[tuple[tuple[str, Any], ...]] = Counter()
    facts_counter: Counter[tuple[str, ...]] = Counter()
    preserve_counter: Counter[tuple[str, ...]] = Counter()
    avoid_counter: Counter[tuple[str, ...]] = Counter()
    style_counter: Counter[str] = Counter()
    by_signature_cases: dict[tuple[tuple[str, Any], ...], list[str]] = {}
    split_counts: Counter[str] = Counter()

    for row in rows:
        target = compact_target(row)
        label_sig = label_signature(target)
        action_sig = label_signature(target, ("action", "strategy"))
        response_sig = response_plan_signature(target)
        label_counter[label_sig] += 1
        action_strategy_counter[action_sig] += 1
        response_counter[response_sig] += 1
        facts_counter[tuple(string_list(target.get("facts")))] += 1
        preserve_counter[tuple(string_list(target.get("preserve")))] += 1
        avoid_counter[tuple(string_list(target.get("avoid")))] += 1
        style_counter[say_style(str(target.get("say") or ""))] += 1
        split_counts[str(row.get("_audit_split") or row.get("split") or row.get("curriculum_stage") or "unknown")] += 1
        by_signature_cases.setdefault(label_sig, []).append(str(row.get("case_id") or ""))

    dominant = label_counter.most_common(1)
    minority = []
    for signature, count in label_counter.most_common()[1:8]:
        minority.append(
            {
                "signature": signature_to_dict(signature),
                "count": count,
                "case_ids": sorted(by_signature_cases.get(signature, []))[:12],
            }
        )
    return {
        "case_count": len(rows),
        "split_counts": dict(sorted(split_counts.items())),
        "label_signature_count": len(label_counter),
        "action_strategy_signature_count": len(action_strategy_counter),
        "response_plan_signature_count": len(response_counter),
        "facts_signature_count": len(facts_counter),
        "preserve_signature_count": len(preserve_counter),
        "avoid_signature_count": len(avoid_counter),
        "say_style_count": len(style_counter),
        "action_strategy_consistent": len(action_strategy_counter) <= 1,
        "facts_consistent": len(facts_counter) <= 1,
        "preserve_consistent": len(preserve_counter) <= 1,
        "avoid_consistent": len(avoid_counter) <= 1,
        "say_style_consistent": len(style_counter) <= 1,
        "dominant_label_signature": signature_to_dict(dominant[0][0]) if dominant else {},
        "dominant_label_signature_count": dominant[0][1] if dominant else 0,
        "minority_label_signatures": minority,
        "action_strategy_distribution": counter_records(action_strategy_counter, limit=12),
        "facts_distribution": counter_records(facts_counter, limit=12),
        "preserve_distribution": counter_records(preserve_counter, limit=12),
        "avoid_distribution": counter_records(avoid_counter, limit=12),
        "say_style_distribution": counter_records(style_counter, limit=12),
    }


def field_mismatches(expected: dict[str, Any], predicted: dict[str, Any]) -> list[str]:
    fields = (
        "act",
        "sub",
        "buyer",
        "intent",
        "rel",
        "neg",
        "update",
        "block",
        "action",
        "strategy",
        "facts",
        "preserve",
        "avoid",
        "say",
        "flags",
    )
    return [field for field in fields if normalized(expected.get(field)) != normalized(predicted.get(field))]


def classify_sales_move(expected: dict[str, Any], predicted: dict[str, Any]) -> bool:
    if not predicted:
        return True
    expected_action = expected.get("action")
    predicted_action = predicted.get("action")
    expected_act = expected.get("act")
    predicted_act = predicted.get("act")
    if expected_action == predicted_action and expected.get("strategy") == predicted.get("strategy"):
        return False
    if predicted_action == "terminal_close" and expected_action != "terminal_close":
        return True
    if predicted_action == "recommend_plan" and expected_action not in {"recommend_plan", "answer_plan_fit"}:
        return True
    if predicted_action == "respect_boundary" and expected_act not in {"safety_boundary", "negative_control", "no_fit"}:
        return True
    if predicted_act == "safety_boundary" and expected_act not in {"safety_boundary", "negative_control", "no_fit"}:
        return True
    return False


def eval_failed(case: dict[str, Any]) -> bool:
    return not (
        case.get("schema_valid") is True
        and case.get("verifier_pass") is True
        and case.get("compact_contract_valid") is True
        and case.get("strict_gold_semantic_match") is True
        and case.get("strict_gold_response_plan_match") is True
        and case.get("exact_match") is True
    )


def curriculum_eval_cases(result: dict[str, Any], split_names: tuple[str, ...]) -> list[dict[str, Any]]:
    curriculum = result.get("curriculum_adapter") if isinstance(result.get("curriculum_adapter"), dict) else {}
    splits = curriculum.get("splits") if isinstance(curriculum.get("splits"), dict) else {}
    cases: list[dict[str, Any]] = []
    for split_name in split_names:
        payload = splits.get(split_name) if isinstance(splits.get(split_name), dict) else {}
        for case in payload.get("cases") or []:
            if isinstance(case, dict):
                cases.append(case)
    return cases


def curriculum_split_paths(result: dict[str, Any]) -> dict[str, Path]:
    curriculum = result.get("curriculum_adapter") if isinstance(result.get("curriculum_adapter"), dict) else {}
    splits = curriculum.get("splits") if isinstance(curriculum.get("splits"), dict) else {}
    paths: dict[str, Path] = {}
    for split_name, payload in splits.items():
        if not isinstance(payload, dict):
            continue
        path_value = payload.get("path")
        if isinstance(path_value, str) and path_value:
            paths[split_name] = ROOT / path_value
    return paths


def rows_by_case_from_paths(paths: dict[str, Path]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for split_name, path in paths.items():
        if not path.is_file():
            continue
        for row in read_jsonl(path):
            case_id = str(row.get("case_id") or "")
            if not case_id:
                continue
            copied = dict(row)
            copied["_audit_split"] = split_name
            rows[case_id] = copied
    return rows


def tracked_model_or_adapter_files() -> list[str]:
    completed = subprocess.run(
        ["git", "--no-optional-locks", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    if completed.returncode != 0:
        return []
    return [
        line.strip().replace("\\", "/")
        for line in completed.stdout.splitlines()
        if line.strip().lower().endswith(WEIGHT_SUFFIXES) or line.strip().replace("\\", "/").startswith("local_artifacts/")
    ]


def audit_side_effects() -> dict[str, Any]:
    return {
        "local_model_calls_made": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "live_tts_calls_made": False,
        "provider_side_effects_made": False,
        "model_download_attempted": False,
        "model_redownloaded": False,
        "model_weights_committed": False,
        "adapter_files_committed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "raw_private_transcript_included": False,
        "raw_private_transcript_copied_to_public_evidence": False,
        "case_text_stored_in_evidence": False,
    }


def report_json_block(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False)
