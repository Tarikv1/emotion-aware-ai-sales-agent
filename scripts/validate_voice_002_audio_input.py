#!/usr/bin/env python3
import json
import math
import subprocess
import sys
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "run_voice_input_turn.py"
GENERATED_DIR = ROOT / ".tmp" / "VOICE-002"
AUDIO_PATH = GENERATED_DIR / "VOICE-002-customer-placeholder.wav"
TRANSCRIPT = "Nur wenn Sie garantieren koennen, dass es stabil ist."


def write_placeholder_wav(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 8000
    duration_seconds = 0.35
    frame_total = int(sample_rate * duration_seconds)
    amplitude = 800
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for frame in range(frame_total):
            sample = int(amplitude * math.sin(2 * math.pi * 440 * frame / sample_rate))
            wav_file.writeframesraw(sample.to_bytes(2, byteorder="little", signed=True))


def run_voice_input(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def load_stdout_json(completed: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(completed.stdout)


def assert_no_secret_patterns(text: str) -> None:
    assert "sk-" not in text
    assert "OPENAI_API_KEY" not in text
    assert "Authorization: Bearer" not in text


def main() -> None:
    assert SCRIPT_PATH.exists(), "VOICE-002 audio-input script is missing"
    sys.path.insert(0, str(ROOT / "scripts"))
    from run_voice_input_turn import render_listener

    write_placeholder_wav(AUDIO_PATH)

    missing_consent = run_voice_input(
        "--campaign",
        "campaign-prod-005-b2c-telecom",
        "--stage",
        "relevance-check",
        "--audio",
        str(AUDIO_PATH),
        "--transcript",
        TRANSCRIPT,
        check=False,
    )
    assert missing_consent.returncode != 0
    assert "consent" in (missing_consent.stdout + missing_consent.stderr).lower()

    completed = run_voice_input(
        "--campaign",
        "campaign-prod-005-b2c-telecom",
        "--stage",
        "relevance-check",
        "--audio",
        str(AUDIO_PATH),
        "--transcript",
        TRANSCRIPT,
        "--consent-confirmed",
    )
    packet = load_stdout_json(completed)

    assert packet["voice_input_run_id"] == "VOICE-002-manual-transcript"
    assert packet["voice_milestone"] == "VOICE-002"
    assert packet["provider"] == "manual-transcript"
    assert packet["consent"]["confirmed"] is True
    assert packet["audio_input"]["path"].endswith("VOICE-002-customer-placeholder.wav")
    assert packet["audio_input"]["format"] == "wav"
    assert packet["audio_input"]["byte_size"] > 44
    assert packet["audio_input"]["duration_seconds"] > 0
    assert packet["transcription"]["transcript"] == TRANSCRIPT
    assert packet["transcription"]["language"] == "de"
    assert packet["transcription"]["requires_api_key"] is False
    assert packet["response_packet"]["provider"] == "dry-run"
    assert packet["response_packet"]["campaign"]["language"] == "de"
    assert packet["response_packet"]["decision"]["campaign_language"] == "de"
    assert packet["response_packet"]["decision"]["response_language"] == "de"
    assert packet["response_packet"]["decision"]["sales_difficulty"] == "claim-boundary"
    assert packet["response_packet"]["decision"]["call_control"] == "transfer-or-escalate"
    assert packet["response_packet"]["tts_text"] == packet["response_packet"]["decision"]["agent_response"]
    assert "spezialisten" in packet["response_packet"]["tts_text"].lower() or "details" in packet["response_packet"]["tts_text"].lower()
    assert "i can route" not in packet["response_packet"]["tts_text"].lower()

    listener_html = render_listener(packet)
    assert TRANSCRIPT in listener_html
    assert packet["response_packet"]["tts_text"] in listener_html
    assert "speechSynthesis" in listener_html
    assert 'utterance.lang = "de-DE"' in listener_html

    serialized = json.dumps(packet) + listener_html
    assert_no_secret_patterns(serialized)


if __name__ == "__main__":
    main()
