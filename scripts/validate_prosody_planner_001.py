#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLANNER_PATH = ROOT / "runtime" / "audio_backends" / "prosody_planner.py"
TAXONOMY_PATH = ROOT / "runtime" / "audio_backends" / "prosody_sales_taxonomy.json"
MAPPING_PATH = ROOT / "runtime" / "audio_backends" / "sales_prosody_mapping.json"
RULES_PATH = ROOT / "runtime" / "audio_backends" / "prosody_composition_rules.json"
POLICY_PATH = ROOT / "runtime" / "audio_backends" / "prosody_backend_mapping_policy.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "PROSODY-PLANNER-PROTOTYPE-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "PROSODY-PLANNER-PROTOTYPE-001" / "report.md"

REQUIRED_PLAN_FIELDS = {
    "voice_intent",
    "selected_prosody_labels",
    "pace",
    "warmth",
    "confidence",
    "energy",
    "pause_policy",
    "emphasis_terms",
    "avoid",
    "backend_hints",
    "fish_inspired_tags_internal_only",
    "spoken_text_tag_injection_allowed",
    "live_runtime_wiring_changed",
}
FORBIDDEN_PLANNER_TEXT = (
    "requests.",
    "openai",
    "elevenlabs",
    "fish_speech",
    "fishaudio",
    "kokoro",
    "ollama",
    "transformers",
    "subprocess",
    "socket",
    "http",
)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AssertionError(f"missing file: {rel(path)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"{rel(path)} must be a JSON object")
    return payload


def has_raw_tag(text: str) -> bool:
    return bool(re.search(r"\[[^\]\n]{2,80}\]", text))


def load_planner_module() -> Any:
    if not PLANNER_PATH.is_file():
        raise AssertionError(f"missing file: {rel(PLANNER_PATH)}")
    module_text = PLANNER_PATH.read_text(encoding="utf-8").lower()
    for forbidden in FORBIDDEN_PLANNER_TEXT:
        if forbidden in module_text:
            raise AssertionError(f"planner contains forbidden provider/inference/network token: {forbidden}")
    spec = importlib.util.spec_from_file_location("prosody_planner_under_test", PLANNER_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("could not import prosody planner")
    module = importlib.util.module_from_spec(spec)
    sys.modules["prosody_planner_under_test"] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    failures: list[str] = []
    try:
        taxonomy = load_json(TAXONOMY_PATH)
        load_json(MAPPING_PATH)
        load_json(RULES_PATH)
        policy = load_json(POLICY_PATH)
        planner = load_planner_module()
    except AssertionError as exc:
        print(json.dumps({"status": "fail", "failures": [str(exc)]}, indent=2))
        return 1

    for function_name in (
        "load_prosody_taxonomy",
        "load_sales_prosody_mapping",
        "load_composition_rules",
        "plan_prosody_for_sales_turn",
        "validate_prosody_plan",
    ):
        if not callable(getattr(planner, function_name, None)):
            failures.append(f"planner missing callable: {function_name}")

    label_ids = {
        item.get("label_id")
        for item in taxonomy.get("labels", [])
        if isinstance(item, dict) and isinstance(item.get("label_id"), str)
    }
    test_contexts = [
        {
            "buyer_emotion": "confused",
            "buyer_confusion_level": "high",
            "sales_move": "plan_explanation",
            "objection_type": "none",
            "backend_id": "elevenlabs_existing_provider",
        },
        {
            "buyer_emotion": "skeptical",
            "buyer_skepticism_level": "high",
            "sales_move": "source_affiliation_answer",
            "objection_type": "source_affiliation",
        },
        {
            "buyer_emotion": "frustrated",
            "buyer_friction_level": "high",
            "sales_move": "repair",
            "buyer_said_already_told_you": True,
        },
        {
            "buyer_emotion": "neutral",
            "sales_move": "boundary_response",
            "safety_boundary_detected": True,
            "objection_type": "privacy",
        },
        {
            "buyer_emotion": "interested",
            "sales_move": "close",
            "decision_stage": "terminal_acceptance",
            "close_readiness": "accepted",
        },
        {
            "buyer_emotion": "neutral",
            "sales_move": "repair",
            "asr_uncertainty_detected": True,
        },
    ]

    plans: list[dict[str, Any]] = []
    for index, context in enumerate(test_contexts, start=1):
        try:
            plan = planner.plan_prosody_for_sales_turn(context)
        except Exception as exc:  # pragma: no cover - validator output path
            failures.append(f"context {index} planner raised: {exc}")
            continue
        if not isinstance(plan, dict):
            failures.append(f"context {index} did not return a dict")
            continue
        plans.append(plan)
        missing = sorted(REQUIRED_PLAN_FIELDS - set(plan))
        if missing:
            failures.append(f"context {index} plan missing fields: {missing}")
        selected = plan.get("selected_prosody_labels")
        if not isinstance(selected, list) or not selected:
            failures.append(f"context {index} selected_prosody_labels must be non-empty")
        else:
            unknown = sorted(str(value) for value in selected if value not in label_ids)
            if unknown:
                failures.append(f"context {index} selected unknown labels: {unknown}")
        if plan.get("spoken_text_tag_injection_allowed") is not False:
            failures.append(f"context {index} must block spoken text tag injection")
        if plan.get("live_runtime_wiring_changed") is not False:
            failures.append(f"context {index} must not change live runtime wiring")
        if plan.get("fish_inspired_tags_internal_only") is not True:
            failures.append(f"context {index} must keep Fish tags internal only")
        validation_errors = planner.validate_prosody_plan(plan)
        if validation_errors:
            failures.append(f"context {index} plan validation errors: {validation_errors}")

    backend_policies = policy.get("backend_policies", {}) if isinstance(policy.get("backend_policies"), dict) else {}
    if backend_policies.get("elevenlabs_current_provider", {}).get("current_voice_path") is not True:
        failures.append("backend policy must preserve ElevenLabs as current provider")
    if backend_policies.get("elevenlabs_current_provider", {}).get("raw_fish_tag_injection_allowed") is not False:
        failures.append("backend policy must block raw Fish tags in ElevenLabs")
    if backend_policies.get("fish_future_research", {}).get("active_now") is not False:
        failures.append("Fish future research policy must not be active now")
    if backend_policies.get("liquid_audio", {}).get("current_tts_backend") is not False:
        failures.append("Liquid must not be current TTS backend")

    for evidence_path in (RESULT_PATH, REPORT_PATH):
        if not evidence_path.is_file():
            failures.append(f"missing evidence file: {rel(evidence_path)}")
    if RESULT_PATH.is_file():
        result = load_json(RESULT_PATH)
        if int(result.get("examples_count") or 0) < 40:
            failures.append("planner evidence must include at least 40 examples")
        if result.get("spoken_text_tag_injection_allowed") is not False:
            failures.append("planner evidence must block spoken text tag injection")
        if result.get("live_runtime_wiring_changed") is not False:
            failures.append("planner evidence must not change live runtime wiring")
        if result.get("provider_calls_made") is not False:
            failures.append("planner evidence must record no provider calls")
        for example in result.get("examples", []):
            if not isinstance(example, dict):
                failures.append("planner evidence examples must be objects")
                continue
            if example.get("tag_injection_allowed") is not False:
                failures.append(f"{example.get('example_id')} must block tag injection")
            if example.get("buyer_facing_text_contains_raw_fish_tags") is not False:
                failures.append(f"{example.get('example_id')} must not contain buyer-facing Fish tags")
            for field_name in ("plain_text", "prosody_shaped_text"):
                if has_raw_tag(str(example.get(field_name) or "")):
                    failures.append(f"{example.get('example_id')}.{field_name} contains a raw bracket tag")

    output = {
        "status": "pass" if not failures else "fail",
        "planner": rel(PLANNER_PATH),
        "test_plan_count": len(plans),
        "spoken_text_tag_injection_allowed": False,
        "live_runtime_wiring_changed": False,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "failures": failures,
    }
    print(json.dumps(output, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
