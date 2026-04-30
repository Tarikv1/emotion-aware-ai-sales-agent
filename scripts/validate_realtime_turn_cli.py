#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = ROOT / "scripts" / "realtime_turn_cli.py"


def run_cli(*args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(CLI_PATH), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def main() -> None:
    assert CLI_PATH.exists(), "Realtime turn CLI is missing"

    guarantee = run_cli(
        "--campaign",
        "campaign-prod-005-b2c-telecom",
        "--stage",
        "relevance-check",
        "--transcript",
        "Nur wenn Sie garantieren koennen, dass es stabil ist.",
    )
    assert guarantee["campaign_id"] == "campaign-prod-005-b2c-telecom"
    assert guarantee["decision"]["sales_difficulty"] == "claim-boundary"
    assert guarantee["decision"]["interest_state"] == "needs-human"
    assert guarantee["decision"]["next_action"] == "escalate"
    assert guarantee["decision"]["call_control"] == "transfer-or-escalate"
    assert guarantee["decision"]["response_mode"] == "fast-response"
    assert guarantee["decision"]["first_response_latency_ms"] >= 0

    lookup = run_cli(
        "--campaign",
        "campaign-prod-005-b2c-telecom",
        "--stage",
        "product-detail-check",
        "--transcript",
        "Welcher genaue Tarif ist das und wie viel Datenvolumen ist enthalten?",
    )
    assert lookup["decision"]["response_mode"] == "bridge-then-background"
    assert lookup["decision"]["call_control"] == "bridge-then-continue"
    assert lookup["decision"]["bridge_response"]
    assert "campaign-knowledge-lookup" in lookup["decision"]["background_modules"]

    silence = run_cli(
        "--campaign",
        "campaign-prod-005-b2c-energy",
        "--stage",
        "opening-permission",
        "--input-type",
        "silence-timeout",
        "--silence-count",
        "2",
    )
    assert silence["decision"]["call_control"] == "end-call"
    assert silence["decision"]["next_action"] == "close-politely"


if __name__ == "__main__":
    main()
