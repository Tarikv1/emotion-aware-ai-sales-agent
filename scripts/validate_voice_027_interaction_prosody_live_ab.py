#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

from local_voice_config import LOCAL_VOICE_IDS_PATH, load_local_voice_ids, value_if_present


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_voice_027_interaction_prosody_live_ab.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "voice-027-interaction-prosody-live-ab.json"
EXPECTED_RUN_DIR = ROOT / "research" / "experiments" / "generated" / "VOICE-027-interaction-prosody-live-ab"
EXPECTED_RESULTS_PATH = EXPECTED_RUN_DIR / "results.json"
EXPECTED_REPORT_PATH = EXPECTED_RUN_DIR / "report.md"
EXPECTED_AUDIO_DIR = EXPECTED_RUN_DIR / "audio"
VALIDATION_RUN_DIR = ROOT / ".tmp" / "voice-027-validation" / f"run-{uuid.uuid4().hex}"
RESULTS_PATH = VALIDATION_RUN_DIR / "results.json"
REPORT_PATH = VALIDATION_RUN_DIR / "report.md"
AUDIO_DIR = VALIDATION_RUN_DIR / "audio"


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=90)


def load_runner_module() -> Any:
    spec = importlib.util.spec_from_file_location("run_voice_027_interaction_prosody_live_ab", RUNNER_PATH)
    assert_condition(spec is not None and spec.loader is not None, "Could not load VOICE-027 runner module.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_runner_default_paths() -> None:
    module = load_runner_module()
    assert_condition(module.DEFAULT_RUN_DIR == EXPECTED_RUN_DIR, "VOICE-027 default run directory should be organized.")
    assert_condition(module.DEFAULT_OUT == EXPECTED_RESULTS_PATH, "VOICE-027 default results path should be results.json inside the run folder.")
    assert_condition(module.DEFAULT_REPORT_OUT == EXPECTED_REPORT_PATH, "VOICE-027 default report path should be report.md inside the run folder.")
    assert_condition(module.DEFAULT_AUDIO_DIR == EXPECTED_AUDIO_DIR, "VOICE-027 default audio path should be audio/ inside the run folder.")


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
        assert_condition(voice_id not in payload_text, "A raw local voice ID leaked into a generated artifact.")


def validate_result_pair(results: list[dict[str, Any]], script_id: str) -> None:
    by_variant = {result["variant_id"]: result for result in results if result["script_id"] == script_id}
    assert_condition(set(by_variant) == {"voice_025_baseline", "with_voice_026"}, f"{script_id} is missing an A/B variant.")

    baseline = by_variant["voice_025_baseline"]
    interaction = by_variant["with_voice_026"]
    assert_condition(baseline["speech_realism_enabled"] is True, f"{script_id} baseline should keep speech realism enabled.")
    assert_condition(interaction["speech_realism_enabled"] is True, f"{script_id} B variant should keep speech realism enabled.")
    assert_condition(baseline["speech_interaction_enabled"] is False, f"{script_id} baseline should disable VOICE-026.")
    assert_condition(interaction["speech_interaction_enabled"] is True, f"{script_id} B variant should enable VOICE-026.")
    assert_condition(baseline["speech_interaction_marker_count"] == 0, f"{script_id} baseline should not add interaction markers.")
    assert_condition(
        interaction["speech_interaction_marker_count"] >= 1,
        f"{script_id} B variant should add at least one interaction marker.",
    )
    assert_condition(
        baseline["tts_input_text"] != interaction["tts_input_text"],
        f"{script_id} A/B TTS text should differ so listening can isolate VOICE-026.",
    )
    assert_condition(
        baseline["provider_rendering"]["plain_text"] != interaction["provider_rendering"]["plain_text"],
        f"{script_id} provider plain text should differ between A/B variants.",
    )

    for result in [baseline, interaction]:
        assert_condition(result["api_key_value_logged"] is False, f"{script_id} must not log API keys.")
        assert_condition(result["voice_id_value_logged"] is False, f"{script_id} must not log raw voice IDs.")
        assert_condition(result["customer_audio_uploaded"] is False, f"{script_id} must not upload customer audio.")
        assert_condition(result["private_audio_used"] is False, f"{script_id} must not use private audio.")
        assert_condition(result["voice_cloning_used"] is False, f"{script_id} must not use voice cloning.")
        assert_condition(result["validation"]["passed"] is True, f"{script_id} {result['variant_id']} validation failed.")
        assert_condition(
            result["provider_rendering_validation"]["passed"] is True,
            f"{script_id} {result['variant_id']} provider rendering validation failed.",
        )
        assert_condition(
            result["spoken_text_normalization"]["validation"]["passed"] is True,
            f"{script_id} {result['variant_id']} spoken-text normalization failed.",
        )
        assert_condition(
            result["speech_realism"]["validation"]["passed"] is True,
            f"{script_id} {result['variant_id']} speech-realism validation failed.",
        )
        assert_condition(
            result["speech_interaction"]["validation"]["passed"] is True,
            f"{script_id} {result['variant_id']} speech-interaction validation failed.",
        )
        assert_condition(
            result["prosody"]["validation"]["passed"] is True,
            f"{script_id} {result['variant_id']} prosody validation failed.",
        )
        assert_condition(result["validation"]["protected_segment_change_count"] == 0, f"{script_id} changed protected text.")
        assert_condition(result["validation"]["unsafe_agreement_marker_count"] == 0, f"{script_id} used unsafe agreement markers.")


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
    assert_condition(completed.returncode == 0, f"VOICE-027 forced-missing live gate failed: {completed.stderr or completed.stdout}")
    payload = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    assert_condition(payload["summary"]["live_call_requested"] is True, "Forced-missing path should request live mode.")
    assert_condition(payload["summary"]["api_calls_made"] == 0, "Forced-missing path must not call provider.")
    assert_condition(payload["summary"]["audio_files_created"] == 0, "Forced-missing path must not create audio.")
    assert_condition(payload["summary"]["fallback_count"] == payload["summary"]["result_count"], "Forced-missing path should fallback every result.")


def main() -> None:
    assert_condition(RUNNER_PATH.exists(), "VOICE-027 runner is missing.")
    assert_condition(CASES_PATH.exists(), "VOICE-027 case file is missing.")
    validate_runner_default_paths()

    completed = run_default_harness()
    assert_condition(completed.returncode == 0, f"VOICE-027 runner failed: {completed.stderr or completed.stdout}")
    assert_condition(RESULTS_PATH.exists(), "VOICE-027 results were not created.")
    assert_condition(REPORT_PATH.exists(), "VOICE-027 report was not created.")

    payload_text = RESULTS_PATH.read_text(encoding="utf-8") + "\n" + REPORT_PATH.read_text(encoding="utf-8")
    payload = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    summary = payload["summary"]

    assert_condition(payload["voice_milestone"] == "VOICE-027", "Unexpected voice milestone.")
    assert_condition(summary["script_count"] == 4, "VOICE-027 should cover four scripts.")
    assert_condition(summary["variant_count"] == 2, "VOICE-027 should compare two variants.")
    assert_condition(summary["result_count"] == 8, "VOICE-027 dry run should produce eight A/B results.")
    assert_condition(summary["languages"] == {"de": 4, "en": 4}, "VOICE-027 should cover English and German equally.")
    assert_condition(summary["live_call_requested"] is False, "VOICE-027 default mode should be dry-run.")
    assert_condition(summary["api_calls_made"] == 0, "VOICE-027 default mode must not call providers.")
    assert_condition(summary["audio_files_created"] == 0, "VOICE-027 dry-run must not create audio.")
    assert_condition(summary["customer_audio_uploaded"] is False, "VOICE-027 must not upload customer audio.")
    assert_condition(summary["private_audio_used"] is False, "VOICE-027 must not use private audio.")
    assert_condition(summary["voice_cloning_used"] is False, "VOICE-027 must not use voice cloning.")
    assert_condition(summary["raw_voice_ids_logged"] is False, "VOICE-027 must not log raw voice IDs.")
    assert_condition(summary["with_voice_026_marker_count"] >= 4, "VOICE-027 should add interaction markers to B variants.")
    assert_condition(summary["voice_025_baseline_marker_count"] == 0, "VOICE-027 baseline variants should have no interaction markers.")
    assert_condition(summary["unsafe_agreement_marker_count"] == 0, "VOICE-027 should avoid unsafe agreement markers.")
    assert_condition(summary["protected_segment_change_count"] == 0, "VOICE-027 changed protected text.")

    script_ids = {script["script_id"] for script in payload["listening_scripts"]}
    for script_id in script_ids:
        validate_result_pair(payload["results"], script_id)

    assert_no_raw_local_voice_ids(payload_text)
    report_text = REPORT_PATH.read_text(encoding="utf-8")
    assert_condition("Live mode requires `--live`" in report_text, "VOICE-027 report should document live opt-in.")
    assert_condition("raw voice IDs" in report_text, "VOICE-027 report should document raw voice ID boundary.")
    assert_condition("VOICE-026" in report_text, "VOICE-027 report should describe the isolated layer.")

    validate_forced_missing_key_path()
    completed = run_default_harness()
    assert_condition(completed.returncode == 0, f"VOICE-027 dry-run restore failed: {completed.stderr or completed.stdout}")

    print("VOICE-027 interaction prosody live A/B validation passed.")


if __name__ == "__main__":
    main()
