#!/usr/bin/env python3
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "scripts" / "run_rule_baseline.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "prod-004-sales-difficulty-gauntlet.json"


def load_baseline_module():
    spec = importlib.util.spec_from_file_location("run_rule_baseline", BASELINE_PATH)
    assert spec and spec.loader, "Could not load rule baseline module"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    module = load_baseline_module()
    cases = module.load_cases(CASES_PATH)
    results = [module.run_case(case) for case in cases]
    summary = module.aggregate(results)

    assert summary["turn_total"] == 20, "PROD-004 should still have 20 turns"
    assert summary["final_total"] == 14, "PROD-004 should still have 14 cases"

    assert summary["emotion_matches"] >= 17, f"Emotion matches too low: {summary}"
    assert summary["interest_state_matches"] >= 19, f"Interest-state matches too low: {summary}"
    assert summary["strategy_matches"] >= 18, f"Strategy matches too low: {summary}"
    assert summary["final_call_status_matches"] >= 13, f"Final call-status matches too low: {summary}"
    assert summary["final_interest_state_matches"] >= 13, f"Final interest-state matches too low: {summary}"
    assert summary["final_strategy_matches"] >= 13, f"Final strategy matches too low: {summary}"
    assert summary["final_appointment_matches"] == 14, f"Appointment matches regressed: {summary}"


if __name__ == "__main__":
    main()
