#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "runtime" / "runtime_manifest.json"

REQUIRED_RUNTIME_PATHS = {
    "runtime/core/realtime_turns.py",
    "runtime/entrypoints/realtime_turn_cli.py",
    "runtime/entrypoints/generate_guarded_response.py",
    "runtime/contracts/product_agent_output_contract.py",
    "runtime/policy/core_sales_delivery_playbook.py",
    "runtime/voice/runtime_voice_delivery.py",
    "runtime/voice/runtime_tts_delivery.py",
    "runtime/providers/tts_provider_clients.py",
    "runtime/speech/spoken_text_normalization.py",
    "runtime/speech/speech_naturalness.py",
    "runtime/contracts/campaign_profile_contract.py",
    "runtime/campaigns/examples",
    "runtime/prompts/product-qualification-agent.txt",
    "runtime/config/local/voice_ids.example.json",
    "runtime/architecture/REALTIME_AGENT_ARCHITECTURE.md",
    "runtime/entrypoints/REALTIME_TURN_CLI.md",
    "runtime/policy/CALL_TERMINATION_POLICY.md",
    "runtime/policy/BILINGUAL_REALTIME_CORE.md",
    "runtime/providers/VOICE_PROVIDER_RUN_BOUNDARY.md",
    "runtime/providers/VOICE_GENERATED_AUDIO_ASSET_LOG.md",
    "runtime/persistence/SQLITE_PROTOTYPE.md",
    "runtime/contracts/emotion_state_contracts.py",
    "runtime/contracts/emotion_pattern_contracts.py",
    "runtime/contracts/emotion_state_brain_extension.py",
}

REQUIRED_BOUNDARY_FLAGS = {
    "runtime_behavior_changed": False,
    "response_text_changed": False,
    "retrieval_enabled": False,
    "provider_calls_made": False,
    "llm_used": False,
    "private_data_read": False,
    "voice_playback_unblocked": False,
    "public_demo_polish_unblocked": False,
    "payment_collection_allowed": False,
    "contract_signing_allowed": False,
    "production_runtime_promotion_allowed": False,
}

BLOCKED_MANIFEST_PREFIXES = (
    ".tmp/",
    "data/private/",
    "data/private-restricted/",
)

LEGACY_ENTRYPOINT_WRAPPERS = {
    "scripts/realtime_turn_cli.py",
    "scripts/generate_guarded_response.py",
    "scripts/generate_runtime_voice_delivery.py",
    "scripts/generate_runtime_tts_delivery.py",
    "scripts/run_realtime_turn_simulation.py",
}

STALE_RUNTIME_PATH_TEXT = (
    "packages/prompts/product-qualification-agent.txt",
    "config/local/voice_ids.example.json",
    "db/sqlite_schema.sql",
    "docs/product/CALL_TERMINATION_POLICY.md",
    "docs/product/REALTIME_AGENT_ARCHITECTURE.md",
    "docs/product/REALTIME_TURN_CLI.md",
    "docs/product/BILINGUAL_REALTIME_CORE.md",
    "docs/product/VOICE_PROVIDER_RUN_BOUNDARY.md",
    "docs/product/VOICE_GENERATED_AUDIO_ASSET_LOG.md",
    "docs/product/SQLITE_PROTOTYPE.md",
    "`campaigns/examples/",
    '"campaigns/examples/',
    "'campaigns/examples/",
)

CANONICAL_RUNTIME_DOC_STUBS = {
    "docs/product/REALTIME_AGENT_ARCHITECTURE.md": "runtime/architecture/REALTIME_AGENT_ARCHITECTURE.md",
    "docs/product/REALTIME_TURN_CLI.md": "runtime/entrypoints/REALTIME_TURN_CLI.md",
    "docs/product/CALL_TERMINATION_POLICY.md": "runtime/policy/CALL_TERMINATION_POLICY.md",
    "docs/product/BILINGUAL_REALTIME_CORE.md": "runtime/policy/BILINGUAL_REALTIME_CORE.md",
    "docs/product/VOICE_PROVIDER_RUN_BOUNDARY.md": "runtime/providers/VOICE_PROVIDER_RUN_BOUNDARY.md",
    "docs/product/VOICE_GENERATED_AUDIO_ASSET_LOG.md": "runtime/providers/VOICE_GENERATED_AUDIO_ASSET_LOG.md",
    "docs/product/SQLITE_PROTOTYPE.md": "runtime/persistence/SQLITE_PROTOTYPE.md",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"Runtime manifest missing: {path.relative_to(ROOT)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail("Runtime manifest must be a JSON object.")
    return payload


def assert_manifest_shape(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != 1:
        fail("Runtime manifest schema_version must be 1.")
    if payload.get("status") != "runtime-sources-and-docs-moved-with-legacy-wrappers":
        fail("Runtime manifest status must record the moved-source/docs plus legacy-wrapper boundary.")
    for key in ("runtime_entries", "non_runtime_defaults", "boundary_flags", "move_readiness"):
        if key not in payload:
            fail(f"Runtime manifest missing key: {key}")
    if not isinstance(payload["runtime_entries"], list) or not payload["runtime_entries"]:
        fail("Runtime manifest must list runtime_entries.")
    if not isinstance(payload["non_runtime_defaults"], list) or not payload["non_runtime_defaults"]:
        fail("Runtime manifest must list non_runtime_defaults.")


def assert_boundary_flags(payload: dict[str, Any]) -> None:
    flags = payload.get("boundary_flags")
    if not isinstance(flags, dict):
        fail("boundary_flags must be an object.")
    for key, expected in REQUIRED_BOUNDARY_FLAGS.items():
        if flags.get(key) is not expected:
            fail(f"boundary flag {key} must stay {expected!r} for this organization-only checkpoint.")


def assert_runtime_entries(payload: dict[str, Any]) -> None:
    seen_paths: set[str] = set()
    manifest_paths: set[str] = set()
    for index, entry in enumerate(payload["runtime_entries"], start=1):
        if not isinstance(entry, dict):
            fail(f"runtime_entries[{index}] must be an object.")

        relative_path = entry.get("path")
        path_type = entry.get("path_type")
        tier = entry.get("tier")
        role = entry.get("runtime_role")
        surface = entry.get("behavior_surface")
        legacy_path = entry.get("legacy_path")

        if not isinstance(relative_path, str) or not relative_path:
            fail(f"runtime_entries[{index}] missing path.")
        normalized = relative_path.replace("\\", "/")
        if normalized in seen_paths:
            fail(f"Duplicate runtime manifest path: {normalized}")
        seen_paths.add(normalized)
        manifest_paths.add(normalized)

        if normalized.startswith(BLOCKED_MANIFEST_PREFIXES):
            fail(f"Runtime manifest must not point at blocked private/temp path: {normalized}")
        if normalized.startswith("research/experiments/generated/"):
            fail(f"Generated evidence cannot be listed as runtime source: {normalized}")
        if not normalized.startswith("runtime/"):
            fail(f"Runtime source must physically live under runtime/: {normalized}")

        if path_type not in {"file", "directory"}:
            fail(f"{normalized} has invalid path_type: {path_type!r}")
        actual_path = ROOT / normalized
        if path_type == "file" and not actual_path.is_file():
            fail(f"Runtime manifest file is missing: {normalized}")
        if path_type == "directory" and not actual_path.is_dir():
            fail(f"Runtime manifest directory is missing: {normalized}")
        if path_type == "file" and actual_path.suffix in {".py", ".md", ".txt", ".json"}:
            runtime_text = actual_path.read_text(encoding="utf-8")
            stale_text = [item for item in STALE_RUNTIME_PATH_TEXT if item in runtime_text]
            if stale_text:
                fail(f"{normalized} contains stale pre-move runtime path text: {stale_text}")

        if not isinstance(tier, str) or not tier:
            fail(f"{normalized} missing tier.")
        if not isinstance(role, str) or len(role.strip()) < 20:
            fail(f"{normalized} needs a specific runtime_role.")
        if not isinstance(surface, list) or not surface or not all(isinstance(item, str) and item for item in surface):
            fail(f"{normalized} needs behavior_surface entries.")
        if legacy_path is not None:
            if not isinstance(legacy_path, str) or not legacy_path:
                fail(f"{normalized} has invalid legacy_path.")
            legacy_normalized = legacy_path.replace("\\", "/")
            if not legacy_normalized.startswith("scripts/"):
                fail(f"{normalized} legacy_path must stay under scripts/ for command compatibility.")
            legacy_file = ROOT / legacy_normalized
            if not legacy_file.is_file():
                fail(f"{normalized} legacy wrapper is missing: {legacy_normalized}")
            legacy_text = legacy_file.read_text(encoding="utf-8")
            expected_import = normalized[:-3].replace("/", ".")
            if expected_import not in legacy_text or "import *" not in legacy_text:
                fail(f"{legacy_normalized} must be a thin compatibility wrapper for {expected_import}.")
            if "sys.path.insert(0, str(ROOT))" not in legacy_text:
                fail(f"{legacy_normalized} must add the project root before importing {expected_import}.")
            if legacy_normalized in LEGACY_ENTRYPOINT_WRAPPERS:
                if 'if __name__ == "__main__":' not in legacy_text or f"from {expected_import} import main" not in legacy_text:
                    fail(f"{legacy_normalized} must call {expected_import}.main() when executed directly.")

    missing = sorted(REQUIRED_RUNTIME_PATHS - manifest_paths)
    if missing:
        fail(f"Runtime manifest missing required runtime path(s): {', '.join(missing)}")


def assert_non_runtime_defaults(payload: dict[str, Any]) -> None:
    defaults = payload["non_runtime_defaults"]
    patterns = {item.get("pattern") for item in defaults if isinstance(item, dict)}
    required_patterns = {
        "research/experiments/generated/**",
        "research/experiments/cases/**",
        "scripts/prod_*.py",
        "scripts/run_prod_*.py",
        "scripts/validate_*.py",
        ".tmp/**",
        "data/private/**",
    }
    missing = sorted(required_patterns - patterns)
    if missing:
        fail(f"Runtime manifest missing non-runtime default pattern(s): {', '.join(missing)}")
    for index, item in enumerate(defaults, start=1):
        if not isinstance(item, dict):
            fail(f"non_runtime_defaults[{index}] must be an object.")
        if not isinstance(item.get("pattern"), str) or not item["pattern"]:
            fail(f"non_runtime_defaults[{index}] missing pattern.")
        if not isinstance(item.get("reason"), str) or len(item["reason"].strip()) < 20:
            fail(f"non_runtime_defaults[{index}] needs a specific reason.")


def assert_runtime_doc_stubs() -> None:
    for old_path, canonical_path in CANONICAL_RUNTIME_DOC_STUBS.items():
        stub = ROOT / old_path
        canonical = ROOT / canonical_path
        if not canonical.is_file():
            fail(f"Canonical runtime doc is missing: {canonical_path}")
        if not stub.is_file():
            fail(f"Compatibility doc stub is missing: {old_path}")
        text = stub.read_text(encoding="utf-8")
        if "# Moved:" not in text or canonical_path not in text:
            fail(f"{old_path} must be a compatibility pointer to {canonical_path}.")
        if len(text) > 350:
            fail(f"{old_path} must stay a short compatibility stub, not duplicate runtime-facing content.")


def main() -> None:
    payload = load_manifest(MANIFEST_PATH)
    assert_manifest_shape(payload)
    assert_boundary_flags(payload)
    assert_runtime_entries(payload)
    assert_non_runtime_defaults(payload)
    assert_runtime_doc_stubs()
    print(
        json.dumps(
            {
                "status": "pass",
                "manifest": str(MANIFEST_PATH.relative_to(ROOT)),
                "runtime_entry_count": len(payload["runtime_entries"]),
                "non_runtime_default_count": len(payload["non_runtime_defaults"]),
                "runtime_behavior_changed": payload["boundary_flags"]["runtime_behavior_changed"],
                "response_text_changed": payload["boundary_flags"]["response_text_changed"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
