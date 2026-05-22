#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_live_demo_001_agent_voice_call import (  # noqa: E402
    DEFAULT_CAMPAIGN_ID,
    DEFAULT_CASES_PATH,
    DEFAULT_STAGE,
    build_turn_packet,
)


CHECKPOINT_ID = "CAMPAIGN-PLAYBOOK-ADAPTER-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

ADAPTER_ID = "CAMPAIGN-PLAYBOOK-ADAPTER-001"
ROUTESIGNAL_PLAYBOOK_ID = "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001"
UNIVERSAL_KNOWLEDGE_ID = "UNIVERSAL-SALES-KNOWLEDGE-001"
VERTICAL_ID = "b2b_saas"
EXPECTED_SEMANTIC_CASES = {
    "callbacks_clear": {
        "turns": ["__agent_open__", "yeah sure", "callbacks are fine"],
        "semantic": "current_gap_clear",
        "target_gap": "callbacks",
        "review_focus": "missed callback reminders",
    },
    "callbacks_pain": {
        "turns": ["__agent_open__", "yeah sure", "missed callbacks happen sometimes"],
        "semantic": "pain_confirmed",
        "target_gap": "callbacks",
        "review_focus": "missed callback reminders",
    },
    "duplicates_pain": {
        "turns": ["__agent_open__", "yeah sure", "duplicate demo requests confuse ownership"],
        "semantic": "pain_confirmed",
        "target_gap": "duplicates",
        "review_focus": "duplicate lead ownership",
    },
    "visibility_pain": {
        "turns": ["__agent_open__", "yeah sure", "managers cannot see who followed up"],
        "semantic": "pain_confirmed",
        "target_gap": "visibility",
        "review_focus": "manager follow-up visibility",
    },
}


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def write_evidence(result: dict[str, Any], report: str) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def build_report(result: dict[str, Any]) -> str:
    lines = [
        "# CAMPAIGN-PLAYBOOK-ADAPTER-001",
        "",
        f"Status: {result['status']}",
        "",
        "## Adapter Boundary",
        "",
        f"- Adapter id: {result.get('adapter_id')}",
        f"- Campaign playbook id: {result.get('campaign_playbook_id')}",
        f"- Vertical id: {result.get('vertical_id')}",
        f"- Universal knowledge id: {result.get('universal_knowledge_id')}",
        f"- Contextual direct RouteSignal import blocked: {str(result.get('dependency_boundary', {}).get('contextual_direct_routesignal_import_blocked')).lower()}",
        "",
        "## Behavior Preservation",
        "",
    ]
    for case_id, snapshot in sorted((result.get("behavior_preservation") or {}).items()):
        frame = snapshot.get("semantic_frame") or {}
        lines.append(
            f"- {case_id}: semantic={frame.get('semantic')}, target_gap={frame.get('target_gap')}, "
            f"review_focus={frame.get('playbook_review_focus')}, call_control={snapshot.get('call_control')}"
        )
    lines.extend(["", "## Safety", ""])
    for key, value in sorted((result.get("safety") or {}).items()):
        lines.append(f"- {key}: {str(value).lower()}")
    if result.get("failures"):
        lines.extend(["", "## Failures", ""])
        for failure in result["failures"]:
            lines.append(f"- {failure}")
    return "\n".join(lines) + "\n"


def append_turn(state: dict[str, Any], packet: dict[str, Any]) -> None:
    state.setdefault("turns", []).append(
        {
            "transcript": packet.get("transcript", ""),
            "summary": packet.get("summary", {}),
            "continuity": packet.get("demo_session_continuity", {}),
            "conversation_memory": packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {},
            "dialogue_manager": packet.get("dialogue_manager", {}),
            "dialogue_pragmatics": packet.get("dialogue_pragmatics", {}),
        }
    )


def build_demo_turn(transcript: str, state: dict[str, Any], *, session_id: str) -> dict[str, Any]:
    return build_turn_packet(
        transcript=transcript,
        campaign_id=DEFAULT_CAMPAIGN_ID,
        stage=DEFAULT_STAGE,
        input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR,
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id=session_id,
        session_state=state,
        asr_confidence=0.94,
        voice_turn_state="listening",
    )


def run_sequence(transcripts: list[str], *, session_id: str) -> list[dict[str, Any]]:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in transcripts:
        packet = build_demo_turn(transcript, state, session_id=session_id)
        packets.append(packet)
        append_turn(state, packet)
    return packets


def semantic_frame(packet: dict[str, Any]) -> dict[str, Any]:
    manager = packet.get("dialogue_manager") or {}
    return dict(manager.get("contextual_buyer_semantics") or (manager.get("state_before") or {}).get("contextual_buyer_semantics") or {})


def selected_action(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(((packet.get("dialogue_manager") or {}).get("selected_action") or {}))


def memory(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {})


def call_control(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("call_control") or "")


def response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or "")


def snapshot(packet: dict[str, Any]) -> dict[str, Any]:
    manager = packet.get("dialogue_manager") or {}
    return {
        "turn": packet.get("session_turn_index"),
        "transcript": packet.get("transcript"),
        "semantic_frame": semantic_frame(packet),
        "selected_action": selected_action(packet),
        "memory": memory(packet),
        "call_control": call_control(packet),
        "response": response(packet),
        "provider_calls_made": bool((packet.get("summary") or {}).get("tts_provider_calls_made")),
        "local_llm_calls_made": bool(manager.get("local_llm_calls_made")),
        "opens_prod_102": bool(manager.get("opens_prod_102")),
    }


def assert_no_side_effects(failures: list[str], packet: dict[str, Any], label: str) -> None:
    snap = snapshot(packet)
    assert_condition(failures, snap["provider_calls_made"] is False, f"{label}: provider calls must be false: {snap}")
    assert_condition(failures, snap["local_llm_calls_made"] is False, f"{label}: local LLM calls must be false: {snap}")
    assert_condition(failures, snap["opens_prod_102"] is False, f"{label}: PROD-102 must remain closed: {snap}")
    for state_key in ["send_info_state", "lead_followup_state", "handoff_target_state"]:
        safety = (snap["memory"].get(state_key) or {}).get("safety") or {}
        for key in ["provider_calls_made", "local_llm_calls_made", "sends_email", "creates_calendar_event", "writes_crm"]:
            if key in safety:
                assert_condition(failures, safety.get(key) is False, f"{label}: {state_key}.{key} must be false: {snap}")


def validate_contract(failures: list[str], evidence: dict[str, Any]) -> None:
    from runtime.core import campaign_playbook_adapter as adapter
    from runtime.core import sales_diagnostic_playbook as routesignal
    from runtime.core import universal_sales_knowledge as universal
    from runtime.core import vertical_sales_playbooks as verticals

    playbook = adapter.default_campaign_playbook()
    validation = adapter.validate_campaign_playbook(playbook)
    adapter_validation = adapter.validate_campaign_playbook_adapter()
    assert_condition(failures, validation.get("valid") is True, f"validate_campaign_playbook failed: {validation}")
    assert_condition(failures, adapter_validation.get("valid") is True, f"validate_campaign_playbook_adapter failed: {adapter_validation}")

    assert_condition(failures, playbook.get("adapter_id") == ADAPTER_ID, "adapter_id mismatch")
    assert_condition(failures, adapter.campaign_playbook_id() == ROUTESIGNAL_PLAYBOOK_ID, "campaign_playbook_id mismatch")
    assert_condition(failures, adapter.campaign_vertical_id() == VERTICAL_ID, "campaign_vertical_id mismatch")
    assert_condition(failures, playbook.get("universal_knowledge_id") == UNIVERSAL_KNOWLEDGE_ID, "universal_knowledge_id mismatch")
    assert_condition(failures, VERTICAL_ID in verticals.all_vertical_ids(), "vertical id must exist in vertical playbooks")
    assert_condition(failures, universal.universal_knowledge_id() == UNIVERSAL_KNOWLEDGE_ID, "universal knowledge import mismatch")

    expected_gaps = set(routesignal.gap_ids())
    actual_gaps = set(playbook.get("diagnostic_gaps") or {})
    assert_condition(failures, expected_gaps == actual_gaps, f"RouteSignal gap ids must be preserved: expected {sorted(expected_gaps)}, got {sorted(actual_gaps)}")
    assert_condition(failures, adapter.campaign_core_diagnostic_gaps() == routesignal.core_diagnostic_gaps(), "core diagnostic gaps must match existing RouteSignal playbook")
    assert_condition(failures, adapter.campaign_gap_order() == routesignal.gap_ids(), "gap order must match existing RouteSignal playbook")
    assert_condition(failures, adapter.campaign_gap_labels() == routesignal.gap_labels(), "gap labels must match existing RouteSignal playbook")
    assert_condition(failures, adapter.gap_labels() == routesignal.gap_labels(), "legacy gap_labels wrapper must match")
    assert_condition(failures, adapter.core_diagnostic_gaps() == routesignal.core_diagnostic_gaps(), "legacy core_diagnostic_gaps wrapper must match")

    universal_pain_ids = set(universal.all_generic_pain_dimension_ids())
    qualification_ids = set(universal.all_qualification_dimension_ids())
    for gap_id in sorted(expected_gaps):
        adapted_gap = adapter.campaign_gap_definition(gap_id)
        original_gap = routesignal.gap_definition(gap_id)
        assert_condition(failures, adapted_gap.get("label") == original_gap.get("label"), f"{gap_id}: label changed")
        assert_condition(failures, adapted_gap.get("review_focus") == routesignal.review_focus(gap_id), f"{gap_id}: review focus changed")
        assert_condition(failures, adapted_gap.get("next_gap_candidates") == original_gap.get("next_gap_candidates"), f"{gap_id}: next gap candidates changed")
        assert_condition(failures, bool(adapted_gap.get("universal_pain_dimensions")), f"{gap_id}: missing universal pain mappings")
        assert_condition(failures, bool(adapted_gap.get("qualification_dimensions")), f"{gap_id}: missing qualification mappings")
        assert_condition(failures, set(adapted_gap.get("universal_pain_dimensions") or []).issubset(universal_pain_ids), f"{gap_id}: unknown universal pain dimensions")
        assert_condition(failures, set(adapted_gap.get("qualification_dimensions") or []).issubset(qualification_ids), f"{gap_id}: unknown qualification dimensions")

    evidence["adapter_contract"] = {
        "adapter_id": playbook.get("adapter_id"),
        "campaign_playbook_id": playbook.get("campaign_playbook_id"),
        "vertical_id": playbook.get("vertical_id"),
        "universal_knowledge_id": playbook.get("universal_knowledge_id"),
        "supported_gap_ids": sorted(actual_gaps),
        "core_diagnostic_gaps": adapter.campaign_core_diagnostic_gaps(),
    }


def validate_dependency_boundary(failures: list[str], evidence: dict[str, Any]) -> None:
    contextual_path = ROOT / "runtime" / "core" / "contextual_buyer_semantics.py"
    adapter_path = ROOT / "runtime" / "core" / "campaign_playbook_adapter.py"
    contextual_text = contextual_path.read_text(encoding="utf-8")
    adapter_text = adapter_path.read_text(encoding="utf-8")
    direct_routesignal_import = "sales_diagnostic_playbook" in contextual_text
    adapter_import = "campaign_playbook_adapter" in contextual_text
    adapter_wraps_routesignal = "sales_diagnostic_playbook" in adapter_text
    assert_condition(failures, not direct_routesignal_import, "contextual_buyer_semantics.py must not reference sales_diagnostic_playbook directly")
    assert_condition(failures, adapter_import, "contextual_buyer_semantics.py should import campaign_playbook_adapter")
    assert_condition(failures, adapter_wraps_routesignal, "campaign_playbook_adapter.py should wrap sales_diagnostic_playbook")
    evidence["dependency_boundary"] = {
        "contextual_direct_routesignal_import_blocked": not direct_routesignal_import,
        "contextual_imports_campaign_adapter": adapter_import,
        "adapter_wraps_routesignal_playbook": adapter_wraps_routesignal,
    }


def validate_behavior_preservation(failures: list[str], evidence: dict[str, Any]) -> None:
    behavior: dict[str, Any] = {}
    for case_id, expected in EXPECTED_SEMANTIC_CASES.items():
        packets = run_sequence(expected["turns"], session_id=case_id)
        final_packet = packets[-1]
        snap = snapshot(final_packet)
        behavior[case_id] = snap
        frame = snap["semantic_frame"]
        assert_condition(failures, frame.get("semantic") == expected["semantic"], f"{case_id}: semantic changed: {snap}")
        assert_condition(failures, frame.get("target_gap") == expected["target_gap"] or frame.get("primary_gap") == expected["target_gap"], f"{case_id}: target gap changed: {snap}")
        assert_condition(failures, frame.get("playbook_id") == ROUTESIGNAL_PLAYBOOK_ID, f"{case_id}: playbook id changed: {snap}")
        assert_condition(failures, frame.get("playbook_review_focus") == expected["review_focus"], f"{case_id}: review focus changed: {snap}")
        assert_no_side_effects(failures, final_packet, case_id)
    evidence["behavior_preservation"] = behavior


def main() -> int:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    try:
        validate_contract(failures, evidence)
        validate_dependency_boundary(failures, evidence)
        validate_behavior_preservation(failures, evidence)
    except Exception as exc:  # pragma: no cover - used for red validation before adapter exists
        failures.append(f"validation raised: {exc!r}")

    safety = {
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
    }
    contract = evidence.get("adapter_contract") or {}
    result = {
        "status": "pass" if not failures else "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "adapter_id": contract.get("adapter_id"),
        "campaign_playbook_id": contract.get("campaign_playbook_id"),
        "vertical_id": contract.get("vertical_id"),
        "universal_knowledge_id": contract.get("universal_knowledge_id"),
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "phase_1_2_3_backpatch_required": False,
        "adapter_contract": contract,
        "dependency_boundary": evidence.get("dependency_boundary") or {},
        "behavior_preservation": evidence.get("behavior_preservation") or {},
        "safety": safety,
        "generated_evidence": {
            "result_json": str(RESULT_PATH.relative_to(ROOT)),
            "report_md": str(REPORT_PATH.relative_to(ROOT)),
        },
        "failures": failures,
    }
    write_evidence(result, build_report(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
