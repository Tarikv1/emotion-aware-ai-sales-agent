#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_hosted_backend_config.json"
ARCH_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_integration_architecture_plan.json"
CONTRACT_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_sales_brain_tool_contract.json"
MOCK_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_sales_brain_mock.py"
PROMPT_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_sandbox_agent_prompt.md"
STAGE_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_sandbox_call_stage_plan.json"

SOURCE_URLS = [
    "https://docs.ultravox.ai/",
    "https://docs.ultravox.ai/gettingstarted/how-ultravox-works",
    "https://docs.ultravox.ai/tools/overview",
    "https://docs.ultravox.ai/agents/call-stages",
    "https://docs.ultravox.ai/gettingstarted/prompting",
    "https://github.com/fixie-ai/ultravox",
]

SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|u[a-z]?v[A-Za-z0-9_-]{20,}|ULTRAVOX_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key:\s*[A-Za-z0-9])"
)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def fail(message: str) -> None:
    raise AssertionError(message)


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing file: {rel(path)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"{rel(path)} must be a JSON object")
    return payload


def assert_value(payload: dict, key: str, expected) -> None:
    if payload.get(key) != expected:
        fail(f"{key} must be {expected!r}, got {payload.get(key)!r}")


def assert_contains_all(values: list, required: list[str], label: str) -> None:
    missing = [item for item in required if item not in values]
    if missing:
        fail(f"{label} missing required value(s): {missing}")


def assert_no_secret_text(path: Path) -> None:
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    match = SECRET_PATTERN.search(text)
    if match:
        fail(f"{rel(path)} contains a secret-like token: {match.group(0)!r}")


def assert_no_forbidden_artifacts() -> None:
    forbidden_suffixes = {".wav", ".mp3", ".flac", ".m4a", ".ogg", ".gguf", ".safetensors", ".pt", ".pth", ".bin"}
    phase_dirs = [
        ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-SANDBOX-001",
        ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TOOL-BOUNDARY-MOCK-001",
        ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001",
    ]
    found = []
    for phase_dir in phase_dirs:
        if phase_dir.exists():
            found.extend(rel(path) for path in phase_dir.rglob("*") if path.suffix.lower() in forbidden_suffixes)
    if found:
        fail(f"phase evidence must not contain audio/model artifacts: {found}")


def main() -> None:
    for path in (CONFIG_PATH, ARCH_PATH, CONTRACT_PATH, MOCK_PATH, PROMPT_PATH, STAGE_PATH):
        if not path.is_file():
            fail(f"required Phase 4J0 artifact missing: {rel(path)}")
        assert_no_secret_text(path)

    config = load_json(CONFIG_PATH)
    assert_value(config, "backend_id", "ultravox_hosted_realtime")
    assert_value(config, "role_in_project", "hosted_speech_native_interface_candidate")
    assert_value(config, "not_sales_brain", True)
    assert_value(config, "project_sales_brain_required", True)
    assert_value(config, "canonical_memory_owner", "project_runtime")
    assert_value(config, "ultravox_session_memory_allowed", True)
    assert_value(config, "final_campaign_truth_owner", "project_runtime")
    assert_value(config, "tool_call_required_for_sales_moves", True)
    assert_value(config, "live_wiring_allowed", False)
    assert_value(config, "outbound_phone_calls_allowed", False)
    assert_value(config, "provider_calls_allowed_by_default", False)
    assert_value(config, "provider_calls_allowed_only_with_env_gates", True)
    assert_contains_all(config.get("source_urls", []), SOURCE_URLS, "source_urls")
    assert_contains_all(config.get("secrets_required", []), ["ULTRAVOX_API_KEY"], "secrets_required")
    assert_contains_all(
        config.get("env_gates", []),
        ["ENABLE_ULTRAVOX_SANDBOX=1", "ULTRAVOX_API_KEY present", "LOCAL_ULTRAVOX_ALLOW_PROVIDER_CALLS=1"],
        "env_gates",
    )
    assert_contains_all(
        config.get("evidence_policy", []),
        ["no raw private audio", "no customer data", "synthetic/sanitized prompts only", "transcripts sanitized", "no audio committed"],
        "evidence_policy",
    )

    arch = load_json(ARCH_PATH)
    assert_value(arch, "project_sales_brain_owner", "project_runtime")
    assert_value(arch, "campaign_truth_owner", "project_runtime")
    assert_value(arch, "canonical_memory_owner", "project_runtime")
    assert_value(arch, "ultravox_product_truth_owner", False)
    assert_value(arch, "live_wiring_allowed", False)
    modes = {mode.get("mode_id"): mode for mode in arch.get("modes", []) if isinstance(mode, dict)}
    if modes.get("mode_a", {}).get("status") != "rejected_not_allowed":
        fail("Mode A must be rejected/not allowed")
    if modes.get("mode_b", {}).get("status") != "preferred_sandbox_candidate":
        fail("Mode B must be the preferred sandbox candidate")
    if modes.get("mode_c", {}).get("status") != "fallback_candidate":
        fail("Mode C must be the fallback candidate")
    mode_b = modes.get("mode_b", {})
    assert_contains_all(
        list(mode_b),
        [
            "tool_request_schema",
            "tool_response_schema",
            "memory_handoff_rules",
            "verifier_boundary",
            "side_effect_prohibition",
            "transcript_evidence_handling",
            "failure_fallback",
        ],
        "mode_b",
    )

    contract = load_json(CONTRACT_PATH)
    assert_value(contract, "tool_name", "project_sales_brain_next_move")
    assert_value(contract, "synthetic_only", True)
    assert_contains_all(
        contract.get("hard_rules", []),
        [
            "no CRM/email/calendar side effects",
            "no fake follow-up",
            "no unsupported product claims",
            "no raw Fish tags",
            "no internal policy language",
            "no raw private transcript/audio in public evidence",
            "if unsure, return natural clarification",
        ],
        "hard_rules",
    )
    response_fields = contract.get("response_fields", {})
    if response_fields.get("side_effects_allowed", {}).get("constant") is not False:
        fail("tool contract must force side_effects_allowed false")

    prompt_text = PROMPT_PATH.read_text(encoding="utf-8").lower()
    for required in (
        "ultravox is the voice interface",
        "do not invent product facts",
        "project_sales_brain_next_move",
        "do not claim email/calendar/crm actions",
        "do not claim openai affiliation",
        "keep turns short",
        "stop or no contact",
    ):
        if required not in prompt_text:
            fail(f"prompt missing required boundary text: {required}")

    stage_plan = load_json(STAGE_PATH)
    assert_value(stage_plan, "live_wiring_allowed", False)
    assert_contains_all(
        [stage.get("stage_id") for stage in stage_plan.get("stages", []) if isinstance(stage, dict)],
        ["opening_orientation", "discovery", "objection_handling", "recommendation", "close", "boundary_stop", "fallback"],
        "call stages",
    )

    mock_text = MOCK_PATH.read_text(encoding="utf-8").lower()
    for forbidden in ("openai", "elevenlabs", "ollama", "kokoro", "liquid", "subprocess", "urllib", "requests"):
        if forbidden in mock_text:
            fail(f"mock tool must not contain provider/inference token: {forbidden}")

    assert_no_forbidden_artifacts()
    print("ULTRAVOX hosted backend config validation passed.")


if __name__ == "__main__":
    main()
