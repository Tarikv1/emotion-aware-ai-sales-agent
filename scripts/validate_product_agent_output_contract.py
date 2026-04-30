#!/usr/bin/env python3
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "scripts" / "product_agent_output_contract.py"


def load_contract_module():
    assert CONTRACT_PATH.exists(), "Shared product-agent output contract is missing"
    spec = importlib.util.spec_from_file_location("product_agent_output_contract", CONTRACT_PATH)
    assert spec and spec.loader, "Could not load output contract module"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    module = load_contract_module()

    assert hasattr(module, "STRATEGY_DEFINITIONS"), "Missing strategy definitions"
    assert hasattr(module, "CALL_CONTROL_VALUES"), "Missing call-control values"
    assert hasattr(module, "normalize_final_outcome"), "Missing final-outcome normalizer"
    assert hasattr(module, "normalize_turn_output"), "Missing turn-output normalizer"
    assert hasattr(module, "strategy_taxonomy_prompt_block"), "Missing prompt taxonomy renderer"
    assert hasattr(module, "call_control_prompt_block"), "Missing call-control prompt renderer"

    for strategy in [
        "rapport",
        "inquiry",
        "evidence-or-benefit",
        "emotional-appeal",
        "direct-ask-or-commitment",
    ]:
        assert strategy in module.STRATEGY_DEFINITIONS, f"Missing strategy definition for {strategy}"

    normalized = module.normalize_final_outcome(
        {
            "call_status": "completed",
            "interest_state": "needs-human",
            "selected_strategy": "direct-ask-or-commitment",
            "appointment_scheduled": False,
            "appointment_time": None,
            "escalation_reason": None,
            "call_summary": "Lead asked for a specialist.",
            "next_action": "Follow up.",
        }
    )
    assert normalized["call_status"] == "escalated", "needs-human must normalize to escalated"
    assert normalized["selected_strategy"] == "rapport", "needs-human handoff should normalize to rapport"
    assert normalized["escalation_reason"], "escalated outcomes need an escalation reason"
    assert normalized["call_control"] == "transfer-or-escalate", "needs-human should transfer or escalate"

    normalized = module.normalize_final_outcome(
        {
            "call_status": "completed",
            "interest_state": "interested",
            "selected_strategy": "direct-ask-or-commitment",
            "appointment_scheduled": False,
            "appointment_time": None,
            "escalation_reason": None,
            "call_summary": "Lead wants a non-binding callback.",
            "next_action": "Schedule callback.",
        }
    )
    assert normalized["call_status"] == "ready-for-scheduling", "interested non-appointment should be ready"
    assert normalized["call_control"] == "continue-call", "ready-for-scheduling should keep the call open"

    prompt_block = module.strategy_taxonomy_prompt_block()
    assert "Use `rapport`" in prompt_block
    assert "Use `direct-ask-or-commitment`" in prompt_block
    assert "end-call" in module.call_control_prompt_block()


if __name__ == "__main__":
    main()
