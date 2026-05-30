from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "RUNTIME-ACTION-METADATA-DISCOVERY-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
EXPERIMENT_ID = "RUNTIME-ACTION-METADATA-DISCOVERY-001"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def discovered_sources() -> list[dict[str, Any]]:
    return [
        {
            "path": "runtime/campaigns/public_openai_chatgpt_plans_dialogue.py",
            "functions": [
                "_next_best_action_for_state",
                "_commercial_sales_state",
                "memory_update_for_turn",
                "classify_turn",
            ],
            "usable_metadata": [
                "next_commercial_action",
                "buyer_decision_stage",
                "active_decision_frame",
                "current_buyer_question_type",
                "last_recommendation_given",
                "recommendation_confidence",
                "buyer_fit_level",
                "commercial_stage",
            ],
            "notes": "Campaign logic already names commercial stage, next action, fit, recommendation path, and buyer question type.",
        },
        {
            "path": "runtime/core/contextual_buyer_semantics.py",
            "functions": ["_frame", "classify_contextual_buyer_semantics"],
            "usable_metadata": [
                "semantic",
                "action_id",
                "dialogue_focus",
                "response_strategy",
                "response_variation_key",
                "next_best_sales_action",
                "should_recommend",
                "should_close",
                "should_disqualify",
                "evidence",
            ],
            "notes": "Semantic frames expose non-generative decision fields and candidate response hashes can be derived without storing raw text.",
        },
        {
            "path": "runtime/core/realtime_turns.py",
            "functions": ["build_runtime_decision", "run_case"],
            "usable_metadata": [
                "runtime_decision",
                "response_mode",
                "call_control",
                "selected_strategy",
                "next_action",
                "sales_difficulty",
                "interest_state",
            ],
            "notes": "Replay decisions expose call control and strategy fields suitable for offline comparison.",
        },
        {
            "path": "runtime/core/live_voice_session_policy.py",
            "functions": ["policy helpers only"],
            "usable_metadata": ["boundary markers", "terminal markers", "repair markers"],
            "notes": "Useful as a secondary signal reference, but not selected as the primary extraction source because it is response-adjacent.",
        },
    ]


def main() -> int:
    required_paths = [
        ROOT / "runtime" / "campaigns" / "public_openai_chatgpt_plans_dialogue.py",
        ROOT / "runtime" / "core" / "contextual_buyer_semantics.py",
        ROOT / "runtime" / "core" / "realtime_turns.py",
        ROOT / "runtime" / "core" / "live_voice_session_policy.py",
    ]
    missing = [rel(path) for path in required_paths if not path.is_file()]
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass" if not missing else "fail",
        "missing_source_files": missing,
        "discovered_metadata_sources": discovered_sources(),
        "proposed_metadata_extraction_source": "runtime_result passed into shadow_runtime_logger, with fallback discovery across runtime_decision, semantic_frame, and commercial_state dictionaries",
        "recommended_mapping_approach": "Map extracted runtime metadata to controlled action_selector action_id labels through runtime_to_action_label_map.json, then compare in read-only shadow mode.",
        "metadata_contract": "runtime/action_selector/runtime_action_metadata_contract.py",
        "mapping_file": "runtime/action_selector/runtime_to_action_label_map.json",
        "extractor_file": "runtime/action_selector/runtime_action_metadata_extractor.py",
        "read_only": True,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "side_effects_allowed": False,
        "live_runtime_wiring_allowed": False,
        "memory_mutation_allowed": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "ultravox_calls_made": False,
        "elevenlabs_calls_made": False,
        "local_llm_calls_made": False,
        "ollama_calls_made": False,
        "tts_calls_made": False,
        "raw_private_data": False,
    }
    write_json(RESULT_PATH, result)
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Proposed extraction source: {result['proposed_metadata_extraction_source']}",
        f"- Recommended mapping approach: {result['recommended_mapping_approach']}",
        "- Runtime behavior changed: false",
        "- Response text changed: false",
        "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama/TTS calls: false",
        "- Raw private data: false",
        "",
        "## Sources",
        "",
    ]
    for source in result["discovered_metadata_sources"]:
        lines.append(f"- {source['path']}: {', '.join(source['usable_metadata'])}")
    write_text(REPORT_PATH, "\n".join(lines))
    print(json.dumps({"status": result["status"], "source_count": len(result["discovered_metadata_sources"])}, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
