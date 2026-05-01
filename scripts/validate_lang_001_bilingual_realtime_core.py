#!/usr/bin/env python3
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_realtime_turn_simulation.py"
GUARDED_RESPONSE_SCRIPT = ROOT / "scripts" / "generate_guarded_response.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "lang-001-bilingual-realtime-core.json"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated"
RESULTS_OUT = GENERATED_DIR / "LANG-001-bilingual-realtime-results.json"
REPORT_OUT = GENERATED_DIR / "LANG-001-bilingual-realtime-report.md"

SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|OPENAI_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9])"
)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_runner_module():
    assert_condition(RUNNER_PATH.exists(), "Realtime turn simulation runner is missing.")
    spec = importlib.util.spec_from_file_location("run_realtime_turn_simulation", RUNNER_PATH)
    assert_condition(bool(spec and spec.loader), "Could not load realtime turn simulation runner.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_command(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True)


def assert_no_secret_patterns(text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match is not None:
        raise AssertionError(f"Potential secret-like token found: {match.group(0)!r}")


def main() -> None:
    assert_condition(CASES_PATH.exists(), "LANG-001 bilingual realtime case file is missing.")
    module = load_runner_module()

    campaigns, cases = module.load_realtime_cases(CASES_PATH)
    assert_condition(len(campaigns) >= 2, "LANG-001 needs at least German and English campaign profiles.")
    assert_condition(len(cases) >= 16, "LANG-001 should cover paired German/English realtime scenarios.")
    campaign_languages = {campaign["campaign_id"]: campaign.get("language") for campaign in campaigns}
    assert_condition({"de", "en"}.issubset(set(campaign_languages.values())), "LANG-001 campaigns must include German and English.")

    results = [module.run_case(case, campaigns) for case in cases]
    summary = module.aggregate(results)
    assert_condition(summary["case_total"] == len(cases), summary)
    for key in [
        "response_mode_matches",
        "latency_bucket_matches",
        "background_modules_matches",
        "emotion_matches",
        "sales_difficulty_matches",
        "interest_state_matches",
        "strategy_matches",
        "next_action_matches",
        "call_control_matches",
        "response_language_matches",
        "response_marker_matches",
    ]:
        assert_condition(summary[key] == len(cases), f"{key} mismatch: {summary}")
    assert_condition(summary["live_path_subagent_violations"] == 0, summary)

    language_counts = {"de": 0, "en": 0}
    observed_scenarios = {"de": set(), "en": set()}
    for result in results:
        decision = result["runtime_decision"]
        expected = result["expected_runtime"]
        language = expected["response_language"]
        language_counts[language] += 1
        observed_scenarios[language].add(result["runtime_scenario"])
        assert_condition(decision["response_language"] == language, f"{result['case_id']} response language mismatch.")
        assert_condition(decision["campaign_language"] == language, f"{result['case_id']} campaign language mismatch.")
        response_text = decision["agent_response"].lower()
        expected_markers = [marker.lower() for marker in expected["response_must_include_any"]]
        assert_condition(
            any(marker in response_text for marker in expected_markers),
            f"{result['case_id']} response text lacks expected language markers: {decision['agent_response']}",
        )
        if language == "de":
            assert_condition(
                not any(marker in response_text for marker in ["understood", "of course", "goodbye", "one moment"]),
                f"{result['case_id']} German response leaked English stock wording.",
            )
        if language == "en":
            assert_condition(
                not any(marker in response_text for marker in ["verstanden", "natuerlich", "auf wiederhoeren"]),
                f"{result['case_id']} English response leaked German stock wording.",
            )

    assert_condition(language_counts["de"] == language_counts["en"], language_counts)
    assert_condition(observed_scenarios["de"] == observed_scenarios["en"], observed_scenarios)

    completed = run_command(
        [
            sys.executable,
            str(RUNNER_PATH),
            "--cases",
            str(CASES_PATH),
            "--out",
            str(RESULTS_OUT),
            "--report-out",
            str(REPORT_OUT),
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr)
    assert_condition(RESULTS_OUT.exists(), "Expected LANG-001 JSON results artifact.")
    assert_condition(REPORT_OUT.exists(), "Expected LANG-001 Markdown report artifact.")
    payload = json.loads(RESULTS_OUT.read_text(encoding="utf-8"))
    assert_condition(payload["summary"]["case_total"] == len(cases), payload["summary"])
    assert_condition(payload["summary"]["response_language_matches"] == len(cases), payload["summary"])

    guarded_run = run_command(
        [
            sys.executable,
            str(GUARDED_RESPONSE_SCRIPT),
            "--campaign",
            "campaign-lang-001-de-consumer",
            "--stage",
            "relevance-check",
            "--transcript",
            "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt.",
            "--cases",
            str(CASES_PATH),
        ]
    )
    assert_condition(guarded_run.returncode == 0, guarded_run.stderr)
    guarded_payload = json.loads(guarded_run.stdout)
    guarded_response = guarded_payload["final_response"].lower()
    assert_condition(
        guarded_payload["decision_snapshot"]["response_language"] == "de",
        "Guarded response snapshot should preserve German response language.",
    )
    assert_condition(
        any(marker in guarded_response for marker in ["verstehe", "preis", "aufwand"]),
        f"Guarded German response should stay German: {guarded_payload['final_response']}",
    )
    assert_condition(
        not any(marker in guarded_response for marker in ["that makes sense", "monthly price", "worth your time"]),
        f"Guarded German response leaked English stock wording: {guarded_payload['final_response']}",
    )

    report = REPORT_OUT.read_text(encoding="utf-8")
    assert_condition("Bilingual Realtime" in report, "Report should identify bilingual realtime validation.")
    assert_condition("Response-language matches" in report, "Report should include language match score.")
    assert_no_secret_patterns(json.dumps(payload) + report)
    print("LANG-001 bilingual realtime core validation passed.")


if __name__ == "__main__":
    main()
