#!/usr/bin/env python3
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "scripts" / "product_agent_output_contract.py"
POLICY_DOC = ROOT / "docs" / "product" / "CALL_TERMINATION_POLICY.md"
PROMPT_PATH = ROOT / "packages" / "prompts" / "product-qualification-agent.txt"


def load_contract_module():
    spec = importlib.util.spec_from_file_location("product_agent_output_contract", CONTRACT_PATH)
    assert spec and spec.loader, "Could not load product-agent output contract"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    module = load_contract_module()
    assert POLICY_DOC.exists(), "Call termination policy doc is missing"

    expected_controls = {
        "continue-call",
        "bridge-then-continue",
        "transfer-or-escalate",
        "end-call",
        "schedule-and-end",
    }
    assert set(module.CALL_CONTROL_VALUES) == expected_controls, "Unexpected call-control values"

    assert module.call_control_for_next_action("suppress-contact", "do-not-call") == "end-call"
    assert module.call_control_for_next_action("close-politely", "not-interested") == "end-call"
    assert module.call_control_for_next_action("escalate", "needs-human") == "transfer-or-escalate"
    assert module.call_control_for_next_action("confirm-scheduling", "interested") == "schedule-and-end"
    assert module.call_control_for_next_action("create-follow-up-task", "maybe-interested") == "end-call"
    assert module.call_control_for_next_action("ask-follow-up", "maybe-interested") == "continue-call"

    normalized_turn = module.normalize_turn_output(
        {
            "stage": "opening-permission",
            "detected_emotion": "skeptical-or-negative",
            "interest_state": "do-not-call",
            "selected_strategy": "rapport",
            "next_action": "suppress-contact",
            "agent_response": "Understood. I will mark this so you are not contacted again. Goodbye.",
            "confidence": 0.9,
            "rationale": "Lead requested no further contact.",
        }
    )
    assert normalized_turn["call_control"] == "end-call", "do-not-call should end the call"

    normalized_outcome = module.normalize_final_outcome(
        {
            "call_status": "completed",
            "interest_state": "do-not-call",
            "selected_strategy": "rapport",
            "appointment_scheduled": False,
            "appointment_time": None,
            "escalation_reason": None,
            "call_summary": "Lead requested no more calls.",
            "next_action": "suppress future outreach",
        }
    )
    assert normalized_outcome["call_control"] == "end-call", "final do-not-call should end call"

    policy = POLICY_DOC.read_text(encoding="utf-8")
    for phrase in [
        "Immediate End-Call Triggers",
        "Polite Close Then End Call",
        "Escalate Instead Of Hanging Up",
        "Repeated Silence",
        "Voicemail",
        "call_control",
    ]:
        assert phrase in policy, f"Policy doc missing: {phrase}"

    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    assert '"call_control"' in prompt, "Prompt must request call_control"
    assert "end-call" in prompt, "Prompt must define end-call behavior"


if __name__ == "__main__":
    main()
