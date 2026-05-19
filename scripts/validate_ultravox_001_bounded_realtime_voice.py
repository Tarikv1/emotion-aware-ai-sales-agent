#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "evaluate_ultravox_001_bounded_realtime_voice.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "ultravox-001-bounded-realtime-voice-evaluation.json"
GENERATED_DIR = ROOT / ".tmp" / "ULTRAVOX-001"
OUT_JSON = GENERATED_DIR / "ULTRAVOX-001-bounded-realtime-voice-evaluation.json"
REPORT_OUT = GENERATED_DIR / "ULTRAVOX-001-bounded-realtime-voice-evaluation-report.md"

SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|ULTRAVOX_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9])"
)

OFFICIAL_HOST_SUFFIXES = {
    "docs.ultravox.ai",
    "ultravox.ai",
    "www.ultravox.ai",
    "github.com",
    "huggingface.co",
}


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_no_secret_patterns(text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match is not None:
        raise AssertionError(f"Potential secret-like token found: {match.group(0)!r}")


def is_official_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return host in OFFICIAL_HOST_SUFFIXES or any(host.endswith(f".{suffix}") for suffix in OFFICIAL_HOST_SUFFIXES)


def run_evaluation() -> dict:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--cases",
            str(CASES_PATH),
            "--out",
            str(OUT_JSON),
            "--report-out",
            str(REPORT_OUT),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def main() -> None:
    assert_condition(SCRIPT_PATH.exists(), "ULTRAVOX-001 evaluator is missing.")
    assert_condition(CASES_PATH.exists(), "ULTRAVOX-001 case file is missing.")

    result = run_evaluation()
    assert_condition(result["evaluation_milestone"] == "ULTRAVOX-001", "Unexpected evaluation milestone.")
    assert_condition(result["retrieved_on"] == "2026-05-17", "Source retrieval date should be explicit.")
    assert_condition(result["summary"]["candidate_count"] == 4, "Expected exactly four architecture candidates.")
    assert_condition(result["summary"]["case_count"] == 5, "Expected five fixed evaluation cases.")
    assert_condition(result["summary"]["source_count"] >= 9, "Expected official UltraVox source coverage.")
    assert_condition(result["summary"]["official_source_count"] == result["summary"]["source_count"], "All sources must be official/primary.")
    assert_condition(result["summary"]["api_calls_made"] is False, "ULTRAVOX-001 must not make API calls.")
    assert_condition(result["summary"]["audio_uploaded"] is False, "ULTRAVOX-001 must not upload audio.")
    assert_condition(result["summary"]["secrets_required"] is False, "ULTRAVOX-001 must not require secrets.")
    assert_condition(result["summary"]["integration_allowed"] is False, "ULTRAVOX-001 must not integrate runtime behavior.")
    assert_condition(result["summary"]["live_provider_calls_allowed"] is False, "Live UltraVox calls must remain blocked.")
    assert_condition(result["summary"]["customer_audio_upload_allowed"] is False, "Customer audio upload must remain blocked.")
    assert_condition(result["summary"]["voice_cloning_allowed"] is False, "Voice cloning must remain blocked.")
    assert_condition(result["summary"]["provider_owned_business_logic_allowed"] is False, "Provider-owned business logic must remain blocked.")
    assert_condition(result["summary"]["durable_provider_agent_allowed"] is False, "Durable provider agents must remain blocked.")
    assert_condition(result["summary"]["opens_prod_102"] is False, "ULTRAVOX-001 must not open PROD-102.")

    recommendations = result["recommendations"]
    assert_condition(
        recommendations["first_bounded_evaluation"]["candidate_id"] == "ultravox-hosted-api-provider-adapter",
        "Hosted API provider adapter should be the first bounded evaluation.",
    )
    assert_condition(
        recommendations["self_host_research_lane"]["candidate_id"] == "ultravox-open-source-self-host-lane",
        "Open-source self-host should remain the research lane.",
    )
    assert_condition(
        recommendations["do_not_productize_first"]["candidate_id"] == "ultravox-hosted-console-agent",
        "Hosted console agent should not be productized first.",
    )
    assert_condition(
        recommendations["baseline_control"]["candidate_id"] == "current-resp003-tts-bridge-baseline",
        "RESP-003 should remain the baseline control.",
    )

    source_ids = {source["source_id"] for source in result["sources"]}
    for source in result["sources"]:
        assert_condition(source["retrieved_on"] == "2026-05-17", f"{source['source_id']} missing retrieval date.")
        assert_condition(is_official_url(source["url"]), f"{source['source_id']} is not official/primary: {source['url']}")

    required_candidates = {
        "ultravox-hosted-api-provider-adapter",
        "ultravox-hosted-console-agent",
        "ultravox-open-source-self-host-lane",
        "current-resp003-tts-bridge-baseline",
    }
    candidates = result["ranked_candidates"]
    candidate_ids = {candidate["candidate_id"] for candidate in candidates}
    assert_condition(required_candidates == candidate_ids, f"Unexpected candidates: {sorted(candidate_ids)}")

    for candidate in candidates:
        assert_condition(set(candidate["source_ids"]).issubset(source_ids), f"{candidate['candidate_id']} cites unknown source IDs.")
        assert_condition(candidate["live_allowed_now"] is False, f"{candidate['candidate_id']} should not be live now.")
        assert_condition(candidate["direct_copy_status"] == "none", f"{candidate['candidate_id']} should not copy external code.")
        if candidate["candidate_id"] == "ultravox-hosted-console-agent":
            assert_condition(candidate["provider_owned_business_logic"] is True, "Console agent risk should be explicit.")
            assert_condition(candidate["durable_provider_agent_required"] is True, "Console agent durable-agent risk should be explicit.")
            assert_condition(candidate["guarded_runtime_fit"] == 1, "Console agent should be a weak guarded-runtime fit.")
        if candidate["candidate_id"] == "ultravox-hosted-api-provider-adapter":
            assert_condition(candidate["api_key_required"] is True, "Hosted API live path requires an API key.")
            assert_condition(candidate["customer_audio_upload_if_live"] is True, "Hosted API live path uploads live audio.")
            assert_condition(candidate["provider_owned_business_logic"] is False, "Provider adapter should not own business logic.")
        if candidate["candidate_id"] == "ultravox-open-source-self-host-lane":
            assert_condition(candidate["api_key_required"] is False, "Self-host lane should not require a provider API key.")
            assert_condition(candidate["implementation_effort_inverse"] == 1, "Self-host effort should be treated as high.")
            assert_condition(candidate["guarded_runtime_fit"] == 5, "Self-host lane should preserve local control.")
        if candidate["candidate_id"] == "current-resp003-tts-bridge-baseline":
            assert_condition(candidate["recommended_role"] == "baseline-control", "RESP-003 should remain baseline only.")

    assert_condition(OUT_JSON.exists(), "Expected ULTRAVOX-001 JSON artifact.")
    assert_condition(REPORT_OUT.exists(), "Expected ULTRAVOX-001 Markdown report artifact.")
    report_text = REPORT_OUT.read_text(encoding="utf-8")
    assert_condition("No UltraVox API calls were made" in report_text, "Report should state no UltraVox API calls.")
    assert_condition("No audio was uploaded" in report_text, "Report should state no audio upload.")
    assert_condition("does not open `PROD-102`" in report_text, "Report should state PROD-102 remains closed.")
    assert_condition("ultravox-hosted-api-provider-adapter" in report_text, "Report should identify hosted API adapter.")
    assert_condition("ultravox-open-source-self-host-lane" in report_text, "Report should identify self-host lane.")
    assert_condition("ultravox-hosted-console-agent" in report_text, "Report should identify console-agent risk.")
    assert_condition("current-resp003-tts-bridge-baseline" in report_text, "Report should identify baseline.")

    serialized = json.dumps(result) + report_text
    assert_no_secret_patterns(serialized)
    print("ULTRAVOX-001 bounded realtime voice evaluation validation passed.")


if __name__ == "__main__":
    main()
