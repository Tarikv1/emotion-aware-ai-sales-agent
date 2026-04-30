#!/usr/bin/env python3
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "scripts" / "run_rule_baseline.py"
PROD_001_CASES = ROOT / "research" / "experiments" / "cases" / "prod-001-qualification-simulation.json"


def load_baseline_module():
    spec = importlib.util.spec_from_file_location("run_rule_baseline", BASELINE_PATH)
    assert spec and spec.loader, "Could not load rule baseline module"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    module = load_baseline_module()
    cases = module.load_cases(PROD_001_CASES)
    summary = module.aggregate([module.run_case(case) for case in cases])

    assert summary["turn_total"] == 32, f"Unexpected PROD-001 turn total: {summary}"
    assert summary["emotion_matches"] == 18, f"PROD-001 emotion baseline changed: {summary}"
    assert summary["interest_state_matches"] == 32, f"PROD-001 interest-state regression: {summary}"
    assert summary["strategy_matches"] == 32, f"PROD-001 strategy regression: {summary}"
    assert summary["final_call_status_matches"] == 12, f"PROD-001 final status regression: {summary}"
    assert summary["final_interest_state_matches"] == 12, f"PROD-001 final interest regression: {summary}"
    assert summary["final_strategy_matches"] == 12, f"PROD-001 final strategy regression: {summary}"
    assert summary["final_appointment_matches"] == 12, f"PROD-001 appointment regression: {summary}"


if __name__ == "__main__":
    main()
