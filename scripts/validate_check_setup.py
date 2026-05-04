#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_setup.py"

SECRET_VALUES = {
    "OPENAI_API_KEY": "TEST_OPENAI_VALUE_MUST_NOT_APPEAR",
    "CARTESIA_API_KEY": "TEST_CARTESIA_VALUE_MUST_NOT_APPEAR",
    "CARTESIA_VOICE_ID": "voice-id-secret-that-must-not-appear",
}

SECRET_PATTERN = re.compile(
    "|".join(re.escape(value) for value in SECRET_VALUES.values())
)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_setup_check() -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(SECRET_VALUES)
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--json"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )


def main() -> None:
    assert_condition(SCRIPT_PATH.exists(), "Product setup verifier is missing.")

    completed = run_setup_check()
    combined_output = completed.stdout + completed.stderr
    assert_condition(SECRET_PATTERN.search(combined_output) is None, "Setup verifier leaked an environment value.")

    payload = json.loads(completed.stdout)
    assert_condition(payload["project"] == "emotion-aware-ai-sales-agent", "Unexpected project name.")
    assert_condition(payload["status"] == "pass", "Current repo setup should pass required checks.")
    assert_condition(payload["summary"]["network_calls_made"] is False, "Setup verifier must not make network calls.")
    assert_condition(payload["summary"]["secret_values_logged"] is False, "Setup verifier must not log secret values.")

    checks_by_id = {check["id"]: check for check in payload["checks"]}
    for required_check in [
        "python.version",
        "dir.scripts",
        "dir.docs_product",
        "dir.research_experiments_generated",
        "dir.data_private",
        "dir.config_local",
        "file.agents",
        "file.docs_third_party_inspirations",
        "file.docs_thesis_speech_realism_references",
        "file.docs_thesis_reference_registry",
        "file.docs_thesis_writing_guide",
        "file.docs_product_review_gates",
        "file.docs_product_product_brief",
        "file.docs_product_context_reading_policy",
        "file.docs_product_project_drift_guard",
        "file.docs_product_voice_018_sales_voice_tuning",
        "file.docs_product_voice_019_sales_tuned_live_ab_audio",
        "file.docs_product_voice_020_elevenlabs_voice_design",
        "file.docs_product_voice_021_custom_voice_comparison",
        "file.docs_product_voice_022_spoken_text_normalization",
        "file.docs_product_voice_023_speech_realism",
        "file.docs_data_private_call_center_policy",
        "file.docs_data_private_call_learning_pipeline",
        "file.data_private_gitignore",
        "file.config_local_gitignore",
        "file.config_local_voice_ids_example",
        "file.scripts_check_project_drift",
        "file.scripts_validate_project_drift_guard",
        "file.scripts_check_thesis_reference_registry",
        "file.scripts_validate_thesis_reference_registry",
        "file.scripts_check_thesis_update_gate",
        "file.scripts_validate_thesis_update_gate",
        "file.scripts_validate_private_data_boundary",
        "file.scripts_check_private_call_learning_pipeline",
        "file.scripts_init_private_call_learning_workspace",
        "file.scripts_validate_private_call_learning_pipeline",
        "file.scripts_local_voice_config",
        "file.scripts_validate_local_voice_config",
        "file.scripts_read_relevant",
        "file.scripts_validate_read_relevant",
        "file.scripts_validate_context_reading_policy",
        "file.scripts_sales_voice_tuning",
        "file.scripts_run_voice_018_sales_voice_tuning",
        "file.scripts_validate_voice_018_sales_voice_tuning",
        "file.scripts_run_voice_019_sales_tuned_live_ab_audio",
        "file.scripts_validate_voice_019_sales_tuned_live_ab_audio",
        "file.scripts_run_voice_020_elevenlabs_voice_design",
        "file.scripts_validate_voice_020_elevenlabs_voice_design",
        "file.scripts_run_voice_021_custom_voice_comparison",
        "file.scripts_validate_voice_021_custom_voice_comparison",
        "file.scripts_spoken_text_normalization",
        "file.scripts_run_voice_022_spoken_text_normalization",
        "file.scripts_validate_voice_022_spoken_text_normalization",
        "file.scripts_speech_realism",
        "file.scripts_run_voice_023_speech_realism",
        "file.scripts_validate_voice_023_speech_realism",
        "file.scripts_realtime_turn_cli",
        "file.scripts_start_guarded_local_server",
        "file.research_private_call_learning_001",
        "file.research_case_private_call_learning_001",
        "file.research_case_voice_023_speech_realism",
        "write.research_experiments_generated",
    ]:
        assert_condition(required_check in checks_by_id, f"Missing setup check: {required_check}")
        assert_condition(checks_by_id[required_check]["status"] == "pass", f"Setup check failed: {required_check}")

    env_by_name = {entry["name"]: entry for entry in payload["environment"]}
    for name in SECRET_VALUES:
        assert_condition(name in env_by_name, f"Missing environment gate: {name}")
        assert_condition(env_by_name[name]["present"] is True, f"Expected test env var to be detected: {name}")
        assert_condition(env_by_name[name]["value_logged"] is False, f"Environment value should not be logged: {name}")
        assert_condition(env_by_name[name]["required_for_default_setup"] is False, f"{name} should not be required by default.")

    print("Product setup verifier validation passed.")


if __name__ == "__main__":
    main()
