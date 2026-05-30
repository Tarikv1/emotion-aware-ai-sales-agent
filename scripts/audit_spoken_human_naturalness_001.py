from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXPERIMENT_ID = "SPOKEN-HUMAN-NATURALNESS-AUDIT-001"
EXPANSION_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-EXPANSION-001"
GENERATED = ROOT / "research" / "experiments" / "generated"
OUT_DIR = GENERATED / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
EXPANSION_RESULT_PATH = GENERATED / EXPANSION_ID / "result.json"
DECISION_REPORT_PATH = GENERATED / EXPANSION_ID / "decision_report.md"
RECOMMENDATION_ID = "limited_offline_sanitized_shadow_logging_and_spoken_naturalness_review_next"

CATEGORY_IDS = [
    "robotic_internal_wording",
    "overly_formal_or_policy_like",
    "empty_candidate_response",
    "missing_human_acknowledgment",
    "missing_sales_progression",
    "premature_scheduling_or_callback_push",
    "weak_value_framing",
    "repetitive_review_language",
    "too_long_for_spoken_call",
    "good_human_spoken_examples",
]

ROBOTIC_PATTERNS = [
    r"\bi should still tie that\b",
    r"\bi can only check whether\b",
    r"\bi can only check\b",
    r"\bthe useful next step\b",
    r"\bcampaign relevance\b",
    r"\bscope\b",
    r"\bsemantic\b",
    r"\bdiagnostic gap\b",
    r"\bpolicy boundary\b",
    r"\bmetadata\b",
    r"\bcandidate response\b",
    r"\bi should not route\b",
    r"\bruntime\b",
    r"\bselector\b",
    r"^\s*do you have a minute for one quick question\b",
]

FORMAL_POLICY_PATTERNS = [
    r"\bas an ai\b",
    r"\bai assistant\b",
    r"\bi am unable to\b",
    r"\bi cannot assist\b",
    r"\bi do not have the ability\b",
    r"\bi understand your concern\b",
    r"\bi cannot verify that claim here\b",
    r"\bbefore i claim it\b",
    r"\bexact setup fit needs verified material\b",
    r"\bcheck the plan page before upgrading\b",
    r"\bcannot give detailed\b",
    r"\bcompliance\b",
    r"\bregulated\b",
    r"\bpolicy boundary\b",
    r"\bunsupported claim\b",
    r"\bclaim boundary\b",
    r"\bapproved pricing\b",
    r"\bverified details\b",
]

REVIEW_PATTERNS = [
    r"\bqualified human\b",
    r"\bhuman review\b",
    r"\bsafe review\b",
    r"\breview by a specialist before any recommendation\b",
]

ACK_PATTERN = re.compile(
    r"^\s*(got it|understood|sure|yes|no|right|fair|thanks|correct|that makes sense|you're right|you are right|okay|ok)\b",
    re.I,
)

PROGRESSION_PATTERN = re.compile(
    r"\b(next step|worth|useful|fit|need|issue|problem|causing|helps|fix|specialist|plan|coverage|premium|workflow|manual|integration|recommend|what|which|why|how|is .+\?)\b",
    re.I,
)

SCHEDULING_PATTERN = re.compile(
    r"\b(callback|call back|email|schedule|appointment|what time|time should|when works|book|tomorrow at)\b",
    re.I,
)
STRONG_VALUE_PATTERN = re.compile(
    r"\b(issue|problem|slowing|pain|risk|worth|fix|helps|save|reduce|coverage|premium|plan fit|workflow|manual work|integration|value)\b",
    re.I,
)
SHORT_REVIEW_NEXT_STEP_PATTERN = re.compile(r"\bthe next step is a short workflow review\b", re.I)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def sentence_split(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", str(text or "").strip()) if part.strip()]


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", text))


def response_excerpt(text: str, limit: int = 220) -> str:
    cleaned = " ".join(str(text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def normalize(text: str) -> str:
    return " ".join(str(text or "").casefold().split())


def category_bucket() -> dict[str, Any]:
    return {"count": 0, "examples": []}


def add_issue(categories: dict[str, dict[str, Any]], category: str, case: dict[str, Any], reason: str, excerpt: str | None = None) -> None:
    payload = categories[category]
    payload["count"] += 1
    if len(payload["examples"]) >= 8:
        return
    payload["examples"].append(
        {
            "case_id": case["case_id"],
            "campaign_coverage": case["campaign_coverage"],
            "campaign_id": case["campaign_id"],
            "vertical_id": case["vertical_id"],
            "reason": reason,
            "excerpt": response_excerpt(excerpt if excerpt is not None else case.get("candidate_response") or ""),
        }
    )


def match_any(patterns: list[str], text: str) -> str:
    for pattern in patterns:
        if re.search(pattern, text, flags=re.I):
            return pattern
    return ""


def audit_cases(cases: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    categories: dict[str, dict[str, Any]] = {category: category_bucket() for category in CATEGORY_IDS}
    for case in cases:
        response = str(case.get("candidate_response") or "")
        issue_count_before = total_issue_count(categories)
        if not response.strip():
            add_issue(categories, "empty_candidate_response", case, "empty candidate response")
            add_issue(categories, "missing_sales_progression", case, "empty candidate response")
            add_issue(categories, "missing_human_acknowledgment", case, "empty candidate response")
            add_issue(categories, "weak_value_framing", case, "empty candidate response")
            continue

        robotic = match_any(ROBOTIC_PATTERNS, response)
        if robotic:
            add_issue(categories, "robotic_internal_wording", case, f"matched {robotic}")

        formal = match_any(FORMAL_POLICY_PATTERNS, response)
        if formal:
            add_issue(categories, "overly_formal_or_policy_like", case, f"matched {formal}")

        review_phrase = match_any(REVIEW_PATTERNS, response)
        review_count = len(re.findall(r"\breview\b", response, flags=re.I))
        if review_phrase:
            add_issue(categories, "repetitive_review_language", case, f"matched {review_phrase}")
        elif review_count > 1:
            add_issue(categories, "repetitive_review_language", case, f"review repeated {review_count} times")

        for sentence in sentence_split(response):
            if word_count(sentence) > 28:
                add_issue(
                    categories,
                    "too_long_for_spoken_call",
                    case,
                    f"sentence has {word_count(sentence)} words",
                    sentence,
                )

        sequence_index = int(case.get("sequence_index") or 0)
        weak_value = STRONG_VALUE_PATTERN.search(response) is None
        if SHORT_REVIEW_NEXT_STEP_PATTERN.search(response) and weak_value:
            add_issue(
                categories,
                "weak_value_framing",
                case,
                "short workflow review appears before strong value framing",
            )
        if SCHEDULING_PATTERN.search(response) and (sequence_index <= 2 or weak_value):
            add_issue(
                categories,
                "premature_scheduling_or_callback_push",
                case,
                "scheduling or callback language appears before enough value framing",
            )

        if not PROGRESSION_PATTERN.search(response):
            add_issue(categories, "missing_sales_progression", case, "no clear fit, value, or next-step progression")

        if not ACK_PATTERN.search(response):
            add_issue(categories, "missing_human_acknowledgment", case, "response lacks a compact human-style acknowledgment")

        if weak_value:
            add_issue(categories, "weak_value_framing", case, "no strong buyer-value frame before the response move")

        if total_issue_count(categories) == issue_count_before:
            add_issue(categories, "good_human_spoken_examples", case, "compact acknowledgment plus sales progression")
    return categories


def total_issue_count(categories: dict[str, dict[str, Any]]) -> int:
    return sum(
        int(payload.get("count") or 0)
        for category, payload in categories.items()
        if category != "good_human_spoken_examples"
    )


def build_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Cases inspected: {result['case_count']}",
        f"- Naturalness issue count: {result['naturalness_issue_count']}",
        "- Private live transcripts inspected: false",
        "- Provider/model/local LLM/TTS/CRM/email/calendar/audio calls: false",
        "- Automatic runtime rewrite performed: false",
        f"- Recommendation: {result['recommendation_id']}",
        "",
        "## Categories",
        "",
    ]
    for category, payload in result["categories"].items():
        lines.append(f"### {category}")
        lines.append("")
        lines.append(f"- Count: {payload['count']}")
        for example in payload["examples"][:5]:
            excerpt = str(example.get("excerpt") or "").strip()
            suffix = f" | {excerpt}" if excerpt else ""
            lines.append(f"- {example['case_id']} ({example['campaign_coverage']}): {example['reason']}{suffix}")
        lines.append("")
    return "\n".join(lines)


def examples_for(result: dict[str, Any], category: str, limit: int = 4) -> list[dict[str, Any]]:
    payload = (result.get("categories") or {}).get(category) or {}
    return list(payload.get("examples") or [])[:limit]


def build_decision_report(expansion: dict[str, Any], naturalness: dict[str, Any]) -> str:
    disagreements = expansion.get("disagreement_by_campaign") or {}
    disagreement_lines: list[str] = []
    for campaign, counts in sorted(disagreements.items()):
        problem_counts = {key: value for key, value in counts.items() if key != "same_action" and int(value or 0) > 0}
        if problem_counts:
            summary = ", ".join(f"{key}={value}" for key, value in sorted(problem_counts.items()))
            disagreement_lines.append(f"- {campaign}: {summary}")
    if not disagreement_lines:
        disagreement_lines.append("- None recorded.")

    robotic = (
        examples_for(naturalness, "robotic_internal_wording")
        + examples_for(naturalness, "overly_formal_or_policy_like")
        + examples_for(naturalness, "repetitive_review_language")
    )
    scheduling = examples_for(naturalness, "premature_scheduling_or_callback_push")

    lines = [
        f"# {EXPANSION_ID} Decision Report",
        "",
        "## Is the shadow selector still safe offline?",
        "",
        (
            f"Yes, within the offline/sanitized boundary: expansion_status={expansion.get('status')}, "
            f"safety_blockers_count={expansion.get('safety_blockers_count')}, provider calls=false, local LLM calls=false, "
            "response replacement=false, live selector control=false."
        ),
        "",
        "## Which campaigns show selector/runtime disagreement?",
        "",
        *disagreement_lines,
        "",
        "## Which spoken responses sound robotic?",
        "",
    ]
    if robotic:
        for example in robotic[:6]:
            lines.append(
                f"- {example['case_id']} ({example['campaign_coverage']}): {example['reason']} | {example['excerpt']}"
            )
    else:
        lines.append("- No robotic/internal wording examples were flagged.")
    lines.extend(
        [
            "",
            "## Which responses risk turning the sales agent into a scheduling bot?",
            "",
        ]
    )
    if scheduling:
        for example in scheduling:
            lines.append(
                f"- {example['case_id']} ({example['campaign_coverage']}): {example['reason']} | {example['excerpt']}"
            )
    else:
        lines.append("- No scheduling-bot drift examples were flagged.")
    lines.extend(
        [
            "",
            "## What should be fixed before any live selector control?",
            "",
            "- Replace robotic/internal wording with short spoken phrasing in runtime-owned response renderers.",
            "- Resolve selector/runtime disagreement by campaign before using selector output for behavior.",
            "- Keep safety boundaries natural, but remove policy, metadata, semantic, and scope language from buyer-facing speech.",
            "- Keep progression toward qualification, objection handling, and close criteria; do not reduce the agent to booking a callback.",
            "",
            "## Does the system remain aligned with the final goal: autonomous emotion-aware sales closing?",
            "",
            (
                "Partially. The phase is aligned as evidence infrastructure for autonomous emotion-aware sales closing, "
                "but the naturalness findings show the current spoken layer still needs sales-quality repair before live control."
            ),
            "",
            f"Recommendation: {RECOMMENDATION_ID}",
            "",
            "Do not enable live selector control.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    from scripts.run_non_llm_action_selector_runtime_shadow_expansion_001 import build_safe_fixture_cases

    cases = build_safe_fixture_cases()
    categories = audit_cases(cases)
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "case_count": len(cases),
        "naturalness_issue_count": total_issue_count(categories),
        "categories": categories,
        "private_live_transcripts_inspected": False,
        "provider_calls_made": False,
        "model_calls_made": False,
        "openai_api_calls_made": False,
        "ultravox_calls_made": False,
        "elevenlabs_calls_made": False,
        "local_llm_calls_made": False,
        "ollama_calls_made": False,
        "tts_calls_made": False,
        "crm_calls_made": False,
        "email_calls_made": False,
        "calendar_calls_made": False,
        "audio_data_used": False,
        "automatic_runtime_rewrite_performed": False,
        "runtime_response_replacement_performed": False,
        "live_selector_control_recommended": False,
        "recommendation_id": RECOMMENDATION_ID,
    }
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    expansion = read_json(EXPANSION_RESULT_PATH)
    if expansion:
        write_text(DECISION_REPORT_PATH, build_decision_report(expansion, result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "case_count": result["case_count"],
                "naturalness_issue_count": result["naturalness_issue_count"],
                "recommendation_id": result["recommendation_id"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
