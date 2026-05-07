#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_core_sales_delivery_playbook.py"
RESULT = ROOT / "research" / "experiments" / "generated" / "CORE-sales-delivery-playbook" / "result.json"
REPORT = ROOT / "research" / "experiments" / "generated" / "CORE-sales-delivery-playbook" / "report.md"
DOC = ROOT / "docs" / "product" / "CORE_SALES_DELIVERY_PLAYBOOK.md"


def assert_condition(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    completed = subprocess.run(
        [sys.executable, str(RUNNER)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(completed.returncode == 0, completed.stderr)
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    report_text = REPORT.read_text(encoding="utf-8")
    doc_text = DOC.read_text(encoding="utf-8")

    assert_condition(payload["core_pack_id"] == "CORE-sales-delivery-playbook", payload)
    assert_condition(payload["runtime_default_enabled"] is True, payload)
    assert_condition(payload["external_provider_calls_made"] is False, payload)
    assert_condition(payload["private_customer_data_used"] is False, payload)
    assert_condition(payload["campaign_facts_override_rag"] is True, payload)
    assert_condition(payload["persuasion_boundary"]["ethical_persuasion_allowed"] is True, payload)
    assert_condition(payload["persuasion_boundary"]["fake_urgency_allowed"] is False, payload)
    assert_condition(payload["persuasion_boundary"]["invented_scarcity_allowed"] is False, payload)
    assert_condition(payload["emotion_boundary"]["observable_empathy_allowed"] is True, payload)
    assert_condition(payload["emotion_boundary"]["hidden_state_certainty_allowed"] is False, payload)
    assert_condition(len(payload["sales_playbook"]["common_objection_rules"]) >= 8, payload["sales_playbook"])
    assert_condition(len(payload["delivery_pack"]["speech_delivery_rules"]) >= 8, payload["delivery_pack"])
    assert_condition("source_excerpt" not in json.dumps(payload).lower(), "Core pack must not store source excerpts.")
    assert_condition("data/private" not in json.dumps(payload).replace("\\", "/").lower(), "Core pack must not reference private paths.")
    assert_condition("fake urgency" in report_text.lower(), "Report should document fake urgency boundary.")
    assert_condition("Campaign facts override RAG" in doc_text, "Product doc should state campaign facts override RAG.")
    print("Core sales delivery playbook validation passed.")


if __name__ == "__main__":
    main()
