#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.compact_planner_contract import (  # noqa: E402
    COMPACT_VALUE_CONTRACT_VERSION,
    compact_label_quality_issues,
    validate_compact_value_contract,
)
from runtime.llm_brain.conversation_brain_prompts import render_conversation_brain_prompt  # noqa: E402
from runtime.llm_brain.conversation_brain_schema import (  # noqa: E402
    COMPACT_PLANNER_SCHEMA_MODE,
    expand_compact_planner_output,
    validate_compact_conversation_brain_output,
)
from runtime.llm_brain.conversation_brain_verifier import verify_conversation_brain_output  # noqa: E402


EXPERIMENT_ID = "LOCAL-QWEN-TINY-OVERFIT-DATASET-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
TRAIN_PATH = OUT_DIR / "train.jsonl"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
CAMPAIGN_ID = "public-openai-chatgpt-plans"
PUBLIC_PLAN_NAMES_SUMMARY = (
    "ChatGPT public plan categories include Free, Plus, Pro, Business, and Enterprise; "
    "the official source remains authoritative."
)
BASE_PRIOR_STATE = {
    "adoption_state": "unknown",
    "campaign_id": CAMPAIGN_ID,
    "team_state": "unknown",
    "usage_intensity": "unknown",
}
COMMON_FORBIDDEN_MARKERS = [
    "internal policy",
    "RouteSignal",
    "PROD-102",
    "we at OpenAI",
    "sent the email",
    "created the calendar",
    "guaranteed",
    "unlimited access",
    "http://",
    "https://",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def target(
    *,
    act: str,
    sub: str,
    obj: list[str],
    rel_value: str,
    neg: str,
    buyer: str,
    intent: str,
    update: dict[str, Any] | None = None,
    block: list[str] | None = None,
    action: str,
    strategy: str,
    facts: list[str] | None = None,
    preserve: list[str] | None = None,
    avoid: list[str] | None = None,
    say: str,
    flags: list[str] | None = None,
    conf: float = 0.91,
) -> dict[str, Any]:
    return {
        "act": act,
        "sub": sub,
        "obj": obj,
        "rel": rel_value,
        "neg": neg,
        "buyer": buyer,
        "intent": intent,
        "update": update
        or {"adoption": "", "use": [], "intensity": "", "team": False, "recommend": "", "close": ""},
        "block": block or [],
        "action": action,
        "strategy": strategy,
        "facts": facts or [],
        "preserve": preserve or [],
        "avoid": avoid or [],
        "say": say,
        "flags": flags or [],
        "conf": conf,
    }


TINY_CASES: list[dict[str, Any]] = [
    {
        "case_id": "tiny_current_tool_and_001",
        "category": "current tool with AND",
        "sanitized_buyer_text": "I use ChatGPT and other AI tools.",
        "last_agent_question": "",
        "target_compact_json": target(
            act="adoption_state",
            sub="current_chatgpt_and_other_ai_user",
            obj=["ChatGPT", "other AI tools"],
            rel_value="and",
            neg="none",
            buyer="evaluating",
            intent="medium",
            update={
                "adoption": "current_chatgpt_and_other_ai_user",
                "use": [],
                "intensity": "",
                "team": False,
                "recommend": "",
                "close": "",
            },
            action="ask_use_case_gap",
            strategy="preserve_buyer_words",
            preserve=["ChatGPT", "other AI tools"],
            say=(
                "Got it - you already use ChatGPT and other AI tools. "
                "The useful next detail is where the gap is."
            ),
        ),
    },
    {
        "case_id": "tiny_current_tool_or_002",
        "category": "current tool with OR",
        "sanitized_buyer_text": "I use ChatGPT or maybe Claude.",
        "last_agent_question": "",
        "target_compact_json": target(
            act="current_tool_context",
            sub="current_chatgpt_or_other_ai_unknown",
            obj=["ChatGPT", "Claude"],
            rel_value="or",
            neg="none",
            buyer="evaluating",
            intent="medium",
            update={
                "adoption": "current_chatgpt_or_other_ai_unknown",
                "use": [],
                "intensity": "",
                "team": False,
                "recommend": "",
                "close": "",
            },
            action="ask_use_case_gap",
            strategy="preserve_buyer_words",
            preserve=["ChatGPT", "Claude"],
            say="Got it - ChatGPT or maybe Claude. The useful next detail is what you use it for.",
        ),
    },
    {
        "case_id": "tiny_negated_team_003",
        "category": "negated team",
        "sanitized_buyer_text": "I'm by myself, not a team.",
        "last_agent_question": "",
        "target_compact_json": target(
            act="team_scope",
            sub="not_team_personal_use",
            obj=["by myself", "not a team"],
            rel_value="and",
            neg="team_state",
            buyer="individual_user",
            intent="information",
            update={"adoption": "", "use": [], "intensity": "", "team": False, "recommend": "", "close": ""},
            block=["team_state"],
            action="ask_individual_usage_intensity",
            strategy="preserve_buyer_words",
            preserve=["by myself", "not a team"],
            avoid=["team plan", "business workspace"],
            say="Understood - by myself, not a team. I would keep this on an individual-use path first.",
        ),
    },
    {
        "case_id": "tiny_use_case_fidelity_004",
        "category": "use case fidelity",
        "sanitized_buyer_text": "I use it for coding workflow and probably voice.",
        "last_agent_question": "",
        "target_compact_json": target(
            act="use_case_scope",
            sub="coding_voice_use_case",
            obj=["coding workflow", "voice"],
            rel_value="and",
            neg="none",
            buyer="evaluating",
            intent="evaluation",
            update={
                "adoption": "",
                "use": ["coding workflow", "voice"],
                "intensity": "",
                "team": False,
                "recommend": "",
                "close": "",
            },
            action="ask_usage_intensity",
            strategy="preserve_buyer_words",
            preserve=["coding workflow", "voice"],
            avoid=["writing"],
            say="Got it - coding workflow and voice. Are you using it lightly, moderately, or heavily?",
        ),
    },
    {
        "case_id": "tiny_plan_category_005",
        "category": "plan category explanation",
        "sanitized_buyer_text": "What are Free, Plus, Pro, Business, and Enterprise?",
        "last_agent_question": "",
        "target_compact_json": target(
            act="orientation_or_explanation",
            sub="plan_category_explanation",
            obj=["Free", "Plus", "Pro", "Business", "Enterprise"],
            rel_value="and",
            neg="none",
            buyer="confused",
            intent="information",
            action="answer_plan_category",
            strategy="explain_without_overclaiming",
            facts=["public_plan_names"],
            preserve=["Free", "Plus", "Pro", "Business", "Enterprise"],
            say=(
                "Free, Plus, Pro, Business, and Enterprise are ChatGPT public plan categories. "
                "The official source remains authoritative."
            ),
            flags=["needs_fact_check"],
        ),
    },
    {
        "case_id": "tiny_midcycle_upgrade_006",
        "category": "midcycle upgrade",
        "sanitized_buyer_text": "What if I start with the lower Pro tier and upgrade later?",
        "last_agent_question": "",
        "target_compact_json": target(
            act="plan_change_question",
            sub="midcycle_upgrade_question",
            obj=["lower Pro tier", "upgrade later"],
            rel_value="and",
            neg="none",
            buyer="price_sensitive",
            intent="evaluation",
            action="answer_plan_change",
            strategy="explain_without_overclaiming",
            facts=["public_plan_names"],
            preserve=["lower Pro tier", "upgrade later"],
            avoid=["automatically upgrades", "guaranteed"],
            say=(
                "I would treat lower Pro tier and upgrade later as separate decisions, "
                "then verify the current rules before promising timing."
            ),
            flags=["needs_fact_check"],
        ),
    },
    {
        "case_id": "tiny_terminal_acceptance_007",
        "category": "terminal acceptance",
        "sanitized_buyer_text": "Ok, I'll check that, thanks.",
        "last_agent_question": "",
        "target_compact_json": target(
            act="terminal_acceptance",
            sub="terminal_thanks_acceptance",
            obj=["thanks"],
            rel_value="none",
            neg="none",
            buyer="evaluating",
            intent="none",
            update={
                "adoption": "",
                "use": [],
                "intensity": "",
                "team": False,
                "recommend": "",
                "close": "terminal_thanks_acceptance",
            },
            action="terminal_close",
            strategy="terminal_close",
            preserve=["thanks"],
            avoid=["new question"],
            say="Thanks - check that, and come back when you are ready.",
        ),
    },
    {
        "case_id": "tiny_safety_boundary_008",
        "category": "safety boundary",
        "sanitized_buyer_text": "Don't put me in CRM.",
        "last_agent_question": "",
        "target_compact_json": target(
            act="safety_boundary",
            sub="no_crm_request",
            obj=["external action boundary"],
            rel_value="none",
            neg="none",
            buyer="skeptical",
            intent="boundary",
            block=["crm"],
            action="respect_boundary",
            strategy="respect_boundary",
            preserve=[],
            avoid=["CRM", "record"],
            say="I will respect that boundary and not take any external action.",
        ),
    },
]


def context_for_case(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "normalized_transcript": case["sanitized_buyer_text"],
        "prior_state": dict(BASE_PRIOR_STATE),
        "approved_campaign_fact_ids": ["public_plan_names"],
        "approved_campaign_fact_summaries": {"public_plan_names": PUBLIC_PLAN_NAMES_SUMMARY},
        "smoke_contract": {},
        "last_agent_question": case["last_agent_question"],
        "campaign_id": CAMPAIGN_ID,
    }


def verifier_case(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "sanitized_buyer_text": case["sanitized_buyer_text"],
        "approved_campaign_fact_ids": ["public_plan_names"],
        "approved_campaign_fact_summaries": {"public_plan_names": PUBLIC_PLAN_NAMES_SUMMARY},
    }


def build_row(case: dict[str, Any]) -> tuple[dict[str, Any], list[str], str]:
    compact = case["target_compact_json"]
    compact_errors = validate_compact_conversation_brain_output(compact)
    contract_errors = validate_compact_value_contract(compact)
    quality_errors = [f"{item['field']}:{item['issue']}:{item['value']}" for item in compact_label_quality_issues(compact)]
    expanded, adapter_errors = expand_compact_planner_output(compact)
    verifier_errors = verify_conversation_brain_output(expanded, verifier_case(case)) if not adapter_errors else []
    errors = [*compact_errors, *contract_errors, *quality_errors, *adapter_errors, *verifier_errors]
    prompt = render_conversation_brain_prompt(context_for_case(case), schema_mode=COMPACT_PLANNER_SCHEMA_MODE)
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    row = {
        "case_id": case["case_id"],
        "category": case["category"],
        "source_type": "synthetic_tiny_overfit",
        "campaign_id": CAMPAIGN_ID,
        "sanitized_buyer_text": case["sanitized_buyer_text"],
        "prompt": prompt,
        "prompt_sha256": prompt_hash,
        "target_compact_json": compact,
        "target_full_json": expanded if not adapter_errors else {},
        "target_source": "hand_authored_tiny_overfit_contract",
        "approved_campaign_fact_summaries": {"public_plan_names": PUBLIC_PLAN_NAMES_SUMMARY},
        "prior_state": dict(BASE_PRIOR_STATE),
        "expected_safety_constraints": {
            "forbidden_response_markers": [*COMMON_FORBIDDEN_MARKERS, *compact.get("avoid", [])],
            "acceptable_response_markers": list(compact.get("preserve") or compact.get("obj") or []),
            "provider_calls_allowed": False,
            "openai_api_calls_allowed": False,
            "live_tts_calls_allowed": False,
            "fake_side_effects_allowed": False,
            "raw_private_transcript_allowed": False,
        },
        "failure_tags": [],
        "negative_example_metadata": {},
        "privacy_level": "synthetic_sanitized_only",
        "raw_private_transcript_included": False,
        "split": "train",
        "compact_value_contract_version": COMPACT_VALUE_CONTRACT_VERSION,
    }
    return row, errors, prompt_hash


def build_report(result: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        "## Summary",
        "",
        f"- status: {result['status']}",
        f"- rows: {result['case_count']}",
        f"- target_schema_issue_count: {result['target_schema_issue_count']}",
        f"- target_contract_issue_count: {result['target_contract_issue_count']}",
        f"- target_verifier_issue_count: {result['target_verifier_issue_count']}",
        f"- target_label_quality_issue_count: {result['target_label_quality_issue_count']}",
        f"- raw_private_transcript_included: {str(result['raw_private_transcript_included']).lower()}",
        f"- provider_side_effects_made: {str(result['side_effects']['provider_side_effects_made']).lower()}",
        f"- runtime_behavior_changed: {str(result['side_effects']['runtime_behavior_changed']).lower()}",
        f"- response_text_changed: {str(result['side_effects']['response_text_changed']).lower()}",
        "",
        "## Cases",
        "",
    ]
    for row in rows:
        compact = row["target_compact_json"]
        lines.append(
            f"- `{row['case_id']}`: {row['category']} -> act={compact['act']}, "
            f"sub={compact['sub']}, action={compact['action']}, strategy={compact['strategy']}"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- All rows are synthetic sanitized tiny-overfit cases.",
            "- Targets use compact planner contract values only.",
            "- No model, provider, OpenAI, CRM, email, calendar, or TTS calls are made.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    rows: list[dict[str, Any]] = []
    issue_counts: Counter[str] = Counter()
    prompt_hashes: dict[str, str] = {}
    case_errors: dict[str, list[str]] = {}
    for case in TINY_CASES:
        row, errors, prompt_hash = build_row(case)
        rows.append(row)
        prompt_hashes[row["case_id"]] = prompt_hash
        if errors:
            case_errors[row["case_id"]] = errors
            for error in errors:
                if error.startswith("compact."):
                    issue_counts["target_contract_issue_count"] += 1
                elif "deprecated_label" in error or "case_id_label" in error or "generic_" in error:
                    issue_counts["target_label_quality_issue_count"] += 1
                elif "compact" in error:
                    issue_counts["target_schema_issue_count"] += 1
                else:
                    issue_counts["target_verifier_issue_count"] += 1
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass" if not case_errors else "fail",
        "case_count": len(rows),
        "train_path": rel(TRAIN_PATH),
        "categories": [row["category"] for row in rows],
        "case_ids": [row["case_id"] for row in rows],
        "prompt_sha256_by_case": prompt_hashes,
        "compact_value_contract_version": COMPACT_VALUE_CONTRACT_VERSION,
        "target_schema_issue_count": int(issue_counts["target_schema_issue_count"]),
        "target_contract_issue_count": int(issue_counts["target_contract_issue_count"]),
        "target_verifier_issue_count": int(issue_counts["target_verifier_issue_count"]),
        "target_label_quality_issue_count": int(issue_counts["target_label_quality_issue_count"]),
        "case_errors": case_errors,
        "raw_private_transcript_included": False,
        "failed_qwen_outputs_used_as_targets": False,
        "side_effects": {
            "local_model_calls_made": False,
            "local_model_call_count": 0,
            "provider_calls_made": False,
            "openai_api_calls_made": False,
            "live_tts_calls_made": False,
            "provider_side_effects_made": False,
            "runtime_behavior_changed": False,
            "response_text_changed": False,
            "model_download_attempted": False,
            "model_redownloaded": False,
            "model_weights_committed": False,
            "adapter_weights_committed": False,
        },
    }
    write_jsonl(TRAIN_PATH, rows)
    write_json(RESULT_PATH, result)
    REPORT_PATH.write_text(build_report(result, rows), encoding="utf-8")
    print(json.dumps({"status": result["status"], "rows": len(rows), "case_errors": case_errors}, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
