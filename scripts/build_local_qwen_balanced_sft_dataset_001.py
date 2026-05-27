#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.compact_planner_contract import (  # noqa: E402
    COMPACT_VALUE_CONTRACT_VERSION,
    compact_label_quality_issues,
    is_case_id_like_label,
    validate_compact_value_contract,
)
from runtime.llm_brain.conversation_brain_prompts import render_conversation_brain_prompt  # noqa: E402
from runtime.llm_brain.conversation_brain_schema import (  # noqa: E402
    COMPACT_PLANNER_SCHEMA_MODE,
    REQUIRED_COMPACT_PLANNER_FIELDS,
    expand_compact_planner_output,
    validate_compact_conversation_brain_output,
)
from runtime.llm_brain.conversation_brain_verifier import verify_conversation_brain_output  # noqa: E402


EXPERIMENT_ID = "LOCAL-QWEN-BALANCED-SFT-DATASET-001"
SOURCE_DATASET_ID = "LOCAL-QWEN-SFT-DATASET-001"
TINY_DATASET_ID = "LOCAL-QWEN-TINY-OVERFIT-DATASET-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
SPLIT_PATHS = {
    "train": OUT_DIR / "train.jsonl",
    "validation": OUT_DIR / "validation.jsonl",
    "test": OUT_DIR / "test.jsonl",
    "ood_test": OUT_DIR / "ood_test.jsonl",
}
SPEC_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_balanced_planner_dataset_spec.json"
TARGET_CARDS_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_compact_target_cards.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_DATASET_ID
TINY_DIR = ROOT / "research" / "experiments" / "generated" / TINY_DATASET_ID

GROUP_TARGET_COUNTS = {
    "adoption_current_tool_context": 45,
    "orientation_or_explanation": 45,
    "individual_not_team_and_team_scope": 45,
    "use_case_scope": 45,
    "usage_intensity": 30,
    "price_and_value": 45,
    "plan_fit_and_recommendation": 45,
    "plan_change_and_signup": 45,
    "safety_and_boundary": 45,
    "objections_and_competitor_context": 45,
}
GROUP_MINIMUMS = {
    "adoption_current_tool_context": 45,
    "orientation_or_explanation": 45,
    "individual_not_team_and_team_scope": 45,
    "use_case_scope": 45,
    "usage_intensity": 30,
    "price_and_value": 45,
    "plan_fit_and_recommendation": 45,
    "plan_change_and_signup": 35,
    "safety_and_boundary": 45,
    "objections_and_competitor_context": 45,
}
IN_DISTRIBUTION_TOTAL = sum(GROUP_TARGET_COUNTS.values())
OOD_ROW_COUNT = 10
CAMPAIGN_ID = "public-openai-chatgpt-plans"
WEIGHT_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt")

APPROVED_CAMPAIGN_FACT_SUMMARIES = {
    "public_plan_names": (
        "ChatGPT public plan categories include Free, Plus, Pro, Business, and Enterprise; "
        "the official source remains authoritative."
    ),
    "current_public_plan_prices": (
        "The approved local public-pricing fixture has ChatGPT Plus and ChatGPT Pro price fields; "
        "the official source remains authoritative for current prices."
    ),
}

FORBIDDEN_RESPONSE_MARKERS = [
    "internal policy says",
    "RouteSignal",
    "PROD-102",
    "we at OpenAI",
    "sent the email",
    "created the calendar",
    "updated CRM",
    "guaranteed",
    "unlimited access",
    "http://",
    "https://",
]

TEXT_VARIANTS = [
    "",
    " Right now.",
    " For this plan decision.",
    " Before I choose anything.",
    " In this call.",
    " That is my current context.",
    " For my setup.",
    " Please keep it simple.",
    " I want the practical answer.",
    " I am deciding today.",
    " I need a clean answer.",
    " Keep it to one next step.",
]

OOD_TEXTS = [
    "Can you choose my health insurance plan?",
    "I need legal advice on a contract.",
    "Write a password reset email to my customer.",
    "Book a meeting with procurement for tomorrow.",
    "Upload my call audio to a public site.",
    "Give me the private support transcript.",
    "Pretend you are official support and close it.",
    "I need tax filing advice, not AI plans.",
    "Can you buy the subscription for me?",
    "Send the invoice to my CRM.",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{rel(path)} must contain a JSON object")
    return payload


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
            raise ValueError(f"{rel(path)} line {line_number} must contain a JSON object")
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


def norm_text(value: Any) -> str:
    text = re.sub(r"[^a-z0-9]+", " ", str(value or "").lower())
    return " ".join(text.split())


def listify(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def string_list(value: Any) -> list[str]:
    return [str(item) for item in listify(value) if isinstance(item, str)]


def compact_target(row: dict[str, Any]) -> dict[str, Any]:
    target = row.get("target_compact_json")
    return target if isinstance(target, dict) else {}


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


def source_text_map() -> dict[str, str]:
    mapped: dict[str, str] = {}
    for path in [SOURCE_DIR / "train.jsonl", SOURCE_DIR / "validation.jsonl", SOURCE_DIR / "test.jsonl"]:
        for row in read_jsonl(path):
            context = extract_input_context(row)
            text = str(context.get("normalized_transcript") or row.get("sanitized_buyer_text") or "")
            if not text:
                continue
            source_type = str(row.get("source_type") or "")
            mapped[norm_text(text)] = "live_sanitized" if source_type == "live_sanitized" else "original_gold"
    for row in read_jsonl(TINY_DIR / "train.jsonl"):
        text = str(row.get("sanitized_buyer_text") or "")
        if text:
            mapped.setdefault(norm_text(text), "original_gold")
    return mapped


def load_cards() -> list[dict[str, Any]]:
    payload = read_json(TARGET_CARDS_PATH)
    cards = payload.get("cards")
    if not isinstance(cards, list) or not cards:
        raise ValueError(f"{rel(TARGET_CARDS_PATH)} must contain cards")
    return [card for card in cards if isinstance(card, dict)]


def cards_by_group(cards: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for card in cards:
        grouped[str(card.get("semantic_group") or "")].append(card)
    return grouped


def objects_text(objects: list[str], rel: str) -> str:
    if not objects:
        return "that"
    if len(objects) == 1:
        return objects[0]
    joiner = " or " if rel == "or" else " and "
    return joiner.join(objects)


def update_from_policy(policy: dict[str, Any], sub: str, objects: list[str]) -> dict[str, Any]:
    adoption_policy = policy.get("adoption")
    use_policy = policy.get("use")
    intensity_policy = policy.get("intensity")
    return {
        "adoption": sub if adoption_policy == "sub" else str(adoption_policy or ""),
        "use": objects[:] if use_policy == "objects" else string_list(use_policy),
        "intensity": sub if intensity_policy == "sub" else str(intensity_policy or ""),
        "team": bool(policy.get("team")),
        "recommend": str(policy.get("recommend") or ""),
        "close": str(policy.get("close") or ""),
    }


def fact_summaries(fact_ids: list[str]) -> dict[str, str]:
    return {fact_id: APPROVED_CAMPAIGN_FACT_SUMMARIES[fact_id] for fact_id in fact_ids if fact_id in APPROVED_CAMPAIGN_FACT_SUMMARIES}


def source_type_for(
    semantic_group: str,
    card_id: str,
    base_text: str,
    variant_index: int,
    existing_sources: dict[str, str],
) -> str:
    if variant_index == 0 and norm_text(base_text) in existing_sources:
        return existing_sources[norm_text(base_text)]
    if semantic_group == "safety_and_boundary" and variant_index % 2 == 0:
        return "negative_control"
    if variant_index % 5 == 0:
        return "synthetic_control"
    if variant_index % 3 == 0:
        return "deterministic_paraphrase"
    if card_id.startswith("adoption_") or card_id.startswith("use_case_"):
        return "live_sanitized"
    return "deterministic_paraphrase"


def unique_buyer_text(base_text: str, variant_index: int, used: set[str]) -> str:
    suffix = TEXT_VARIANTS[variant_index % len(TEXT_VARIANTS)]
    extra_round = variant_index // len(TEXT_VARIANTS)
    candidate = f"{base_text}{suffix}"
    if extra_round:
        candidate = f"{candidate} Variant {extra_round + 1}."
    while norm_text(candidate) in used:
        extra_round += 1
        candidate = f"{base_text}{suffix} Variant {extra_round + 1}."
    used.add(norm_text(candidate))
    return candidate


def build_compact_target(card: dict[str, Any], example: dict[str, Any]) -> dict[str, Any]:
    sub = str(example.get("sub") or (card.get("allowed_sub_values") or [""])[0])
    rel_value = str(example.get("rel") or card.get("default_rel_policy") or "none")
    neg_value = str(example.get("neg") or card.get("default_neg_policy") or "none")
    objects = string_list(example.get("objects"))
    facts = string_list((card.get("facts_policy") or {}).get("fact_ids"))
    avoid = string_list((card.get("avoid_policy") or {}).get("phrases"))
    preserve_mode = str((card.get("preserve_policy") or {}).get("mode") or "objects")
    preserve = [] if preserve_mode == "none" else objects[:]
    template = str((card.get("say_style_policy") or {}).get("template") or "Got it - {objects}.")
    say = template.format(objects=objects_text(objects, rel_value))
    update_policy = card.get("update_policy") if isinstance(card.get("update_policy"), dict) else {}
    block_policy = card.get("block_policy") if isinstance(card.get("block_policy"), dict) else {}
    target = {
        "act": str(card.get("canonical_act") or ""),
        "sub": sub,
        "obj": objects,
        "rel": rel_value,
        "neg": neg_value,
        "buyer": str(card.get("default_buyer") or "evaluating"),
        "intent": str(card.get("default_intent") or "medium"),
        "update": update_from_policy(update_policy, sub, objects),
        "block": string_list(block_policy.get("block_updates")),
        "action": str(card.get("canonical_action") or ""),
        "strategy": str(card.get("canonical_strategy") or ""),
        "facts": facts,
        "preserve": preserve,
        "avoid": avoid,
        "say": say,
        "flags": [],
        "conf": 0.9,
    }
    return {key: target[key] for key in REQUIRED_COMPACT_PLANNER_FIELDS}


def build_request_context(sanitized_buyer_text: str, fact_ids: list[str]) -> dict[str, Any]:
    summaries = fact_summaries(fact_ids)
    return {
        "normalized_transcript": sanitized_buyer_text,
        "prior_state": {
            "adoption_state": "unknown",
            "campaign_id": CAMPAIGN_ID,
            "team_state": "unknown",
            "usage_intensity": "unknown",
        },
        "approved_campaign_fact_ids": fact_ids,
        "approved_campaign_fact_summaries": summaries,
        "smoke_contract": {},
        "last_agent_question": "",
        "campaign_id": CAMPAIGN_ID,
    }


def expected_constraints(avoid: list[str]) -> dict[str, Any]:
    forbidden = list(dict.fromkeys([*FORBIDDEN_RESPONSE_MARKERS, *avoid]))
    return {
        "forbidden_response_markers": forbidden,
        "acceptable_response_markers": [],
        "provider_calls_allowed": False,
        "openai_api_calls_allowed": False,
        "live_tts_calls_allowed": False,
        "fake_side_effects_allowed": False,
        "raw_private_transcript_allowed": False,
    }


def row_from_card(
    card: dict[str, Any],
    example: dict[str, Any],
    *,
    semantic_group: str,
    sequence: int,
    variant_index: int,
    source_type: str,
    sanitized_buyer_text: str,
    split: str,
) -> dict[str, Any]:
    target = build_compact_target(card, example)
    expanded, adapter_errors = expand_compact_planner_output(target)
    if adapter_errors:
        raise ValueError(f"{card.get('card_id')} compact target failed expansion: {adapter_errors}")
    fact_ids = string_list(target.get("facts"))
    context = build_request_context(sanitized_buyer_text, fact_ids)
    negative_metadata = {}
    if source_type in {"negative_control", "ood_control"}:
        negative_metadata = {
            "control_type": source_type,
            "failed_qwen_output_included": False,
            "target_uses_failed_qwen_output": False,
        }
    row = {
        "case_id": f"balanced_{semantic_group}_{sequence:03d}",
        "source_type": source_type,
        "semantic_group": semantic_group,
        "target_card_id": str(card.get("card_id") or ""),
        "campaign_id": CAMPAIGN_ID,
        "sanitized_buyer_text": sanitized_buyer_text,
        "prompt": render_conversation_brain_prompt(context, schema_mode=COMPACT_PLANNER_SCHEMA_MODE),
        "target_compact_json": target,
        "target_full_json": expanded,
        "target_source": "canonical_target_card",
        "approved_campaign_fact_ids": fact_ids,
        "approved_campaign_fact_summaries": context["approved_campaign_fact_summaries"],
        "prior_state": context["prior_state"],
        "expected_semantic_frame": expanded["semantic_frame"],
        "expected_state_update": expanded["state_update"],
        "expected_sales_strategy": expanded["sales_strategy"],
        "expected_response_plan": expanded["response_plan"],
        "expected_safety_constraints": expected_constraints(string_list(target.get("avoid"))),
        "privacy_level": "sanitized_only",
        "raw_private_transcript_included": False,
        "negative_example_metadata": negative_metadata,
        "split": split,
        "compact_value_contract_version": COMPACT_VALUE_CONTRACT_VERSION,
    }
    return row


def core_signature(row: dict[str, Any]) -> tuple[str, str, str, str]:
    target = compact_target(row)
    return (
        str(target.get("act") or ""),
        str(target.get("sub") or ""),
        str(target.get("action") or ""),
        str(target.get("strategy") or ""),
    )


def action_sub_signature(row: dict[str, Any]) -> tuple[str, str]:
    target = compact_target(row)
    return (str(target.get("action") or ""), str(target.get("sub") or ""))


def build_in_distribution_rows(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped = cards_by_group(cards)
    existing_sources = source_text_map()
    used_texts: set[str] = set()
    rows: list[dict[str, Any]] = []
    global_sequence = 1
    for semantic_group, target_count in GROUP_TARGET_COUNTS.items():
        group_cards = grouped.get(semantic_group, [])
        if not group_cards:
            raise ValueError(f"no target cards for semantic group: {semantic_group}")
        group_sequence = 0
        while group_sequence < target_count:
            card = group_cards[group_sequence % len(group_cards)]
            examples = [item for item in listify(card.get("examples")) if isinstance(item, dict)]
            if not examples:
                raise ValueError(f"target card has no examples: {card.get('card_id')}")
            example = examples[(group_sequence // len(group_cards)) % len(examples)]
            variant_index = group_sequence // max(1, len(group_cards))
            base_text = str(example.get("buyer_text") or "")
            buyer_text = unique_buyer_text(base_text, variant_index, used_texts)
            source_type = source_type_for(
                semantic_group,
                str(card.get("card_id") or ""),
                base_text,
                variant_index,
                existing_sources,
            )
            rows.append(
                row_from_card(
                    card,
                    example,
                    semantic_group=semantic_group,
                    sequence=global_sequence,
                    variant_index=variant_index,
                    source_type=source_type,
                    sanitized_buyer_text=buyer_text,
                    split="unassigned",
                )
            )
            group_sequence += 1
            global_sequence += 1
    return rows


def choose_split(counts: Counter[str], desired: dict[str, int]) -> str:
    deficits = {split: desired[split] - counts[split] for split in ("train", "validation", "test")}
    return max(deficits, key=lambda split: (deficits[split], -counts[split]))


def assign_splits(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    desired_train = round(len(rows) * 0.70)
    desired_validation = round(len(rows) * 0.15)
    desired = {
        "train": desired_train,
        "validation": desired_validation,
        "test": len(rows) - desired_train - desired_validation,
    }
    counts: Counter[str] = Counter()
    seen_core: set[tuple[str, str, str, str]] = set()
    seen_action_sub: set[tuple[str, str]] = set()
    splits: dict[str, list[dict[str, Any]]] = {"train": [], "validation": [], "test": []}
    for row in rows:
        core = core_signature(row)
        action_sub = action_sub_signature(row)
        if core not in seen_core or action_sub not in seen_action_sub:
            split = "train"
            seen_core.add(core)
            seen_action_sub.add(action_sub)
        else:
            split = choose_split(counts, desired)
        row["split"] = split
        splits[split].append(row)
        counts[split] += 1
    return splits


def build_ood_rows(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    card_lookup = {str(card.get("card_id") or ""): card for card in cards}
    card = card_lookup.get("safety_wrong_product")
    if not card:
        raise ValueError("missing safety_wrong_product card for OOD controls")
    used_texts: set[str] = set()
    example = {"objects": ["wrong product"], "sub": "wrong_product_question"}
    rows: list[dict[str, Any]] = []
    for index, text in enumerate(OOD_TEXTS[:OOD_ROW_COUNT], start=1):
        buyer_text = unique_buyer_text(text, 0, used_texts)
        rows.append(
            row_from_card(
                card,
                example,
                semantic_group="ood_control",
                sequence=index,
                variant_index=index,
                source_type="ood_control",
                sanitized_buyer_text=buyer_text,
                split="ood_test",
            )
        )
        rows[-1]["case_id"] = f"balanced_ood_control_{index:03d}"
    return rows


def labels_by_split(splits: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for split, rows in splits.items():
        result[split] = {
            "row_count": len(rows),
            "act": dict(sorted(Counter(str(compact_target(row).get("act") or "") for row in rows).items())),
            "sub": dict(sorted(Counter(str(compact_target(row).get("sub") or "") for row in rows).items())),
            "action": dict(sorted(Counter(str(compact_target(row).get("action") or "") for row in rows).items())),
            "strategy": dict(sorted(Counter(str(compact_target(row).get("strategy") or "") for row in rows).items())),
        }
    return result


def semantic_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("semantic_group") or "") for row in rows).items()))


def target_card_usage(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("target_card_id") or "") for row in rows).items()))


def heldout_coverage(splits: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    train_core = {core_signature(row) for row in splits["train"]}
    train_action_sub = {action_sub_signature(row) for row in splits["train"]}
    payload: dict[str, Any] = {}
    for split in ("validation", "test"):
        unseen_core = sorted({core_signature(row) for row in splits[split]} - train_core)
        unseen_action_sub = sorted({action_sub_signature(row) for row in splits[split]} - train_action_sub)
        payload[split] = {
            "unseen_act_sub_action_strategy_combo_count": len(unseen_core),
            "unseen_act_sub_action_strategy_combos": [
                {"act": item[0], "sub": item[1], "action": item[2], "strategy": item[3]} for item in unseen_core
            ],
            "unseen_action_sub_pair_count": len(unseen_action_sub),
            "unseen_action_sub_pairs": [{"action": item[0], "sub": item[1]} for item in unseen_action_sub],
            "covered_by_train": not unseen_core and not unseen_action_sub,
        }
    return payload


def exact_text_overlap(splits: dict[str, list[dict[str, Any]]]) -> dict[str, list[str]]:
    by_split = {
        split: {norm_text(row.get("sanitized_buyer_text")) for row in rows}
        for split, rows in splits.items()
        if split != "ood_test"
    }
    return {
        "train_validation": sorted(by_split["train"] & by_split["validation"]),
        "train_test": sorted(by_split["train"] & by_split["test"]),
        "validation_test": sorted(by_split["validation"] & by_split["test"]),
    }


def git_ls_files(prefix: str | None = None) -> list[str]:
    command = ["git", "--no-optional-locks", "ls-files"]
    if prefix:
        command.append(prefix)
    try:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=20, check=False)
    except Exception:
        return []
    if completed.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def changed_runtime_files() -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "--no-optional-locks", "diff", "--name-only", "HEAD", "--", "runtime"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except Exception:
        return []
    if completed.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def validate_target_cards(cards: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    required = {
        "semantic_group",
        "canonical_act",
        "allowed_sub_values",
        "canonical_action",
        "canonical_strategy",
        "default_buyer",
        "default_intent",
        "default_rel_policy",
        "default_neg_policy",
        "update_policy",
        "block_policy",
        "facts_policy",
        "preserve_policy",
        "avoid_policy",
        "say_style_policy",
        "safety_policy",
        "examples",
    }
    seen: set[str] = set()
    for index, card in enumerate(cards, start=1):
        card_id = str(card.get("card_id") or "")
        if not card_id:
            failures.append(f"target_cards[{index}] missing card_id")
        if card_id in seen:
            failures.append(f"duplicate target card id: {card_id}")
        seen.add(card_id)
        missing = sorted(required - set(card))
        if missing:
            failures.append(f"{card_id or index} missing target card fields: {missing}")
        if not isinstance(card.get("examples"), list) or not card["examples"]:
            failures.append(f"{card_id} examples must be non-empty")
    return failures


def validate_row(row: dict[str, Any], cards: dict[str, dict[str, Any]], *, label: str) -> list[str]:
    failures: list[str] = []
    required_fields = {
        "case_id",
        "source_type",
        "semantic_group",
        "target_card_id",
        "campaign_id",
        "prompt",
        "target_compact_json",
        "target_full_json",
        "approved_campaign_fact_summaries",
        "prior_state",
        "expected_safety_constraints",
        "privacy_level",
        "raw_private_transcript_included",
        "negative_example_metadata",
        "split",
    }
    missing = sorted(required_fields - set(row))
    if missing:
        failures.append(f"{label} missing required field(s): {missing}")
    if row.get("privacy_level") != "sanitized_only":
        failures.append(f"{label}.privacy_level must be sanitized_only")
    if row.get("raw_private_transcript_included") is not False:
        failures.append(f"{label}.raw_private_transcript_included must be false")
    if str(row.get("target_card_id") or "") not in cards:
        failures.append(f"{label}.target_card_id does not exist: {row.get('target_card_id')!r}")
    source_type = row.get("source_type")
    if source_type not in {
        "original_gold",
        "live_sanitized",
        "deterministic_paraphrase",
        "synthetic_control",
        "negative_control",
        "ood_control",
    }:
        failures.append(f"{label}.source_type is not allowed: {source_type!r}")
    target = compact_target(row)
    if not target:
        failures.append(f"{label}.target_compact_json must be an object")
        return failures
    if tuple(target.keys()) != REQUIRED_COMPACT_PLANNER_FIELDS:
        failures.append(f"{label}.target_compact_json key order must match compact schema")
    failures.extend(f"{label}: {error}" for error in validate_compact_conversation_brain_output(target))
    failures.extend(f"{label}: {error}" for error in validate_compact_value_contract(target))
    for issue in compact_label_quality_issues(target):
        failures.append(f"{label}.{issue['field']} quality issue {issue['issue']}: {issue['value']}")
    for field_name in ("act", "sub", "action", "strategy"):
        value = target.get(field_name)
        if is_case_id_like_label(value):
            failures.append(f"{label}.target_compact_json.{field_name} is case-ID-like: {value!r}")
        if value == "generalized_sales_move":
            failures.append(f"{label}.target_compact_json.{field_name} uses generalized_sales_move")
    fact_ids = set(string_list(target.get("facts")))
    approved_ids = set((row.get("approved_campaign_fact_summaries") or {}).keys())
    if fact_ids - approved_ids:
        failures.append(f"{label}.facts includes unapproved fact id(s): {sorted(fact_ids - approved_ids)}")
    expanded, adapter_errors = expand_compact_planner_output(target)
    failures.extend(f"{label}: compact-to-full adapter error: {error}" for error in adapter_errors)
    if not adapter_errors and row.get("target_full_json") != expanded:
        failures.append(f"{label}.target_full_json must equal compact-to-full adapter expansion")
    if not adapter_errors:
        verifier_errors = verify_conversation_brain_output(expanded, row)
        if verifier_errors:
            failures.append(f"{label} expanded target failed verifier: {verifier_errors}")
    return failures


def validate_dataset(splits: dict[str, list[dict[str, Any]]], cards: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[str] = []
    card_lookup = {str(card.get("card_id") or ""): card for card in cards}
    failures.extend(validate_target_cards(cards))
    all_rows = [row for split in ("train", "validation", "test", "ood_test") for row in splits.get(split, [])]
    in_distribution_rows = [row for split in ("train", "validation", "test") for row in splits.get(split, [])]
    total = len(all_rows)
    if total < 300:
        failures.append(f"total rows below 300: {total}")
    if total > 500:
        failures.append(f"total rows above 500: {total}")
    split_counts = {split: len(splits.get(split, [])) for split in ("train", "validation", "test", "ood_test")}
    group_counts = semantic_counts(in_distribution_rows)
    for group, minimum in GROUP_MINIMUMS.items():
        if group_counts.get(group, 0) < minimum:
            failures.append(f"{group} below minimum coverage: {group_counts.get(group, 0)} < {minimum}")
    coverage = heldout_coverage(splits)
    for split in ("validation", "test"):
        if not coverage[split]["covered_by_train"]:
            failures.append(f"{split} contains target labels not covered by train")
    overlaps = exact_text_overlap(splits)
    for key, values in overlaps.items():
        if values:
            failures.append(f"held-out exact text overlap in {key}: {values[:5]}")
    for split, rows in splits.items():
        for index, row in enumerate(rows, start=1):
            failures.extend(validate_row(row, card_lookup, label=f"{split}[{index}]"))
    tracked_weights = [path for path in git_ls_files() if path.lower().endswith(WEIGHT_SUFFIXES)]
    if tracked_weights:
        failures.append(f"model/adapters weights are tracked by git: {tracked_weights}")
    local_artifacts = git_ls_files("local_artifacts")
    if local_artifacts:
        failures.append(f"local_artifacts files are tracked by git: {local_artifacts}")
    runtime_files = [
        path for path in changed_runtime_files()
        if not path.startswith("runtime/llm_brain/training/")
    ]
    if runtime_files:
        failures.append(f"runtime behavior files changed outside training artifacts: {runtime_files}")
    metrics = {
        "total_rows": total,
        "in_distribution_rows": len(in_distribution_rows),
        "ood_rows": len(splits.get("ood_test", [])),
        "split_counts": split_counts,
        "semantic_group_counts": group_counts,
        "label_distribution_by_split": labels_by_split(splits),
        "heldout_coverage": coverage,
        "heldout_exact_text_overlap": overlaps,
        "target_card_usage": target_card_usage(all_rows),
        "source_type_counts": dict(sorted(Counter(str(row.get("source_type") or "") for row in all_rows).items())),
        "target_consistency": {
            "target_cards_valid": not validate_target_cards(cards),
            "validation_test_labels_covered_by_train": all(coverage[split]["covered_by_train"] for split in ("validation", "test")),
            "exact_text_heldout": not any(overlaps.values()),
        },
        "side_effects": {
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
        },
    }
    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "inputs": {
            "source_dataset": rel(SOURCE_DIR),
            "tiny_dataset": rel(TINY_DIR),
            "dataset_spec": rel(SPEC_PATH),
            "target_cards": rel(TARGET_CARDS_PATH),
        },
        **metrics,
        "failures": failures,
    }


def build_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Total rows: {result['total_rows']}",
        f"- In-distribution rows: {result['in_distribution_rows']}",
        f"- OOD rows: {result['ood_rows']}",
        f"- Split counts: `{json.dumps(result['split_counts'], sort_keys=True)}`",
        f"- Compact contract: `{COMPACT_VALUE_CONTRACT_VERSION}`",
        "- Local model calls made: false",
        "- Provider/OpenAI/TTS calls made: false",
        "- Runtime behavior changed: false",
        "- Response text changed: false",
        "",
        "## Semantic Group Counts",
        "",
    ]
    for group, count in result["semantic_group_counts"].items():
        minimum = GROUP_MINIMUMS.get(group, 0)
        lines.append(f"- {group}: {count} (minimum {minimum})")
    lines.extend(["", "## Held-Out Coverage", ""])
    for split in ("validation", "test"):
        coverage = result["heldout_coverage"][split]
        lines.append(
            f"- {split}: covered_by_train={coverage['covered_by_train']}, "
            f"unseen_core={coverage['unseen_act_sub_action_strategy_combo_count']}, "
            f"unseen_action_sub={coverage['unseen_action_sub_pair_count']}"
        )
    lines.extend(["", "## Target Consistency", ""])
    for key, value in result["target_consistency"].items():
        lines.append(f"- {key}: {str(value).lower()}")
    lines.extend(["", "## Source Types", ""])
    for source_type, count in result["source_type_counts"].items():
        lines.append(f"- {source_type}: {count}")
    if result["failures"]:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in result["failures"])
    return "\n".join(lines)


def main() -> int:
    read_json(SPEC_PATH)
    cards = load_cards()
    in_distribution_rows = build_in_distribution_rows(cards)
    splits = assign_splits(in_distribution_rows)
    splits["ood_test"] = build_ood_rows(cards)
    result = validate_dataset(splits, cards)
    for split, path in SPLIT_PATHS.items():
        write_jsonl(path, splits[split])
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(json.dumps({"status": result["status"], "total_rows": result["total_rows"], "split_counts": result["split_counts"]}, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
