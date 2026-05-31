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


CHECKPOINT_ID = "PHASE-4L3-OPENAI-SPOKEN-SALES-QUALITY-MULTITURN-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

FORBIDDEN_IMPORT_ROOTS = {"elevenlabs", "httpx", "openai", "requests", "ultravox", "urllib"}
SHADOW_ENV_GATES = phase4l2.SHADOW_ENV_GATES
FALSE_FLAGS = phase4l2.FALSE_FLAGS

CHANGED_SOURCE_FILES = [
    "runtime/campaigns/public_openai_chatgpt_plans_dialogue.py",
    "scripts/validate_phase_4l3_openai_spoken_sales_quality_multiturn_001.py",
]

BEFORE_WEAK_EXAMPLES = {
    "source_affiliation_boundary": (
        "I'm not calling from OpenAI. This is a public-data simulation using OpenAI's public pricing and help pages. "
        "I can summarize those public pages, but check them before upgrading. What are you trying to decide about ChatGPT?"
    ),
    "plan_category_explanation": (
        "They are subscription options: Free is no-cost, Go is the lower-cost paid step, Plus and Pro are individual plans, Business is for teams, "
        "and Enterprise is for larger organizations. Are you looking for personal use, team use, or enterprise controls?"
    ),
}

MULTI_TURN_CASES: list[dict[str, Any]] = [
    {
        "case_id": "heavy_individual_close_path",
        "scenario": "heavy_individual_close_path",
        "turns": [
            "I code and write heavily every day and keep hitting limits.",
            "What should I compare?",
            "Pro sounds right. How do I sign up?",
        ],
        "expected_sales_progression": (
            "Recommend Pro over Plus from the stated limit pain, avoid restarting discovery, and close to the official "
            "self-serve plan/profile path without account or payment side effects."
        ),
        "must_include_all": ["pro", "official chatgpt plans page"],
        "must_include_any": [["plus", "lower-cost"], ["profile upgrade", "official chatgpt plans page"]],
        "must_not_include": ["what would you mainly use", "are you using chatgpt today", "i sent", "i booked", "i charged"],
        "no_side_effect_close": True,
    },
    {
        "case_id": "light_no_fit_path",
        "scenario": "light_no_fit_path",
        "turns": [
            "I only use ChatGPT once in a while for light personal tasks.",
            "Free seems enough.",
            "I do not want to pay.",
        ],
        "expected_sales_progression": "Disqualify paid pressure, confirm the Free/stay-free path, and stop with low pressure.",
        "must_include_all": ["free"],
        "must_include_any": [["not push", "no paid close", "stay free", "stop here"]],
        "must_not_include": ["buy pro", "upgrade now", "you need pro"],
        "low_pressure_close": True,
    },
    {
        "case_id": "team_admin_enterprise_path",
        "scenario": "team_admin_enterprise_path",
        "turns": [
            "This is for a team.",
            "We need admin controls, security review, procurement, SSO, and SCIM.",
            "Would Go, Plus, or Pro be enough?",
        ],
        "expected_sales_progression": (
            "Avoid individual Go/Plus/Pro pressure, keep Business/Enterprise as the comparison, and route procurement or "
            "security needs to Enterprise/contact sales without fake scheduling."
        ),
        "must_include_all": ["business", "enterprise"],
        "must_include_any": [["contact sales", "procurement", "security review", "sso", "scim"]],
        "must_not_include": ["go is enough", "plus is enough", "pro is enough", "i booked", "scheduled"],
        "team_or_enterprise_route": True,
    },
    {
        "case_id": "privacy_security_boundary_path",
        "scenario": "privacy_security_boundary_path",
        "turns": [
            "What about data privacy, security, and compliance?",
            "Can you guarantee legal compliance for our company?",
        ],
        "expected_sales_progression": (
            "Answer from source-bounded official terms only, do not give legal/security guarantees, and route company review "
            "to official terms or Enterprise/contact-sales path."
        ),
        "must_include_any": [["cannot give a legal", "cannot promise", "official openai"], ["contact-sales", "contact sales", "terms"]],
        "must_not_include": ["guaranteed compliant", "legally compliant if", "your data is never used"],
        "source_bounded": True,
    },
    {
        "case_id": "competitor_gap_progression_path",
        "scenario": "competitor_current_tool_path",
        "turns": [
            "I already use Claude, Copilot, and Gemini.",
            "Why add ChatGPT?",
            "The gap is file analysis and I keep hitting limits when writing and coding.",
        ],
        "expected_sales_progression": (
            "Avoid invented superiority, sell only against the named gap, then progress to Plus/Pro plan fit."
        ),
        "must_include_all": ["plus", "pro"],
        "must_include_any": [["gap", "file", "limits", "headroom"]],
        "must_not_include": ["better than claude", "beats claude", "superior to", "switch now"],
        "competitor_safe": True,
    },
    {
        "case_id": "competitor_no_fit_path",
        "scenario": "competitor_current_tool_path",
        "turns": [
            "I already use Claude and Copilot.",
            "Why add ChatGPT?",
            "Actually my current tool covers everything and I do not want to pay.",
        ],
        "expected_sales_progression": "Disqualify paid pressure when the buyer says the current tool covers the job.",
        "must_include_any": [["not push", "stay with the current tool", "no paid close", "stay free"]],
        "must_not_include": ["buy pro", "upgrade now", "you need pro"],
        "low_pressure_close": True,
    },
    {
        "case_id": "and_fidelity_multiturn_path",
        "scenario": "and_or_fidelity_path",
        "turns": [
            "I use ChatGPT and Claude already.",
            "The gap is coding workflow and usage limits.",
        ],
        "expected_sales_progression": "Preserve that the buyer uses ChatGPT and another tool, then progress from the named gap.",
        "expected_conjunction_relation": "and",
        "must_include_any": [["chatgpt and", "both chatgpt", "current setup"], ["gap", "limits", "coding"]],
        "must_not_include": ["chatgpt or another"],
    },
    {
        "case_id": "or_fidelity_multiturn_path",
        "scenario": "and_or_fidelity_path",
        "turns": [
            "It might be ChatGPT or Claude; I am not sure which one the team uses.",
            "How should we decide?",
        ],
        "expected_sales_progression": "Preserve uncertainty between ChatGPT or another tool instead of rewriting it into a both-tools claim.",
        "expected_conjunction_relation": "either_or",
        "must_include_any": [["chatgpt or", "may be chatgpt", "which one"]],
        "must_not_include": ["using both chatgpt", "both chatgpt and"],
    },
    {
        "case_id": "repeated_question_repair_path",
        "scenario": "repeated_question_repair_path",
        "turns": [
            "I use ChatGPT for coding and writing heavily every day.",
            "I already told you that. What should I compare?",
        ],
        "expected_sales_progression": "Acknowledge prior heavy-use context, answer shorter/differently, and move to the plan decision.",
        "must_include_all": ["pro", "plus"],
        "must_include_any": [["since you", "heavy coding", "based on"]],
        "must_not_include": ["what would you mainly use", "are you using it occasionally"],
        "final_response_must_differ_from_previous": True,
    },
    {
        "case_id": "source_affiliation_route_path",
        "scenario": "source_affiliation_route_path",
        "turns": [
            "Are you OpenAI?",
            "Where does this information come from?",
            "What should I do next?",
        ],
        "expected_sales_progression": (
            "Avoid OpenAI affiliation, explain the public source boundary, and move to plan fit or the official route."
        ),
        "must_include_any": [["official", "plan page", "decide", "choosing"], ["yourself", "team", "fit"]],
        "must_not_include": ["i am from openai", "official openai representative", "authorized by openai"],
        "must_not_claim_affiliation": True,
    },
]


def normalize(value: str) -> str:
    return phase4l2.normalize(value)


def contains_any(text: str, needles: list[str]) -> bool:
    return phase4l2.contains_any(text, needles)


def contains_all(text: str, needles: list[str]) -> bool:
    return phase4l2.contains_all(text, needles)


def response_word_count(text: str) -> int:
    return phase4l2.response_word_count(text)


def run_turn_sequence(turns: list[str]) -> dict[str, Any]:
    return phase4l2.run_turn_sequence(turns)


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


def evaluate_multi_turn_case(case: dict[str, Any]) -> dict[str, Any]:
    run = run_turn_sequence(list(case["turns"]))
    response = str(run.get("final_response") or "")
    responses = [str(item) for item in run.get("responses") or []]
    final_frame = run.get("final_frame") if isinstance(run.get("final_frame"), dict) else {}
    all_response_text = "\n".join(responses)
    failures: list[str] = []

    if not response.strip():
        failures.append("final response was empty")
    if not contains_all(response, list(case.get("must_include_all") or [])):
        failures.append("required final-response terms missing")
    for group in case.get("must_include_any") or []:
        if not contains_any(response, list(group)):
            failures.append(f"required any-term group missing: {group}")
    if contains_any(all_response_text, list(case.get("must_not_include") or [])):
        failures.append("forbidden response term present")
    if case.get("must_not_claim_affiliation") and phase4l2.bad_affiliation_claim(all_response_text):
        failures.append("response claimed official OpenAI affiliation")
    expected_relation = case.get("expected_conjunction_relation")
    if expected_relation and final_frame.get("conjunction_relation") != expected_relation:
        failures.append(f"conjunction_relation mismatch: {final_frame.get('conjunction_relation')!r}")
    if case.get("final_response_must_differ_from_previous") and len(responses) >= 2:
        if normalize(responses[-1]) == normalize(responses[-2]):
            failures.append("final response repeated previous response exactly")
    if response_word_count(response) > 95:
        failures.append("final response was too long for spoken sales use")
    if phase4l2.contamination_hits_in_text(all_response_text):
        failures.append("OpenAI-primary multi-turn response contains RouteSignal contamination")
    if case.get("no_side_effect_close") and contains_any(all_response_text, ["i sent", "i booked", "i charged", "created a crm"]):
        failures.append("close implied a side effect")
    if case.get("team_or_enterprise_route") and contains_any(response, ["plus is enough", "pro is enough"]):
        failures.append("team/admin path pressured individual plans")
    if case.get("competitor_safe") and contains_any(all_response_text, ["better than claude", "beats claude", "superior to"]):
        failures.append("competitor response invented superiority")
    if case.get("low_pressure_close") and contains_any(all_response_text, ["upgrade now", "buy pro", "you need pro"]):
        failures.append("low-fit response pressured paid plan")

    return {
        "case_id": case["case_id"],
        "scenario": case["scenario"],
        "turns": list(case["turns"]),
        "expected_sales_progression": case["expected_sales_progression"],
        "actual_semantic_action_response_summary": {
            "semantic": str(final_frame.get("semantic") or ""),
            "dialogue_focus": str(final_frame.get("dialogue_focus") or ""),
            "action_id": str(final_frame.get("action_id") or "continue_with_session_policy"),
            "conjunction_relation": str(final_frame.get("conjunction_relation") or ""),
            "response_summary": response.split(".")[0].strip(),
        },
        "responses": responses,
        "actual_response": response,
        "pass": not failures,
        "failures": failures,
    }


def evaluate_before_after_weak_examples(single_turn_matrix: list[dict[str, Any]]) -> dict[str, Any]:
    by_case = {item["case_id"]: item for item in single_turn_matrix}
    source_after = str(by_case["source_affiliation_boundary"]["actual_response"])
    plan_after = str(by_case["plan_category_explanation"]["actual_response"])

    source_failures: list[str] = []
    if "public-data simulation" in normalize(source_after):
        source_failures.append("still uses public-data simulation wording")
    if not contains_all(source_after, ["not calling from openai", "public"]):
        source_failures.append("missing safe non-affiliation and public-source boundary")
    if not contains_any(source_after, ["decide", "choosing", "fit"]):
        source_failures.append("does not move toward plan-fit decision")
    if "?" not in source_after:
        source_failures.append("does not ask a next sales question")
    if response_word_count(source_after) > 55:
        source_failures.append("source response is too long for the target spoken style")
    if phase4l2.bad_affiliation_claim(source_after):
        source_failures.append("claims official OpenAI affiliation")

    plan_failures: list[str] = []
    if normalize(plan_after).startswith("they are subscription options"):
        plan_failures.append("still starts like a static FAQ definition")
    if not contains_all(plan_after, ["free", "go", "plus", "pro", "business", "enterprise"]):
        plan_failures.append("missing required plan categories")
    if not contains_any(plan_after, ["individual", "personal"]):
        plan_failures.append("missing individual/personal route")
    if not contains_any(plan_after, ["team", "teams"]):
        plan_failures.append("missing team route")
    if not contains_any(plan_after, ["procurement", "security", "admin"]):
        plan_failures.append("missing stronger procurement/security/admin next question")
    if "?" not in plan_after:
        plan_failures.append("does not ask a next sales question")
    if response_word_count(plan_after) > 55:
        plan_failures.append("plan category response is too long for the target spoken style")

    return {
        "source_affiliation_boundary": {
            "before_response": BEFORE_WEAK_EXAMPLES["source_affiliation_boundary"],
            "before_status": "safe_but_boundary_heavy",
            "after_response": source_after,
            "after_status": "pass" if not source_failures else "fail",
            "failures": source_failures,
        },
        "plan_category_explanation": {
            "before_response": BEFORE_WEAK_EXAMPLES["plan_category_explanation"],
            "before_status": "accurate_but_faq_like",
            "after_response": plan_after,
            "after_status": "pass" if not plan_failures else "fail",
            "failures": plan_failures,
        },
    }


def scenario_counts(case_matrix: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for item in case_matrix:
        scenario = str(item["scenario"])
        counts.setdefault(scenario, {"case_count": 0, "pass": 0, "fail": 0})
        counts[scenario]["case_count"] += 1
        counts[scenario]["pass" if item["pass"] else "fail"] += 1
    return counts


def route_signal_response_contamination(single_turn: list[dict[str, Any]], multi_turn: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for item in single_turn:
        terms = phase4l2.contamination_hits_in_text(str(item.get("actual_response") or ""))
        if terms:
            hits.append({"matrix": "single_turn_4l2", "case_id": item["case_id"], "terms": terms})
    for item in multi_turn:
        terms = phase4l2.contamination_hits_in_text("\n".join(str(response) for response in item.get("responses") or []))
        if terms:
            hits.append({"matrix": "multi_turn_4l3", "case_id": item["case_id"], "terms": terms})
    return hits


def build_result() -> dict[str, Any]:
    single_turn = phase4l2.build_case_matrix()
    multi_turn = [evaluate_multi_turn_case(case) for case in MULTI_TURN_CASES]
    weak_status = evaluate_before_after_weak_examples(single_turn)
    contamination_hits = route_signal_response_contamination(single_turn, multi_turn)
    single_failures = [item for item in single_turn if not item["pass"]]
    multi_failures = [item for item in multi_turn if not item["pass"]]
    weak_failures = [
        case_id
        for case_id, payload in weak_status.items()
        if payload.get("after_status") != "pass"
    ]
    scenario_matrix_counts = scenario_counts(multi_turn)
    all_pass = not single_failures and not multi_failures and not weak_failures and not contamination_hits
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if all_pass else "fail",
        "primary_benchmark_campaign": "public OpenAI ChatGPT plans",
        "routesignal_role": "secondary regression fixture only",
        "changed_source_files": CHANGED_SOURCE_FILES,
        "single_turn_4l2_status": "pass" if not single_failures else "fail",
        "single_turn_4l2_regression_count": len(single_failures),
        "single_turn_4l2_case_count": len(single_turn),
        "single_turn_4l2_matrix": single_turn,
        "multi_turn_4l3_status": "pass" if not multi_failures else "fail",
        "multi_turn_4l3_case_count": len(multi_turn),
        "multi_turn_case_matrix": multi_turn,
        "pass_fail_counts_by_scenario": scenario_matrix_counts,
        "multi_turn_pass_fail_count": {
            "pass": sum(1 for item in multi_turn if item["pass"]),
            "fail": sum(1 for item in multi_turn if not item["pass"]),
        },
        "before_after_weak_example_status": weak_status,
        "strong_spoken_examples": [
            {
                "case_id": "heavy_individual_close_path",
                "why_strong": "Uses the prior pain signal to recommend Pro versus Plus and close to the official self-serve route.",
            },
            {
                "case_id": "team_admin_enterprise_path",
                "why_strong": "Keeps admin/security/procurement needs out of individual Plus/Pro pressure.",
            },
            {
                "case_id": "source_affiliation_route_path",
                "why_strong": "Keeps the OpenAI affiliation boundary while still moving toward plan fit.",
            },
        ],
        "remaining_weak_examples": [
            {"case_id": case_id, "failures": weak_status[case_id]["failures"]}
            for case_id in weak_failures
        ],
        "routesignal_contamination_check": {
            "openai_primary_response_contamination_count": len(contamination_hits),
            "openai_primary_response_hits": contamination_hits,
            "openai_path_source_hits": phase4l2.scan_source_for_contamination(phase4l2.OPENAI_PATH_SCAN_FILES),
            "generic_path_source_hits": phase4l2.scan_source_for_contamination(phase4l2.GENERIC_PATH_SCAN_FILES),
        },
        "source_affiliation_safety_status": "pass" if weak_status["source_affiliation_boundary"]["after_status"] == "pass" else "fail",
        "plan_fit_close_status": "pass"
        if scenario_matrix_counts["heavy_individual_close_path"]["fail"] == 0
        and scenario_matrix_counts["light_no_fit_path"]["fail"] == 0
        and scenario_matrix_counts["team_admin_enterprise_path"]["fail"] == 0
        else "fail",
        "repeated_question_repair_status": "pass" if scenario_matrix_counts["repeated_question_repair_path"]["fail"] == 0 else "fail",
        "and_or_fidelity_status": "pass" if scenario_matrix_counts["and_or_fidelity_path"]["fail"] == 0 else "fail",
        "no_side_effect_confirmation": {
            "selector_control_allowed": False,
            "response_replacement_performed": False,
            "provider_model_tts_crm_email_calendar_payment_account_side_effect_path_enabled": False,
            "raw_private_transcript_or_audio_added_to_public_evidence": False,
            "live_readiness_claimed": False,
        },
        "no_live_readiness_confirmation": True,
        **{key: False for key in FALSE_FLAGS},
    }


def build_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        f"- Status: {result['status']}",
        "- Primary benchmark campaign: public OpenAI ChatGPT plans",
        "- RouteSignal role: secondary regression fixture only",
        f"- Changed source files: {', '.join(result['changed_source_files'])}",
        f"- Original 4L2 single-turn status: {result['single_turn_4l2_status']}",
        f"- Single-turn 4L2 regression count: {result['single_turn_4l2_regression_count']}",
        f"- Multi-turn 4L3 status: {result['multi_turn_4l3_status']}",
        f"- Multi-turn pass/fail count: {json.dumps(result['multi_turn_pass_fail_count'], sort_keys=True)}",
        "- RouteSignal contamination in OpenAI-primary responses: "
        + str(result["routesignal_contamination_check"]["openai_primary_response_contamination_count"]),
        "- Source/affiliation safety status: " + str(result["source_affiliation_safety_status"]),
        "- Plan fit / close status: " + str(result["plan_fit_close_status"]),
        "- Repeated-question repair status: " + str(result["repeated_question_repair_status"]),
        "- AND/OR fidelity status: " + str(result["and_or_fidelity_status"]),
        "- No live selector control was enabled.",
        "- No response replacement was enabled.",
        "- No provider/model/TTS/CRM/email/calendar/payment/account path was enabled.",
        "- No raw private transcript/audio was added to public evidence.",
        "- No live readiness claim was made.",
        "",
        "## Pass/Fail Counts By Scenario",
        "",
        "| Scenario | Cases | Pass | Fail |",
        "| --- | ---: | ---: | ---: |",
    ]
    for scenario, counts in result["pass_fail_counts_by_scenario"].items():
        lines.append(f"| `{scenario}` | {counts['case_count']} | {counts['pass']} | {counts['fail']} |")
    lines.extend(["", "## Before/After Weak Examples", ""])
    for case_id, payload in result["before_after_weak_example_status"].items():
        lines.extend(
            [
                f"### {case_id}",
                "",
                f"- Before status: {payload['before_status']}",
                f"- Before response: {payload['before_response']}",
                f"- After status: {payload['after_status']}",
                f"- After response: {payload['after_response']}",
                f"- Failures: {json.dumps(payload['failures'])}",
                "",
            ]
        )
    lines.extend(["## Multi-turn Case Matrix", ""])
    for item in result["multi_turn_case_matrix"]:
        summary = item["actual_semantic_action_response_summary"]
        lines.extend(
            [
                f"### {item['case_id']}",
                "",
                f"- Scenario: {item['scenario']}",
                f"- Expected progression: {item['expected_sales_progression']}",
                f"- Actual semantic/action/response summary: semantic={summary['semantic']}; action={summary['action_id']}; "
                f"focus={summary['dialogue_focus']}; relation={summary['conjunction_relation']}; summary={summary['response_summary']}",
                f"- Pass: {str(item['pass']).lower()}",
                f"- Failures: {json.dumps(item['failures'])}",
                f"- Final response: {item['actual_response']}",
                "",
            ]
        )
    lines.extend(["## 4L2 Single-turn Matrix", ""])
    for item in result["single_turn_4l2_matrix"]:
        lines.append(f"- `{item['case_id']}`: pass={str(item['pass']).lower()}; response={item['actual_response']}")
    lines.extend(["", "## Strong Spoken Examples", ""])
    for item in result["strong_spoken_examples"]:
        lines.append(f"- `{item['case_id']}`: {item['why_strong']}")
    lines.extend(["", "## Remaining Weak Examples", ""])
    if result["remaining_weak_examples"]:
        for item in result["remaining_weak_examples"]:
            lines.append(f"- `{item['case_id']}`: {json.dumps(item['failures'])}")
    else:
        lines.append("- None in required 4L3 weak-example targets.")
    lines.extend(
        [
            "",
            "## RouteSignal Contamination Check",
            "",
            "- OpenAI-primary response contamination count: "
            + str(result["routesignal_contamination_check"]["openai_primary_response_contamination_count"]),
            "- OpenAI path source hits remain classified as buyer-input boundary triggers only.",
            "- Generic path source hits remain legacy default-playbook guard debt, not 4L3 scope.",
            "",
            "## No-side-effect Confirmation",
            "",
            "- Selector control remains blocked.",
            "- Response replacement remains blocked.",
            "- No provider/model/TTS/CRM/email/calendar/payment/account side-effect path was enabled.",
            "- No live readiness claim was made.",
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
    for key in [
        "status",
        "changed_source_files",
        "single_turn_4l2_regression_count",
        "multi_turn_4l3_case_count",
        "multi_turn_case_matrix",
        "pass_fail_counts_by_scenario",
        "before_after_weak_example_status",
        "remaining_weak_examples",
        "routesignal_contamination_check",
        "source_affiliation_safety_status",
        "plan_fit_close_status",
        "repeated_question_repair_status",
        "and_or_fidelity_status",
    ]:
        if actual.get(key) != expected.get(key):
            failures.append(f"{key} mismatch")
    for key in FALSE_FLAGS:
        if actual.get(key) is not False:
            failures.append(f"{key} must be false: {actual.get(key)!r}")


def validate_report(failures: list[str]) -> None:
    if not REPORT_PATH.is_file():
        return
    text = REPORT_PATH.read_text(encoding="utf-8")
    required = [
        "Original 4L2 single-turn status",
        "Single-turn 4L2 regression count",
        "Multi-turn Case Matrix",
        "Before/After Weak Examples",
        "Strong Spoken Examples",
        "Remaining Weak Examples",
        "RouteSignal Contamination Check",
        "No-side-effect Confirmation",
        "Selector control remains blocked.",
        "Response replacement remains blocked.",
        "No provider/model/TTS/CRM/email/calendar/payment/account side-effect path was enabled.",
        "No live readiness claim was made.",
    ]
    for phrase in required:
        if phrase not in text:
            failures.append(f"report missing phrase: {phrase}")
    for case in MULTI_TURN_CASES:
        if case["case_id"] not in text:
            failures.append(f"report missing multi-turn case id: {case['case_id']}")


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
        failures.append("current OpenAI-primary 4L3 harness has failing cases")
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
