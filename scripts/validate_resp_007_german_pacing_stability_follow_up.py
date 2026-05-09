#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_resp_007_german_pacing_stability_follow_up.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "resp-007-german-pacing-stability-follow-up.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "RESP-007-german-pacing-stability-follow-up" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "RESP-007-german-pacing-stability-follow-up" / "report.md"
REVIEW_PATH = ROOT / "research" / "experiments" / "generated" / "RESP-007-german-pacing-stability-follow-up" / "human-listening-review.md"
PRODUCT_DOC = ROOT / "docs" / "product" / "RESP_007_GERMAN_PACING_STABILITY_FOLLOW_UP.md"

SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|sk_car_[A-Za-z0-9_-]{20,}|ELEVENLABS_API_KEY\s*=\s*[^\s]+|CARTESIA_API_KEY\s*=\s*[^\s]+|xi-api-key\s*[:=]\s*[A-Za-z0-9]|X-API-Key\s*[:=]\s*[A-Za-z0-9])"
)


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=90)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    assert_condition(RUNNER.exists(), "RESP-007 German pacing-stability runner is missing.")
    assert_condition(CASE_PATH.exists(), "RESP-007 German pacing-stability case file is missing.")
    assert_condition(PRODUCT_DOC.exists(), "RESP-007 product doc is missing.")

    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--cases",
            str(CASE_PATH),
            "--out",
            str(RESULT_PATH),
            "--report-out",
            str(REPORT_PATH),
            "--review-out",
            str(REVIEW_PATH),
        ]
    )
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    assert_condition(RESULT_PATH.exists(), "RESP-007 result JSON was not written.")
    assert_condition(REPORT_PATH.exists(), "RESP-007 report was not written.")
    assert_condition(REVIEW_PATH.exists(), "RESP-007 human review sheet was not written.")

    payload = load_json(RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8")
    review = REVIEW_PATH.read_text(encoding="utf-8")
    product_doc = PRODUCT_DOC.read_text(encoding="utf-8")
    summary = payload["summary"]

    assert_condition(payload["experiment_id"] == "RESP-007-german-pacing-stability-follow-up", payload)
    assert_condition(payload["source_checkpoint"] == "RESP-006-german-runtime-version-ab-listening-check", payload)
    assert_condition(summary["case_count"] == 1, summary)
    assert_condition(summary["variant_count"] == 2, summary)
    assert_condition(summary["german_case_count"] == 1, summary)
    assert_condition(summary["same_question_for_all_variants"] is True, summary)
    assert_condition(summary["same_answer_content_for_all_variants"] is True, summary)
    assert_condition(summary["only_delivery_surface_changed"] is True, summary)
    assert_condition(summary["voice_personality_selector_unblocked"] is False, summary)
    assert_condition(summary["live_call_requested"] is False, summary)
    assert_condition(summary["api_calls_made"] == 0, summary)
    assert_condition(summary["audio_files_created"] == 0, summary)
    assert_condition(summary["customer_audio_uploaded"] is False, summary)
    assert_condition(summary["voice_cloning_used"] is False, summary)
    assert_condition(summary["synthetic_prompts_only"] is True, summary)
    assert_condition(summary["quality_claim_allowed"] is False, summary)
    assert_condition(summary["raw_secret_values_logged"] is False, summary)

    case = payload["cases"][0]
    assert_condition(case["language"] == "de", case)
    assert_condition(case["source_resp_006_case_id"] == "RESP-006-SAME-Q-DE-COMPLEX", case)
    assert_condition(case["question"] == case["variants"][0]["question"] == case["variants"][1]["question"], case)
    assert_condition(case["final_response"] == case["answer_content_text"], case)

    variants = {variant["variant_kind"]: variant for variant in case["variants"]}
    assert_condition(set(variants) == {"old_plain_pacing_stabilized", "new_shaped_pacing_stabilized"}, variants)
    old = variants["old_plain_pacing_stabilized"]
    new = variants["new_shaped_pacing_stabilized"]
    assert_condition(old["source_variant_kind"] == "old_plain_guarded", old)
    assert_condition(new["source_variant_kind"] == "new_shaped_runtime", new)
    assert_condition(old["answer_content_text"] == case["final_response"], old)
    assert_condition(new["answer_content_text"] == case["final_response"], new)
    assert_condition(old["normalized_tts_content_text"] == case["final_response"], old)
    assert_condition(new["normalized_tts_content_text"] == case["final_response"], new)
    assert_condition(old["tts_input_text"] != old["answer_content_text"], old)
    assert_condition(new["tts_input_text"] != new["answer_content_text"], new)
    assert_condition("opening_rush_guard" in old["pacing_stability"]["targets"], old)
    assert_condition("late_drag_prevention" in old["pacing_stability"]["targets"], old)
    assert_condition("late_speed_cap" in new["pacing_stability"]["targets"], new)
    assert_condition(new["source_voice_settings"].get("speed", 0) > new["voice_settings"].get("speed", 9), new)
    assert_condition(new["voice_settings"].get("speed", 9) <= 1.04, new)
    assert_condition(old["voice_settings"].get("speed", 0) >= 1.0, old)
    assert_condition(old["voice_settings"].get("speed", 0) <= 1.04, old)
    assert_condition(old["pacing_stability"]["content_changed"] is False, old)
    assert_condition(new["pacing_stability"]["content_changed"] is False, new)

    for variant in case["variants"]:
        assert_condition(variant["api_key_value_logged"] is False, variant)
        assert_condition(variant["voice_id_value_logged"] is False, variant)
        assert_condition(variant["customer_audio_uploaded"] is False, variant)
        assert_condition(variant["voice_cloning_used"] is False, variant)
        assert_condition(variant["generated_text_sent_to_provider"] is False, variant)
        assert_condition(variant["request_preview"]["headers"]["xi-api-key"] == "<redacted>", variant)
        assert_condition("<redacted" in json.dumps(variant["request_preview"], ensure_ascii=False), variant)

    assert_condition("German pacing-stability follow-up" in report, report)
    assert_condition("same answer content" in report, report)
    assert_condition("old_plain_pacing_stabilized" in review, review)
    assert_condition("new_shaped_pacing_stabilized" in review, review)
    assert_condition("voice-personality selector remains blocked" in product_doc, product_doc)
    assert_condition("dry-run" in product_doc.lower(), product_doc)

    combined = json.dumps(payload, ensure_ascii=False) + report + review + completed.stdout + completed.stderr
    match = SECRET_PATTERN.search(combined)
    if match is not None:
        raise AssertionError(f"Potential secret-like value found: {match.group(0)!r}")

    print("RESP-007 German pacing-stability follow-up validation passed.")


if __name__ == "__main__":
    main()
