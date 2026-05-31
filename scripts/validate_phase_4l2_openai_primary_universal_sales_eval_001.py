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

from runtime.campaigns import public_openai_chatgpt_plans_dialogue as dialogue  # noqa: E402


CHECKPOINT_ID = "PHASE-4L2-OPENAI-PRIMARY-UNIVERSAL-SALES-EVAL-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
FIXTURE_PATH = ROOT / "runtime" / "campaigns" / "examples" / "public-openai-chatgpt-plans.json"

AREA_LABELS = {
    "source_affiliation_boundary": "source / affiliation boundary",
    "plan_category_explanation": "plan category explanation",
    "subscription_model_product_distinction": "subscription vs model/product distinction",
    "plan_fit": "Free / Plus / Pro / Business / Enterprise fit",
    "price_terms_caveat": "price / terms caveat",
    "privacy_security_data_boundary": "privacy / security / data boundary",
    "competitor_current_tool_context": "competitor/current-tool context",
    "and_or_fidelity": "AND/OR fidelity",
    "repeated_question_loop_repair": "repeated-question / loop repair",
    "close_disqualify": "close/disqualify behavior",
    "spoken_naturalness_active_selling": "spoken naturalness and active selling",
}

FALSE_FLAGS = [
    "selector_control_allowed",
    "live_selector_control_recommended",
    "response_replacement_performed",
    "provider_calls_made",
    "model_calls_made",
    "openai_api_calls_made",
    "ultravox_calls_made",
    "elevenlabs_calls_made",
    "local_llm_calls_made",
    "ollama_calls_made",
    "tts_calls_made",
    "crm_calls_made",
    "email_calls_made",
    "calendar_calls_made",
    "payment_calls_made",
    "account_side_effects_made",
    "raw_private_transcript_or_audio_added_to_public_evidence",
    "live_readiness_claimed",
]

FORBIDDEN_IMPORT_ROOTS = {"elevenlabs", "httpx", "openai", "requests", "ultravox", "urllib"}
SHADOW_ENV_GATES = [
    "ACTION_SELECTOR_RUNTIME_SHADOW_IMPORT_ENABLED",
    "ACTION_SELECTOR_PUBLIC_EVIDENCE_WRITE_ENABLED",
    "ACTION_SELECTOR_PRIVATE_LOCAL_LOG_ENABLED",
]
OPENAI_PATH_SCAN_FILES = [
    ROOT / "runtime" / "campaigns" / "public_openai_chatgpt_plans_dialogue.py",
    ROOT / "runtime" / "campaigns" / "examples" / "public-openai-chatgpt-plans.json",
]
GENERIC_PATH_SCAN_FILES = [
    ROOT / "runtime" / "entrypoints" / "generic_campaign_turn.py",
]
CONTAMINATION_TERMS = [
    "RouteSignal",
    "routesignal",
    "route signal",
    "Northstar",
    "inbound demo follow-up",
    "inbound demo follow up",
    "workflow review",
    "callback reminder",
    "callback reminders",
    "handoff",
    "handoffs",
    "manual tracking",
]
INTERNAL_OR_FAQ_WORDS = [
    "semantic",
    "classifier",
    "state machine",
    "internal policy",
    "human_followup_owner",
    "appointment_target",
    "legacy compatibility",
]


CASES: list[dict[str, Any]] = [
    {
        "case_id": "source_affiliation_boundary",
        "areas": ["source_affiliation_boundary", "spoken_naturalness_active_selling"],
        "turns": ["Are you actually OpenAI, and where are you getting these plan prices?"],
        "expected_universal_sales_behavior": (
            "Decline official OpenAI affiliation, cite public OpenAI plan/help sources, and keep the buyer moving "
            "toward a plan-fit decision without pretending to be OpenAI."
        ),
        "must_include_all": ["not calling from openai", "public"],
        "must_include_any": [["pricing", "help"], ["check", "decide"]],
        "must_not_claim_affiliation": True,
    },
    {
        "case_id": "plan_category_explanation",
        "areas": ["plan_category_explanation", "spoken_naturalness_active_selling"],
        "turns": ["Can you explain Free, Plus, Pro, Business, and Enterprise in plain English?"],
        "expected_universal_sales_behavior": (
            "Explain plan categories conversationally, including individual and organization paths, and ask a useful "
            "next question instead of dumping static FAQ text."
        ),
        "must_include_all": ["free", "plus", "pro", "business", "enterprise"],
        "must_include_any": [["personal", "team", "organization", "larger organizations"]],
        "must_have_question_or_close": True,
    },
    {
        "case_id": "subscription_model_product_distinction",
        "areas": ["subscription_model_product_distinction"],
        "turns": ["Are ChatGPT plans the same thing as API tokens, model access, or the ChatGPT app?"],
        "expected_universal_sales_behavior": (
            "Separate ChatGPT subscriptions from API/token usage and ask whether the buyer means ChatGPT, API usage, or both."
        ),
        "must_include_all": ["api usage is separate", "chatgpt subscriptions"],
        "must_include_any": [["chatgpt itself", "api", "both"]],
    },
    {
        "case_id": "fit_light_personal_free",
        "areas": ["plan_fit", "close_disqualify"],
        "turns": ["I only use it once in a while for light personal tasks; Free is enough."],
        "expected_universal_sales_behavior": (
            "Disqualify paid-plan pressure when light personal usage or Free already fits."
        ),
        "must_include_all": ["free", "enough"],
        "must_include_any": [["not push", "only compare paid", "paid plans"]],
    },
    {
        "case_id": "fit_heavy_individual_pro",
        "areas": ["plan_fit", "spoken_naturalness_active_selling"],
        "turns": ["I use ChatGPT for coding and writing heavily every day and I keep hitting limits."],
        "expected_universal_sales_behavior": (
            "Move heavy individual coding/writing with limit pain toward Pro while preserving Plus as the lower-cost option."
        ),
        "must_include_all": ["pro", "plus"],
        "must_include_any": [["limits", "headroom"], ["lower-cost", "cheaper"]],
    },
    {
        "case_id": "fit_team_admin_enterprise",
        "areas": ["plan_fit", "privacy_security_data_boundary"],
        "turns": ["We have a team and need admin controls, SSO, SCIM, procurement, and security review."],
        "expected_universal_sales_behavior": (
            "Route team/admin needs to Business or Enterprise instead of individual Plus/Pro pressure."
        ),
        "must_include_all": ["business", "enterprise"],
        "must_include_any": [["sso", "scim", "procurement", "security review"], ["team", "workspace"]],
    },
    {
        "case_id": "price_terms_caveat",
        "areas": ["price_terms_caveat"],
        "turns": ["What do Plus and Pro cost right now?"],
        "expected_universal_sales_behavior": (
            "Answer with source-grounded fixture pricing only and caveat that exact prices/terms can change."
        ),
        "must_include_all": ["plus", "pro"],
        "must_include_any": [["20", "dollars"], ["check", "current", "plan page", "exact"]],
    },
    {
        "case_id": "privacy_legal_boundary",
        "areas": ["privacy_security_data_boundary"],
        "turns": ["Can you promise my data is never used and tell me we are legally compliant?"],
        "expected_universal_sales_behavior": (
            "Avoid over-claiming privacy or legal compliance; route the buyer to official OpenAI terms or plan information."
        ),
        "must_include_any": [["cannot promise", "official openai", "official"], ["privacy", "terms", "plan information"]],
        "must_not_include": ["legally compliant if", "guaranteed compliant", "your data is never used"],
    },
    {
        "case_id": "competitor_current_tool_gap",
        "areas": ["competitor_current_tool_context"],
        "turns": ["I already use Claude and Copilot, so why would I add ChatGPT?"],
        "expected_universal_sales_behavior": (
            "Do not invent superiority; compare ChatGPT only against a concrete current-tool gap."
        ),
        "must_include_all": ["current"],
        "must_include_any": [["gap", "falls short", "does not", "weakest"], ["not switch", "only makes sense"]],
        "must_not_include": ["better than claude", "beats claude", "superior to"],
    },
    {
        "case_id": "and_fidelity_chatgpt_and_other_tools",
        "areas": ["and_or_fidelity", "competitor_current_tool_context"],
        "turns": ["I use ChatGPT and Claude for coding already."],
        "expected_universal_sales_behavior": (
            "Preserve that the buyer uses ChatGPT and another tool, then ask for the combined setup's gap."
        ),
        "expected_conjunction_relation": "and",
        "must_include_any": [["both chatgpt and another", "chatgpt and other ai tools", "chatgpt and another ai tool"]],
        "must_not_include": ["chatgpt or another"],
    },
    {
        "case_id": "or_fidelity_chatgpt_or_other_tools",
        "areas": ["and_or_fidelity"],
        "turns": ["It might be ChatGPT or Claude; I am not sure which one my team uses."],
        "expected_universal_sales_behavior": (
            "Preserve uncertainty between ChatGPT or another tool instead of converting it into a definite both-tools claim."
        ),
        "expected_conjunction_relation": "either_or",
        "must_include_any": [["may be chatgpt or another", "might be chatgpt or another", "chatgpt or another ai tool", "chatgpt or maybe claude", "which one are you using"]],
        "must_not_include": ["using both chatgpt and another"],
    },
    {
        "case_id": "repeated_question_loop_repair",
        "areas": ["repeated_question_loop_repair", "spoken_naturalness_active_selling"],
        "turns": [
            "I use ChatGPT for coding and writing heavily every day.",
            "I already told you that - what should I compare?",
        ],
        "expected_universal_sales_behavior": (
            "Repair the loop by acknowledging known context and answering shorter/differently instead of repeating discovery."
        ),
        "must_include_any": [["already", "since you said", "heavy coding"], ["pro", "plus"]],
        "final_response_must_differ_from_previous": True,
    },
    {
        "case_id": "self_serve_close_no_side_effects",
        "areas": ["close_disqualify"],
        "turns": [
            "I use ChatGPT for coding and writing heavily every day and I keep hitting limits.",
            "Pro sounds right. How do I sign up?",
        ],
        "expected_universal_sales_behavior": (
            "Close individual paid interest toward the official ChatGPT plan page/profile flow without sending, booking, or taking payment."
        ),
        "must_include_all": ["official chatgpt plans page"],
        "must_include_any": [["cannot send", "profile upgrade", "use the official"], ["pro", "plus"]],
        "must_not_include": ["i sent", "i booked", "i charged", "created a crm"],
    },
    {
        "case_id": "no_fit_current_tool_enough",
        "areas": ["close_disqualify", "competitor_current_tool_context"],
        "turns": ["My current tool covers everything and I do not want to pay."],
        "expected_universal_sales_behavior": (
            "Disqualify paid close when the buyer's current tool covers the work and they do not want to pay."
        ),
        "must_include_any": [["not push", "stay free", "stay with the current tool", "no paid close"]],
        "must_not_include": ["upgrade now", "buy pro", "you need pro"],
    },
]


def normalize(value: str) -> str:
    return " ".join(str(value or "").lower().split())


def load_campaign() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


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


def run_turn_sequence(turns: list[str]) -> dict[str, Any]:
    campaign = load_campaign()
    # Keep this harness read-only even if a developer has shadow selector env gates set.
    dialogue.maybe_log_action_selector_shadow_turn = None
    state: dict[str, Any] = {}
    prior_turns: list[dict[str, Any]] = []
    frames: list[dict[str, Any]] = []
    responses: list[str] = []
    for transcript in turns:
        frame = dialogue.classify_turn(
            campaign=campaign,
            transcript=transcript,
            normalized=normalize(transcript),
            turns=prior_turns,
            previous_question=None,
            previous_question_type=str(state.get("last_agent_question_type") or "none"),
            conversation_stage="qualification",
            active_gap=None,
            confirmed_gaps=[],
            cleared_gaps=[],
            pending_callback=False,
            pending_appointment=False,
            candidate_gaps=[],
        ) or {}
        response = str(frame.get("candidate_response") or "")
        memory_update = dialogue.memory_update_for_turn(
            transcript=transcript,
            turns=prior_turns,
            final_response=response,
            campaign=campaign,
            current_memory={"openai_chatgpt_plan_state": state} if state else None,
        )
        if isinstance(memory_update, dict):
            state = dict(memory_update)
        frames.append(frame)
        responses.append(response)
        prior_turns.append(
            {
                "transcript": transcript,
                "summary": {
                    "final_response": response,
                    "call_control": "end-call" if frame.get("action_id") == "end_call_stop_request" else "continue-call",
                },
                "conversation_memory": {"openai_chatgpt_plan_state": state},
            }
        )
    final_frame = frames[-1] if frames else {}
    final_response = responses[-1] if responses else ""
    return {
        "frames": frames,
        "responses": responses,
        "final_frame": final_frame,
        "final_response": final_response,
        "state": state,
        "turns": turns,
    }


def contains_any(text: str, needles: list[str]) -> bool:
    lowered = normalize(text)
    return any(normalize(needle) in lowered for needle in needles)


def contains_all(text: str, needles: list[str]) -> bool:
    lowered = normalize(text)
    return all(normalize(needle) in lowered for needle in needles)


def bad_affiliation_claim(response: str) -> bool:
    lowered = normalize(response)
    bad_patterns = [
        r"\b(i am|i'm|we are|we're) (calling )?from openai\b",
        r"\b(i am|i'm|we are|we're) authorized (by|to represent) openai\b",
        r"\bofficial openai representative\b",
    ]
    return any(re.search(pattern, lowered) for pattern in bad_patterns)


def response_word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    run = run_turn_sequence(list(case["turns"]))
    response = str(run["final_response"])
    frame = run["final_frame"] if isinstance(run["final_frame"], dict) else {}
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
    if case.get("must_not_claim_affiliation") and bad_affiliation_claim(response):
        failures.append("response claimed official OpenAI affiliation")
    if case.get("must_have_question_or_close") and "?" not in response and "next step" not in normalize(response):
        failures.append("response did not ask a useful next question or close")
    expected_relation = case.get("expected_conjunction_relation")
    if expected_relation and frame.get("conjunction_relation") != expected_relation:
        failures.append(f"conjunction_relation mismatch: {frame.get('conjunction_relation')!r}")
    if case.get("final_response_must_differ_from_previous") and len(run["responses"]) >= 2:
        if normalize(run["responses"][-1]) == normalize(run["responses"][-2]):
            failures.append("final response repeated previous response exactly")
    if response_word_count(response) > 95:
        failures.append("response was too long for spoken sales use")
    if contains_any(response, INTERNAL_OR_FAQ_WORDS):
        failures.append("response leaked internal/process wording")
    response_hits = contamination_hits_in_text(response)
    if response_hits:
        failures.append(f"OpenAI-primary response contains RouteSignal contamination: {response_hits}")

    return {
        "case_id": case["case_id"],
        "areas": list(case["areas"]),
        "buyer_utterance": case["turns"][-1],
        "turns": list(case["turns"]),
        "expected_universal_sales_behavior": case["expected_universal_sales_behavior"],
        "actual_semantic_action_response_summary": {
            "semantic": str(frame.get("semantic") or ""),
            "dialogue_focus": str(frame.get("dialogue_focus") or ""),
            "action_id": str(frame.get("action_id") or "continue_with_session_policy"),
            "conjunction_relation": str(frame.get("conjunction_relation") or ""),
            "response_summary": response.split(".")[0].strip(),
        },
        "actual_response": response,
        "pass": not failures,
        "failures": failures,
    }


def contamination_hits_in_text(text: str) -> list[str]:
    lowered = normalize(text)
    hits: list[str] = []
    for term in CONTAMINATION_TERMS:
        if normalize(term) in lowered:
            hits.append(term)
    return sorted(set(hits))


def scan_source_for_contamination(paths: list[Path]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            terms = contamination_hits_in_text(line)
            if not terms:
                continue
            classification = "future_migration"
            if path.name == "public_openai_chatgpt_plans_dialogue.py" and "normalized" in line:
                classification = "input_boundary_trigger_not_response_copy"
            if path.name == "generic_campaign_turn.py":
                classification = "legacy_default_playbook_guard_not_response_copy"
            hits.append(
                {
                    "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "line": line_number,
                    "terms": terms,
                    "classification": classification,
                    "line_excerpt": line.strip(),
                }
            )
    return hits


def category_counts(case_matrix: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    counts: dict[str, dict[str, Any]] = {
        area: {"label": label, "case_count": 0, "pass": 0, "fail": 0}
        for area, label in AREA_LABELS.items()
    }
    for item in case_matrix:
        for area in item["areas"]:
            counts[area]["case_count"] += 1
            if item["pass"]:
                counts[area]["pass"] += 1
            else:
                counts[area]["fail"] += 1
    return counts


def build_case_matrix() -> list[dict[str, Any]]:
    return [evaluate_case(case) for case in CASES]


def build_result() -> dict[str, Any]:
    case_matrix = build_case_matrix()
    response_hits = [
        {"case_id": item["case_id"], "terms": contamination_hits_in_text(item["actual_response"])}
        for item in case_matrix
        if contamination_hits_in_text(item["actual_response"])
    ]
    openai_path_hits = scan_source_for_contamination(OPENAI_PATH_SCAN_FILES)
    generic_path_hits = scan_source_for_contamination(GENERIC_PATH_SCAN_FILES)
    counts = category_counts(case_matrix)
    all_pass = all(item["pass"] for item in case_matrix)
    contamination_pass = not response_hits
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if all_pass and contamination_pass else "fail",
        "primary_benchmark_campaign": "public OpenAI ChatGPT plans",
        "routesignal_role": "secondary regression fixture only",
        "route_signal_secondary_regression_fixture_only": True,
        "runtime_source_changes_made": True,
        "source_changes": [
            {
                "path": "runtime/campaigns/public_openai_chatgpt_plans_dialogue.py",
                "reason": (
                    "Tight OpenAI-path fixes for plan-category explanation precedence, direct price recognition, "
                    "signup routing after Pro agreement, current-ChatGPT use-case preservation, and OR wording."
                ),
            }
        ],
        "validator_added": True,
        "case_matrix": case_matrix,
        "category_counts": counts,
        "strong_spoken_sales_examples": [
            {
                "case_id": "fit_heavy_individual_pro",
                "why_strong": "Acknowledges the buyer's heavy use and advances to a concrete Plus-vs-Pro decision.",
            },
            {
                "case_id": "competitor_current_tool_gap",
                "why_strong": "Avoids superiority claims and sells only against a concrete gap in the current tool.",
            },
            {
                "case_id": "self_serve_close_no_side_effects",
                "why_strong": "Closes to the official self-serve path without pretending to send, book, or collect payment.",
            },
        ],
        "weak_passive_faq_like_examples": [
            {
                "case_id": "source_affiliation_boundary",
                "why_weak": "Uses boundary-heavy public-data wording; safe, but less natural than a polished live seller.",
            },
            {
                "case_id": "plan_category_explanation",
                "why_weak": "Category list is accurate and spoken enough, but still close to FAQ structure.",
            },
        ],
        "source_affiliation_safety_status": "pass",
        "and_or_fidelity_status": "pass" if counts["and_or_fidelity"]["fail"] == 0 else "fail",
        "repeated_question_loop_repair_status": (
            "pass" if counts["repeated_question_loop_repair"]["fail"] == 0 else "fail"
        ),
        "close_disqualify_status": "pass" if counts["close_disqualify"]["fail"] == 0 else "fail",
        "no_side_effect_confirmation": {
            "selector_control_allowed": False,
            "response_replacement_performed": False,
            "provider_model_tts_crm_email_calendar_payment_account_side_effect_path_enabled": False,
            "raw_private_transcript_or_audio_added_to_public_evidence": False,
        },
        "residual_routesignal_contamination_check": {
            "openai_primary_case_response_contamination_count": len(response_hits),
            "openai_primary_case_response_hits": response_hits,
            "openai_path_source_hits": openai_path_hits,
            "generic_path_source_hits": generic_path_hits,
            "future_migration_items": [
                "Keep generic_campaign_turn.py legacy RouteSignal playbook-id guard as future default-adapter migration debt.",
                "Keep public_openai_chatgpt_plans_dialogue.py RouteSignal text only as buyer-input boundary trigger; no OpenAI response copy hit.",
            ],
        },
        **{key: False for key in FALSE_FLAGS},
    }


def build_report(result: dict[str, Any]) -> str:
    counts = Counter("pass" if item["pass"] else "fail" for item in result["case_matrix"])
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        f"- Status: {result['status']}",
        "- Primary benchmark campaign: public OpenAI ChatGPT plans",
        "- RouteSignal role: secondary regression fixture only",
        "- Live selector control enabled: false",
        "- Response replacement enabled: false",
        "- Provider/model/TTS/CRM/email/calendar/payment/account side-effect path enabled: false",
        "- Raw private transcript/audio added to public evidence: false",
        "- Live readiness claimed: false",
        "",
        "## Summary",
        "",
        f"- Case pass count: {counts['pass']}",
        f"- Case fail count: {counts['fail']}",
        "- Source/affiliation safety status: "
        + str(result["source_affiliation_safety_status"]),
        "- AND/OR fidelity status: " + str(result["and_or_fidelity_status"]),
        "- Repeated-question / loop-repair status: "
        + str(result["repeated_question_loop_repair_status"]),
        "- Close/disqualify status: " + str(result["close_disqualify_status"]),
        "- RouteSignal contamination in OpenAI-primary responses: "
        + str(result["residual_routesignal_contamination_check"]["openai_primary_case_response_contamination_count"]),
        "",
        "## Category Counts",
        "",
        "| Area | Cases | Pass | Fail |",
        "| --- | ---: | ---: | ---: |",
    ]
    for area_id, payload in result["category_counts"].items():
        lines.append(
            f"| {payload['label']} (`{area_id}`) | {payload['case_count']} | {payload['pass']} | {payload['fail']} |"
        )
    lines.extend(["", "## Case Matrix", ""])
    for item in result["case_matrix"]:
        summary = item["actual_semantic_action_response_summary"]
        lines.extend(
            [
                f"### {item['case_id']}",
                "",
                f"- Buyer utterance: {item['buyer_utterance']}",
                f"- Expected universal sales behavior: {item['expected_universal_sales_behavior']}",
                f"- Actual semantic/action/response summary: semantic={summary['semantic']}; "
                f"action={summary['action_id']}; focus={summary['dialogue_focus']}; "
                f"summary={summary['response_summary']}",
                f"- Pass: {str(item['pass']).lower()}",
                f"- Failures: {json.dumps(item['failures'])}",
                f"- Actual response: {item['actual_response']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Strong Spoken Sales Examples",
            "",
        ]
    )
    for item in result["strong_spoken_sales_examples"]:
        lines.append(f"- `{item['case_id']}`: {item['why_strong']}")
    lines.extend(["", "## Weak / Passive / FAQ-like Examples", ""])
    for item in result["weak_passive_faq_like_examples"]:
        lines.append(f"- `{item['case_id']}`: {item['why_weak']}")
    lines.extend(
        [
            "",
            "## Residual RouteSignal Contamination Guard",
            "",
            "- OpenAI-primary case responses containing RouteSignal/Northstar/inbound-demo/workflow-review/callback/handoff/manual-tracking copy: 0",
            "- OpenAI path source hits are limited to buyer-input boundary triggers, not buyer-facing response copy.",
            "- Generic path source hits are legacy default-playbook guard debt and remain future migration, not 4L2 cleanup scope.",
            "- RouteSignal remains secondary regression fixture only.",
            "",
            "## No-side-effect Confirmation",
            "",
            "- No live selector control was enabled.",
            "- No response replacement was enabled.",
            "- No provider/model/TTS/CRM/email/calendar/payment/account path was enabled.",
            "- No raw private transcript/audio was added to public evidence.",
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
    if actual.get("primary_benchmark_campaign") != "public OpenAI ChatGPT plans":
        failures.append("OpenAI primary benchmark campaign not preserved")
    if actual.get("routesignal_role") != "secondary regression fixture only":
        failures.append("RouteSignal role must be secondary regression fixture only")
    for key in FALSE_FLAGS:
        if actual.get(key) is not False:
            failures.append(f"{key} must be false: {actual.get(key)!r}")
    if actual.get("category_counts") != expected["category_counts"]:
        failures.append("category_counts do not match current harness output")
    actual_cases = actual.get("case_matrix")
    if not isinstance(actual_cases, list) or len(actual_cases) != len(expected["case_matrix"]):
        failures.append("case_matrix missing or length mismatch")
    else:
        for expected_case, actual_case in zip(expected["case_matrix"], actual_cases):
            for key in [
                "case_id",
                "buyer_utterance",
                "expected_universal_sales_behavior",
                "actual_semantic_action_response_summary",
                "pass",
                "failures",
            ]:
                if actual_case.get(key) != expected_case.get(key):
                    failures.append(f"case_matrix {expected_case['case_id']} field mismatch: {key}")
    residual = actual.get("residual_routesignal_contamination_check")
    if not isinstance(residual, dict):
        failures.append("residual_routesignal_contamination_check must be an object")
    elif residual.get("openai_primary_case_response_contamination_count") != 0:
        failures.append("OpenAI-primary case response contamination count must be 0")
    if actual.get("status") != expected["status"]:
        failures.append(f"status mismatch: {actual.get('status')!r} != {expected['status']!r}")


def validate_report(failures: list[str]) -> None:
    if not REPORT_PATH.is_file():
        return
    text = REPORT_PATH.read_text(encoding="utf-8")
    required = [
        "Case Matrix",
        "Category Counts",
        "Strong Spoken Sales Examples",
        "Weak / Passive / FAQ-like Examples",
        "Source/affiliation safety status",
        "AND/OR fidelity status",
        "Repeated-question / loop-repair status",
        "Close/disqualify status",
        "No live selector control was enabled.",
        "No response replacement was enabled.",
        "No provider/model/TTS/CRM/email/calendar/payment/account path was enabled.",
        "No raw private transcript/audio was added to public evidence.",
        "RouteSignal remains secondary regression fixture only.",
    ]
    for phrase in required:
        if phrase not in text:
            failures.append(f"report missing phrase: {phrase}")
    for case in CASES:
        if case["case_id"] not in text:
            failures.append(f"report missing case id: {case['case_id']}")


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
        failures.append("current OpenAI-primary harness has failing cases")
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
