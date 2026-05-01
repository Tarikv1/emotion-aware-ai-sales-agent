#!/usr/bin/env python3
import json
import os
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


def run_voice_process(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


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
    assert packet["campaign"]["language"] == "de"
    assert packet["decision"]["campaign_language"] == "de"
    assert packet["decision"]["response_language"] == "de"
    assert packet["decision"]["sales_difficulty"] == "claim-boundary"
    assert packet["decision"]["call_control"] == "transfer-or-escalate"
    assert packet["tts_text"] == packet["decision"]["agent_response"]
    assert "spezialisten" in packet["tts_text"].lower() or "details" in packet["tts_text"].lower()
    assert "i can route" not in packet["tts_text"].lower()
    assert packet["audio_output_path"] is None

    serialized = json.dumps(packet)
    assert "sk-" not in serialized
    assert "OPENAI_API_KEY" not in serialized
    assert "Authorization: Bearer" not in serialized

    audio_path = ROOT / "research" / "experiments" / "generated" / f"VOICE-001-sapi-check-{os.getpid()}.wav"
    sapi_result = run_voice_process(
        "--campaign",
        "campaign-prod-005-b2c-telecom",
        "--stage",
        "relevance-check",
        "--transcript",
        "Nur wenn Sie garantieren koennen, dass es stabil ist.",
        "--provider",
        "windows-sapi",
        "--out-audio",
        str(audio_path),
    )
    if sapi_result.returncode == 0:
        assert audio_path.exists(), "windows-sapi success must create an audio file"
        assert audio_path.stat().st_size > 44, "windows-sapi success must create a playable WAV"
        try:
            audio_path.unlink()
        except PermissionError:
            pass
    else:
        combined_output = sapi_result.stdout + sapi_result.stderr
        assert "did not create a playable WAV" in combined_output
        if audio_path.exists():
            try:
                audio_path.unlink()
            except PermissionError:
                pass


if __name__ == "__main__":
    main()
