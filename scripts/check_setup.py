#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any


PROJECT_NAME = "emotion-aware-ai-sales-agent"
ROOT = Path(__file__).resolve().parents[1]
MIN_PYTHON = (3, 10)

REQUIRED_DIRS = [
    ("dir.scripts", "scripts", "Script directory"),
    ("dir.docs_product", "docs/product", "Product documentation"),
    ("dir.docs_data", "docs/data", "Data documentation"),
    ("dir.research_experiments", "research/experiments", "Experiment notes"),
    ("dir.research_experiments_cases", "research/experiments/cases", "Experiment case files"),
    ("dir.research_experiments_generated", "research/experiments/generated", "Generated experiment artifacts"),
    ("dir.packages_prompts", "packages/prompts", "Prompt package"),
    ("dir.data_public", "data/public", "Public data folder"),
    ("dir.data_private", "data/private", "Local-only private call-center data folder"),
    ("dir.data_processed", "data/processed", "Processed data folder"),
]

OPTIONAL_DIRS = [
    ("dir.data_private_restricted", "data/private-restricted", "Restricted data folder"),
]

REQUIRED_FILES = [
    ("file.agents", "AGENTS.md", "Project-local Codex instructions"),
    ("file.readme", "README.md", "Project README"),
    ("file.program", "program.md", "Research program"),
    ("file.docs_third_party_inspirations", "docs/third-party-inspirations.md", "Third-party inspiration and attribution notes"),
    ("file.docs_product_review_gates", "docs/product-review-gates.md", "Product review gates"),
    ("file.docs_product_commands", "docs/product/COMMANDS.md", "Product command map"),
    ("file.docs_product_product_brief", "docs/product/PRODUCT_BRIEF.md", "Product brief"),
    ("file.docs_product_client_mvp_workflow", "docs/product/CLIENT_MVP_WORKFLOW.md", "Client MVP workflow"),
    ("file.docs_product_context_reading_policy", "docs/product/CONTEXT_READING_POLICY.md", "Context reading policy"),
    ("file.docs_product_project_self_containment", "docs/product/PROJECT_SELF_CONTAINMENT_POLICY.md", "Project self-containment policy"),
    ("file.docs_product_project_drift_guard", "docs/product/PROJECT_DRIFT_GUARD.md", "Project drift guard"),
    ("file.docs_product_voice_provider_run_boundary", "docs/product/VOICE_PROVIDER_RUN_BOUNDARY.md", "Voice provider run boundary"),
    ("file.docs_product_voice_generated_audio_asset_log", "docs/product/VOICE_GENERATED_AUDIO_ASSET_LOG.md", "Voice generated audio asset log"),
    ("file.docs_product_realtime_agent_architecture", "docs/product/REALTIME_AGENT_ARCHITECTURE.md", "Realtime architecture"),
    ("file.docs_product_realtime_turn_cli", "docs/product/REALTIME_TURN_CLI.md", "Realtime CLI docs"),
    ("file.docs_product_voice_007_provider_readiness", "docs/product/VOICE_007_PROVIDER_READINESS_GATE.md", "Voice provider readiness gate"),
    ("file.docs_product_voice_012_speech_naturalness", "docs/product/VOICE_012_SPEECH_NATURALNESS_LAYER.md", "Voice speech naturalness layer"),
    ("file.docs_product_voice_013_elevenlabs_tts", "docs/product/VOICE_013_ELEVENLABS_TTS_SMOKE_TEST.md", "ElevenLabs TTS smoke test"),
    ("file.docs_product_voice_014_provider_listening", "docs/product/VOICE_014_PROVIDER_LISTENING_COMPARISON.md", "Voice provider listening comparison"),
    ("file.docs_product_voice_015_prosody_naturalness", "docs/product/VOICE_015_PROSODY_NATURALNESS_LAYER.md", "Voice prosody naturalness layer"),
    ("file.docs_product_voice_016_provider_prosody", "docs/product/VOICE_016_PROVIDER_PROSODY_RENDERING.md", "Voice provider prosody rendering"),
    ("file.docs_product_voice_017_live_ab_audio", "docs/product/VOICE_017_LIVE_AB_AUDIO.md", "Voice live A/B audio harness"),
    ("file.docs_product_voice_018_sales_voice_tuning", "docs/product/VOICE_018_SALES_VOICE_TUNING.md", "Voice sales tuning"),
    ("file.docs_product_voice_019_sales_tuned_live_ab_audio", "docs/product/VOICE_019_SALES_TUNED_LIVE_AB_AUDIO.md", "Voice sales tuned live A/B audio"),
    ("file.docs_product_resp_002_runtime_voice_delivery", "docs/product/RESP_002_RUNTIME_VOICE_DELIVERY.md", "Runtime voice delivery"),
    ("file.docs_product_resp_003_runtime_live_tts", "docs/product/RESP_003_RUNTIME_LIVE_TTS.md", "Runtime live TTS delivery"),
    ("file.docs_data_data_usage_policy", "docs/data/DATA_USAGE_POLICY.md", "Data usage policy"),
    ("file.docs_data_private_call_center_policy", "docs/data/PRIVATE_CALL_CENTER_DATA_POLICY.md", "Private call-center data policy"),
    ("file.data_private_gitignore", "data/private/.gitignore", "Private data local ignore rule"),
    ("file.scripts_realtime_turn_cli", "scripts/realtime_turn_cli.py", "Realtime turn CLI"),
    ("file.scripts_start_guarded_local_server", "scripts/start_guarded_local_server.py", "Guarded local server launcher"),
    ("file.scripts_product_agent_output_contract", "scripts/product_agent_output_contract.py", "Product output contract"),
    ("file.scripts_validate_product_agent_output_contract", "scripts/validate_product_agent_output_contract.py", "Output contract validator"),
    ("file.scripts_validate_self_contained_project_policy", "scripts/validate_self_contained_project_policy.py", "Self-contained project policy validator"),
    ("file.scripts_check_project_drift", "scripts/check_project_drift.py", "Project drift guard"),
    ("file.scripts_validate_project_drift_guard", "scripts/validate_project_drift_guard.py", "Project drift guard validator"),
    ("file.scripts_validate_private_data_boundary", "scripts/validate_private_data_boundary.py", "Private data boundary validator"),
    ("file.scripts_evaluate_voice_provider_readiness", "scripts/evaluate_voice_provider_readiness.py", "Voice provider readiness evaluator"),
    ("file.scripts_speech_naturalness", "scripts/speech_naturalness.py", "Speech naturalness renderer"),
    ("file.scripts_validate_voice_012_speech_naturalness", "scripts/validate_voice_012_speech_naturalness.py", "Speech naturalness validator"),
    ("file.scripts_run_voice_013_elevenlabs_tts_smoke", "scripts/run_voice_013_elevenlabs_tts_smoke.py", "ElevenLabs TTS smoke runner"),
    ("file.scripts_validate_voice_013_elevenlabs_tts_smoke", "scripts/validate_voice_013_elevenlabs_tts_smoke.py", "ElevenLabs TTS smoke validator"),
    ("file.scripts_run_voice_014_provider_listening_comparison", "scripts/run_voice_014_provider_listening_comparison.py", "Provider listening comparison runner"),
    ("file.scripts_validate_voice_014_provider_listening_comparison", "scripts/validate_voice_014_provider_listening_comparison.py", "Provider listening comparison validator"),
    ("file.scripts_prosody_naturalness", "scripts/prosody_naturalness.py", "Prosody naturalness planner"),
    ("file.scripts_run_voice_015_prosody_naturalness", "scripts/run_voice_015_prosody_naturalness.py", "Prosody naturalness runner"),
    ("file.scripts_validate_voice_015_prosody_naturalness", "scripts/validate_voice_015_prosody_naturalness.py", "Prosody naturalness validator"),
    ("file.scripts_provider_prosody_rendering", "scripts/provider_prosody_rendering.py", "Provider prosody renderer"),
    ("file.scripts_run_voice_016_provider_prosody", "scripts/run_voice_016_provider_prosody_rendering.py", "Provider prosody rendering runner"),
    ("file.scripts_validate_voice_016_provider_prosody", "scripts/validate_voice_016_provider_prosody_rendering.py", "Provider prosody rendering validator"),
    ("file.scripts_run_voice_017_live_ab_audio", "scripts/run_voice_017_live_ab_audio.py", "Live A/B audio runner"),
    ("file.scripts_validate_voice_017_live_ab_audio", "scripts/validate_voice_017_live_ab_audio.py", "Live A/B audio validator"),
    ("file.scripts_sales_voice_tuning", "scripts/sales_voice_tuning.py", "Sales voice tuning module"),
    ("file.scripts_run_voice_018_sales_voice_tuning", "scripts/run_voice_018_sales_voice_tuning.py", "Sales voice tuning runner"),
    ("file.scripts_validate_voice_018_sales_voice_tuning", "scripts/validate_voice_018_sales_voice_tuning.py", "Sales voice tuning validator"),
    ("file.scripts_run_voice_019_sales_tuned_live_ab_audio", "scripts/run_voice_019_sales_tuned_live_ab_audio.py", "Sales tuned live A/B audio runner"),
    ("file.scripts_validate_voice_019_sales_tuned_live_ab_audio", "scripts/validate_voice_019_sales_tuned_live_ab_audio.py", "Sales tuned live A/B audio validator"),
    ("file.scripts_runtime_voice_delivery", "scripts/runtime_voice_delivery.py", "Runtime voice delivery module"),
    ("file.scripts_generate_runtime_voice_delivery", "scripts/generate_runtime_voice_delivery.py", "Runtime voice delivery runner"),
    ("file.scripts_validate_resp_002_runtime_voice_delivery", "scripts/validate_resp_002_runtime_voice_delivery.py", "Runtime voice delivery validator"),
    ("file.scripts_tts_provider_clients", "scripts/tts_provider_clients.py", "Project-local TTS provider clients"),
    ("file.scripts_runtime_tts_delivery", "scripts/runtime_tts_delivery.py", "Runtime live TTS delivery module"),
    ("file.scripts_generate_runtime_tts_delivery", "scripts/generate_runtime_tts_delivery.py", "Runtime live TTS delivery runner"),
    ("file.scripts_validate_resp_003_runtime_live_tts", "scripts/validate_resp_003_runtime_live_tts.py", "Runtime live TTS delivery validator"),
    ("file.scripts_run_product_simulation", "scripts/run_product_simulation.py", "Product simulation runner"),
    ("file.scripts_run_rule_baseline", "scripts/run_rule_baseline.py", "Rule baseline runner"),
    ("file.scripts_read_relevant", "scripts/read_relevant.py", "Product-local relevant reader"),
    ("file.scripts_validate_read_relevant", "scripts/validate_read_relevant.py", "Relevant reader validator"),
    ("file.scripts_validate_context_reading_policy", "scripts/validate_context_reading_policy.py", "Context reading policy validator"),
]

OPTIONAL_ENV_VARS = [
    ("OPENAI_API_KEY", "Optional LLM product-agent runs"),
    ("CARTESIA_API_KEY", "Optional live Cartesia TTS smoke tests"),
    ("CARTESIA_VOICE_ID", "Optional live Cartesia TTS smoke tests"),
    ("CARTESIA_VOICE_ID_DE", "Optional live Cartesia German TTS smoke tests"),
    ("CARTESIA_VOICE_ID_EN", "Optional live Cartesia English TTS smoke tests"),
    ("ELEVENLABS_API_KEY", "Optional live ElevenLabs TTS smoke tests"),
    ("ELEVENLABS_VOICE_ID", "Optional live ElevenLabs TTS smoke tests"),
    ("ELEVENLABS_VOICE_ID_DE", "Optional live ElevenLabs German TTS smoke tests"),
    ("ELEVENLABS_VOICE_ID_EN", "Optional live ElevenLabs English TTS smoke tests"),
]


def build_check(check_id: str, status: str, severity: str, message: str, path: str | None = None) -> dict[str, Any]:
    check: dict[str, Any] = {
        "id": check_id,
        "status": status,
        "severity": severity,
        "message": message,
    }
    if path is not None:
        check["path"] = path
    return check


def check_python_version() -> dict[str, Any]:
    current = sys.version_info
    current_text = f"{current.major}.{current.minor}.{current.micro}"
    minimum_text = ".".join(str(part) for part in MIN_PYTHON)
    if (current.major, current.minor) >= MIN_PYTHON:
        return build_check(
            "python.version",
            "pass",
            "required",
            f"Python {current_text} meets minimum {minimum_text}.",
        )
    return build_check(
        "python.version",
        "fail",
        "required",
        f"Python {current_text} is below minimum {minimum_text}.",
    )


def check_directories(root: Path) -> list[dict[str, Any]]:
    checks = []
    for check_id, relative_path, label in REQUIRED_DIRS:
        path = root / relative_path
        if path.is_dir():
            checks.append(build_check(check_id, "pass", "required", f"{label} exists.", relative_path))
        else:
            checks.append(build_check(check_id, "fail", "required", f"{label} is missing.", relative_path))
    for check_id, relative_path, label in OPTIONAL_DIRS:
        path = root / relative_path
        if path.is_dir():
            checks.append(build_check(check_id, "pass", "optional", f"{label} exists.", relative_path))
        else:
            checks.append(
                build_check(
                    check_id,
                    "pass",
                    "optional",
                    f"{label} is absent. Default setup does not require restricted private data.",
                    relative_path,
                )
            )
    return checks


def check_files(root: Path) -> list[dict[str, Any]]:
    checks = []
    for check_id, relative_path, label in REQUIRED_FILES:
        path = root / relative_path
        if path.is_file():
            checks.append(build_check(check_id, "pass", "required", f"{label} exists.", relative_path))
        else:
            checks.append(build_check(check_id, "fail", "required", f"{label} is missing.", relative_path))
    return checks


def check_write_path(root: Path) -> dict[str, Any]:
    relative_path = "research/experiments/generated"
    write_dir = root / relative_path
    if not write_dir.is_dir():
        return build_check(
            "write.research_experiments_generated",
            "fail",
            "required",
            "Generated experiment artifact directory is missing.",
            relative_path,
        )
    if not os.access(write_dir, os.W_OK):
        return build_check(
            "write.research_experiments_generated",
            "fail",
            "required",
            "Generated experiment artifact directory does not appear writable.",
            relative_path,
        )

    return build_check(
        "write.research_experiments_generated",
        "pass",
        "required",
        "Generated experiment artifact directory is present and reports writable. No file was written.",
        relative_path,
    )


def build_environment_report() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "present": bool(os.environ.get(name)),
            "required_for_default_setup": False,
            "value_logged": False,
            "used_for": description,
        }
        for name, description in OPTIONAL_ENV_VARS
    ]


def summarize_checks(checks: list[dict[str, Any]], strict: bool) -> tuple[str, dict[str, Any]]:
    failures = [check for check in checks if check["status"] == "fail"]
    warnings = [check for check in checks if check["status"] == "warning"]
    status = "fail" if failures or (strict and warnings) else "pass"
    return status, {
        "check_count": len(checks),
        "failures": len(failures),
        "warnings": len(warnings),
        "strict": strict,
        "network_calls_made": False,
        "secret_values_logged": False,
    }


def build_report(root: Path, strict: bool) -> dict[str, Any]:
    checks = [
        build_check(
            "root.exists",
            "pass" if root.is_dir() else "fail",
            "required",
            "Project root exists." if root.is_dir() else "Project root is missing.",
            ".",
        ),
        check_python_version(),
    ]
    checks.extend(check_directories(root))
    checks.extend(check_files(root))
    checks.append(check_write_path(root))

    status, summary = summarize_checks(checks, strict)
    return {
        "project": PROJECT_NAME,
        "root": str(root),
        "status": status,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "python": platform.python_version(),
        },
        "summary": summary,
        "environment": build_environment_report(),
        "checks": checks,
    }


def print_text_report(report: dict[str, Any]) -> None:
    print(f"{report['project']} setup check")
    print(f"Root: {report['root']}")
    print(f"Status: {report['status']}")
    print(
        "Summary: "
        f"{report['summary']['failures']} failure(s), "
        f"{report['summary']['warnings']} warning(s), "
        f"{report['summary']['check_count']} check(s)"
    )
    print("Network calls made: false")
    print("Secret values logged: false")
    print()
    print("Environment gates:")
    for entry in report["environment"]:
        state = "present" if entry["present"] else "not set"
        print(f"- {entry['name']}: {state}; value logged: false; default required: false")
    print()
    print("Checks:")
    for check in report["checks"]:
        path = f" [{check['path']}]" if "path" in check else ""
        print(f"- {check['status'].upper()} {check['id']}{path}: {check['message']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check local setup for the Emotion Aware AI Sales Agent product repo.")
    parser.add_argument("--root", default=str(ROOT), help="Project root to check. Defaults to this repository root.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    report = build_report(root, args.strict)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_text_report(report)

    raise SystemExit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
