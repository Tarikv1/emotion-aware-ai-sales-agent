#!/usr/bin/env python3
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_llm_product_agent.py"


def main() -> None:
    assert RUNNER_PATH.exists(), "LLM product agent runner is missing"

    spec = importlib.util.spec_from_file_location("run_llm_product_agent", RUNNER_PATH)
    assert spec and spec.loader, "Could not load runner module"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for name in [
        "load_cases_and_campaigns",
        "planned_model_call_count",
        "log_progress",
        "build_final_outcome",
        "score_case",
        "render_report",
        "missing_api_key_message",
    ]:
        assert hasattr(module, name), f"Runner missing {name}"

    cases, campaigns = module.load_cases_and_campaigns(
        ROOT / "research" / "experiments" / "cases" / "prod-004-sales-difficulty-gauntlet.json"
    )
    assert len(cases) == 14, "Expected 14 PROD-004 cases"
    assert len(campaigns) == 5, "Expected 5 PROD-004 campaigns"
    assert module.planned_model_call_count(cases) == 34, "Expected 34 PROD-004 model calls"
    assert "OPENAI_API_KEY" in module.missing_api_key_message("OPENAI_API_KEY")


if __name__ == "__main__":
    main()
