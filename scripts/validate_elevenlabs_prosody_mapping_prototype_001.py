#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

from prosody_quality_common import assert_common_no_side_effects, load_json


ROOT = Path(__file__).resolve().parents[1]
AUDIO_DIR = ROOT / "runtime" / "audio_backends"
POLICY_PATH = AUDIO_DIR / "elevenlabs_prosody_mapping_policy.json"
MAPPER_PATH = AUDIO_DIR / "elevenlabs_prosody_mapper.py"
RESULT_DIR = ROOT / "research" / "experiments" / "generated" / "ELEVENLABS-PROSODY-MAPPING-PROTOTYPE-001"
RESULT_PATH = RESULT_DIR / "result.json"
REPORT_PATH = RESULT_DIR / "report.md"
TAXONOMY_PATH = AUDIO_DIR / "prosody_sales_taxonomy.json"

REQUIRED_LAYERS = {
    "text_shaping",
    "punctuation",
    "sentence_length",
    "pause_hinting_by_punctuation",
    "emphasis_by_word_choice",
    "style_prompt_hint",
    "voice_settings_hint",
}
REQUIRED_UNSUPPORTED = {
    "raw_fish_bracket_tags",
    "fake_laughter",
    "fake_emotion_tags",
    "unverified_voice_cloning",
    "unsupported_claim_confidence",
    "manipulative urgency",
}
REQUIRED_SAFETY_RULES = {
    "no raw bracket tags in spoken text",
    "no internal policy language",
    "no fake side effects",
    "no overclaiming",
    "no pressure after boundary",
    "no emotional exaggeration",
    "no hidden action claims",
    "no raw URLs unless explicit metadata mode",
}
REQUIRED_EXAMPLE_FIELDS = {
    "example_id",
    "input_context",
    "base_text",
    "prosody_plan",
    "shaped_text",
    "style_prompt_hint",
    "voice_settings_hint",
    "pause_punctuation_plan",
    "emphasis_terms",
    "safety_warnings",
    "raw_fish_tags_present",
    "internal_labels_exposed",
    "provider_call_required",
    "live_wiring_allowed",
    "validation_result",
}
FORBIDDEN_CODE_PATTERNS = (
    r"from\s+elevenlabs\b",
    r"import\s+elevenlabs\b",
    r"\brequests\.",
    r"\bhttpx\.",
    r"\burllib\.request\b",
    r"\bsocket\b",
    r"\bsubprocess\b",
    r"\bapi[_-]?key\b",
    r"xi-api-key",
    r"\btext_to_speech\b",
    r"\bgenerate_audio\b",
    r"\blive_tts\b",
)
INTERNAL_TEXT_MARKERS = (
    "classifier",
    "confidence score",
    "policy",
    "internal label",
    "prosody label",
    "fish tag",
    "mapping layer",
)
RAW_TAG_RE = re.compile(r"\[[^\]\n]{2,80}\]")
URL_RE = re.compile(r"\b(?:https?://|www\.)\S+", re.IGNORECASE)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_module() -> Any:
    spec = importlib.util.spec_from_file_location("elevenlabs_prosody_mapper_under_test", MAPPER_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("could not import ElevenLabs prosody mapper")
    module = importlib.util.module_from_spec(spec)
    sys.modules["elevenlabs_prosody_mapper_under_test"] = module
    spec.loader.exec_module(module)
    return module


def has_raw_tag(text: str) -> bool:
    return bool(RAW_TAG_RE.search(text))


def text_contains_internal_marker(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in INTERNAL_TEXT_MARKERS)


def scan_code(path: Path, failures: list[str]) -> None:
    if not path.is_file():
        failures.append(f"missing file: {rel(path)}")
        return
    text = path.read_text(encoding="utf-8").lower()
    for pattern in FORBIDDEN_CODE_PATTERNS:
        if re.search(pattern, text):
            failures.append(f"{rel(path)} contains forbidden provider/audio pattern: {pattern}")


def validate_policy(policy: dict[str, Any], failures: list[str]) -> None:
    if policy.get("current_voice_path") != "elevenlabs":
        failures.append("policy.current_voice_path must be elevenlabs")
    for key in (
        "provider_calls_allowed",
        "live_wiring_allowed",
        "raw_fish_tags_allowed_in_spoken_text",
        "internal_labels_exposed_to_buyer",
    ):
        if policy.get(key) is not False:
            failures.append(f"policy.{key} must be false")
    supported = set(policy.get("supported_mapping_layers", []))
    if supported != REQUIRED_LAYERS:
        failures.append(f"policy.supported_mapping_layers mismatch: {sorted(supported)}")
    unsupported = set(policy.get("unsupported_mapping_layers", []))
    missing_unsupported = sorted(REQUIRED_UNSUPPORTED - unsupported)
    if missing_unsupported:
        failures.append(f"policy missing unsupported layers: {missing_unsupported}")
    safety_rules = set(policy.get("safety_rules", []))
    missing_safety = sorted(REQUIRED_SAFETY_RULES - safety_rules)
    if missing_safety:
        failures.append(f"policy missing safety rules: {missing_safety}")
    layer_definitions = policy.get("mapping_layers")
    if not isinstance(layer_definitions, dict):
        failures.append("policy.mapping_layers must be an object")
        return
    for layer in REQUIRED_LAYERS:
        definition = layer_definitions.get(layer)
        if not isinstance(definition, dict):
            failures.append(f"policy.mapping_layers.{layer} must be an object")
            continue
        for field in ("purpose", "allowed_inputs", "disallowed_inputs", "output_field", "buyer_facing_safety_notes"):
            value = definition.get(field)
            if value in (None, "", []):
                failures.append(f"policy.mapping_layers.{layer}.{field} must be populated")


def validate_mapper_api(failures: list[str]) -> Any | None:
    try:
        mapper = load_module()
    except Exception as exc:
        failures.append(f"mapper import failed: {exc}")
        return None
    for function_name in (
        "load_elevenlabs_mapping_policy",
        "map_prosody_plan_to_elevenlabs_hints",
        "shape_text_for_voice",
        "validate_elevenlabs_prosody_mapping",
    ):
        if not callable(getattr(mapper, function_name, None)):
            failures.append(f"mapper missing callable: {function_name}")
    return mapper


def validate_examples(result: dict[str, Any], label_ids: set[str], failures: list[str]) -> None:
    examples = result.get("examples")
    if not isinstance(examples, list):
        failures.append("result.examples must be a list")
        return
    if len(examples) < 60:
        failures.append(f"example count must be >= 60, got {len(examples)}")
    if result.get("example_count") != len(examples):
        failures.append("result.example_count must match examples length")
    if result.get("examples_count") not in (None, len(examples)):
        failures.append("result.examples_count must match examples length when present")
    for key in (
        "provider_calls_made",
        "elevenlabs_calls_made",
        "live_tts_calls_made",
        "runtime_behavior_changed",
        "response_text_changed",
        "fish_inference_performed",
        "liquid_inference_performed",
        "kokoro_inference_performed",
        "local_model_generation_made",
        "ollama_generation_made",
        "training_performed",
    ):
        if result.get(key) is not False:
            failures.append(f"result.{key} must be false")
    for example in examples:
        if not isinstance(example, dict):
            failures.append("examples must contain objects")
            continue
        missing = sorted(REQUIRED_EXAMPLE_FIELDS - set(example))
        if missing:
            failures.append(f"{example.get('example_id')}: missing fields {missing}")
        shaped_text = str(example.get("shaped_text") or "")
        if has_raw_tag(shaped_text):
            failures.append(f"{example.get('example_id')}: shaped_text contains raw bracket tag")
        if URL_RE.search(shaped_text):
            failures.append(f"{example.get('example_id')}: shaped_text contains raw URL")
        if text_contains_internal_marker(shaped_text):
            failures.append(f"{example.get('example_id')}: shaped_text exposes internal language")
        exposed_labels = sorted(label_id for label_id in label_ids if label_id in shaped_text)
        if exposed_labels:
            failures.append(f"{example.get('example_id')}: shaped_text exposes label ids {exposed_labels[:5]}")
        for key in ("raw_fish_tags_present", "internal_labels_exposed", "provider_call_required", "live_wiring_allowed"):
            if example.get(key) is not False:
                failures.append(f"{example.get('example_id')}.{key} must be false")
        validation = example.get("validation_result")
        if not isinstance(validation, dict):
            failures.append(f"{example.get('example_id')}: validation_result must be an object")
        elif validation.get("status") != "pass":
            failures.append(f"{example.get('example_id')}: validation_result.status must be pass")


def main() -> int:
    failures: list[str] = []
    for path in (POLICY_PATH, MAPPER_PATH, RESULT_PATH, REPORT_PATH):
        if not path.is_file():
            failures.append(f"missing file: {rel(path)}")
    scan_code(MAPPER_PATH, failures)
    scan_code(ROOT / "scripts" / "generate_elevenlabs_prosody_mapping_examples_001.py", failures)

    policy = load_json(POLICY_PATH) if POLICY_PATH.is_file() else {}
    if policy:
        validate_policy(policy, failures)
    mapper = validate_mapper_api(failures) if MAPPER_PATH.is_file() else None
    if mapper is not None:
        try:
            loaded = mapper.load_elevenlabs_mapping_policy()
            if loaded.get("mapping_version") != policy.get("mapping_version"):
                failures.append("mapper policy loader returned unexpected policy")
        except Exception as exc:
            failures.append(f"mapper policy load failed: {exc}")

    taxonomy = load_json(TAXONOMY_PATH) if TAXONOMY_PATH.is_file() else {}
    label_ids = {
        item.get("label_id")
        for item in taxonomy.get("labels", [])
        if isinstance(item, dict) and isinstance(item.get("label_id"), str)
    }
    result = load_json(RESULT_PATH) if RESULT_PATH.is_file() else {}
    if result:
        validate_examples(result, label_ids, failures)
        failures.extend(assert_common_no_side_effects(result))

    output = {
        "status": "pass" if not failures else "fail",
        "policy": rel(POLICY_PATH),
        "mapper": rel(MAPPER_PATH),
        "examples_result": rel(RESULT_PATH),
        "example_count": len(result.get("examples", [])) if isinstance(result.get("examples"), list) else 0,
        "provider_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "failures": failures,
    }
    print(json.dumps(output, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
