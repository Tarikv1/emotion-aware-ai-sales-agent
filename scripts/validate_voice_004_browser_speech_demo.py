#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "run_browser_speech_demo.py"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated"
HTML_OUT = GENERATED_DIR / "VOICE-004-browser-speech-demo.html"
METADATA_OUT = GENERATED_DIR / "VOICE-004-browser-speech-demo-metadata.json"
DECISION_OUT = GENERATED_DIR / "VOICE-004-browser-speech-demo-decision.json"
TRANSCRIPT = "Nur wenn Sie garantieren koennen, dass es stabil ist."


def run_demo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )


def assert_no_secret_patterns(text: str) -> None:
    assert "sk-" not in text
    assert "OPENAI_API_KEY" not in text
    assert "Authorization: Bearer" not in text


def main() -> None:
    assert SCRIPT_PATH.exists(), "VOICE-004 browser speech demo script is missing"

    run_demo(
        "--export-html",
        str(HTML_OUT),
        "--export-metadata",
        str(METADATA_OUT),
    )
    assert HTML_OUT.exists()
    assert METADATA_OUT.exists()

    html = HTML_OUT.read_text(encoding="utf-8")
    metadata = json.loads(METADATA_OUT.read_text(encoding="utf-8"))

    assert "SpeechRecognition" in html
    assert "webkitSpeechRecognition" in html
    assert "consentCheckbox" in html
    assert "/decide" in html
    assert "speechSynthesis" in html
    assert "No API key" in html
    assert metadata["voice_milestone"] == "VOICE-004"
    assert metadata["provider"] == "browser-speech-recognition-demo"
    assert metadata["requires_api_key"] is False
    assert metadata["audio_uploaded_to_local_server"] is False
    assert metadata["local_server_endpoints"] == ["/", "/metadata", "/decide"]

    completed = run_demo(
        "--decision-transcript",
        TRANSCRIPT,
        "--decision-out",
        str(DECISION_OUT),
    )
    stdout_packet = json.loads(completed.stdout)
    file_packet = json.loads(DECISION_OUT.read_text(encoding="utf-8"))
    assert stdout_packet == file_packet

    assert file_packet["voice_milestone"] == "VOICE-004"
    assert file_packet["provider"] == "browser-speech-recognition-demo"
    assert file_packet["asr_adapter"]["transcript"] == TRANSCRIPT
    assert file_packet["asr_adapter"]["requires_api_key"] is False
    assert file_packet["asr_adapter"]["audio_uploaded_to_local_server"] is False
    assert file_packet["response_packet"]["decision"]["sales_difficulty"] == "claim-boundary"
    assert file_packet["response_packet"]["decision"]["call_control"] == "transfer-or-escalate"
    assert file_packet["response_packet"]["tts_text"] == file_packet["response_packet"]["decision"]["agent_response"]

    serialized = html + json.dumps(metadata) + json.dumps(file_packet)
    assert_no_secret_patterns(serialized)


if __name__ == "__main__":
    main()
