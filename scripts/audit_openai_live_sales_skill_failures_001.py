#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


CHECKPOINT_ID = "OPENAI-LIVE-SALES-SKILL-FAILURE-AUDIT-001"
LATEST_TRANSCRIPT = (
    ROOT
    / "data"
    / "private"
    / "live-demo-003"
    / "raw-turns"
    / "browser-transcript"
    / "LIVE-DEMO-001-1ee53a37-c72e-41d7-87f6-472f4b7315fc-transcript.json"
)
FIXTURE_PATH = ROOT / "runtime" / "campaigns" / "examples" / "public-openai-chatgpt-plans.json"
GENERATED_ROOT = ROOT / "research" / "experiments" / "generated"
OUT_DIR = GENERATED_ROOT / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

EVIDENCE_FILES = [
    GENERATED_ROOT / "PUBLIC-OPENAI-COMMERCIAL-CLOSING-001" / "result.json",
    GENERATED_ROOT / "PUBLIC-OPENAI-LIVE-REHEARSAL-001" / "result.json",
    GENERATED_ROOT / "PUBLIC-OPENAI-MEMORY-PROGRESSION-001" / "result.json",
    GENERATED_ROOT / "PUBLIC-OPENAI-LIVE-SALES-READINESS-001" / "result.json",
    GENERATED_ROOT / "PUBLIC-OPENAI-LIVE-SALES-FLOW-001" / "result.json",
]

REQUIRED_SKILL_FAILURE_CLASSES = {
    "missed_recommendation_after_context",
    "missed_close_after_buying_signal",
    "over_qualification_after_enough_context",
    "weak_value_frame_after_price",
    "passive_competitor_handling",
    "repeated_safety_caveat",
    "no_decision_frame",
    "information_dump_without_momentum",
    "no_summary_of_known_buyer_context",
    "weak_opening_value",
    "weak_choice_close",
    "weak_objection_reframe",
    "no_fit_not_handled_cleanly",
}

PRIVATE_SNIPPET_LABELS = [
    (re.compile(r"plus.*enough|enough.*plus", re.I), "buyer_asks_plus_sufficiency"),
    (re.compile(r"pro.*better|pro.*probably|pro.*right", re.I), "buyer_agrees_pro_direction"),
    (re.compile(r"how much|price|cost", re.I), "buyer_asks_price"),
    (re.compile(r"sign up|upgrade|next step|official page", re.I), "buyer_asks_signup"),
    (re.compile(r"another (ai|llm)|claude|gemini|copilot|current tool", re.I), "buyer_mentions_competitor_or_current_tool"),
    (re.compile(r"coding|writing|code|draft", re.I), "buyer_names_coding_or_writing"),
    (re.compile(r"heavy|every day|daily", re.I), "buyer_names_heavy_use"),
    (re.compile(r"hitting limits|hit limits|blocked by limits|running out", re.I), "buyer_names_limit_pain"),
    (re.compile(r"too expensive|do not want to pay|don't want to pay|subscription", re.I), "buyer_price_or_subscription_objection"),
    (re.compile(r"works fine|enough|no need", re.I), "buyer_current_solution_or_no_fit_signal"),
    (re.compile(r"chachu|chat jpt|chat gbt|chat g p t", re.I), "asr_chatgpt_alias_variant"),
]

PRODUCT_FACT_RE = re.compile(r"20 dollars|100 dollar|200 dollar|business|enterprise|free|plus|pro", re.I)
DIRECT_BUYING_RE = re.compile(r"plus.*enough|how much|price|cost|sign up|upgrade|pro.*better|why switch|too expensive", re.I)
GENERIC_DISCOVERY_RE = re.compile(r"what matters most|what would you mainly use|occasionally or heavily every day|using chatgpt today.*another ai tool", re.I)
RECOMMENDATION_RE = re.compile(r"\brecommend|i would|i'd|compare pro|pro first|stronger fit|choose plus|choose pro", re.I)
CLOSE_RE = re.compile(r"official chatgpt plans page|profile upgrade flow|contact sales|next step", re.I)
VALUE_FRAME_RE = re.compile(r"because|based on|given|since|lower-cost|cheaper|safer|usage headroom|limits|team controls|current tool", re.I)
COMPETITOR_CAVEAT_RE = re.compile(r"you may not need to switch", re.I)
INTERNAL_POLICY_RE = re.compile(r"adoption state|plan fit still needs|i should not assume buying intent", re.I)
RAW_URL_RE = re.compile(r"https?://|www\.", re.I)
FAKE_SIDE_EFFECT_RE = re.compile(r"i sent|i emailed|i booked|created .*calendar|created .*crm|charged your card", re.I)
PIPELINE_RE = re.compile(r"asr|tts|latency|audio|voice", re.I)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def normalize(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def sha12(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def sanitized_labels(text: str) -> list[str]:
    labels = [label for pattern, label in PRIVATE_SNIPPET_LABELS if pattern.search(text)]
    return labels or ["no_private_phrase_exported"]


def classify_turn(customer: str, agent: str, *, turn_index: int) -> tuple[str, list[str]]:
    combined = f"{customer}\n{agent}"
    labels = sanitized_labels(customer)
    sales_failures: list[str] = []
    category = "no_defect"

    enough_context = (
        ("buyer_names_coding_or_writing" in labels and ("buyer_names_heavy_use" in labels or "buyer_asks_plus_sufficiency" in labels))
        or "buyer_asks_plus_sufficiency" in labels
        or "buyer_agrees_pro_direction" in labels
    )
    buying_signal = "buyer_agrees_pro_direction" in labels or "buyer_asks_signup" in labels
    price_question = "buyer_asks_price" in labels
    competitor = "buyer_mentions_competitor_or_current_tool" in labels
    no_fit = "buyer_current_solution_or_no_fit_signal" in labels or "buyer_price_or_subscription_objection" in labels

    if turn_index == 1 and not re.search(r"decide|worth looking|one minute|value", agent, re.I):
        sales_failures.append("weak_opening_value")
    if enough_context and not RECOMMENDATION_RE.search(agent):
        sales_failures.append("missed_recommendation_after_context")
    if enough_context and GENERIC_DISCOVERY_RE.search(agent):
        sales_failures.append("over_qualification_after_enough_context")
    if buying_signal and not CLOSE_RE.search(agent):
        sales_failures.append("missed_close_after_buying_signal")
    if price_question and PRODUCT_FACT_RE.search(agent) and not VALUE_FRAME_RE.search(agent):
        sales_failures.append("weak_value_frame_after_price")
    if price_question and PRODUCT_FACT_RE.search(agent) and not RECOMMENDATION_RE.search(agent):
        sales_failures.append("information_dump_without_momentum")
    if competitor and COMPETITOR_CAVEAT_RE.search(agent) and not re.search(r"gap|weakest|does not|current tool", agent, re.I):
        sales_failures.append("passive_competitor_handling")
    if COMPETITOR_CAVEAT_RE.search(agent) and turn_index > 4:
        sales_failures.append("repeated_safety_caveat")
    if DIRECT_BUYING_RE.search(customer) and not re.search(r"plus.*pro|pro.*plus|free.*paid|business.*enterprise|current tool", agent, re.I):
        sales_failures.append("no_decision_frame")
    if enough_context and not re.search(r"based on|given|since|you said|for coding|for writing|heavy", agent, re.I):
        sales_failures.append("no_summary_of_known_buyer_context")
    if enough_context and not re.search(r"choose|lower-cost|safer|matters more|if price|if avoiding", agent, re.I):
        sales_failures.append("weak_choice_close")
    if competitor and not re.search(r"gap|current tool|current setup|does not|weakest", agent, re.I):
        sales_failures.append("weak_objection_reframe")
    if no_fit and re.search(r"official chatgpt plans page|choose pro|compare pro first", agent, re.I):
        sales_failures.append("no_fit_not_handled_cleanly")

    if INTERNAL_POLICY_RE.search(agent) or RAW_URL_RE.search(agent) or FAKE_SIDE_EFFECT_RE.search(agent):
        category = "campaign_adapter_sales_defect"
    elif PIPELINE_RE.search(combined) and not agent:
        category = "live_pipeline_defect"
    elif sales_failures:
        category = "universal_sales_skill_defect"
    elif DIRECT_BUYING_RE.search(customer) and not PRODUCT_FACT_RE.search(agent):
        category = "campaign_product_fact_defect"

    return category, sorted(set(sales_failures))


def private_turn_findings() -> list[dict[str, Any]]:
    payload = load_json(LATEST_TRANSCRIPT)
    if not isinstance(payload, dict):
        return [
            {
                "source": rel(LATEST_TRANSCRIPT),
                "category": "live_pipeline_defect",
                "sales_skill_failure_classes": [],
                "sanitized_buyer_signal_labels": ["latest_private_transcript_unreadable"],
            }
        ]
    turns = payload.get("turns") if isinstance(payload.get("turns"), list) else []
    findings: list[dict[str, Any]] = []
    for turn in turns:
        if not isinstance(turn, dict):
            continue
        customer = str(turn.get("customer_transcript") or "")
        agent = str(turn.get("agent_response") or "")
        category, sales_failures = classify_turn(customer, agent, turn_index=int(turn.get("turn_index") or len(findings) + 1))
        if category == "no_defect" and not sales_failures:
            continue
        findings.append(
            {
                "source": rel(LATEST_TRANSCRIPT),
                "turn_index": turn.get("turn_index"),
                "category": category,
                "sales_skill_failure_classes": sales_failures,
                "sanitized_buyer_signal_labels": sanitized_labels(customer),
                "customer_transcript_hash": sha12(customer),
                "agent_response_hash": sha12(agent),
                "raw_private_transcript_copied": False,
            }
        )
    return findings


def generated_evidence_findings() -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in EVIDENCE_FILES:
        payload = load_json(path)
        if not isinstance(payload, dict):
            continue
        failed_cases = payload.get("failed_cases") if isinstance(payload.get("failed_cases"), list) else []
        for case in failed_cases[:40]:
            if not isinstance(case, dict):
                continue
            failures = [str(item) for item in case.get("failures") or []]
            classes: set[str] = set()
            text = " ".join(failures).lower()
            if "no recommendation" in text or "generic discovery" in text:
                classes.add("missed_recommendation_after_context")
            if "close" in text or "next step" in text:
                classes.add("missed_close_after_buying_signal")
            if "value frame" in text:
                classes.add("weak_value_frame_after_price")
            if "competitor caveat" in text:
                classes.add("passive_competitor_handling")
            if "decision frame" in text or "plus vs pro" in text:
                classes.add("no_decision_frame")
            if "loop" in text or "repeated" in text:
                classes.add("over_qualification_after_enough_context")
            category = "validator_gap" if payload.get("status") == "pass" and failures else "universal_sales_skill_defect"
            if classes:
                findings.append(
                    {
                        "source": rel(path),
                        "case_id": case.get("id") or case.get("case_id"),
                        "category": category,
                        "sales_skill_failure_classes": sorted(classes),
                        "final_response_hash": case.get("final_response_hash") or sha12(str(case.get("final_response") or "")),
                        "raw_private_transcript_copied": False,
                    }
                )
    return findings


def fixture_summary() -> dict[str, Any]:
    fixture = load_json(FIXTURE_PATH)
    if not isinstance(fixture, dict):
        return {"available": False}
    return {
        "available": True,
        "campaign_id": fixture.get("campaign_id"),
        "source_policy": fixture.get("source_policy"),
        "objective": fixture.get("objective"),
        "can_send_email": fixture.get("can_send_email"),
        "should_speak_raw_url": fixture.get("should_speak_raw_url"),
        "product_fact_count": len(fixture.get("source_grounded_claims") or []),
    }


def write_evidence(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = "\n".join(
        [
            f"# {CHECKPOINT_ID}",
            "",
            f"- Status: `{result['status']}`",
            f"- Private findings: `{result['private_finding_count']}`",
            f"- Generated evidence findings: `{result['generated_evidence_finding_count']}`",
            f"- Raw private transcript copied: `{str(result['raw_private_transcript_copied_to_public_evidence']).lower()}`",
            f"- Side effects false: `{str(result['side_effects_false']).lower()}`",
            "",
            "## Category Counts",
            "",
            "```json",
            json.dumps(result["category_counts"], indent=2, sort_keys=True),
            "```",
            "",
            "## Sales Skill Failure Counts",
            "",
            "```json",
            json.dumps(result["sales_skill_failure_class_counts"], indent=2, sort_keys=True),
            "```",
            "",
            "## Sanitized Findings",
            "",
            "```json",
            json.dumps(result["findings"][:25], indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    private = private_turn_findings()
    generated = generated_evidence_findings()
    findings = private + generated
    category_counts = Counter(str(item.get("category")) for item in findings)
    class_counts = Counter(
        skill_class
        for item in findings
        for skill_class in item.get("sales_skill_failure_classes", [])
    )
    missing_expected_classes = sorted(REQUIRED_SKILL_FAILURE_CLASSES - set(class_counts))
    result = {
        "status": "pass",
        "checkpoint_id": CHECKPOINT_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "latest_private_transcript_source": rel(LATEST_TRANSCRIPT),
        "fixture": fixture_summary(),
        "private_finding_count": len(private),
        "generated_evidence_finding_count": len(generated),
        "finding_count": len(findings),
        "category_counts": dict(sorted(category_counts.items())),
        "sales_skill_failure_class_counts": dict(sorted(class_counts.items())),
        "required_sales_skill_failure_classes": sorted(REQUIRED_SKILL_FAILURE_CLASSES),
        "missing_expected_sales_skill_failure_classes_in_current_evidence": missing_expected_classes,
        "findings": findings,
        "raw_private_transcript_copied_to_public_evidence": False,
        "side_effects_false": True,
        "provider_calls_made": False,
        "live_tts_calls_made": False,
        "local_llm_calls_made": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
    }
    write_evidence(result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "finding_count": result["finding_count"],
                "private_finding_count": result["private_finding_count"],
                "generated_evidence_finding_count": result["generated_evidence_finding_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
