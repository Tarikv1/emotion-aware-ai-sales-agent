#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = ROOT / "runtime" / "audio_backends" / "prosody_sales_taxonomy.json"
POLICY_PATH = ROOT / "runtime" / "audio_backends" / "prosody_backend_mapping_policy.json"
REGISTRY_PATH = ROOT / "runtime" / "audio_backends" / "audio_backend_candidates.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "FISH-INSPIRED-PROSODY-TAXONOMY-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "FISH-INSPIRED-PROSODY-TAXONOMY-001" / "report.md"

REQUIRED_SOURCE_URLS = {
    "https://fish.audio/s2/",
    "https://huggingface.co/fishaudio/s2-pro",
    "https://github.com/fishaudio/fish-speech",
    "https://speech.fish.audio/",
}
REQUIRED_CATEGORIES = {
    "pacing",
    "pause",
    "volume",
    "pitch",
    "tone",
    "warmth",
    "confidence",
    "energy",
    "clarity",
    "emotion_response",
    "objection_handling",
    "trust_building",
    "sales_delivery",
    "plan_explanation",
    "recommendation_delivery",
    "closing_delivery",
    "repair",
    "clarification",
    "boundary_respect",
    "phone_call_delivery",
    "multilingual_delivery",
    "source_and_truthfulness",
    "safety_and_compliance",
    "unsafe_or_disallowed",
}
REQUIRED_LABEL_IDS = {
    "pacing.very_slow_explanation",
    "pacing.measured_slow",
    "pacing.conversational_medium",
    "pacing.brisk_but_clear",
    "pacing.urgent_but_controlled",
    "pause.micro_pause",
    "pause.short_pause",
    "pause.pause_before_price",
    "volume.no_shouting",
    "volume.no_whisper_live_unless_backend_supported",
    "pitch.avoid_pitch_spike",
    "tone.no_hype",
    "warmth.no_false_intimacy",
    "confidence.no_unverified_certainty",
    "energy.no_forced_excitement",
    "clarity.no_internal_terms",
    "emotion_response.confused_buyer_reassurance",
    "emotion_response.distrustful_buyer_transparency",
    "objection.price_acknowledge",
    "objection.avoid_argument",
    "trust.transparent_source_boundary",
    "sales.no_monologue",
    "plan.explain_api_boundary",
    "recommend.do_not_overrecommend",
    "close.no_fake_email",
    "repair.already_told_you_acknowledge",
    "clarify.no_classifier_language",
    "boundary.respect_stop_request",
    "phone.barge_in_recovery",
    "multilingual.avoid_idiom",
    "source.no_affiliation_claim",
    "safety.no_raw_fish_tags_in_elevenlabs",
    "unsafe.no_manipulative_urgency",
    "unsafe.no_roleplay_as_human_employee_if_not_true",
}
REQUIRED_LABEL_FIELDS = {
    "label_id",
    "category",
    "display_name",
    "description",
    "when_to_use",
    "when_not_to_use",
    "fish_inspired_tags",
    "sales_contexts",
    "buyer_emotions",
    "backend_mapping",
    "safety_notes",
    "allowed_in_live",
    "internal_only",
    "can_affect_text_shape",
    "can_affect_voice_style",
    "risk_level",
    "disallowed_for",
}
REQUIRED_BACKEND_HINTS = {
    "elevenlabs_hint",
    "plain_text_hint",
    "future_fish_hint",
    "kokoro_hint",
    "liquid_hint",
}
FORBIDDEN_WEIGHT_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt", ".onnx")
FORBIDDEN_AUDIO_SUFFIXES = (".mp3", ".wav", ".flac", ".m4a", ".ogg")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AssertionError(f"missing file: {rel(path)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"{rel(path)} must be a JSON object")
    return payload


def git_lines(args: list[str]) -> list[str]:
    completed = subprocess.run(
        ["git", "--no-optional-locks", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def tracked_forbidden_files() -> tuple[list[str], list[str]]:
    tracked = git_lines(["ls-files"])
    weights = [path for path in tracked if path.lower().endswith(FORBIDDEN_WEIGHT_SUFFIXES) or path.startswith("local_artifacts/")]
    audio = [path for path in tracked if path.lower().endswith(FORBIDDEN_AUDIO_SUFFIXES)]
    return weights, audio


def changed_live_runtime_files() -> list[str]:
    changed = git_lines(["diff", "--name-only", "HEAD"])
    blocked_prefixes = (
        "runtime/core/",
        "runtime/entrypoints/",
        "runtime/providers/",
        "runtime/speech/",
        "runtime/voice/",
        "runtime/policy/",
        "runtime/contracts/",
        "runtime/campaigns/",
    )
    return [path for path in changed if path.startswith(blocked_prefixes)]


def has_raw_tag(value: str) -> bool:
    return bool(re.search(r"\[[^\]\n]{2,80}\]", value))


def main() -> int:
    failures: list[str] = []
    try:
        taxonomy = load_json(TAXONOMY_PATH)
    except AssertionError as exc:
        print(json.dumps({"status": "fail", "failures": [str(exc)]}, indent=2))
        return 1

    labels = taxonomy.get("labels")
    if not isinstance(labels, list):
        failures.append("taxonomy.labels must be a list")
        labels = []
    label_count = len(labels)
    if label_count < 250:
        failures.append(f"taxonomy label count must be >= 250, got {label_count}")
    if label_count > 400 and not taxonomy.get("count_over_400_justification"):
        failures.append(f"taxonomy label count must be <= 400 unless justified, got {label_count}")

    source_urls = set(taxonomy.get("source_urls") or [])
    if not REQUIRED_SOURCE_URLS.issubset(source_urls):
        failures.append(f"taxonomy missing Fish source URLs: {sorted(REQUIRED_SOURCE_URLS - source_urls)}")

    facts = taxonomy.get("fish_s2_facts", {}) if isinstance(taxonomy.get("fish_s2_facts"), dict) else {}
    if facts.get("tag_count_reference") != "15000+ unique tags":
        failures.append("Fish 15,000+ tags must be referenced as inspiration")
    if facts.get("raw_tag_universe_imported") is not False:
        failures.append("Fish raw tag universe must not be imported wholesale")
    if facts.get("curated_internal_taxonomy") is not True:
        failures.append("taxonomy must identify itself as curated internal taxonomy")

    boundary = taxonomy.get("boundary_flags", {}) if isinstance(taxonomy.get("boundary_flags"), dict) else {}
    for key in (
        "fish_install_performed",
        "fish_inference_performed",
        "provider_calls_made",
        "elevenlabs_calls_made",
        "live_tts_calls_made",
        "local_model_generation_made",
        "model_weights_committed",
        "audio_files_committed",
        "live_runtime_wiring_changed",
        "runtime_behavior_changed",
        "response_text_changed",
        "spoken_text_tag_injection_allowed",
    ):
        if boundary.get(key) is not False:
            failures.append(f"boundary_flags.{key} must be false")

    categories = {item.get("category") for item in labels if isinstance(item, dict)}
    missing_categories = sorted(REQUIRED_CATEGORIES - categories)
    if missing_categories:
        failures.append(f"missing required categories: {missing_categories}")
    label_ids = {item.get("label_id") for item in labels if isinstance(item, dict)}
    missing_label_ids = sorted(REQUIRED_LABEL_IDS - label_ids)
    if missing_label_ids:
        failures.append(f"missing required label IDs: {missing_label_ids}")
    if len(label_ids) != label_count:
        failures.append("label IDs must be unique")

    unsafe_count = 0
    for label in labels:
        if not isinstance(label, dict):
            failures.append("all label entries must be objects")
            continue
        label_id = str(label.get("label_id") or "")
        missing_fields = sorted(REQUIRED_LABEL_FIELDS - set(label))
        if missing_fields:
            failures.append(f"{label_id} missing fields: {missing_fields}")
            continue
        if label.get("category") not in REQUIRED_CATEGORIES:
            failures.append(f"{label_id} has invalid category: {label.get('category')!r}")
        if not label_id or "." not in label_id:
            failures.append(f"{label_id!r} must be hierarchical")
        for list_field in ("fish_inspired_tags", "sales_contexts", "buyer_emotions", "disallowed_for"):
            if not isinstance(label.get(list_field), list):
                failures.append(f"{label_id}.{list_field} must be a list")
        backend_mapping = label.get("backend_mapping")
        if not isinstance(backend_mapping, dict):
            failures.append(f"{label_id}.backend_mapping must be an object")
        else:
            missing_hints = sorted(REQUIRED_BACKEND_HINTS - set(backend_mapping))
            if missing_hints:
                failures.append(f"{label_id}.backend_mapping missing hints: {missing_hints}")
            elevenlabs_hint = str(backend_mapping.get("elevenlabs_hint") or "").lower()
            if has_raw_tag(elevenlabs_hint):
                failures.append(f"{label_id} leaks bracket tags into ElevenLabs hint")
        if label.get("risk_level") not in {"low", "medium", "high"}:
            failures.append(f"{label_id}.risk_level must be low/medium/high")
        if label.get("allowed_in_live") is not False:
            failures.append(f"{label_id}.allowed_in_live must stay false in Phase 4I2")
        if label.get("fish_inspired_tags") and label.get("internal_only") is not True:
            failures.append(f"{label_id} has Fish-inspired tags but is not internal_only")
        if label.get("category") == "unsafe_or_disallowed" or label_id.startswith("unsafe."):
            unsafe_count += 1
            if label.get("risk_level") != "high":
                failures.append(f"{label_id} unsafe label must be high risk")
            if "live_call" not in label.get("disallowed_for", []):
                failures.append(f"{label_id} unsafe label must be disallowed for live_call")

    if unsafe_count < 10:
        failures.append(f"unsafe/disallowed labels count must be meaningful, got {unsafe_count}")

    policy = load_json(POLICY_PATH)
    eleven = policy.get("backend_policies", {}).get("elevenlabs_current_provider", {})
    if eleven.get("current_voice_path") is not True:
        failures.append("ElevenLabs must remain current provider voice path")
    if eleven.get("raw_fish_tag_injection_allowed") is not False:
        failures.append("ElevenLabs policy must block raw Fish tag injection")
    liquid = policy.get("backend_policies", {}).get("liquid_audio", {})
    if liquid.get("current_tts_backend") is not False:
        failures.append("Liquid must not be marked as current TTS backend")
    if liquid.get("status") != "architecture_inspiration_only":
        failures.append("Liquid must remain architecture inspiration only")
    kokoro = policy.get("backend_policies", {}).get("kokoro_future", {})
    if kokoro.get("status") != "optional_future_benchmark_only":
        failures.append("Kokoro must remain optional future benchmark only")

    registry = load_json(REGISTRY_PATH)
    candidates = {item.get("backend_id"): item for item in registry.get("candidates", []) if isinstance(item, dict)}
    if candidates.get("elevenlabs_existing_provider", {}).get("integration_classification") != "current_runtime_provider":
        failures.append("registry must keep ElevenLabs as current runtime provider")
    if candidates.get("liquid_audio_lfm25", {}).get("tts_backend_candidate_status") != "rejected_by_manual_listening_review":
        failures.append("registry must keep Liquid rejected by manual listening review")
    if candidates.get("fish_audio_s2", {}).get("integration_classification") != "architecture_inspiration_only":
        failures.append("registry must keep Fish architecture inspiration only")
    if candidates.get("kokoro_82m", {}).get("integration_classification") != "benchmark_candidate":
        failures.append("registry must keep Kokoro as benchmark candidate")

    for evidence_path in (RESULT_PATH, REPORT_PATH):
        if not evidence_path.is_file():
            failures.append(f"missing evidence file: {rel(evidence_path)}")
    if RESULT_PATH.is_file():
        result = load_json(RESULT_PATH)
        if result.get("taxonomy_label_count") != label_count:
            failures.append("taxonomy evidence label count does not match taxonomy")
        if result.get("fish_tags_internal_only") is not True:
            failures.append("taxonomy evidence must mark Fish tags internal only")

    weights, audio = tracked_forbidden_files()
    if weights:
        failures.append(f"tracked model/checkpoint files are forbidden: {weights[:20]}")
    if audio:
        failures.append(f"tracked audio files are forbidden: {audio[:20]}")
    live_changes = changed_live_runtime_files()
    if live_changes:
        failures.append(f"live runtime files changed: {live_changes}")

    output = {
        "status": "pass" if not failures else "fail",
        "taxonomy": rel(TAXONOMY_PATH),
        "label_count": label_count,
        "category_count": len(categories),
        "unsafe_disallowed_count": unsafe_count,
        "source_url_count": len(source_urls),
        "fish_tags_internal_only": not any(
            isinstance(label, dict) and label.get("fish_inspired_tags") and label.get("internal_only") is not True
            for label in labels
        ),
        "spoken_text_tag_injection_allowed": False,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "failures": failures,
    }
    print(json.dumps(output, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
