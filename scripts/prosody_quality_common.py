from __future__ import annotations

import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIO_DIR = ROOT / "runtime" / "audio_backends"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated"

TAXONOMY_PATH = AUDIO_DIR / "prosody_sales_taxonomy.json"
RULES_PATH = AUDIO_DIR / "prosody_composition_rules.json"
MAPPING_PATH = AUDIO_DIR / "sales_prosody_mapping.json"
BACKEND_POLICY_PATH = AUDIO_DIR / "prosody_backend_mapping_policy.json"
PLANNER_PATH = AUDIO_DIR / "prosody_planner.py"
ELEVENLABS_READINESS_PATH = AUDIO_DIR / "elevenlabs_prosody_mapping_readiness.json"

TAXONOMY_AUDIT_DIR = GENERATED_DIR / "PROSODY-TAXONOMY-QUALITY-AUDIT-001"
MAPPING_AUDIT_DIR = GENERATED_DIR / "SALES-PROSODY-MAPPING-QUALITY-AUDIT-001"
DRY_RUN_AUDIT_DIR = GENERATED_DIR / "PROSODY-PLANNER-DRY-RUN-AUDIT-001"
ELEVENLABS_READINESS_DIR = GENERATED_DIR / "ELEVENLABS-PROSODY-MAPPING-READINESS-001"
QUALITY_DECISION_DIR = GENERATED_DIR / "PROSODY-TAXONOMY-QUALITY-DECISION-001"
CLEANUP_PLAN_DIR = GENERATED_DIR / "PROSODY-TAXONOMY-CLEANUP-PLAN-001"
CLEANUP_EVIDENCE_DIR = GENERATED_DIR / "PROSODY-TAXONOMY-CLEANUP-001"

FISH_TAXONOMY_EVIDENCE = GENERATED_DIR / "FISH-INSPIRED-PROSODY-TAXONOMY-001" / "result.json"
SALES_MAPPING_EVIDENCE = GENERATED_DIR / "SALES-PROSODY-MAPPING-001" / "result.json"
PLANNER_EVIDENCE = GENERATED_DIR / "PROSODY-PLANNER-PROTOTYPE-001" / "result.json"

FORBIDDEN_FALSE_FLAGS = (
    "fish_install_performed",
    "fish_inference_performed",
    "liquid_inference_performed",
    "kokoro_inference_performed",
    "provider_calls_made",
    "openai_api_calls_made",
    "elevenlabs_calls_made",
    "live_tts_calls_made",
    "local_model_generation_made",
    "ollama_generation_made",
    "training_performed",
    "model_weights_committed",
    "audio_files_committed",
    "live_runtime_wiring_changed",
    "runtime_behavior_changed",
    "response_text_changed",
    "spoken_text_tag_injection_allowed",
)
FORBIDDEN_WEIGHT_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt", ".onnx")
FORBIDDEN_AUDIO_SUFFIXES = (".mp3", ".wav", ".flac", ".m4a", ".ogg")
TAG_RE = re.compile(r"\[[^\]\n]{2,80}\]")
PRESSURE_TERMS = (
    "manipulative",
    "pressure",
    "guilt",
    "fear",
    "urgency",
    "fake laughter",
    "flirt",
    "overclaim",
    "unsupported claim",
    "raw url",
    "fake side effect",
)
REQUIRED_CONTEXTS = {
    "confusion",
    "skepticism",
    "price_objection",
    "competitor_objection",
    "privacy_objection",
    "buyer_correction",
    "asr_uncertainty",
    "already_told_you",
    "terminal_acceptance",
    "no_fit",
    "boundary_request",
    "source_affiliation_question",
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{rel(path)} must be a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_report(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


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


def base_boundary_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_FALSE_FLAGS}


def boundary_failures(payload: dict[str, Any], prefix: str = "payload") -> list[str]:
    flags = payload.get("boundary_flags", {}) if isinstance(payload.get("boundary_flags"), dict) else {}
    failures = []
    for key in FORBIDDEN_FALSE_FLAGS:
        if flags.get(key) is not False:
            failures.append(f"{prefix}.boundary_flags.{key} must be false")
    return failures


def has_raw_tag(text: str) -> bool:
    return bool(TAG_RE.search(text))


def label_index(taxonomy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["label_id"]: item
        for item in taxonomy.get("labels", [])
        if isinstance(item, dict) and isinstance(item.get("label_id"), str)
    }


def count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(Counter(str(item.get(key, "")) for item in items))


def group_by_signature(items: list[dict[str, Any]], fields: tuple[str, ...]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for item in items:
        signature: list[str] = []
        for field in fields:
            value = item.get(field)
            if isinstance(value, list):
                signature.append(json.dumps(value, sort_keys=True))
            else:
                signature.append(str(value))
        groups[tuple(signature)].append(str(item.get("label_id") or item.get("mapping_id") or item.get("rule_id")))
    return [
        {"signature": list(signature), "ids": ids, "count": len(ids)}
        for signature, ids in groups.items()
        if len(ids) > 1
    ]


def status_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(str(item.get("status", "unknown")) for item in items)
    return {key: counts.get(key, 0) for key in ("pass", "warning", "fail", "needs_human_review", "unknown")}


def required_artifact_paths() -> list[Path]:
    return [
        TAXONOMY_PATH,
        RULES_PATH,
        MAPPING_PATH,
        BACKEND_POLICY_PATH,
        PLANNER_PATH,
        FISH_TAXONOMY_EVIDENCE,
        SALES_MAPPING_EVIDENCE,
        PLANNER_EVIDENCE,
    ]


def assert_common_no_side_effects(payload: dict[str, Any]) -> list[str]:
    failures = boundary_failures(payload)
    weights, audio = tracked_forbidden_files()
    if weights:
        failures.append(f"tracked model/checkpoint files are forbidden: {weights[:20]}")
    if audio:
        failures.append(f"tracked audio files are forbidden: {audio[:20]}")
    live_changes = changed_live_runtime_files()
    if live_changes:
        failures.append(f"live runtime files changed: {live_changes}")
    if payload.get("fish_tags_internal_only") is not True:
        failures.append("Fish tags must be internal only")
    if payload.get("raw_fish_tags_allowed_in_elevenlabs_text") is not False:
        failures.append("raw Fish tags must not be allowed in ElevenLabs text")
    return failures
