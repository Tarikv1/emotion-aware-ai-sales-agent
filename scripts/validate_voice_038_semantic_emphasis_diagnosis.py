#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.config.local_voice_config import LOCAL_VOICE_IDS_PATH, load_local_voice_ids, value_if_present


RUNNER_PATH = ROOT / "scripts" / "run_voice_038_semantic_emphasis_diagnosis.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "voice-038-semantic-emphasis-diagnosis.json"
DOC_PATH = ROOT / "docs" / "product" / "VOICE_038_SEMANTIC_EMPHASIS_DIAGNOSIS.md"
EXPECTED_RUN_DIR = ROOT / "research" / "experiments" / "generated" / "VOICE-038-semantic-emphasis-diagnosis"
EXPECTED_RESULTS_PATH = EXPECTED_RUN_DIR / "results.json"
EXPECTED_REPORT_PATH = EXPECTED_RUN_DIR / "report.md"
EXPECTED_AUDIO_DIR = EXPECTED_RUN_DIR / "audio"
VALIDATION_RUN_DIR = ROOT / ".tmp" / "voice-038-validation" / f"run-{uuid.uuid4().hex}"
RESULTS_PATH = VALIDATION_RUN_DIR / "results.json"
REPORT_PATH = VALIDATION_RUN_DIR / "report.md"
AUDIO_DIR = VALIDATION_RUN_DIR / "audio"

REQUIRED_VARIANTS = {
    "baseline_original_clause",
    "clear_opening_simple_clause",
    "chunked_decision_clause",
    "benefit_first_clause",
    "semantic_focus_question",
    "opening_alternative",
}
FRAGILE_CLAUSE = "whether reviewing options is worth your time"


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=90)


def load_runner_module() -> Any:
    spec = importlib.util.spec_from_file_location("run_voice_038_semantic_emphasis_diagnosis", RUNNER_PATH)
    assert_condition(spec is not None and spec.loader is not None, "Could not load VOICE-038 runner module.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect_local_voice_ids(node: Any, parent_key: str = "") -> list[str]:
    values: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key in {"voice_id", "en", "de", "default", "english_sales_voice_v1", "german_sales_voice_v1"}:
                voice_id = value_if_present(value)
                if voice_id:
                    values.append(voice_id)
                continue
            values.extend(collect_local_voice_ids(value, key))
    elif isinstance(node, list):
        for value in node:
            values.extend(collect_local_voice_ids(value, parent_key))
    elif parent_key in {"aliases", "candidates"}:
        voice_id = value_if_present(node)
        if voice_id:
            values.append(voice_id)
    return values


def assert_no_raw_local_voice_ids(payload_text: str) -> None:
    if not LOCAL_VOICE_IDS_PATH.is_file():
        return
    local_config = load_local_voice_ids(LOCAL_VOICE_IDS_PATH)
    for voice_id in collect_local_voice_ids(local_config):
        assert_condition(voice_id not in payload_text, "A raw local voice ID leaked into a VOICE-038 artifact.")


def validate_default_paths() -> None:
    module = load_runner_module()
    assert_condition(module.DEFAULT_RUN_DIR == EXPECTED_RUN_DIR, "VOICE-038 default run directory should be organized.")
    assert_condition(module.DEFAULT_OUT == EXPECTED_RESULTS_PATH, "VOICE-038 default output should be results.json in the run folder.")
    assert_condition(module.DEFAULT_REPORT_OUT == EXPECTED_REPORT_PATH, "VOICE-038 report should be report.md in the run folder.")
    assert_condition(module.DEFAULT_AUDIO_DIR == EXPECTED_AUDIO_DIR, "VOICE-038 audio should go under audio/ in the run folder.")


def run_default_harness() -> subprocess.CompletedProcess[str]:
    return run_command(
        [
            sys.executable,
            str(RUNNER_PATH),
            "--cases",
            str(CASES_PATH),
            "--out",
            str(RESULTS_PATH),
            "--report-out",
            str(REPORT_PATH),
            "--audio-dir",
            str(AUDIO_DIR),
        ]
    )


def validate_results(payload: dict[str, Any], payload_text: str) -> None:
    summary = payload["summary"]
    results = payload["results"]
    variant_ids = {result["variant_id"] for result in results}

    assert_condition(payload["voice_milestone"] == "VOICE-038", "Unexpected voice milestone.")
    assert_condition(payload["experiment_scope"]["purpose"] == "semantic-emphasis-rhythm-diagnosis", "Unexpected VOICE-038 purpose.")
    assert_condition(summary["script_count"] == 1, "VOICE-038 should isolate one English script.")
    assert_condition(summary["variant_count"] == len(REQUIRED_VARIANTS), "VOICE-038 should include the expected diagnostic variants.")
    assert_condition(summary["result_count"] == len(REQUIRED_VARIANTS), "VOICE-038 should produce one result per variant.")
    assert_condition(summary["languages"] == {"en": len(REQUIRED_VARIANTS)}, "VOICE-038 should be English-only.")
    assert_condition(REQUIRED_VARIANTS.issubset(variant_ids), "VOICE-038 is missing required variants.")
    assert_condition(summary["live_call_requested"] is False, "VOICE-038 default mode must be dry-run.")
    assert_condition(summary["api_calls_made"] == 0, "VOICE-038 dry-run must not call providers.")
    assert_condition(summary["audio_files_created"] == 0, "VOICE-038 dry-run must not create audio.")
    assert_condition(summary["fallback_count"] == summary["result_count"], "VOICE-038 dry-run should fallback every result.")
    assert_condition(summary["customer_audio_uploaded"] is False, "VOICE-038 must not upload customer audio.")
    assert_condition(summary["private_audio_used"] is False, "VOICE-038 must not use private audio.")
    assert_condition(summary["voice_cloning_used"] is False, "VOICE-038 must not use voice cloning.")
    assert_condition(summary["raw_voice_ids_logged"] is False, "VOICE-038 must not log raw voice IDs.")
    assert_condition(summary["quality_claim_allowed"] is False, "VOICE-038 must not claim quality without listening review.")
    assert_condition(summary["fragile_clause_variants"] >= 1, "VOICE-038 should include at least one fragile-clause baseline.")
    assert_condition(summary["replacement_clause_variants"] >= 4, "VOICE-038 should include multiple replacement-clause variants.")
    assert_condition(summary["break_tag_variant_count"] >= 1, "VOICE-038 should include at least one break-tag rhythm variant.")

    for result in results:
        assert_condition(result["language"] == "en", "VOICE-038 result should be English.")
        assert_condition(result["api_key_value_logged"] is False, "VOICE-038 must not log API key values.")
        assert_condition(result["voice_id_value_logged"] is False, "VOICE-038 must not log voice ID values.")
        assert_condition(result["customer_audio_uploaded"] is False, "VOICE-038 must not upload customer audio.")
        assert_condition(result["private_audio_used"] is False, "VOICE-038 must not use private audio.")
        assert_condition(result["voice_cloning_used"] is False, "VOICE-038 must not use voice cloning.")
        assert_condition(result["synthetic_prompt_only"] is True, "VOICE-038 should use synthetic prompts only.")
        assert_condition(result["validation"]["passed"] is True, f"{result['variant_id']} validation failed.")
        assert_condition("**" not in result["tts_input_text"], f"{result['variant_id']} should not use Markdown emphasis.")
        assert_condition("[emphasis]" not in result["tts_input_text"].lower(), f"{result['variant_id']} should not use fake emphasis tags.")
        assert_condition(0.5 <= float(result["voice_settings"]["stability"]) <= 0.7, "VOICE-038 stability should stay bounded.")
        assert_condition(0.0 <= float(result["voice_settings"]["style"]) <= 0.2, "VOICE-038 style should stay bounded.")
        assert_condition(1.03 <= float(result["voice_settings"]["speed"]) <= 1.1, "VOICE-038 speed should stay in sales-listening bounds.")
        assert_condition(result["fragile_clause_target"] == FRAGILE_CLAUSE, "VOICE-038 should record the fragile clause target.")
        if result["variant_id"] == "baseline_original_clause":
            assert_condition(FRAGILE_CLAUSE in result["tts_input_text"], "Baseline should preserve the fragile clause.")
        else:
            assert_condition(
                FRAGILE_CLAUSE not in result["tts_input_text"],
                f"{result['variant_id']} should test a replacement for the fragile clause.",
            )

    assert_no_raw_local_voice_ids(payload_text)
    report_text = REPORT_PATH.read_text(encoding="utf-8")
    assert_condition("semantic emphasis" in report_text.lower(), "VOICE-038 report should explain semantic emphasis.")
    assert_condition(FRAGILE_CLAUSE in report_text, "VOICE-038 report should name the fragile phrase.")
    assert_condition("human listening review" in report_text.lower(), "VOICE-038 report should require human listening review.")


def validate_forced_missing_key_path() -> None:
    completed = run_command(
        [
            sys.executable,
            str(RUNNER_PATH),
            "--cases",
            str(CASES_PATH),
            "--out",
            str(RESULTS_PATH),
            "--report-out",
            str(REPORT_PATH),
            "--audio-dir",
            str(AUDIO_DIR),
            "--live",
            "--force-key-missing",
            "--timeout-seconds",
            "2",
        ]
    )
    assert_condition(completed.returncode == 0, f"VOICE-038 forced-missing live gate failed: {completed.stderr or completed.stdout}")
    payload = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    assert_condition(payload["summary"]["live_call_requested"] is True, "Forced-missing path should request live mode.")
    assert_condition(payload["summary"]["api_calls_made"] == 0, "Forced-missing path must not call provider.")
    assert_condition(payload["summary"]["audio_files_created"] == 0, "Forced-missing path must not create audio.")
    assert_condition(payload["summary"]["fallback_count"] == payload["summary"]["result_count"], "Forced-missing path should fallback every result.")


def main() -> None:
    assert_condition(RUNNER_PATH.exists(), "VOICE-038 runner is missing.")
    assert_condition(CASES_PATH.exists(), "VOICE-038 case file is missing.")
    assert_condition(DOC_PATH.exists(), "VOICE-038 product doc is missing.")
    validate_default_paths()

    completed = run_default_harness()
    assert_condition(completed.returncode == 0, f"VOICE-038 runner failed: {completed.stderr or completed.stdout}")
    assert_condition(RESULTS_PATH.exists(), "VOICE-038 results were not created.")
    assert_condition(REPORT_PATH.exists(), "VOICE-038 report was not created.")

    payload_text = RESULTS_PATH.read_text(encoding="utf-8") + "\n" + REPORT_PATH.read_text(encoding="utf-8")
    payload = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    validate_results(payload, payload_text)

    validate_forced_missing_key_path()
    completed = run_default_harness()
    assert_condition(completed.returncode == 0, f"VOICE-038 dry-run restore failed: {completed.stderr or completed.stdout}")

    print("VOICE-038 semantic emphasis diagnosis validation passed.")


if __name__ == "__main__":
    main()
