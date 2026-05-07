#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "run_browser_speech_demo.py"
GENERATED_DIR = ROOT / ".tmp" / "VOICE-004"
HTML_OUT = GENERATED_DIR / "VOICE-004-browser-speech-demo.html"
METADATA_OUT = GENERATED_DIR / "VOICE-004-browser-speech-demo-metadata.json"
DECISION_OUT = GENERATED_DIR / "VOICE-004-browser-speech-demo-decision.json"
TRANSCRIPT = "Nur wenn Sie garantieren koennen, dass es stabil ist."
PRICE_TRANSCRIPT = "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt."
UNKNOWN_TRANSCRIPT_ONE = "I am not sure this makes sense for my apartment right now."
UNKNOWN_TRANSCRIPT_TWO = "Can you explain why I should even take this call today?"


def run_demo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )


def assert_no_secret_patterns(text: str) -> None:
    assert re.search(r"sk-[A-Za-z0-9_-]{20,}", text) is None
    assert re.search(r"OPENAI_API_KEY\s*=", text) is None
    assert re.search(r"Authorization:\s*Bearer\s+[A-Za-z0-9]", text) is None


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
    assert "languageSelect" in html
    assert "recognition.lang = languageSelect.value" in html
    assert "priceSampleButton" in html
    assert "lookupSampleButton" in html
    assert "lastSentTranscript" in html
    assert "decisionSummary" in html
    assert "/decide" in html
    assert "speechSynthesis" in html
    assert "No API key" in html
    assert metadata["voice_milestone"] == "VOICE-004"
    assert metadata["provider"] == "browser-speech-recognition-demo"
    assert metadata["requires_api_key"] is False
    assert metadata["audio_uploaded_to_local_server"] is False
    assert "de-DE" in metadata["supported_recognition_languages"]
    assert "en-US" in metadata["supported_recognition_languages"]
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
    assert file_packet["response_packet"]["campaign"]["language"] == "de"
    assert file_packet["response_packet"]["decision"]["campaign_language"] == "de"
    assert file_packet["response_packet"]["decision"]["response_language"] == "de"
    assert file_packet["response_packet"]["response_generation"]["response_generation_id"] == "RESP-001-local-guarded"
    assert file_packet["response_packet"]["response_generation"]["provider"] == "local-guarded-composer"
    assert file_packet["response_packet"]["response_generation"]["llm_used"] is False
    assert file_packet["response_packet"]["response_generation"]["requires_api_key"] is False
    assert file_packet["response_packet"]["response_generation"]["final_response"] == file_packet["response_packet"]["tts_text"]
    assert "spezialisten" in file_packet["response_packet"]["tts_text"].lower()
    assert "telecom specialist" not in file_packet["response_packet"]["tts_text"].lower()
    assert "garantieren" not in file_packet["response_packet"]["tts_text"].lower()
    assert "guarantee" not in file_packet["response_packet"]["tts_text"].lower()
    assert file_packet["response_packet"]["response_generation"]["validation"]["passed"] is True

    price_completed = run_demo("--decision-transcript", PRICE_TRANSCRIPT)
    price_packet = json.loads(price_completed.stdout)
    assert price_packet["response_packet"]["decision"]["sales_difficulty"] == "price-objection"
    assert price_packet["response_packet"]["decision"]["call_control"] == "continue-call"
    assert price_packet["response_packet"]["tts_text"] != file_packet["response_packet"]["tts_text"]
    assert price_packet["response_packet"]["response_generation"]["response_generation_id"] == "RESP-001-local-guarded"

    unknown_one = json.loads(run_demo("--decision-transcript", UNKNOWN_TRANSCRIPT_ONE).stdout)
    unknown_two = json.loads(run_demo("--decision-transcript", UNKNOWN_TRANSCRIPT_TWO).stdout)
    assert unknown_one["response_packet"]["decision"]["sales_difficulty"] == "unknown-runtime-signal"
    assert unknown_two["response_packet"]["decision"]["sales_difficulty"] == "unknown-runtime-signal"
    assert unknown_one["response_packet"]["tts_text"] != unknown_two["response_packet"]["tts_text"]
    assert "pass" in unknown_one["response_packet"]["tts_text"].lower() or "situation" in unknown_one["response_packet"]["tts_text"].lower()
    assert "anruf" in unknown_two["response_packet"]["tts_text"].lower() or "grund" in unknown_two["response_packet"]["tts_text"].lower()
    assert unknown_one["response_packet"]["response_generation"]["response_generation_id"] == "RESP-001-local-guarded"
    assert unknown_two["response_packet"]["response_generation"]["response_generation_id"] == "RESP-001-local-guarded"

    serialized = (
        html
        + json.dumps(metadata)
        + json.dumps(file_packet)
        + json.dumps(price_packet)
        + json.dumps(unknown_one)
        + json.dumps(unknown_two)
    )
    assert_no_secret_patterns(serialized)


if __name__ == "__main__":
    main()
