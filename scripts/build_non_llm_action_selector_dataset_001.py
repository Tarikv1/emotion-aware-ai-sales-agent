from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = ROOT / "research" / "experiments" / "generated"
DATA_SOURCES_ID = "NON-LLM-ACTION-SELECTOR-DATA-SOURCES-001"
DATASET_ID = "NON-LLM-ACTION-SELECTOR-DATASET-001"
DATA_SOURCES_DIR = GENERATED_DIR / DATA_SOURCES_ID
DATASET_DIR = GENERATED_DIR / DATASET_ID

BALANCED_DIR = GENERATED_DIR / "LOCAL-QWEN-BALANCED-SFT-DATASET-001"
OLLAMA_BENCHMARK_SCRIPT = ROOT / "scripts" / "benchmark_ollama_small_live_action_models_001.py"
LABELS_PATH = ROOT / "runtime" / "action_selector" / "action_selector_labels.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
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


def normalize_text(value: Any) -> str:
    text = re.sub(r"[^a-z0-9+/#.]+", " ", str(value or "").casefold())
    return " ".join(text.split())


def labels() -> set[str]:
    payload = read_json(LABELS_PATH)
    return {
        str(item.get("action_id"))
        for item in payload.get("labels", [])
        if isinstance(item, dict) and isinstance(item.get("action_id"), str)
    }


def compact_target(row: dict[str, Any]) -> dict[str, Any]:
    target = row.get("target_compact_json")
    return target if isinstance(target, dict) else {}


def source_role(path: Path) -> tuple[str, str]:
    path_text = rel(path)
    if "LOCAL-QWEN-BALANCED-SFT-DATASET-001" in path_text and path.suffix == ".jsonl":
        return "committed sanitized/synthetic action-target rows", "training_eval"
    if path.name == "qwen_compact_target_cards.json":
        return "canonical compact planner target cards", "reference"
    if path.name == "qwen_balanced_planner_dataset_spec.json":
        return "balanced dataset policy and split requirements", "reference"
    if path.name == "qwen_live_action_contract.json":
        return "prior live-action action-id contract", "reference"
    if path.name == "compact_planner_contract.py":
        return "compact planner label/value contract", "reference"
    if path.name == "live_action_prompt.py":
        return "disabled prior live-action prompt renderer", "reference"
    if path.name == "live_action_verifier.py":
        return "prior live-action verifier and action validation rules", "reference"
    if path.name == "ultravox_sales_brain_tool_contract.json":
        return "hosted voice tool boundary contract", "reference"
    if "LOCAL-OLLAMA-SMALL-LIVE-ACTION-MODEL-BENCHMARK-001" in path_text:
        return "small-model latency and validity benchmark evidence", "reference"
    if "LOCAL-OLLAMA-SMALL-LIVE-ACTION-MODEL-DECISION-001" in path_text:
        return "small-model decision evidence recommending non-LLM path", "reference"
    if path.name == OLLAMA_BENCHMARK_SCRIPT.name:
        return "committed synthetic live-action benchmark case definitions", "test_only"
    return "candidate source", "reference"


def summarize_source(path: Path) -> dict[str, Any]:
    role, usage = source_role(path)
    summary: dict[str, Any] = {
        "path": rel(path),
        "exists": path.exists(),
        "role": role,
        "usage": usage,
        "usable_row_count": 0,
        "available_action_labels": [],
        "label_compatibility_issues": [],
    }
    if not path.exists():
        summary["label_compatibility_issues"].append("missing")
        return summary
    if path.suffix == ".jsonl":
        rows = read_jsonl(path)
        summary["usable_row_count"] = len(rows)
        actions = Counter(str(compact_target(row).get("action") or "") for row in rows)
        summary["source_action_distribution"] = dict(sorted(actions.items()))
        mapped = Counter(map_balanced_row_to_action_id(row) for row in rows)
        summary["available_action_labels"] = sorted(mapped)
        if set(actions) - set(BALANCED_ACTION_COMPATIBILITY_NOTES):
            summary["label_compatibility_issues"].append("unmapped compact action values present")
        return summary
    if path.suffix != ".json":
        if path.name == OLLAMA_BENCHMARK_SCRIPT.name:
            summary["usable_row_count"] = 20
            summary["available_action_labels"] = sorted({case["target_action_id"] for case in benchmark_cases()})
        return summary
    payload = read_json(path)
    if path.name == "result.json" and "LOCAL-QWEN-BALANCED-SFT-DATASET-001" in rel(path):
        summary["usable_row_count"] = int(payload.get("in_distribution_rows") or payload.get("total_rows") or 0)
        by_split = payload.get("label_distribution_by_split")
        if isinstance(by_split, dict):
            labels_seen: set[str] = set()
            for split_payload in by_split.values():
                if isinstance(split_payload, dict) and isinstance(split_payload.get("action"), dict):
                    labels_seen.update(str(key) for key in split_payload["action"])
            summary["source_action_labels"] = sorted(labels_seen)
    elif path.name == "qwen_compact_target_cards.json":
        cards = payload.get("cards") if isinstance(payload.get("cards"), list) else []
        summary["usable_row_count"] = len(cards)
        summary["source_action_labels"] = sorted({str(card.get("canonical_action") or "") for card in cards})
        summary["available_action_labels"] = sorted({map_card_to_action_id(card) for card in cards})
    elif path.name == "qwen_live_action_contract.json":
        action_space = payload.get("action_space") if isinstance(payload.get("action_space"), dict) else {}
        summary["available_action_labels"] = list(action_space.get("semantic_reusable_action_ids") or [])
        summary["label_compatibility_issues"].append("prior contract has fewer repair and plan-detail labels than Phase 4K0")
    elif "LOCAL-OLLAMA-SMALL-LIVE-ACTION-MODEL-BENCHMARK-001" in rel(path):
        summary["usable_row_count"] = int(payload.get("case_count") or 0)
        summary["available_action_labels"] = list((payload.get("model_summaries") or {}).keys())[:0]
        summary["label_compatibility_issues"].append("benchmark result rows do not carry buyer text; script cases are used for test-only rows")
    elif "LOCAL-OLLAMA-SMALL-LIVE-ACTION-MODEL-DECISION-001" in rel(path):
        summary["usable_row_count"] = 0
        summary["label_compatibility_issues"].append("decision evidence only, not training rows")
    elif path.suffix == ".py":
        summary["usable_row_count"] = 20 if path.name == OLLAMA_BENCHMARK_SCRIPT.name else 0
        if path.name == OLLAMA_BENCHMARK_SCRIPT.name:
            summary["available_action_labels"] = sorted({case["target_action_id"] for case in benchmark_cases()})
    return summary


BALANCED_ACTION_COMPATIBILITY_NOTES = {
    "answer_affiliation_boundary": "answer_source_or_affiliation",
    "answer_plan_category": "orient_plan_options or explain_subscription_vs_model",
    "answer_plan_change": "answer_plan_change",
    "answer_plan_fit": "recommend_plus, compare_plus_vs_pro, or compare_pro_tiers",
    "answer_price": "answer_price",
    "answer_signup_path": "answer_signup_path",
    "answer_source": "answer_source_or_affiliation",
    "answer_team_controls": "recommend_business_or_enterprise",
    "answer_without_inventing_facts": "answer_privacy_boundary or respect_boundary",
    "ask_individual_usage_intensity": "clarify_team_vs_individual",
    "ask_usage_intensity": "ask_usage_intensity",
    "ask_use_case_gap": "ask_use_case_gap",
    "compare_competitor_context": "handle_competitor_context",
    "disqualify_no_fit": "disqualify_no_fit",
    "recommend_plan": "recommend_pro",
    "reframe_price_objection": "handle_price_objection",
    "respect_boundary": "respect_boundary",
    "terminal_close": "terminal_close",
}


def map_card_to_action_id(card: dict[str, Any]) -> str:
    fake_row = {
        "target_card_id": card.get("card_id"),
        "target_compact_json": {
            "act": card.get("canonical_act"),
            "sub": (card.get("allowed_sub_values") or [""])[0],
            "action": card.get("canonical_action"),
            "update": card.get("update_policy") if isinstance(card.get("update_policy"), dict) else {},
        },
        "sanitized_buyer_text": card.get("default_buyer") or "",
    }
    return map_balanced_row_to_action_id(fake_row)


def map_balanced_row_to_action_id(row: dict[str, Any]) -> str:
    target = compact_target(row)
    action = str(target.get("action") or "")
    act = str(target.get("act") or "")
    sub = str(target.get("sub") or "")
    card_id = str(row.get("target_card_id") or "")
    text = normalize_text(row.get("sanitized_buyer_text"))
    update = target.get("update") if isinstance(target.get("update"), dict) else {}

    if action == "answer_plan_category":
        if sub == "model_vs_subscription_question" or "model" in text:
            return "explain_subscription_vs_model"
        return "orient_plan_options"
    if action in {"answer_source", "answer_affiliation_boundary"}:
        return "answer_source_or_affiliation"
    if action == "ask_individual_usage_intensity":
        return "clarify_team_vs_individual"
    if action == "answer_team_controls":
        return "recommend_business_or_enterprise"
    if action == "answer_price":
        return "answer_price"
    if action == "answer_plan_fit":
        if sub == "pro_tier_choice" or "pro" in text and "plus" not in text:
            return "compare_pro_tiers"
        if "plus vs pro" in text:
            return "compare_plus_vs_pro"
        return "recommend_plus"
    if action == "recommend_plan":
        recommendation = normalize_text(update.get("recommend"))
        if "pro" in recommendation:
            return "recommend_pro"
        if "business" in recommendation or "enterprise" in recommendation:
            return "recommend_business_or_enterprise"
        if "plus" in recommendation:
            return "recommend_plus"
        return "recommend_pro"
    if action == "reframe_price_objection":
        return "handle_price_objection"
    if action == "compare_competitor_context":
        return "handle_competitor_context"
    if action == "answer_signup_path":
        return "answer_signup_path"
    if action == "answer_plan_change":
        return "answer_plan_change"
    if action == "answer_without_inventing_facts":
        if sub in {"privacy_question", "raw_transcript_request"}:
            return "answer_privacy_boundary"
        return "respect_boundary"
    if action == "respect_boundary":
        if sub in {"privacy_question", "raw_transcript_request"}:
            return "answer_privacy_boundary"
        return "respect_boundary"
    if action == "terminal_close":
        return "terminal_close"
    if action == "disqualify_no_fit" or act == "no_fit":
        return "disqualify_no_fit"
    if action == "ask_usage_intensity":
        return "ask_usage_intensity"
    if action == "ask_use_case_gap":
        return "ask_use_case_gap"
    if card_id.startswith("adoption_no_current"):
        return "ask_adoption_state"
    return "ask_use_case_gap"


def context_from_balanced_row(row: dict[str, Any]) -> dict[str, Any]:
    target = compact_target(row)
    update = target.get("update") if isinstance(target.get("update"), dict) else {}
    semantic = row.get("expected_semantic_frame") if isinstance(row.get("expected_semantic_frame"), dict) else {}
    use_cases = [str(item) for item in update.get("use", []) if str(item or "").strip()] if isinstance(update.get("use"), list) else []
    tools = [str(item) for item in target.get("obj", []) if str(item or "").strip()] if isinstance(target.get("obj"), list) else []
    team = update.get("team")
    if team is True:
        team_status = "team"
    elif team is False:
        team_status = "individual"
    else:
        team_status = str((row.get("prior_state") or {}).get("team_state") or "")
    return {
        "buyer_utterance_text": str(row.get("sanitized_buyer_text") or ""),
        "normalized_buyer_text": normalize_text(row.get("sanitized_buyer_text")),
        "memory_summary": json.dumps(row.get("prior_state") or {}, sort_keys=True, separators=(",", ":")),
        "known_use_case": use_cases,
        "known_tools": tools,
        "known_plan_interest": str(update.get("recommend") or ""),
        "known_team_status": team_status,
        "buyer_emotion": str(semantic.get("buyer_emotion_hint") or target.get("buyer") or ""),
        "buyer_confusion_level": "high" if target.get("buyer") == "confused" else "",
        "buyer_skepticism_level": "high" if target.get("buyer") == "skeptical" else "",
        "buyer_engagement_level": str(target.get("intent") or ""),
        "last_action_id": "",
        "last_answered_topic": "",
        "safety_boundary_detected": target.get("act") == "safety_boundary" or "boundary" in str(target.get("intent") or ""),
        "compact_target": {
            "act": target.get("act"),
            "sub": target.get("sub"),
            "rel": target.get("rel"),
            "neg": target.get("neg"),
            "action": target.get("action"),
            "strategy": target.get("strategy"),
        },
    }


def dataset_row_from_balanced(row: dict[str, Any], split: str) -> dict[str, Any]:
    target_action_id = map_balanced_row_to_action_id(row)
    return {
        "case_id": f"qwen_balanced::{row.get('case_id')}",
        "split": split,
        "buyer_utterance_text": str(row.get("sanitized_buyer_text") or ""),
        "context": context_from_balanced_row(row),
        "target_action_id": target_action_id,
        "source_file": rel(BALANCED_DIR / f"{split}.jsonl"),
        "source_case_id": str(row.get("case_id") or ""),
        "sanitized": True,
        "raw_private_data": False,
        "notes": "Mapped from committed balanced compact-planner synthetic/sanitized target.",
    }


def benchmark_cases() -> list[dict[str, Any]]:
    base_memory = {
        "last_action_id": "",
        "last_action_slot_signature": "",
        "last_agent_question": "",
        "last_response_signature": "",
        "answered_topics": [],
        "asked_topic_counts": {},
        "known_slots": {},
    }

    def case(case_id: str, category: str, buyer: str, target_action_id: str, **overrides: Any) -> dict[str, Any]:
        memory = {**base_memory, **overrides.pop("memory", {})}
        memory["current_buyer_utterance"] = buyer
        return {
            "case_id": case_id,
            "category": category,
            "buyer": buyer,
            "memory": memory,
            "target_action_id": target_action_id,
            **overrides,
        }

    return [
        case("direct_price_001", "direct price", "How much is Plus?", "answer_price"),
        case("terminal_thanks_001", "terminal thanks", "Ok, I will check that, thanks.", "terminal_close", memory={"terminal_acceptance_seen": True}),
        case("current_tool_and_001", "current tool AND", "I use ChatGPT and Claude.", "ask_use_case_gap"),
        case("current_tool_or_001", "current tool OR", "I use ChatGPT or maybe Claude.", "ask_use_case_gap"),
        case("not_team_001", "not team", "I am by myself, not a team.", "clarify_team_vs_individual", memory={"known_slots": {"team_state": False}}),
        case("coding_voice_001", "coding and voice", "I use it for coding workflow and voice.", "ask_usage_intensity"),
        case("plan_explanation_001", "plan explanation", "What are the plans actually?", "orient_plan_options"),
        case("price_objection_001", "price objection", "Plus sounds expensive for what it is.", "handle_price_objection"),
        case("competitor_objection_001", "competitor objection", "Why not just use Claude instead?", "handle_competitor_context"),
        case("unsupported_side_effect_001", "unsupported side-effect request", "Can you just buy Plus for me?", "respect_boundary"),
        case(
            "repeated_question_risk_001",
            "repeated question risk",
            "You just asked that.",
            "avoid_repetition_rephrase",
            memory={
                "last_action_id": "ask_use_case_gap",
                "last_agent_question": "What would you mainly use it for?",
                "last_response_signature": "What would you mainly use it for?",
                "new_buyer_info_since_last_action": False,
            },
        ),
        case(
            "buyer_already_told_you_001",
            "buyer says already told you",
            "I already told you, coding and voice.",
            "repair_already_told_you",
            memory={
                "last_action_id": "ask_use_case_gap",
                "last_agent_question": "What would you mainly use it for?",
                "last_response_signature": "What would you mainly use it for?",
                "known_slots": {"use_case": ["coding", "voice"]},
                "buyer_said_already_told_you": True,
                "new_buyer_info_since_last_action": False,
            },
        ),
        case("asr_ambiguity_cloud_claude_001", "ASR ambiguity cloud/Claude", "I use cloud for this maybe, or Claude, not sure.", "repair_asr_uncertainty"),
        case("no_fit_001", "no-fit", "I barely use AI and the free plan is enough.", "disqualify_no_fit"),
        case("signup_path_001", "signup path", "Where do I sign up?", "answer_signup_path"),
        case("plan_change_001", "plan change", "Can I start lower and upgrade later?", "answer_plan_change"),
        case("source_affiliation_001", "source/affiliation", "Are you from OpenAI or just recommending this?", "answer_source_or_affiliation"),
        case("privacy_data_question_001", "privacy/data question", "Do you store what I say in this call?", "answer_privacy_boundary"),
        case("wrong_product_001", "wrong product", "I need help with Gmail, not ChatGPT.", "disqualify_no_fit"),
        case("unclear_confused_buyer_001", "unclear/confused buyer", "I am confused. What are you actually asking me?", "clarify_question_scope"),
    ]


def context_from_benchmark(case: dict[str, Any]) -> dict[str, Any]:
    memory = case.get("memory") if isinstance(case.get("memory"), dict) else {}
    known_slots = memory.get("known_slots") if isinstance(memory.get("known_slots"), dict) else {}
    use_case = known_slots.get("use_case") if isinstance(known_slots.get("use_case"), list) else []
    team_state = known_slots.get("team_state")
    if team_state is False:
        team_status = "individual"
    elif team_state is True:
        team_status = "team"
    else:
        team_status = ""
    return {
        "buyer_utterance_text": case["buyer"],
        "normalized_buyer_text": normalize_text(case["buyer"]),
        "memory_summary": json.dumps(memory, sort_keys=True, separators=(",", ":")),
        "known_use_case": [str(item) for item in use_case],
        "known_tools": [],
        "known_plan_interest": "",
        "known_team_status": team_status,
        "buyer_emotion": "",
        "buyer_confusion_level": "high" if "confused" in normalize_text(case["buyer"]) else "",
        "buyer_skepticism_level": "high" if "why not" in normalize_text(case["buyer"]) else "",
        "buyer_engagement_level": "",
        "last_action_id": str(memory.get("last_action_id") or ""),
        "last_answered_topic": "",
        "safety_boundary_detected": case["target_action_id"] in {"respect_boundary", "answer_privacy_boundary"},
        "benchmark_category": case["category"],
    }


def dataset_row_from_benchmark(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": f"ollama_benchmark::{case['case_id']}",
        "split": "test",
        "buyer_utterance_text": case["buyer"],
        "context": context_from_benchmark(case),
        "target_action_id": case["target_action_id"],
        "source_file": rel(OLLAMA_BENCHMARK_SCRIPT),
        "source_case_id": case["case_id"],
        "sanitized": True,
        "raw_private_data": False,
        "notes": "Test-only target inferred from committed synthetic benchmark case category and prior action descriptions.",
    }


def build_dataset() -> dict[str, list[dict[str, Any]]]:
    splits: dict[str, list[dict[str, Any]]] = {}
    for split in ("train", "validation", "test"):
        source_rows = read_jsonl(BALANCED_DIR / f"{split}.jsonl")
        splits[split] = [dataset_row_from_balanced(row, split) for row in source_rows]
    existing_texts = {
        normalize_text(row.get("buyer_utterance_text"))
        for rows in splits.values()
        for row in rows
    }
    for case in benchmark_cases():
        if normalize_text(case["buyer"]) in existing_texts:
            continue
        splits["test"].append(dataset_row_from_benchmark(case))
        existing_texts.add(normalize_text(case["buyer"]))
    return splits


def label_distribution(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, int]]:
    return {
        split: dict(sorted(Counter(row["target_action_id"] for row in rows).items()))
        for split, rows in rows_by_split.items()
    }


def exact_text_overlap(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, list[str]]:
    by_split = {
        split: {normalize_text(row.get("buyer_utterance_text")) for row in rows if normalize_text(row.get("buyer_utterance_text"))}
        for split, rows in rows_by_split.items()
    }
    return {
        "train_validation": sorted(by_split["train"] & by_split["validation"]),
        "train_test": sorted(by_split["train"] & by_split["test"]),
        "validation_test": sorted(by_split["validation"] & by_split["test"]),
    }


def case_id_overlap(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, list[str]]:
    by_split = {split: {str(row.get("case_id") or "") for row in rows} for split, rows in rows_by_split.items()}
    return {
        "train_validation": sorted(by_split["train"] & by_split["validation"]),
        "train_test": sorted(by_split["train"] & by_split["test"]),
        "validation_test": sorted(by_split["validation"] & by_split["test"]),
    }


def validate_rows(rows_by_split: dict[str, list[dict[str, Any]]], allowed_labels: set[str]) -> list[str]:
    failures: list[str] = []
    required_fields = {
        "case_id",
        "split",
        "buyer_utterance_text",
        "context",
        "target_action_id",
        "source_file",
        "source_case_id",
        "sanitized",
        "raw_private_data",
        "notes",
    }
    for split, rows in rows_by_split.items():
        for index, row in enumerate(rows, start=1):
            label = f"{split}[{index}]"
            missing = sorted(required_fields - set(row))
            if missing:
                failures.append(f"{label} missing fields: {missing}")
            if row.get("split") != split:
                failures.append(f"{label}.split mismatch")
            if row.get("sanitized") is not True:
                failures.append(f"{label}.sanitized must be true")
            if row.get("raw_private_data") is not False:
                failures.append(f"{label}.raw_private_data must be false")
            if row.get("target_action_id") not in allowed_labels:
                failures.append(f"{label}.target_action_id not controlled: {row.get('target_action_id')}")
            source_file = normalize_text(row.get("source_file"))
            if "data/private" in source_file or "private-restricted" in source_file:
                failures.append(f"{label}.source_file references private data")
            context = row.get("context")
            if not isinstance(context, dict):
                failures.append(f"{label}.context must be object")
    overlaps = exact_text_overlap(rows_by_split)
    for key, values in overlaps.items():
        if values and key in {"train_validation", "train_test"}:
            failures.append(f"held-out exact buyer-text overlap in {key}: {values[:5]}")
    id_overlaps = case_id_overlap(rows_by_split)
    for key, values in id_overlaps.items():
        if values and key in {"train_validation", "train_test"}:
            failures.append(f"held-out case-id overlap in {key}: {values[:5]}")
    if sum(len(rows) for rows in rows_by_split.values()) < 200:
        failures.append("fewer than 200 safe rows available")
    return failures


def discover_sources() -> dict[str, Any]:
    candidate_paths = [
        BALANCED_DIR / "result.json",
        BALANCED_DIR / "report.md",
        BALANCED_DIR / "train.jsonl",
        BALANCED_DIR / "validation.jsonl",
        BALANCED_DIR / "test.jsonl",
        GENERATED_DIR / "LOCAL-OLLAMA-SMALL-LIVE-ACTION-MODEL-BENCHMARK-001" / "result.json",
        GENERATED_DIR / "LOCAL-OLLAMA-SMALL-LIVE-ACTION-MODEL-BENCHMARK-001" / "report.md",
        GENERATED_DIR / "LOCAL-OLLAMA-SMALL-LIVE-ACTION-MODEL-DECISION-001" / "result.json",
        GENERATED_DIR / "LOCAL-OLLAMA-SMALL-LIVE-ACTION-MODEL-DECISION-001" / "report.md",
        ROOT / "runtime" / "llm_brain" / "training" / "qwen_balanced_planner_dataset_spec.json",
        ROOT / "runtime" / "llm_brain" / "training" / "qwen_compact_target_cards.json",
        ROOT / "runtime" / "llm_brain" / "training" / "qwen_live_action_contract.json",
        ROOT / "runtime" / "llm_brain" / "compact_planner_contract.py",
        ROOT / "runtime" / "llm_brain" / "live_action_prompt.py",
        ROOT / "runtime" / "llm_brain" / "live_action_verifier.py",
        ROOT / "runtime" / "audio_backends" / "ultravox_sales_brain_tool_contract.json",
        OLLAMA_BENCHMARK_SCRIPT,
    ]
    discovered = [summarize_source(path) for path in candidate_paths]
    usable_training_rows = sum(
        int(item.get("usable_row_count") or 0)
        for item in discovered
        if item.get("usage") in {"training_eval", "test_only"}
    )
    result = {
        "experiment_id": DATA_SOURCES_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "discovered_source_files": discovered,
        "usable_training_or_eval_rows": usable_training_rows,
        "available_action_labels": sorted({label for item in discovered for label in item.get("available_action_labels", [])}),
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "ultravox_calls_made": False,
        "elevenlabs_calls_made": False,
        "local_llm_calls_made": False,
        "ollama_calls_made": False,
        "model_training_performed": False,
        "live_runtime_wiring_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    return result


def dataset_result(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    allowed = labels()
    failures = validate_rows(rows_by_split, allowed)
    distribution = label_distribution(rows_by_split)
    total_distribution = Counter()
    for split_distribution in distribution.values():
        total_distribution.update(split_distribution)
    rare_labels = {
        label: count
        for label, count in sorted(total_distribution.items())
        if count < 3
    }
    result = {
        "experiment_id": DATASET_ID,
        "generated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "source_artifacts": {
            "primary_dataset": rel(BALANCED_DIR),
            "benchmark_cases": rel(OLLAMA_BENCHMARK_SCRIPT),
            "labels": rel(LABELS_PATH),
        },
        "split_counts": {split: len(rows) for split, rows in rows_by_split.items()},
        "total_rows": sum(len(rows) for rows in rows_by_split.values()),
        "safe_rows_available": sum(len(rows) for rows in rows_by_split.values()),
        "row_count_blocker": "" if sum(len(rows) for rows in rows_by_split.values()) >= 200 else "Fewer than 200 committed sanitized/synthetic rows available.",
        "label_count": len(total_distribution),
        "label_distribution": {split: distribution[split] for split in ("train", "validation", "test")},
        "total_label_distribution": dict(sorted(total_distribution.items())),
        "rare_labels": rare_labels,
        "unused_controlled_labels": sorted(allowed - set(total_distribution)),
        "heldout_exact_text_overlap": exact_text_overlap(rows_by_split),
        "heldout_case_id_overlap": case_id_overlap(rows_by_split),
        "source_file_counts": dict(sorted(Counter(row["source_file"] for rows in rows_by_split.values() for row in rows).items())),
        "privacy": {
            "sanitized_only": True,
            "raw_private_data": False,
            "audio_data_used": False,
            "generated_audio_used": False,
        },
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "ultravox_calls_made": False,
        "elevenlabs_calls_made": False,
        "local_llm_calls_made": False,
        "ollama_calls_made": False,
        "model_training_performed": False,
        "live_runtime_wiring_allowed": False,
        "side_effects_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "failures": failures,
    }
    return result


def build_sources_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {DATA_SOURCES_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Usable training/eval rows: {result['usable_training_or_eval_rows']}",
        "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama calls: false",
        "- Live runtime wiring allowed: false",
        "",
        "## Discovered Sources",
        "",
    ]
    for item in result["discovered_source_files"]:
        lines.append(f"- `{item['path']}`")
        lines.append(f"  - role: {item['role']}")
        lines.append(f"  - usage: {item['usage']}")
        lines.append(f"  - usable_row_count: {item['usable_row_count']}")
        if item.get("available_action_labels"):
            lines.append(f"  - available_action_labels: {', '.join(item['available_action_labels'])}")
        if item.get("label_compatibility_issues"):
            lines.append(f"  - compatibility: {', '.join(item['label_compatibility_issues'])}")
    return "\n".join(lines)


def build_dataset_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {DATASET_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Total rows: {result['total_rows']}",
        f"- Split counts: `{json.dumps(result['split_counts'], sort_keys=True)}`",
        f"- Label count: {result['label_count']}",
        "- Sanitized only: true",
        "- Raw private data: false",
        "- Audio data used: false",
        "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama calls: false",
        "- Live runtime wiring allowed: false",
        "- Runtime behavior changed: false",
        "- Response text changed: false",
        "",
        "## Label Distribution",
        "",
    ]
    for split, distribution in result["label_distribution"].items():
        lines.append(f"### {split}")
        for label, count in distribution.items():
            lines.append(f"- {label}: {count}")
        lines.append("")
    lines.extend(["## Rare Labels", ""])
    if result["rare_labels"]:
        for label, count in result["rare_labels"].items():
            lines.append(f"- {label}: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Held-Out Overlap", ""])
    lines.append(f"- Exact buyer text: `{json.dumps(result['heldout_exact_text_overlap'], sort_keys=True)}`")
    lines.append(f"- Case IDs: `{json.dumps(result['heldout_case_id_overlap'], sort_keys=True)}`")
    if result["failures"]:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in result["failures"])
    return "\n".join(lines)


def main() -> int:
    source_result = discover_sources()
    rows_by_split = build_dataset()
    result = dataset_result(rows_by_split)
    write_json(DATA_SOURCES_DIR / "result.json", source_result)
    write_text(DATA_SOURCES_DIR / "report.md", build_sources_report(source_result))
    for split, rows in rows_by_split.items():
        write_jsonl(DATASET_DIR / f"{split}.jsonl", rows)
    write_json(DATASET_DIR / "result.json", result)
    write_text(DATASET_DIR / "report.md", build_dataset_report(result))
    print(json.dumps({"status": result["status"], "total_rows": result["total_rows"], "split_counts": result["split_counts"]}, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
