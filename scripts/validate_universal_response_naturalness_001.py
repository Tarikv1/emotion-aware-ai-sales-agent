"""Validate naturalness of universal response-shape outputs.

This checkpoint reuses the 4E2E enforced-response matrix and adds customer
speech quality checks. It runs dry-run turn builders only and makes no provider,
live TTS, email, calendar, CRM, or PROD-102 calls.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import validate_universal_response_shape_enforcement_001 as shape_validator  # noqa: E402


CHECKPOINT_ID = "UNIVERSAL-RESPONSE-NATURALNESS-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

MECHANICAL_PATTERNS = {
    "the purpose of": "mechanical purpose phrasing",
    "you should care only if": "mechanical why-care phrasing",
    "useful difference i can state": "defensive differentiation phrasing",
    "one issue": "robotic one-issue phrasing",
    "should i stop here": "repeated stop prompt",
    "should i stop": "weak stop prompt",
    "should i check that": "robotic check-that prompt",
    "should i check one narrow gap": "raw gap prompt",
    "should i keep this to one relevance check": "policy-like relevance prompt",
    "for a operations": "wrong article before operations",
    "review review": "duplicated review wording",
    "follow-up gap": "awkward gap wording",
    "can discuss workflow fit at a general level": "raw allowed-claim wording",
    "approved scope here": "policy-like approved-scope wording",
    "i will not invent proof": "defensive proof wording",
    "around vehicle issue": "missing article before vehicle issue",
    "around service need": "missing article before service need",
    "issue causing any issue": "duplicated issue wording",
    "need causing any issue": "awkward service-need wording",
}

INTERNAL_OR_POLICY_PATTERNS = {
    "approved qualified reviewer path": "internal policy wording",
    "internal policy": "internal policy wording",
    "i am asking whether": "fallback diagnostic menu",
    "as an ai language model": "implementation disclosure wording",
}

UNSAFE_CLAIM_PATTERNS = {
    "we guarantee": "invented guarantee",
    "i guarantee": "invented guarantee",
    "can guarantee": "invented guarantee",
    "guaranteed result": "invented guarantee",
    "promise the result": "invented result promise",
    "promise coverage": "invented coverage promise",
    "exact price is": "invented exact price",
    "exact quote is": "invented exact quote",
    "covered for sure": "invented coverage claim",
    "roi guarantee": "invented ROI guarantee",
    "revenue guarantee": "invented revenue guarantee",
    "security guarantee": "invented security guarantee",
    "refund guarantee": "invented refund guarantee",
}

FULL_MENU_PATTERNS = {
    "which part is least clear": "menu prompt",
    "which part is more familiar": "menu prompt",
    "which part should i check first": "menu prompt",
    "name the point": "menu prompt",
}

FULL_MENU_SCOPE_PATTERNS = {
    "owner, callback reminder, or handoff": "full RouteSignal menu",
    "assignment, reminders, or missed replies": "full RouteSignal menu",
    "premium, coverage fit, or renewal": "full insurance menu",
    "premium or budget, coverage fit, or renewal": "full insurance menu",
    "manual work, integration, or visibility": "full B2B SaaS menu",
    "vehicle issue, repair timing, or warranty": "full automotive menu",
    "service need, scheduling, or estimate": "full home services menu",
}

SNAKE_CASE = re.compile(r"\b[a-z]+_[a-z_]+\b")
MENU_PROMPT_TERMS = ("which part", "what part", "name the point", "check first", "choose", "pick")


def lower(value: Any) -> str:
    return str(value or "").lower()


def has_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(pattern in text for pattern in patterns)


def quality_failures(row: dict[str, Any]) -> list[dict[str, str]]:
    response = str(row.get("final_response") or "")
    lowered = response.lower()
    failures: list[dict[str, str]] = []

    for pattern, reason in MECHANICAL_PATTERNS.items():
        if pattern in lowered:
            failures.append({"type": "mechanical_wording", "detail": reason})
    for pattern, reason in INTERNAL_OR_POLICY_PATTERNS.items():
        if pattern in lowered:
            failures.append({"type": "internal_wording", "detail": reason})
    for pattern, reason in UNSAFE_CLAIM_PATTERNS.items():
        if pattern in lowered:
            failures.append({"type": "unsafe_claim", "detail": reason})
    for pattern, reason in FULL_MENU_PATTERNS.items():
        if pattern in lowered:
            failures.append({"type": "full_diagnostic_menu", "detail": reason})
    if has_any(lowered, tuple(FULL_MENU_SCOPE_PATTERNS)) and has_any(lowered, MENU_PROMPT_TERMS):
        failures.append({"type": "full_diagnostic_menu", "detail": "scope list used as menu prompt"})

    snake_hits = sorted(set(SNAKE_CASE.findall(lowered)))
    if snake_hits:
        failures.append({"type": "raw_snake_case", "detail": ", ".join(snake_hits)})
    if response.count("?") > 1:
        failures.append({"type": "too_many_questions", "detail": "more than one question mark"})
    if not row.get("response_shape_enforcement_enabled"):
        failures.append({"type": "missing_enforcement", "detail": "response-shape enforcement not active"})
    if str(row.get("call_control") or "") != "continue-call":
        failures.append({"type": "wrong_call_control", "detail": str(row.get("call_control") or "")})

    category = str(row.get("category") or "")
    transcript = lower(row.get("transcript"))
    if category == "permission_time_pressure":
        if "one quick check" not in lowered:
            failures.append({"type": "time_pressure_not_concise", "detail": "missing one quick check shape"})
        if len(response.split()) > 28:
            failures.append({"type": "time_pressure_too_long", "detail": f"{len(response.split())} words"})
    if category == "direct_product_value_questions":
        if transcript == "what does your product do" and not has_any(
            lowered,
            (
                "crm workflow tool",
                "quick",
                "fit check",
                "helps teams",
                "checking whether",
                "high-level scope",
            ),
        ):
            failures.append({"type": "direct_answer_weak", "detail": "product-detail answer not direct"})
        if transcript == "what problem do you solve" and not has_any(
            lowered,
            (
                "helps",
                "value",
                "point is",
                "checking whether",
                "avoid",
                "worth",
                "fit check",
            ),
        ):
            failures.append({"type": "direct_answer_weak", "detail": "problem-solved answer not direct"})
        if transcript == "why should i care" and not has_any(
            lowered,
            (
                "value is",
                "avoid",
                "worth",
                "fewer missed",
                "point is",
                "useful",
                "bad-fit",
            ),
        ):
            failures.append({"type": "direct_answer_weak", "detail": "why-care answer not direct"})
        if transcript == "what makes you different" and not has_any(
            lowered,
            (
                "cannot compare exact",
                "clearer ownership",
                "would compare",
                "before any recommendation",
                "difference is the scope",
                "value is",
                "limited scope",
            ),
        ):
            failures.append({"type": "direct_answer_weak", "detail": "differentiation answer not bounded"})
    if category == "objections":
        if not any(token in lowered for token in ("understood", "fair", "no problem")):
            failures.append({"type": "objection_acknowledgement_missing", "detail": "objection not acknowledged"})
        if "should i" in lowered:
            failures.append({"type": "objection_next_action_weak", "detail": "objection used should-I prompt"})

    return failures


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    failures = [row for row in results if row["naturalness_failures"]]
    by_category: dict[str, dict[str, int]] = defaultdict(lambda: {"passed": 0, "failed": 0})
    failure_types: Counter[str] = Counter()
    for row in results:
        bucket = by_category[str(row["category"])]
        if row["naturalness_failures"]:
            bucket["failed"] += 1
        else:
            bucket["passed"] += 1
        for failure in row["naturalness_failures"]:
            failure_types[failure["type"]] += 1
    return {
        "matrix_size": len(results),
        "pass_count": len(results) - len(failures),
        "failure_count": len(failures),
        "by_category": dict(sorted(by_category.items())),
        "failure_types": dict(failure_types.most_common()),
        "failure_examples": failures[:20],
    }


def write_evidence(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    summary = result["summary"]
    report = [
        f"# {CHECKPOINT_ID}",
        "",
        "## Summary",
        f"Status: {result['status']}",
        f"Matrix size: {summary['matrix_size']}",
        f"Pass/fail: {summary['pass_count']} / {summary['failure_count']}",
        "",
        "## Results By Category",
    ]
    for category, counts in summary["by_category"].items():
        report.append(f"- {category}: pass={counts['passed']} fail={counts['failed']}")
    report.extend(["", "## Failure Types"])
    for failure_type, count in summary["failure_types"].items():
        report.append(f"- {failure_type}: {count}")
    report.extend(["", "## Failure Examples"])
    for row in summary["failure_examples"][:12]:
        report.append(
            f"- {row['campaign']} | {row['category']} | {row['transcript']} | "
            f"failures={row['naturalness_failures']} | response={row['final_response']!r}"
        )
    report.extend(
        [
            "",
            "## Side-Effect Boundary",
            f"provider_calls_made: {result['side_effects'].get('provider_calls_made', False)}",
            f"local_llm_calls_made: {result['side_effects'].get('local_llm_calls_made', False)}",
            f"sends_email: {result['side_effects'].get('sends_email', False)}",
            f"creates_calendar_event: {result['side_effects'].get('creates_calendar_event', False)}",
            f"writes_crm: {result['side_effects'].get('writes_crm', False)}",
            f"opens_prod_102: {result['side_effects'].get('opens_prod_102', False)}",
        ]
    )
    (OUT_DIR / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> int:
    rows = shape_validator.run_target_matrix()
    for row in rows:
        row["naturalness_failures"] = quality_failures(row)
        row["naturalness_passed"] = not row["naturalness_failures"]

    side_effects: dict[str, bool] = {}
    for row in rows:
        for flag, active in (row.get("side_effect_flags") or {}).items():
            side_effects[flag] = bool(side_effects.get(flag) or active)

    summary = summarize(rows)
    status = "pass" if summary["failure_count"] == 0 and not any(side_effects.values()) else "fail"
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": status,
        "summary": summary,
        "results": rows,
        "side_effects": side_effects,
    }
    write_evidence(result)
    print(json.dumps({k: result[k] for k in ["checkpoint_id", "status", "summary", "side_effects"]}, indent=2, sort_keys=True))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
