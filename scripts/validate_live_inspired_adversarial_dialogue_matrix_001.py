#!/usr/bin/env python3
"""Validate the live-inspired adversarial dialogue matrix evidence."""

from __future__ import annotations

from collections import Counter
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "LIVE-INSPIRED-ADVERSARIAL-DIALOGUE-MATRIX-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILES = [
    "result.json",
    "report.md",
    "review_packet.md",
    "review_packet.json",
    "review_packet.jsonl",
]

REQUIRED_CAMPAIGNS = {
    "routesignal_live_demo",
    "synthetic-insurance-review",
    "synthetic-telecom-plan-review",
    "synthetic-automotive-service-review",
    "synthetic-membership-plan-review",
}

REQUIRED_FAMILIES = {
    "permission_weak_acknowledgement_variants",
    "direct_product_value_challenge_loops",
    "false_assumption_correction",
    "repeated_product_detail_scope_questions",
    "asr_near_miss_gap_phrases",
    "vague_affirmative_after_context",
    "agent_looping_complaints",
    "impact_before_clean_pain",
    "callback_time_too_early_or_ambiguous",
    "hostile_challenging_buyer",
    "human_context_interruption_pressure",
    "campaign_selector_wrong_campaign_contamination",
    "stop_refusal_pressure_test",
    "commercial_quality_stress",
    "mixed_intent_buyer_turns",
    "buyer_correction_contradiction_stress",
    "repeated_challenge_escalation",
    "buyer_says_agent_is_wrong",
    "early_callback_premature_scheduling",
    "price_budget_affordability_stress",
    "scope_boundary_regulated_detail_stress",
    "long_conversation_state_drift",
    "multi_campaign_contamination_stress",
    "human_context_sales_intent_hybrids",
    "asr_near_miss_invented_transcript_stress",
    "disallowed_persistence_after_stop",
    "commercial_pressure_close_strength_stress",
    "why_human_review_challenge",
    "repeated_answer_variation_anti_loop",
    "sales_realism_score_heuristics",
}

KNOWN_REPLAY_SCENARIOS = {
    "core-routesignal-permission-repeated-ack",
    "core-routesignal-asr-near-miss-callbacks",
    "core-routesignal-near-miss-impact",
    "core-routesignal-vague-followup",
    "core-routesignal-why-care",
    "core-insurance-false-assumption",
    "core-insurance-product-detail-repeat",
    "core-telecom-vague-positive-after-bad-experience",
    "core-telecom-plan-fit-boundary",
}

SIDE_EFFECT_KEYS = {
    "provider_calls_made",
    "local_llm_calls_made",
    "live_tts_used",
    "tts_provider_calls_made",
    "audio_file_created",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
    "customer_audio_uploaded_to_python_server",
    "customer_audio_uploaded_to_tts_provider",
}

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*[A-Za-z0-9_\-]{12,}"),
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(read_text(path))


def add_failure(failures: list[str], message: str) -> None:
    if message not in failures:
        failures.append(message)


def side_effect_failures(flags: dict[str, Any], prefix: str) -> list[str]:
    return [f"{prefix}: side-effect flag true: {key}" for key in SIDE_EFFECT_KEYS if bool(flags.get(key))]


def validate() -> dict[str, Any]:
    failures: list[str] = []
    missing = [name for name in REQUIRED_FILES if not (OUT_DIR / name).exists()]
    for name in missing:
        add_failure(failures, f"missing required output file: {name}")
    if missing:
        return {
            "checkpoint_id": CHECKPOINT_ID,
            "status": "failed",
            "failures": failures,
            "scenario_count": 0,
            "multi_turn_conversation_count": 0,
        }

    result = load_json(OUT_DIR / "result.json")
    packet = load_json(OUT_DIR / "review_packet.json")
    scenarios = packet.get("scenarios") or []

    jsonl_records: list[dict[str, Any]] = []
    for line_number, line in enumerate(read_text(OUT_DIR / "review_packet.jsonl").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            jsonl_records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            add_failure(failures, f"review_packet.jsonl line {line_number} does not parse: {exc}")

    scenario_count = len(scenarios)
    if scenario_count < 500:
        add_failure(failures, f"expected at least 500 scenario runs, got {scenario_count}")
    multi_turn_count = sum(1 for scenario in scenarios if len(scenario.get("buyer_script") or []) >= 3)
    if multi_turn_count < 80:
        add_failure(failures, f"expected at least 80 multi-turn conversations, got {multi_turn_count}")
    if len(jsonl_records) < scenario_count:
        add_failure(failures, f"expected JSONL records for every scenario, got {len(jsonl_records)} for {scenario_count}")

    campaigns = {str(scenario.get("campaign_id") or "") for scenario in scenarios}
    missing_campaigns = sorted(REQUIRED_CAMPAIGNS - campaigns)
    if missing_campaigns:
        add_failure(failures, f"missing campaign coverage: {missing_campaigns}")

    families = {str(scenario.get("scenario_family") or "") for scenario in scenarios}
    missing_families = sorted(REQUIRED_FAMILIES - families)
    if missing_families:
        add_failure(failures, f"missing scenario family coverage: {missing_families}")
    if len(families) < 14:
        add_failure(failures, f"expected at least 14 families, got {len(families)}")

    family_counts = Counter(str(scenario.get("scenario_family") or "") for scenario in scenarios)
    undercovered = {family: count for family, count in family_counts.items() if family in REQUIRED_FAMILIES and count < 10}
    if undercovered:
        add_failure(failures, f"families below 10 cases: {dict(sorted(undercovered.items()))}")

    core_gate = [scenario for scenario in scenarios if scenario.get("tier") == "core_gate"]
    core_failures = [scenario for scenario in core_gate if scenario.get("passed") is not True]
    if core_failures:
        add_failure(failures, f"core gate has failing scenarios: {[item.get('scenario_id') for item in core_failures[:10]]}")

    by_id = {str(scenario.get("scenario_id") or ""): scenario for scenario in scenarios}
    missing_replay = sorted(KNOWN_REPLAY_SCENARIOS - set(by_id))
    if missing_replay:
        add_failure(failures, f"missing known 4F2A replay scenarios: {missing_replay}")
    failing_replay = [scenario_id for scenario_id in KNOWN_REPLAY_SCENARIOS if scenario_id in by_id and by_id[scenario_id].get("passed") is not True]
    if failing_replay:
        add_failure(failures, f"known 4F2A replay scenarios failed: {failing_replay}")

    for scenario in scenarios:
        scenario_id = str(scenario.get("scenario_id") or "<missing>")
        if scenario.get("requires_human_sales_review") is not True:
            add_failure(failures, f"{scenario_id}: requires_human_sales_review is not true")
        if scenario.get("codex_assigned_final_sales_quality") is not False:
            add_failure(failures, f"{scenario_id}: Codex assigned final sales quality")
        failures.extend(side_effect_failures(scenario.get("side_effect_flags") or {}, scenario_id))
        for turn in scenario.get("turns") or []:
            failures.extend(side_effect_failures(turn.get("side_effect_flags") or {}, f"{scenario_id}/turn-{turn.get('turn_index')}"))

    packet_text = "\n".join(read_text(OUT_DIR / name) for name in REQUIRED_FILES if (OUT_DIR / name).exists())
    if EMAIL_PATTERN.search(packet_text):
        add_failure(failures, "raw email-like value found in packet")
    for pattern in SECRET_PATTERNS:
        if pattern.search(packet_text):
            add_failure(failures, f"secret-looking pattern found: {pattern.pattern}")

    side_effect_boundary = result.get("side_effect_boundary") or {}
    for key in (
        "provider_calls_made",
        "live_tts_calls_made",
        "local_llm_calls_made",
        "sends_email",
        "creates_calendar_event",
        "writes_crm",
        "opens_prod_102",
    ):
        if bool(side_effect_boundary.get(key)):
            add_failure(failures, f"side-effect boundary true: {key}")

    red_findings = int(result.get("red_finding_count") or 0)
    result_status = str(result.get("status") or "")
    if red_findings and result_status != "red_findings":
        add_failure(failures, "red findings exist but checkpoint status is not red_findings")
    if not red_findings and result_status != "pass":
        add_failure(failures, "no red findings but checkpoint status is not pass")
    if red_findings and not (result.get("top_failure_clusters") or []):
        add_failure(failures, "red findings exist but top_failure_clusters is empty")
    if red_findings and not (result.get("worst_conversations") or []):
        add_failure(failures, "red findings exist but worst_conversations is empty")

    summary = result.get("summary") or {}
    if int(summary.get("scenario_count") or 0) != scenario_count:
        add_failure(failures, "result summary scenario_count does not match packet")
    if int(summary.get("multi_turn_conversation_count") or 0) != multi_turn_count:
        add_failure(failures, "result summary multi_turn_conversation_count does not match packet")

    return {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "scenario_count": scenario_count,
        "multi_turn_conversation_count": multi_turn_count,
        "campaign_count": len(campaigns),
        "family_count": len(families),
        "core_gate_failure_count": len(core_failures),
        "red_finding_count": red_findings,
        "result_status": result_status,
    }


def main() -> None:
    outcome = validate()
    print(json.dumps(outcome, indent=2, sort_keys=True))
    if outcome["failures"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
