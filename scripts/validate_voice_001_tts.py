#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "generate_voice_response.py"


def run_voice_script(*args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def main() -> None:
    assert SCRIPT_PATH.exists(), "VOICE-001 generator script is missing"

    packet = run_voice_script(
        "--campaign",
        "campaign-prod-005-b2c-telecom",
        "--stage",
        "relevance-check",
        "--transcript",
        "Nur wenn Sie garantieren koennen, dass es stabil ist.",
        "--dry-run",
    )

    assert packet["voice_run_id"] == "VOICE-001-dry-run"
    assert packet["provider"] == "dry-run"
    assert packet["voice"]["style"] == "neutral-synthetic-test"
    assert packet["campaign_id"] == "campaign-prod-005-b2c-telecom"
    assert packet["decision"]["sales_difficulty"] == "claim-boundary"
    assert packet["decision"]["call_control"] == "transfer-or-escalate"
    assert packet["tts_text"] == packet["decision"]["agent_response"]
    assert packet["audio_output_path"] is None

    serialized = json.dumps(packet)
    assert "sk-" not in serialized
    assert "OPENAI_API_KEY" not in serialized
    assert "Authorization: Bearer" not in serialized


if __name__ == "__main__":
    main()
