#!/usr/bin/env python3
from __future__ import annotations

import ast
from collections import Counter
import json
import os
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import validate_phase_4l2_openai_primary_universal_sales_eval_001 as phase4l2  # noqa: E402
from scripts import validate_phase_4l3_openai_spoken_sales_quality_multiturn_001 as phase4l3  # noqa: E402
from runtime.campaigns import public_openai_chatgpt_plans_dialogue as dialogue  # noqa: E402


CHECKPOINT_ID = "PHASE-4L4-OPENAI-SOURCE-REFRESH-PLAN-TAXONOMY-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

OFFICIAL_SOURCE_ACCESS_STATUS = "succeeded"
OFFICIAL_SOURCES_INSPECTED = [
    {
        "url": "https://chatgpt.com/pricing/",
        "source_type": "official_pricing_page",
        "use": "current plan names, plan grouping, Go placement, Business/Enterprise route, pricing/terms caveat",
    },
    {
        "url": "https://help.openai.com/en/articles/11989085-what-is-chatgpt-go",
        "source_type": "official_help_article",
        "use": "Go positioning, Go features, signup/profile route, pricing-change caveat",
    },
]
CAPTURED_PLAN_TAXONOMY = {
    "individual": ["Free", "Go", "Plus", "Pro"],
    "business_enterprise": ["Business", "Enterprise"],
}
CHANGED_SOURCE_FILES = [
    "runtime/campaigns/public_openai_chatgpt_plans_dialogue.py",
    "runtime/campaigns/examples/public-openai-chatgpt-plans.json",
    "research/sources/public_openai_chatgpt_plans/source_manifest.json",
    "research/sources/public_openai_chatgpt_plans/source_notes.md",
    "scripts/validate_phase_4l2_openai_primary_universal_sales_eval_001.py",
    "scripts/validate_phase_4l3_openai_spoken_sales_quality_multiturn_001.py",
    "scripts/validate_phase_4l4_openai_source_refresh_plan_taxonomy_001.py",
    "research/experiments/generated/PHASE-4L2-OPENAI-PRIMARY-UNIVERSAL-SALES-EVAL-001/result.json",
    "research/experiments/generated/PHASE-4L2-OPENAI-PRIMARY-UNIVERSAL-SALES-EVAL-001/report.md",
    "research/experiments/generated/PHASE-4L3-OPENAI-SPOKEN-SALES-QUALITY-MULTITURN-001/result.json",
    "research/experiments/generated/PHASE-4L3-OPENAI-SPOKEN-SALES-QUALITY-MULTITURN-001/report.md",
    "research/experiments/generated/PHASE-4L4-OPENAI-SOURCE-REFRESH-PLAN-TAXONOMY-001/result.json",
    "research/experiments/generated/PHASE-4L4-OPENAI-SOURCE-REFRESH-PLAN-TAXONOMY-001/report.md",
]
STALE_ASSUMPTIONS_FOUND_FIXED = [
    "PLAN_LABELS omitted Go.",
    "The main individual plan category response skipped Go.",
    "Several spoken responses treated Plus as the first paid individual step.",
    "The price/terms response answered Plus/Pro while claiming current paid-plan coverage.",
    "The 4L2/4L3 matrices did not exercise Go-specific plan-fit, price, or team-boundary cases.",
]
FALSE_FLAGS = phase4l2.FALSE_FLAGS
FORBIDDEN_IMPORT_ROOTS = {"elevenlabs", "httpx", "openai", "requests", "ultravox", "urllib"}
SHADOW_ENV_GATES = phase4l2.SHADOW_ENV_GATES
STALE_DIALOGUE_PHRASES = [
    "Free, Plus, and Pro are individual plan labels",
    "Plus is the lower-cost paid individual plan",
    "Plus is the lower-cost first paid plan",
    "Plus is usually the first paid plan",
    "Plus is the safer first paid plan",
    "Free, Plus, Pro, Business, or Enterprise",
    "Free, Plus, Pro, Business, and Enterprise",
]
GO_CASES: list[dict[str, Any]] = [
    {
        "case_id": "plan_category_includes_go",
        "turns": ["Can you explain Free, Go, Plus, Pro, Business, and Enterprise in plain English?"],
        "expected_behavior": "Explain all current plan names and separate individual from Business/Enterprise routes.",
        "must_include_all": ["free", "go", "plus", "pro", "business", "enterprise"],
        "must_include_any": [
            ["individual", "personal"],
            ["team", "workspace", "business"],
            ["enterprise", "security", "procurement", "admin", "contact sales"],
        ],
        "must_have_question_or_close": True,
    },
    {
        "case_id": "what_is_go",
        "turns": ["What is Go?"],
        "expected_behavior": "Answer that Go is a lower-cost paid individual step with expanded access beyond Free.",
        "must_include_all": ["go", "free"],
        "must_include_any": [["lower-cost", "paid"], ["expanded", "more access", "popular features"]],
        "must_not_include": ["team workspace route", "enterprise route"],
    },
    {
        "case_id": "light_user_free_or_go",
        "turns": ["I use ChatGPT lightly for personal tasks; is Free or Go enough?"],
        "expected_behavior": "Avoid pushing Plus/Pro and frame Free or Go as enough for light individual use.",
        "must_include_all": ["free", "go"],
        "must_include_any": [["enough", "may be enough"], ["light", "basic", "personal"]],
        "must_not_include": ["you need pro", "upgrade to pro", "business"],
    },
    {
        "case_id": "lower_cost_paid_before_plus",
        "turns": ["I want a lower-cost paid option before Plus or Pro. What should I compare?"],
        "expected_behavior": "Name Go as the lower-cost paid step before Plus/Pro, with official-page caveat.",
        "must_include_all": ["go", "plus", "pro"],
        "must_include_any": [["lower-cost", "before plus", "between free and plus"], ["official", "current terms", "plan page"]],
    },
    {
        "case_id": "go_plus_pro_fit",
        "turns": ["How do I decide between Go, Plus, and Pro?"],
        "expected_behavior": "Frame Go/Plus/Pro as individual paid steps with increasing access and usage headroom.",
        "must_include_all": ["go", "plus", "pro"],
        "must_include_any": [["individual", "personal"], ["usage", "headroom", "limits"], ["lower-cost", "advanced", "heavier"]],
    },
    {
        "case_id": "go_cost_current_pricing",
        "turns": ["What does Go cost right now, and is that current?"],
        "expected_behavior": "Do not invent a Go price; route exact Go price and current terms to the official plan page.",
        "must_include_all": ["go"],
        "must_include_any": [["official chatgpt plans page", "official plan page", "pricing page"], ["current", "exact", "can change"]],
        "must_not_include": ["20 dollars", "100 dollar", "200 dollar", "$20", "$100", "$200"],
    },
    {
        "case_id": "business_enterprise_separate_from_individual",
        "turns": ["Are Business and Enterprise separate from Go, Plus, and Pro?"],
        "expected_behavior": "Separate Go/Plus/Pro individual plans from Business/Enterprise organization routes.",
        "must_include_all": ["go", "plus", "pro", "business", "enterprise"],
        "must_include_any": [["individual", "personal"], ["team", "business", "organization"], ["contact sales", "security", "procurement", "admin"]],
    },
    {
        "case_id": "go_is_not_team_plan",
        "turns": ["Is Go for teams?"],
        "expected_behavior": "Say Go is an individual plan, while Business/Enterprise cover team or organization needs.",
        "must_include_all": ["go", "business", "enterprise"],
        "must_include_any": [["individual", "personal"], ["team", "teams", "workspace", "organization"]],
        "must_not_include": ["go is for teams", "go is the team plan"],
    },
]


def normalize(value: str) -> str:
    return phase4l2.normalize(value)


def contains_any(text: str, needles: list[str]) -> bool:
    return phase4l2.contains_any(text, needles)


def contains_all(text: str, needles: list[str]) -> bool:
    return phase4l2.contains_all(text, needles)


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def evaluate_go_case(case: dict[str, Any]) -> dict[str, Any]:
    run = phase4l2.run_turn_sequence(list(case["turns"]))
    response = str(run.get("final_response") or "")
    frame = run.get("final_frame") if isinstance(run.get("final_frame"), dict) else {}
    failures: list[str] = []

    if not response.strip():
        failures.append("final response was empty")
    if not contains_all(response, list(case.get("must_include_all") or [])):
        failures.append("required response terms missing")
    for group in case.get("must_include_any") or []:
        if not contains_any(response, list(group)):
            failures.append(f"required any-term group missing: {group}")
    if contains_any(response, list(case.get("must_not_include") or [])):
        failures.append("forbidden response term present")
    if case.get("must_have_question_or_close") and "?" not in response and "official chatgpt plans page" not in normalize(response):
        failures.append("response did not ask a useful next question or close")
    if phase4l2.response_word_count(response) > 95:
        failures.append("response was too long for spoken sales use")
    if phase4l2.contamination_hits_in_text(response):
        failures.append("response contains RouteSignal contamination")

    return {
        "case_id": case["case_id"],
        "turns": list(case["turns"]),
        "buyer_utterance": case["turns"][-1],
        "expected_behavior": case["expected_behavior"],
        "actual_semantic_action_response_summary": {
            "semantic": str(frame.get("semantic") or ""),
            "dialogue_focus": str(frame.get("dialogue_focus") or ""),
            "action_id": str(frame.get("action_id") or "continue_with_session_policy"),
            "response_summary": response.split(".")[0].strip(),
        },
        "actual_response": response,
        "pass": not failures,
        "failures": failures,
    }


def source_taxonomy_passes() -> bool:
    plan_labels = {str(value) for value in getattr(dialogue, "PLAN_LABELS", {}).values()}
    expected = {"Free", "Go", "Plus", "Pro", "Business", "Enterprise"}
    return expected.issubset(plan_labels)


def stale_phrase_hits() -> list[dict[str, Any]]:
    paths = [
        ROOT / "runtime" / "campaigns" / "public_openai_chatgpt_plans_dialogue.py",
        ROOT / "scripts" / "validate_phase_4l2_openai_primary_universal_sales_eval_001.py",
        ROOT / "scripts" / "validate_phase_4l3_openai_spoken_sales_quality_multiturn_001.py",
    ]
    hits: list[dict[str, Any]] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for phrase in STALE_DIALOGUE_PHRASES:
                if phrase in line:
                    hits.append(
                        {
                            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                            "line": line_number,
                            "phrase": phrase,
                        }
                    )
    return hits


def route_signal_response_hits(go_cases: list[dict[str, Any]], phase4l3_result: dict[str, Any]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for item in go_cases:
        terms = phase4l2.contamination_hits_in_text(str(item.get("actual_response") or ""))
        if terms:
            hits.append({"matrix": "go_cases_4l4", "case_id": item["case_id"], "terms": terms})
    l3_hits = (
        phase4l3_result.get("routesignal_contamination_check", {})
        if isinstance(phase4l3_result.get("routesignal_contamination_check"), dict)
        else {}
    ).get("openai_primary_response_hits")
    if isinstance(l3_hits, list):
        hits.extend({"matrix": "phase4l3", **item} for item in l3_hits if isinstance(item, dict))
    return hits


def build_result() -> dict[str, Any]:
    go_cases = [evaluate_go_case(case) for case in GO_CASES]
    phase4l3_result = phase4l3.build_result()
    l3_regression_count = int(phase4l3_result.get("single_turn_4l2_regression_count") or 0)
    l3_multi_fail_count = int((phase4l3_result.get("multi_turn_pass_fail_count") or {}).get("fail") or 0)
    route_signal_hits = route_signal_response_hits(go_cases, phase4l3_result)
    stale_hits = stale_phrase_hits()
    go_failures = [item for item in go_cases if not item["pass"]]
    source_taxonomy_ok = source_taxonomy_passes()
    all_pass = (
        OFFICIAL_SOURCE_ACCESS_STATUS == "succeeded"
        and source_taxonomy_ok
        and not go_failures
        and l3_regression_count == 0
        and l3_multi_fail_count == 0
        and phase4l3_result.get("status") == "pass"
        and not route_signal_hits
        and not stale_hits
    )
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if all_pass else "fail",
        "primary_benchmark_campaign": "public OpenAI ChatGPT plans",
        "official_source_access_status": OFFICIAL_SOURCE_ACCESS_STATUS,
        "official_sources_inspected": OFFICIAL_SOURCES_INSPECTED,
        "captured_plan_taxonomy": CAPTURED_PLAN_TAXONOMY,
        "source_taxonomy_status": "pass" if source_taxonomy_ok else "fail",
        "changed_source_files": CHANGED_SOURCE_FILES,
        "stale_assumptions_found_fixed": STALE_ASSUMPTIONS_FOUND_FIXED,
        "stale_assumption_hits_remaining": stale_hits,
        "cases_added_or_updated": [case["case_id"] for case in GO_CASES],
        "go_specific_case_results": go_cases,
        "go_specific_pass_fail_count": {
            "pass": sum(1 for item in go_cases if item["pass"]),
            "fail": sum(1 for item in go_cases if not item["pass"]),
        },
        "phase4l3_regression_status": "pass"
        if phase4l3_result.get("status") == "pass" and l3_regression_count == 0 and l3_multi_fail_count == 0
        else "fail",
        "phase4l3_single_turn_4l2_regression_count": l3_regression_count,
        "phase4l3_multi_turn_fail_count": l3_multi_fail_count,
        "routesignal_contamination_count": len(route_signal_hits),
        "routesignal_contamination_hits": route_signal_hits,
        "no_side_effect_confirmation": {
            "selector_control_allowed": False,
            "response_replacement_performed": False,
            "provider_model_tts_crm_email_calendar_payment_account_side_effect_path_enabled": False,
            "raw_private_transcript_or_audio_added_to_public_evidence": False,
            "live_readiness_claimed": False,
        },
        "selector_response_replacement_status": "blocked",
        "no_live_readiness_confirmation": True,
        **{key: False for key in FALSE_FLAGS},
    }


def build_report(result: dict[str, Any]) -> str:
    counts = Counter("pass" if item["pass"] else "fail" for item in result["go_specific_case_results"])
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Official source access status: {result['official_source_access_status']}",
        "- Primary benchmark campaign: public OpenAI ChatGPT plans",
        f"- Captured individual taxonomy: {', '.join(result['captured_plan_taxonomy']['individual'])}",
        f"- Captured Business/Enterprise taxonomy: {', '.join(result['captured_plan_taxonomy']['business_enterprise'])}",
        f"- Go-specific case pass count: {counts['pass']}",
        f"- Go-specific case fail count: {counts['fail']}",
        f"- 4L3 regression status: {result['phase4l3_regression_status']}",
        f"- 4L3 single-turn regression count: {result['phase4l3_single_turn_4l2_regression_count']}",
        f"- 4L3 multi-turn fail count: {result['phase4l3_multi_turn_fail_count']}",
        f"- RouteSignal contamination count: {result['routesignal_contamination_count']}",
        "- Selector control remains blocked.",
        "- Response replacement remains blocked.",
        "- No provider/model/TTS/CRM/email/calendar/payment/account side-effect path was enabled.",
        "- No raw private transcript/audio was added to public evidence.",
        "- No live readiness claim was made.",
        "",
        "## Official Sources Inspected",
        "",
    ]
    for source in result["official_sources_inspected"]:
        lines.append(f"- {source['url']} ({source['source_type']}): {source['use']}")
    lines.extend(["", "## Stale Assumptions Found / Fixed", ""])
    for item in result["stale_assumptions_found_fixed"]:
        lines.append(f"- {item}")
    if result["stale_assumption_hits_remaining"]:
        lines.extend(["", "## Remaining Stale Phrase Hits", ""])
        for hit in result["stale_assumption_hits_remaining"]:
            lines.append(f"- {hit['path']}:{hit['line']} contains `{hit['phrase']}`")
    lines.extend(["", "## Go-Specific Case Matrix", ""])
    for item in result["go_specific_case_results"]:
        summary = item["actual_semantic_action_response_summary"]
        lines.extend(
            [
                f"### {item['case_id']}",
                "",
                f"- Buyer utterance: {item['buyer_utterance']}",
                f"- Expected behavior: {item['expected_behavior']}",
                f"- Actual semantic/action/response summary: semantic={summary['semantic']}; action={summary['action_id']}; focus={summary['dialogue_focus']}; summary={summary['response_summary']}",
                f"- Pass: {str(item['pass']).lower()}",
                f"- Failures: {json.dumps(item['failures'])}",
                f"- Actual response: {item['actual_response']}",
                "",
            ]
        )
    lines.extend(
        [
            "## No-side-effect Confirmation",
            "",
            "- Selector control blocked: true",
            "- Response replacement blocked: true",
            "- Side-effect provider paths enabled: false",
            "- Live readiness claimed: false",
        ]
    )
    return "\n".join(lines) + "\n"


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def validate_artifacts(failures: list[str], expected: dict[str, Any]) -> None:
    actual = read_json(RESULT_PATH)
    if not RESULT_PATH.is_file():
        failures.append("result.json missing")
        return
    if not REPORT_PATH.is_file():
        failures.append("report.md missing")
    if actual.get("checkpoint_id") != CHECKPOINT_ID:
        failures.append("checkpoint_id mismatch")
    if actual.get("status") not in {"pass", "source_refresh_blocked"}:
        failures.append(f"status must be pass or source_refresh_blocked, got {actual.get('status')!r}")
    for key in [
        "official_source_access_status",
        "official_sources_inspected",
        "captured_plan_taxonomy",
        "source_taxonomy_status",
        "stale_assumptions_found_fixed",
        "stale_assumption_hits_remaining",
        "cases_added_or_updated",
        "go_specific_case_results",
        "go_specific_pass_fail_count",
        "phase4l3_regression_status",
        "phase4l3_single_turn_4l2_regression_count",
        "phase4l3_multi_turn_fail_count",
        "routesignal_contamination_count",
        "selector_response_replacement_status",
    ]:
        if actual.get(key) != expected.get(key):
            failures.append(f"{key} mismatch")
    if actual.get("status") != expected["status"]:
        failures.append(f"status mismatch: {actual.get('status')!r} != {expected['status']!r}")
    if actual.get("status") == "pass":
        all_plans = set(actual.get("captured_plan_taxonomy", {}).get("individual", [])) | set(
            actual.get("captured_plan_taxonomy", {}).get("business_enterprise", [])
        )
        if not {"Free", "Go", "Plus", "Pro", "Business", "Enterprise"}.issubset(all_plans):
            failures.append("captured taxonomy missing required current plan names")
    if actual.get("routesignal_contamination_count") != 0:
        failures.append("RouteSignal contamination count must be 0")
    for key in FALSE_FLAGS:
        if actual.get(key) is not False:
            failures.append(f"{key} must be false: {actual.get(key)!r}")


def validate_report(failures: list[str]) -> None:
    if not REPORT_PATH.is_file():
        return
    text = REPORT_PATH.read_text(encoding="utf-8")
    required = [
        "Official source access status",
        "Official Sources Inspected",
        "Captured individual taxonomy",
        "Stale Assumptions Found / Fixed",
        "Go-Specific Case Matrix",
        "4L3 regression status",
        "RouteSignal contamination count",
        "Selector control remains blocked.",
        "Response replacement remains blocked.",
        "No provider/model/TTS/CRM/email/calendar/payment/account side-effect path was enabled.",
        "No live readiness claim was made.",
    ]
    for phrase in required:
        if phrase not in text:
            failures.append(f"report missing phrase: {phrase}")
    for case in GO_CASES:
        if case["case_id"] not in text:
            failures.append(f"report missing Go case id: {case['case_id']}")


def validate_environment_and_imports(failures: list[str]) -> None:
    forbidden = sorted(imported_roots(Path(__file__)) & FORBIDDEN_IMPORT_ROOTS)
    if forbidden:
        failures.append(f"validator imports forbidden provider/network roots: {forbidden}")
    enabled_gates = [name for name in SHADOW_ENV_GATES if os.environ.get(name) == "1"]
    if enabled_gates:
        failures.append(f"shadow selector write/control env gates must not be enabled: {enabled_gates}")


def write_artifacts() -> None:
    result = build_result()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(build_report(result), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--write-artifacts"]:
        write_artifacts()
        print(json.dumps({"status": "wrote", "checkpoint_id": CHECKPOINT_ID}, indent=2, sort_keys=True))
        return 0
    if argv:
        print(json.dumps({"status": "fail", "failures": [f"unknown arguments: {argv}"]}, indent=2))
        return 2

    failures: list[str] = []
    expected = build_result()
    if expected["status"] != "pass":
        failures.append("current OpenAI 4L4 source refresh taxonomy harness has failing cases")
    validate_artifacts(failures, expected)
    validate_report(failures)
    validate_environment_and_imports(failures)
    if failures:
        print(json.dumps({"status": "fail", "failures": failures}, indent=2, sort_keys=True))
        raise AssertionError(f"{CHECKPOINT_ID} failed with {len(failures)} issue(s).")
    print(json.dumps({"status": "pass", "checkpoint_id": CHECKPOINT_ID}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
