#!/usr/bin/env python3
from __future__ import annotations

import argparse
import http.client
import json
import mimetypes
import re
import sys
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "LIVE-DEMO-TTS-AUDIO-PLAYBACK-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
PRIVATE_ROOTS = [
    ROOT / "data" / "private" / "live-demo-001",
    ROOT / "data" / "private" / "live-demo-003",
]
SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|sk_[A-Za-z0-9-]{20,}|ELEVENLABS_API_KEY\s*=\s*[^\s]+|xi-api-key\s*[:=]\s*[A-Za-z0-9]|Authorization:\s*Bearer\s+[A-Za-z0-9])"
)
BROWSER_AUDIO_TYPES = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav", "audio/ogg"}


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def write_evidence(result: dict[str, Any], report: str) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def make_metadata(private_out: Path) -> dict[str, Any]:
    args = argparse.Namespace(
        host=demo.DEFAULT_HOST,
        port=0,
        campaign=demo.DEFAULT_CAMPAIGN_ID,
        campaign_config=None,
        stage=demo.DEFAULT_STAGE,
        live_tts=False,
        force_key_missing=True,
        timeout_seconds=8.0,
        consent_confirmed=False,
        allow_generic_live_tts=False,
        live_tts_preflight={"api_key_present": False, "voice_id_present": False, "voice_id_source": None},
        live_tts_env_file_status={"path": None, "present": False, "loaded_keys": [], "ignored_keys": []},
    )
    return demo.build_metadata(args, demo.DEFAULT_CASES_PATH, private_out)


def first_bytes(path: Path, count: int = 16) -> bytes:
    with path.open("rb") as handle:
        return handle.read(count)


def hex_preview(data: bytes) -> str:
    return " ".join(f"{byte:02X}" for byte in data)


def detect_signature(data: bytes) -> str:
    if not data:
        return "empty"
    if data.startswith(b"ID3") or (len(data) >= 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0):
        return "mp3"
    if data.startswith(b"RIFF") and data[8:12] == b"WAVE":
        return "wav"
    if data.startswith(b"OggS"):
        return "ogg"
    stripped = data.lstrip()
    if stripped.startswith((b"{", b"[")):
        return "json-or-text"
    if all((byte in b"\r\n\t" or 32 <= byte < 127) for byte in data[: min(12, len(data))]):
        return "text"
    return "unknown"


def content_type_for(path: Path) -> str | None:
    guessed = mimetypes.guess_type(str(path))[0]
    if path.suffix.lower() == ".mp3":
        return "audio/mpeg"
    if path.suffix.lower() == ".wav":
        return "audio/wav"
    if path.suffix.lower() == ".ogg":
        return "audio/ogg"
    return guessed


def latest_private_live_audio_artifact() -> dict[str, Any] | None:
    candidates: list[dict[str, Any]] = []
    for root in PRIVATE_ROOTS:
        if not root.exists():
            continue
        for packet_path in root.rglob("*.json"):
            try:
                packet = json.loads(packet_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            tts = ((packet.get("packet") or {}).get("tts_delivery") or {})
            summary = packet.get("summary") or {}
            if not (
                tts.get("provider_calls_made") is True
                or tts.get("audio_file_created") is True
                or summary.get("tts_provider_calls_made") is True
                or summary.get("tts_audio_file_created") is True
            ):
                continue
            audio_output = str(tts.get("audio_output_path") or "")
            if not audio_output:
                continue
            candidates.append(
                {
                    "packet_path": packet_path,
                    "private_root": root,
                    "packet": packet,
                    "tts": tts,
                    "audio_output_path": audio_output,
                    "last_write_time": packet_path.stat().st_mtime,
                }
            )
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: item["last_write_time"], reverse=True)[0]


def inspect_artifact(artifact: dict[str, Any] | None) -> dict[str, Any]:
    if artifact is None:
        return {"found": False}
    packet = artifact["packet"]
    tts = artifact["tts"]
    audio_path = (ROOT / artifact["audio_output_path"]).resolve()
    exists = audio_path.exists()
    preview = first_bytes(audio_path) if exists else b""
    signature = detect_signature(preview)
    return {
        "found": True,
        "packet_path": demo.project_relative_string(artifact["packet_path"]),
        "private_root": demo.project_relative_string(artifact["private_root"]),
        "campaign_id": packet.get("campaign_id"),
        "campaign_selector_mode": packet.get("campaign_selector_mode"),
        "audio_url": packet.get("audio_url"),
        "audio_output_path": artifact["audio_output_path"],
        "provider_calls_made": tts.get("provider_calls_made"),
        "audio_file_created": tts.get("audio_file_created"),
        "fallback_reason": tts.get("fallback_reason"),
        "response_content_type": tts.get("response_content_type"),
        "exists": exists,
        "size": audio_path.stat().st_size if exists else 0,
        "extension": audio_path.suffix.lower() if exists else "",
        "first_bytes": hex_preview(preview),
        "signature": signature,
        "content_type_guess": content_type_for(audio_path) if exists else None,
    }


def http_get_audio(private_out: Path, query_path: str) -> dict[str, Any]:
    metadata = make_metadata(private_out)
    server = ThreadingHTTPServer((demo.DEFAULT_HOST, 0), demo.make_handler(metadata, demo.DEFAULT_CASES_PATH, private_out))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = http.client.HTTPConnection(demo.DEFAULT_HOST, server.server_address[1], timeout=5)
    try:
        connection.request("GET", "/audio?path=" + quote(query_path.replace("\\", "/"), safe="/"))
        response = connection.getresponse()
        body = response.read()
        text_preview = body[:120].decode("utf-8", errors="replace")
        return {
            "status": response.status,
            "content_type": response.getheader("Content-Type"),
            "content_length_header": response.getheader("Content-Length"),
            "body_length": len(body),
            "body_signature": detect_signature(body[:16]),
            "body_preview": text_preview if response.status >= 400 else "",
        }
    finally:
        connection.close()
        server.shutdown()
        server.server_close()


def validate_existing_artifact(failures: list[str], evidence: dict[str, Any]) -> None:
    artifact = latest_private_live_audio_artifact()
    info = inspect_artifact(artifact)
    evidence["existing_private_audio_artifact"] = info
    if not info.get("found"):
        return
    assert_condition(failures, info["exists"] is True, f"artifact audio path missing: {info}")
    assert_condition(failures, info["size"] > 0, f"artifact audio is empty: {info}")
    assert_condition(failures, info["signature"] in {"mp3", "wav", "ogg"}, f"artifact signature is not browser audio: {info}")
    assert_condition(failures, info["content_type_guess"] in BROWSER_AUDIO_TYPES, f"artifact content type not browser-compatible: {info}")
    assert_condition(failures, SECRET_PATTERN.search(json.dumps(info, ensure_ascii=False)) is None, "secret-like value appeared in artifact evidence")
    served = http_get_audio(artifact["private_root"], info["audio_output_path"])
    evidence["existing_private_audio_serving"] = served
    assert_condition(failures, served["status"] == 200, f"/audio did not serve existing artifact: {served}")
    assert_condition(failures, served["content_type"] in BROWSER_AUDIO_TYPES, f"/audio content type is not browser-compatible: {served}")
    assert_condition(failures, served["body_length"] == info["size"], f"/audio body length mismatch: {served} vs {info}")


def write_minimal_wav(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 8000
    channels = 1
    bits_per_sample = 16
    data = b"\x00\x00" * 8
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    header = (
        b"RIFF"
        + (36 + len(data)).to_bytes(4, "little")
        + b"WAVEfmt "
        + (16).to_bytes(4, "little")
        + (1).to_bytes(2, "little")
        + channels.to_bytes(2, "little")
        + sample_rate.to_bytes(4, "little")
        + byte_rate.to_bytes(4, "little")
        + block_align.to_bytes(2, "little")
        + bits_per_sample.to_bytes(2, "little")
        + b"data"
        + len(data).to_bytes(4, "little")
        + data
    )
    path.write_bytes(header)


def validate_synthetic_audio_serving(failures: list[str], evidence: dict[str, Any]) -> None:
    fixture_root = TMP_DIR / "audio-fixtures"
    valid_wav = fixture_root / "valid fixture.wav"
    invalid_mp3 = fixture_root / "invalid-text.mp3"
    write_minimal_wav(valid_wav)
    invalid_mp3.write_text("not actually audio\n", encoding="utf-8")

    valid_rel = demo.project_relative_string(valid_wav)
    invalid_rel = demo.project_relative_string(invalid_mp3)
    missing_rel = demo.project_relative_string(fixture_root / "missing-file.mp3")
    valid = http_get_audio(TMP_DIR, valid_rel or str(valid_wav))
    invalid = http_get_audio(TMP_DIR, invalid_rel or str(invalid_mp3))
    missing = http_get_audio(TMP_DIR, missing_rel or "missing-file.mp3")
    outside = http_get_audio(TMP_DIR, "scripts/run_live_demo_001_agent_voice_call.py")
    evidence["synthetic_audio_serving"] = {
        "valid": valid,
        "invalid_text_mp3": invalid,
        "missing": missing,
        "outside_private": outside,
    }
    assert_condition(failures, valid["status"] == 200, f"valid wav fixture should serve: {valid}")
    assert_condition(failures, valid["content_type"] in {"audio/wav", "audio/x-wav"}, f"valid wav content type wrong: {valid}")
    assert_condition(failures, valid["body_signature"] == "wav", f"valid wav signature wrong: {valid}")
    assert_condition(failures, invalid["status"] in {400, 404, 415}, f"invalid text mp3 should be rejected, not served: {invalid}")
    assert_condition(failures, missing["status"] in {400, 404}, f"missing audio should return controlled error: {missing}")
    assert_condition(failures, outside["status"] in {400, 404}, f"outside path should be rejected: {outside}")


def validate_audio_url_helpers(failures: list[str], evidence: dict[str, Any]) -> None:
    url = demo.audio_url_for_packet(
        {
            "tts_delivery": {
                "audio_output_path": "data\\private\\live-demo-001\\audio\\file name.mp3",
            }
        }
    )
    evidence["audio_url_helper"] = {"url": url}
    assert_condition(failures, url == "/audio?path=data/private/live-demo-001/audio/file%20name.mp3", f"audio URL should be encoded /audio route: {url}")


def validate_generic_packet_audio_url_normalization(failures: list[str], evidence: dict[str, Any]) -> None:
    original_builder = demo.build_generic_campaign_turn_packet_from_config_path
    raw_audio_path = "data\\private\\live-demo-001\\generic-campaigns\\audio\\fake provider audio.mp3"

    def fake_builder(**kwargs: Any) -> dict[str, Any]:
        return {
            "entrypoint_id": "test-generic-campaign-turn",
            "mode": "live-tts",
            "campaign_id": "synthetic-insurance-review",
            "campaign_playbook_id": "synthetic-insurance-review-playbook",
            "session_id": kwargs.get("session_id"),
            "session_turn_index": 1,
            "stage": kwargs.get("stage"),
            "input_type": kwargs.get("input_type"),
            "transcript": kwargs.get("transcript"),
            "asr": {"audio_uploaded_to_python_server": False},
            "provider_calls_made": True,
            "local_llm_calls_made": False,
            "sends_email": False,
            "creates_calendar_event": False,
            "writes_crm": False,
            "opens_prod_102": False,
            "dialogue_manager": {},
            "conversation_memory": {},
            "demo_conversation_memory": {},
            "packet": {
                "api_calls_made": False,
                "voice_delivery": {"provider_calls_made": False},
                "tts_delivery": {
                    "audio_output_path": raw_audio_path,
                    "provider_calls_made": True,
                    "audio_file_created": True,
                    "customer_audio_uploaded": False,
                    "fallback_reason": None,
                },
            },
            "summary": {
                "final_response": "Synthetic response.",
                "call_control": "continue-call",
                "tts_provider_calls_made": True,
                "tts_audio_file_created": True,
                "tts_fallback_reason": None,
            },
            "audio_url": raw_audio_path,
        }

    demo.build_generic_campaign_turn_packet_from_config_path = fake_builder
    try:
        packet = demo.build_browser_demo_turn_packet(
            transcript="__agent_open__",
            campaign_id=demo.DEFAULT_CAMPAIGN_ID,
            campaign_config_path=ROOT / "runtime" / "campaigns" / "examples" / "synthetic-insurance-review.json",
            stage=demo.DEFAULT_STAGE,
            input_type="agent-open",
            silence_count=0,
            cases_path=demo.DEFAULT_CASES_PATH,
            private_out=ROOT / "data" / "private" / "live-demo-001",
            live_tts=True,
            force_key_missing=False,
            timeout_seconds=8.0,
            session_id="audio-url-normalization",
            session_state={"turns": []},
            generic_live_tts_allowed=True,
        )
    finally:
        demo.build_generic_campaign_turn_packet_from_config_path = original_builder

    evidence["generic_packet_audio_url_normalization"] = {
        "audio_url": packet.get("audio_url"),
        "selected_live_tts_enabled": (packet.get("selected_campaign_config") or {}).get("live_tts_enabled"),
        "provider_calls_made": packet.get("provider_calls_made"),
        "audio_file_created": packet.get("audio_file_created"),
    }
    assert_condition(failures, packet.get("audio_url") == "/audio?path=data/private/live-demo-001/generic-campaigns/audio/fake%20provider%20audio.mp3", f"generic live TTS audio_url should be normalized: {packet.get('audio_url')}")
    assert_condition(failures, "\\" not in str(packet.get("audio_url")), f"generic audio_url should not contain backslashes: {packet.get('audio_url')}")
    assert_condition(failures, (packet.get("selected_campaign_config") or {}).get("live_tts_enabled") is True, f"selected config live TTS trace missing: {packet}")


def validate_browser_error_distinction(failures: list[str], evidence: dict[str, Any]) -> None:
    html = demo.render_html(make_metadata(TMP_DIR / "html"))
    checks = {
        "has_audio_error_handler": "handleAudioPlaybackError" in html,
        "has_provider_audio_error_message": "Provider audio could not be played. Review audio diagnostics or use Browser Fallback Voice manually." in html,
        "audio_play_caught_separately": "await audio.play();" in html and "handleAudioPlaybackError(audioError, payload)" in html,
        "does_not_route_audio_to_turn_error": "audio_playback_error" in html,
    }
    evidence["browser_error_distinction"] = checks
    for key, value in checks.items():
        assert_condition(failures, value is True, f"browser audio error distinction missing: {key}")


def render_report(result: dict[str, Any]) -> str:
    artifact = result.get("existing_private_audio_artifact") or {}
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        f"- Existing failed/live private artifact found: `{str(artifact.get('found', False)).lower()}`",
        f"- Packet path: `{artifact.get('packet_path') or ''}`",
        f"- Audio output path: `{artifact.get('audio_output_path') or ''}`",
        f"- Audio URL: `{artifact.get('audio_url') or ''}`",
        f"- File size: `{artifact.get('size') or 0}`",
        f"- Extension: `{artifact.get('extension') or ''}`",
        f"- Detected signature: `{artifact.get('signature') or ''}`",
        f"- Content type guess: `{artifact.get('content_type_guess') or ''}`",
        f"- Provider calls made in inspected artifact: `{str(artifact.get('provider_calls_made')).lower()}`",
        f"- Audio file created in inspected artifact: `{str(artifact.get('audio_file_created')).lower()}`",
        f"- Live provider call used by this validator: `{str(result.get('live_provider_call_used')).lower()}`",
        f"- Secret-like content found: `{str(result.get('secret_like_content_found')).lower()}`",
        "",
        "## Patch Evidence",
        "",
        f"- Audio URL helper: `{(result.get('audio_url_helper') or {}).get('url') or ''}`",
        f"- Existing artifact serving: `{(result.get('existing_private_audio_serving') or {}).get('status')}` / `{(result.get('existing_private_audio_serving') or {}).get('content_type')}`",
        f"- Browser playback error handling: `{(result.get('browser_error_distinction') or {}).get('has_audio_error_handler')}`",
        "",
        "## Failures",
        "",
    ]
    failures = result.get("failures") or []
    lines.extend([f"- {failure}" for failure in failures] or ["- None"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "checkpoint_id": CHECKPOINT_ID,
        "live_provider_call_used": False,
    }

    validate_existing_artifact(failures, evidence)
    validate_synthetic_audio_serving(failures, evidence)
    validate_audio_url_helpers(failures, evidence)
    validate_generic_packet_audio_url_normalization(failures, evidence)
    validate_browser_error_distinction(failures, evidence)

    evidence_text = json.dumps(evidence, ensure_ascii=False)
    evidence["secret_like_content_found"] = SECRET_PATTERN.search(evidence_text) is not None
    if evidence["secret_like_content_found"]:
        failures.append("secret-like content appeared in evidence")
    evidence["failures"] = failures
    evidence["passed"] = not failures
    write_evidence(evidence, render_report(evidence))
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"{CHECKPOINT_ID}: pass")


if __name__ == "__main__":
    main()
