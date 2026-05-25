#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.campaigns import public_openai_chatgpt_plans_dialogue as public_plan  # noqa: E402
from runtime.core import campaign_registry  # noqa: E402
from runtime.core import dialogue_manager  # noqa: E402
from runtime.core import live_voice_session_policy as session_policy  # noqa: E402


CHECKPOINT_ID = "PUBLIC-OPENAI-MEMORY-PROGRESSION-001"
FIXTURE_PATH = ROOT / "runtime" / "campaigns" / "examples" / "public-openai-chatgpt-plans.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
STATE_KEY = "openai_chatgpt_plan_state"

SIDE_EFFECTS = {
    "provider_calls_made": False,
    "local_llm_calls_made": False,
    "sends_email": False,
    "creates_calendar_event": False,
    "writes_crm": False,
    "opens_prod_102": False,
    "live_tts_calls_made": False,
}

REPEATED_LIMIT_QUESTION_RE = re.compile(r"are you mostly hitting limits, or just trying to choose before upgrading", re.I)
USE_CASE_RESET_RE = re.compile(r"plan fit still needs the actual use case|actual use case|what would you mainly use", re.I)
ADOPTION_RESET_RE = re.compile(r"using chatgpt today.*another ai tool.*not using ai|chatgpt today.*another ai tool", re.I)
RAW_URL_RE = re.compile(r"https?://|www\.", re.I)
FAKE_SIDE_EFFECT_RE = re.compile(r"\b(i sent|emailed|booked|created .*calendar|created .*crm|sent you)\b", re.I)
INTERNAL_RE = re.compile(r"openai_[a-z_]+|known_use_case|route ?signal|human_followup_owner|appointment_target", re.I)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def sha12(text: str) -> str:
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()[:12]


def load_fixture() -> dict[str, Any]:
    return campaign_registry.load_campaign_config(FIXTURE_PATH)


def previous_question(turns: list[dict[str, Any]]) -> str | None:
    if not turns:
        return None
    return str((turns[-1].get("summary") or {}).get("final_response") or "") or None


def empty_action(frame: dict[str, Any], response: str) -> dict[str, Any]:
    return {
        "state_before": {"contextual_buyer_semantics": frame},
        "continuity": {
            "reason": str(frame.get("semantic") or "public_plan_no_semantic"),
            "dialogue_focus": str(frame.get("dialogue_focus") or "qualification"),
            "candidate_response": response,
        },
        "selected_action": {"source": "contextual_buyer_semantics"},
    }


def classify_response(campaign: dict[str, Any], transcript: str, state: dict[str, Any]) -> tuple[dict[str, Any], str]:
    turns = list(state.get("turns") or [])
    prev = previous_question(turns)
    frame = public_plan.classify_turn(
        campaign=campaign,
        transcript=transcript,
        normalized=normalize(transcript),
        turns=turns,
        previous_question=prev,
        previous_question_type=session_policy.question_type_from_response(prev or ""),
        conversation_stage="qualification",
        active_gap=None,
        confirmed_gaps=[],
        cleared_gaps=[],
        pending_callback=False,
        pending_appointment=False,
        candidate_gaps=[],
    )
    if not frame:
        response = "I can keep checking, but plan fit still needs the actual use case."
        frame = {
            "semantic": "public_plan_no_specialized_frame",
            "dialogue_focus": "qualification",
            "candidate_response": response,
            "target_gap": None,
            "applied": False,
        }
    response = str(frame.get("candidate_response") or "")
    action = empty_action(frame, response)
    memory = dialogue_manager.build_conversation_memory(
        action=action,
        session_state=state,
        transcript=transcript,
        final_response=response,
        campaign=campaign,
    )
    turn = {
        "transcript": transcript,
        "summary": {"final_response": response, "transcript": transcript},
        "continuity": {"dialogue_focus": str(frame.get("dialogue_focus") or "qualification")},
        "conversation_memory": memory,
        "dialogue_manager": {"final_response": response, "final_response_source": "contextual_buyer_semantics"},
    }
    state.setdefault("turns", []).append(turn)
    return turn, response


def state_memory(state: dict[str, Any]) -> dict[str, Any]:
    for turn in reversed(state.get("turns") or []):
        memory = turn.get("conversation_memory") or {}
        value = memory.get(STATE_KEY)
        if isinstance(value, dict):
            return value
    return {}


def run_sequence(campaign: dict[str, Any], turns: list[str]) -> dict[str, Any]:
    state: dict[str, Any] = {"turns": []}
    responses: list[str] = []
    for transcript in turns:
        _, response = classify_response(campaign, transcript, state)
        responses.append(response)
    return {
        "turns": turns,
        "responses": responses,
        "final_response": responses[-1] if responses else "",
        "final_memory": state_memory(state),
        "state": state,
    }


def force_duplicate_repair(campaign: dict[str, Any], sequence: list[str], duplicate_response: str | None = None) -> dict[str, Any]:
    run = run_sequence(campaign, sequence)
    state = run["state"]
    response = duplicate_response or run["responses"][-1]
    guard = session_policy.pre_speech_conversation_stability_guard(
        transcript=sequence[-1],
        session_state=state,
        language="en",
        candidate_response=response,
        conversation_memory=(state.get("turns") or [{}])[-1].get("conversation_memory") or {},
        campaign=campaign,
    )
    return {"run": run, "guard": guard, "repair_response": str(guard.get("candidate_response") or "")}


def scenario(id: str, group: str, turns: list[str], expectation: str, *, duplicate: bool = False) -> dict[str, Any]:
    return {
        "id": id,
        "group": group,
        "turns": turns,
        "expectation": expectation,
        "duplicate": duplicate,
        "multi_turn": len(turns) > 1,
    }


def build_scenarios() -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []

    use_cases = [
        "I use it for coding and writing",
        "ChatGPT is for coding and writing",
        "mostly coding and writing",
        "personal coding and writing",
        "I use chat gpt for coding and writing",
        "I use chachu PT for coding and writing",
    ]
    plus_questions = ["Is Plus enough?", "is Plus going to be enough for my use case", "should I start with Plus", "Plus or Pro?"]
    limit_answers = [
        "I am mostly hitting limits and it is frustrating",
        "mostly hitting limits",
        "I am hitting limits",
        "limits are frustrating",
        "already hitting limits",
        "running out of limits",
        "blocked by limits",
        "a bit frustrating",
    ]
    heavy_answers = [
        "a little bit on the heavy side",
        "a little heavy",
        "heavy side",
        "I use it heavily",
        "heavy daily use",
        "every day",
        "advanced tools all week",
        "somewhere in the middle but leaning heavy",
    ]
    price_questions = [
        "how much are the plans",
        "before I move forward I want the price",
        "what are the prices",
        "how much is Plus",
        "how much is Pro",
        "tell me the public plan structure and price",
        "answer the price directly",
    ]

    idx = 1
    for use_case in use_cases:
        for question in plus_questions[:2]:
            for answer in limit_answers[:4]:
                scenarios.append(
                    scenario(
                        f"answered-intensity-{idx:03d}",
                        "answered_intensity_question",
                        [use_case, question, answer],
                        "limit_answer_advances",
                    )
                )
                idx += 1

    for i, answer in enumerate(heavy_answers * 3, start=1):
        scenarios.append(
            scenario(
                f"heavy-side-known-use-{i:03d}",
                "heavy_side_after_known_use_case",
                ["I use it for coding and writing", "somewhere in the middle but is Plus enough", answer],
                "heavy_known_use",
            )
        )

    already_phrases = ["I already told you", "I already said that", "like I said", "you asked that already"]
    for i, phrase in enumerate(already_phrases * 5, start=1):
        scenarios.append(
            scenario(
                f"already-told-{i:03d}",
                "repeated_answer_already_told",
                ["I use it for coding and writing", "a little heavy", phrase, "yes, hitting limits"],
                "already_told_progresses",
            )
        )

    for i, price in enumerate(price_questions * 3, start=1):
        scenarios.append(
            scenario(
                f"price-known-state-{i:03d}",
                "price_after_known_state",
                ["I use it for coding and writing", "heavy", "hitting limits", price],
                "price_known_state",
            )
        )

    pro_turns = [
        "I am trying to compare 100 and 200 dollar Pro tiers",
        "which Pro should I use",
        "I use heavily but do not know how heavy",
        "is the 200 dollar Pro tier necessary",
        "should I use 100 or 200 dollar Pro",
    ]
    for i, turn in enumerate(pro_turns * 4, start=1):
        scenarios.append(scenario(f"pro-tier-{i:03d}", "pro_tier_comparison", [turn], "pro_tier"))

    signup_turns = ["how do I sign up", "where do I upgrade", "show me the official page", "sounds good how do I sign up"]
    for i, close in enumerate(signup_turns * 5, start=1):
        scenarios.append(
            scenario(
                f"signup-known-state-{i:03d}",
                "signup_after_known_recommendation",
                ["coding/writing", "heavy", "hitting limits", close],
                "signup_known_state",
            )
        )

    duplicate_sequences = [
        ["I use it for coding and writing", "Is Plus enough?", "I am mostly hitting limits and it is frustrating"],
        ["I use it for coding and writing", "a little heavy", "I already told you"],
        ["I use it for coding and writing", "heavy", "hitting limits"],
        ["I use it for coding and writing", "how much are the plans", "before I move forward I want the price"],
        ["I use it for coding and writing", "heavy", "how do I sign up"],
    ]
    for i, turns in enumerate(duplicate_sequences * 4, start=1):
        scenarios.append(
            scenario(
                f"duplicate-repair-{i:03d}",
                "duplicate_response_repair_regression",
                turns,
                "duplicate_repair_advances",
                duplicate=True,
            )
        )

    negative_controls = [
        (["I use it for coding and writing", "actually this is for a team"], "team_branch"),
        (["I am not using AI yet"], "no_ai_branch"),
        (["Free is enough"], "free_branch"),
        (["I use it for coding and writing", "is API included"], "api_boundary"),
        (["are you OpenAI"], "affiliation"),
        (["I use another AI tool", "is Plus enough"], "other_ai_branch"),
        (["we need SSO and procurement"], "enterprise_branch"),
        (["I only use it occasionally"], "light_branch"),
        (["just choosing before upgrading"], "choosing_before_upgrade"),
        (["I am mostly hitting limits"], "limit_without_use_case"),
    ]
    for i, (turns, expectation) in enumerate(negative_controls * 3, start=1):
        scenarios.append(scenario(f"negative-control-{i:03d}", "negative_controls", turns, expectation))

    return scenarios


def check_common(item: dict[str, Any], text: str, memory: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if not text.strip():
        failures.append("empty final response")
    if RAW_URL_RE.search(text):
        failures.append("raw URL spoken")
    if FAKE_SIDE_EFFECT_RE.search(text):
        failures.append("fake send/book/CRM side effect")
    if INTERNAL_RE.search(text):
        failures.append("internal field or cross-campaign leakage")
    if "coding" in " ".join(item["turns"]).lower() and not memory:
        failures.append("missing persisted OpenAI campaign memory")
    return failures


def check_expectation(item: dict[str, Any], run: dict[str, Any]) -> list[str]:
    text = run["final_response"]
    lowered = normalize(text)
    memory = run["final_memory"]
    expectation = item["expectation"]
    failures = check_common(item, text, memory)
    state_text = json.dumps(memory, sort_keys=True).lower()

    if expectation == "limit_answer_advances":
        if REPEATED_LIMIT_QUESTION_RE.search(text):
            failures.append("repeated answered hitting-limits question")
        if "pro" not in lowered or "limit" not in lowered:
            failures.append("limit-pain answer did not strengthen Pro recommendation")
        if memory.get("openai_limit_pain") is not True:
            failures.append("openai_limit_pain not persisted true")
        if memory.get("openai_usage_intensity") != "heavy":
            failures.append("openai_usage_intensity not persisted heavy")
        if "coding" not in state_text or "writing" not in state_text:
            failures.append("known coding/writing use case not preserved")
        if text.count("?") > 1:
            failures.append("more than one next action question")

    elif expectation == "heavy_known_use":
        if USE_CASE_RESET_RE.search(text):
            failures.append("known use case was ignored or reset")
        if "plus" not in lowered or "pro" not in lowered:
            failures.append("heavy known-use answer did not compare Plus and Pro")
        if memory.get("openai_usage_intensity") != "heavy":
            failures.append("heavy-side answer did not persist heavy intensity")
        if "coding" not in state_text or "writing" not in state_text:
            failures.append("known coding/writing use case missing from memory")

    elif expectation == "already_told_progresses":
        if USE_CASE_RESET_RE.search(text) or REPEATED_LIMIT_QUESTION_RE.search(text):
            failures.append("already-told path re-asked a known slot")
        if "pro" not in lowered or "limit" not in lowered:
            failures.append("already-told path did not progress after hitting limits")

    elif expectation == "price_known_state":
        if "20" not in lowered and "100" not in lowered and "200" not in lowered:
            failures.append("price answer did not answer price directly")
        if "source of truth" not in lowered:
            failures.append("price answer missed source-of-truth caveat")
        if "limit" not in lowered or "pro" not in lowered or "plus" not in lowered:
            failures.append("price answer did not tie price to known Plus/Pro state")
        if ADOPTION_RESET_RE.search(text):
            failures.append("price answer reset to adoption discovery")
        if memory.get("openai_price_answered") is not True:
            failures.append("openai_price_answered not persisted true")

    elif expectation == "pro_tier":
        if not re.search(r"100|200|pro", lowered):
            failures.append("Pro tier answer did not address Pro tiers")
        if "plus is usually" in lowered:
            failures.append("Pro tier answer regressed to generic Plus/Pro paragraph")
        if text.count("?") > 1:
            failures.append("Pro tier answer asked more than one clarifying question")

    elif expectation == "signup_known_state":
        if "official chatgpt plans page" not in lowered and "profile upgrade flow" not in lowered:
            failures.append("signup close did not use official self-serve path")
        if "pro" not in lowered or "limit" not in lowered:
            failures.append("signup close omitted known Pro/limit recommendation")
        if RAW_URL_RE.search(text) or FAKE_SIDE_EFFECT_RE.search(text):
            failures.append("signup close used raw URL or fake side effect")

    elif expectation == "duplicate_repair_advances":
        guard = run.get("duplicate_guard") or {}
        repair = normalize(str(guard.get("candidate_response") or ""))
        if guard.get("applied") is not True:
            failures.append("duplicate guard did not apply")
        if "actual use case" in repair or "plan fit still needs" in repair:
            failures.append("duplicate repair regressed to generic use-case fallback")
        if "pro" not in repair and "price" not in repair and "official chatgpt plans page" not in repair:
            failures.append("duplicate repair did not advance using known OpenAI state")
        prior = [normalize(response) for response in run["responses"]]
        if repair and repair in prior:
            failures.append("duplicate repair repeated an exact prior response")

    elif expectation == "team_branch":
        if "business" not in lowered and "enterprise" not in lowered:
            failures.append("team change did not route to Business/Enterprise")
    elif expectation == "no_ai_branch":
        if "no pressure" not in lowered and "not start with a paid plan" not in lowered:
            failures.append("no-AI branch did not avoid paid-plan push")
    elif expectation == "free_branch":
        if "free" not in lowered or "paid" not in lowered:
            failures.append("Free-enough branch did not preserve no-fit/low-pressure guidance")
    elif expectation == "api_boundary":
        if "api" not in lowered or "separate" not in lowered:
            failures.append("API boundary not preserved")
        if memory.get("openai_api_boundary_answered") is not True:
            failures.append("openai_api_boundary_answered not persisted true")
    elif expectation == "affiliation":
        if not re.search(r"not .*openai|not calling from openai|not representing openai|public-data simulation", lowered):
            failures.append("OpenAI affiliation disclaimer not preserved")
    elif expectation == "other_ai_branch":
        if "current" not in lowered and "switch" not in lowered and "may not need" not in lowered:
            failures.append("other-AI branch did not avoid forced ChatGPT upgrade")
    elif expectation == "enterprise_branch":
        if "enterprise" not in lowered and "contact sales" not in lowered:
            failures.append("enterprise branch missing")
    elif expectation == "light_branch":
        if "free" not in lowered and "light" not in lowered:
            failures.append("light-use branch did not prefer Free/basic path")
    elif expectation == "choosing_before_upgrade":
        if REPEATED_LIMIT_QUESTION_RE.search(text):
            failures.append("choosing-before-upgrade answer repeated the same question")
    elif expectation == "limit_without_use_case":
        if "what would you mainly use" not in lowered and "coding" not in lowered:
            failures.append("limit without use case should still ask one use-case question")

    return failures


def run_scenario(campaign: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    if item.get("duplicate"):
        duplicate = force_duplicate_repair(campaign, item["turns"])
        run = duplicate["run"]
        run["duplicate_guard"] = duplicate["guard"]
    else:
        run = run_sequence(campaign, item["turns"])
    failures = check_expectation(item, run)
    return {
        "id": item["id"],
        "group": item["group"],
        "expectation": item["expectation"],
        "turn_count": len(item["turns"]),
        "multi_turn": item["multi_turn"],
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "final_response": run["final_response"],
        "final_response_hash": sha12(run["final_response"]),
        "final_memory": run["final_memory"],
        "duplicate_guard": run.get("duplicate_guard"),
    }


def main() -> None:
    campaign = load_fixture()
    scenarios = build_scenarios()
    traces = [run_scenario(campaign, item) for item in scenarios]
    failed = [trace for trace in traces if trace["status"] != "pass"]
    group_counts = Counter(trace["group"] for trace in traces)
    multi_turn_count = sum(1 for trace in traces if trace["multi_turn"])
    expectation_counts = Counter(trace["expectation"] for trace in traces)
    status_by_group: dict[str, Counter[str]] = defaultdict(Counter)
    for trace in traces:
        status_by_group[trace["group"]][trace["status"]] += 1
    failures: list[str] = []
    if len(scenarios) < 120:
        failures.append(f"at least 120 scenarios required, got {len(scenarios)}")
    if multi_turn_count < 85:
        failures.append(f"at least 85 multi-turn scenarios required, got {multi_turn_count}")
    required_groups = {
        "answered_intensity_question",
        "heavy_side_after_known_use_case",
        "repeated_answer_already_told",
        "price_after_known_state",
        "pro_tier_comparison",
        "signup_after_known_recommendation",
        "duplicate_response_repair_regression",
        "negative_controls",
    }
    missing = sorted(required_groups - set(group_counts))
    if missing:
        failures.append(f"missing scenario groups: {missing}")
    failures.extend(f"{trace['id']}: {'; '.join(trace['failures'])}" for trace in failed)

    result = {
        "status": "pass" if not failures else "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "scenario_count": len(scenarios),
        "multi_turn_scenario_count": multi_turn_count,
        "group_counts": dict(sorted(group_counts.items())),
        "expectation_counts": dict(sorted(expectation_counts.items())),
        "status_by_group": {group: dict(counter) for group, counter in sorted(status_by_group.items())},
        "failed_count": len(failed),
        "failed_sample": failed[:20],
        "trace_sample": traces[:24],
        **SIDE_EFFECTS,
        "failures": failures,
    }
    report = "\n".join(
        [
            f"# {CHECKPOINT_ID}",
            "",
            f"- Status: `{result['status']}`",
            f"- Scenarios: `{result['scenario_count']}`",
            f"- Multi-turn scenarios: `{result['multi_turn_scenario_count']}`",
            f"- Failed: `{result['failed_count']}`",
            f"- Side effects false: `{all(result[key] is False for key in SIDE_EFFECTS)}`",
            "",
            "## Groups",
            "",
            *[f"- `{group}`: {dict(counter)}" for group, counter in sorted(status_by_group.items())],
            "",
        ]
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(
        json.dumps(
            {
                "status": result["status"],
                "checkpoint_id": CHECKPOINT_ID,
                "scenario_count": len(scenarios),
                "multi_turn": multi_turn_count,
                "failed": len(failed),
            },
            indent=2,
            sort_keys=True,
        )
    )
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
