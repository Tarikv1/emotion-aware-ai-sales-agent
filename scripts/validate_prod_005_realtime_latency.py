#!/usr/bin/env python3
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_realtime_turn_simulation.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"


def load_runner_module():
    assert RUNNER_PATH.exists(), "Realtime turn simulation runner is missing"
    spec = importlib.util.spec_from_file_location("run_realtime_turn_simulation", RUNNER_PATH)
    assert spec and spec.loader, "Could not load realtime turn simulation runner"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    assert CASES_PATH.exists(), "PROD-005 realtime latency case file is missing"
    module = load_runner_module()

    for name in [
        "load_realtime_cases",
        "run_case",
        "score_case",
        "aggregate",
        "render_report",
    ]:
        assert hasattr(module, name), f"Runner missing {name}"

    campaigns, cases = module.load_realtime_cases(CASES_PATH)
    assert len(campaigns) >= 3, "PROD-005 should use multiple campaign profiles"
    assert len(cases) >= 9, "PROD-005 should cover at least 9 runtime scenarios"

    results = [module.run_case(case, campaigns) for case in cases]
    summary = module.aggregate(results)

    assert summary["case_total"] == len(cases)
    assert summary["response_mode_matches"] == len(cases), summary
    assert summary["call_control_matches"] == len(cases), summary
    assert summary["latency_bucket_matches"] == len(cases), summary
    assert summary["next_action_matches"] == len(cases), summary
    assert summary["response_language_matches"] == len(cases), summary
    assert summary["live_path_subagent_violations"] == 0, summary

    campaign_languages = {campaign["campaign_id"]: campaign.get("language") for campaign in campaigns}
    assert {"de", "en"}.issubset(set(campaign_languages.values())), campaign_languages
    for case, result in zip(cases, results):
        expected_runtime = case["expected_runtime"]
        assert "response_language" in expected_runtime, f"{case['case_id']} missing expected response_language"
        expected_language = expected_runtime["response_language"]
        assert result["runtime_decision"]["response_language"] == expected_language
        assert result["runtime_decision"]["campaign_language"] == expected_language

    expected_controls = {
        "continue-call",
        "bridge-then-continue",
        "transfer-or-escalate",
        "end-call",
        "schedule-and-end",
    }
    observed_controls = {result["runtime_decision"]["call_control"] for result in results}
    assert expected_controls.issubset(observed_controls), observed_controls

    bridge_cases = [
        result for result in results
        if result["runtime_decision"]["response_mode"] == "bridge-then-background"
    ]
    assert bridge_cases, "PROD-005 should include at least one bridge response case"
    assert all(result["runtime_decision"]["bridge_response"] for result in bridge_cases)


if __name__ == "__main__":
    main()
