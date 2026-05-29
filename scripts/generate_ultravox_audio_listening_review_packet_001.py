#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import wave
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SANDBOX_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-001" / "result.json"
QUALITY_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-QUALITY-001" / "result.json"
AGENT_AUDIO_DIR = ROOT / "local_artifacts" / "audio_outputs" / "ultravox" / "agent_outputs"
PACKET_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LISTENING-REVIEW-001"
PACKET_RESULT_PATH = PACKET_DIR / "result.json"
PACKET_REPORT_PATH = PACKET_DIR / "report.md"
MANUAL_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LISTENING-REVIEW-MANUAL-001"
MANUAL_TEMPLATE_JSON = MANUAL_DIR / "manual_review_template.json"
MANUAL_TEMPLATE_MD = MANUAL_DIR / "manual_review_template.md"


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def clip(text: Any, limit: int = 220) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def transcript_snippets(sandbox: dict[str, Any], role: str) -> list[str]:
    snippets: list[str] = []
    for item in sandbox.get("final_transcripts_sanitized", []):
        if isinstance(item, dict) and item.get("role") == role and item.get("text"):
            snippets.append(clip(item.get("text")))
    return snippets


def read_wave_metadata(path: Path) -> dict[str, Any]:
    file_size = path.stat().st_size if path.is_file() else None
    try:
        with wave.open(str(path), "rb") as handle:
            sample_rate = handle.getframerate()
            frame_count = handle.getnframes()
            duration = round(frame_count / sample_rate, 3) if sample_rate else None
            frames = handle.readframes(frame_count)
            waveform_hash = hashlib.sha256(frames).hexdigest()
            return {
                "duration_seconds": duration,
                "sample_rate": sample_rate,
                "file_size_bytes": file_size,
                "waveform_hash": waveform_hash,
            }
    except wave.Error:
        data = path.read_bytes() if path.is_file() else b""
        return {
            "duration_seconds": None,
            "sample_rate": None,
            "file_size_bytes": file_size,
            "waveform_hash": hashlib.sha256(data).hexdigest(),
        }


def candidate_audio_paths(sandbox: dict[str, Any]) -> list[Path]:
    paths: list[Path] = []
    for item in sandbox.get("agent_audio_file_metadata", []):
        if isinstance(item, dict) and item.get("path"):
            paths.append(ROOT / str(item["path"]))
    for path_text in sandbox.get("agent_audio_files_written_under_local_artifacts", []):
        if isinstance(path_text, str):
            paths.append(ROOT / path_text)
    if AGENT_AUDIO_DIR.is_dir():
        paths.extend(sorted(AGENT_AUDIO_DIR.glob("*.wav")))
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        try:
            key = rel(path)
        except ValueError:
            continue
        if key not in seen and path.is_file():
            seen.add(key)
            unique.append(path)
    return unique


def build_audio_entries(sandbox: dict[str, Any]) -> list[dict[str, Any]]:
    user_prompts = [str(item) for item in sandbox.get("synthetic_audio_turns", []) if item]
    user_snippets = transcript_snippets(sandbox, "user")
    agent_snippets = transcript_snippets(sandbox, "agent")
    associated_turn_ids = [
        int(turn.get("turn_index"))
        for turn in sandbox.get("synthetic_audio_turns_status", [])
        if isinstance(turn, dict) and turn.get("sent") is True and isinstance(turn.get("turn_index"), int)
    ]
    entries: list[dict[str, Any]] = []
    for index, path in enumerate(candidate_audio_paths(sandbox), start=1):
        metadata = read_wave_metadata(path)
        entry = {
            "entry_id": f"agent_audio_{index:03d}",
            "local_audio_path": rel(path),
            "case_id": None,
            "turn_id": None,
            "associated_turn_ids": associated_turn_ids,
            "duration_seconds": metadata["duration_seconds"],
            "sample_rate": metadata["sample_rate"],
            "file_size_bytes": metadata["file_size_bytes"],
            "waveform_hash": metadata["waveform_hash"],
            "associated_user_prompt": " | ".join(user_prompts),
            "associated_transcript_snippet": " | ".join(user_snippets),
            "agent_transcript_snippet": " | ".join(agent_snippets),
            "first_audio_latency_seconds": sandbox.get("first_agent_audio_latency_seconds"),
            "audio_files_copied": False,
            "audio_files_committed": False,
        }
        entries.append(entry)
    return entries


def checklist() -> list[dict[str, Any]]:
    return [
        {"field": "intelligibility", "scale": "1-5", "value": None},
        {"field": "naturalness", "scale": "1-5", "value": None},
        {"field": "voice_quality", "scale": "1-5", "value": None},
        {"field": "sales_tone", "scale": "1-5", "value": None},
        {"field": "pacing", "scale": "1-5", "value": None},
        {"field": "artifact_severity", "scale": "1-5", "value": None},
        {"field": "interruption_turn_taking_quality", "scale": "1-5", "value": None},
        {"field": "thesis_demo_suitability", "scale": "1-5", "value": None},
        {"field": "product_fallback_suitability", "scale": "1-5", "value": None},
        {"field": "compared_to_elevenlabs", "scale": "free_text", "value": None},
        {"field": "notes", "scale": "free_text", "value": None},
    ]


def build_manual_template(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "evaluation_id": "ULTRAVOX-AUDIO-LISTENING-REVIEW-MANUAL-001",
        "phase": "4J6",
        "status": "pending_manual_review",
        "source_review_packet": "ULTRAVOX-AUDIO-LISTENING-REVIEW-001",
        "audio_files_copied": False,
        "audio_files_committed": False,
        "manual_listening_checklist": checklist(),
        "per_audio_output_reviews": [
            {
                "entry_id": entry["entry_id"],
                "local_audio_path": entry["local_audio_path"],
                "status": "pending_manual_review",
                "ratings": {item["field"]: None for item in checklist()},
            }
            for entry in packet["agent_audio_review_entries"]
        ],
    }


def build_packet(sandbox: dict[str, Any], quality: dict[str, Any]) -> dict[str, Any]:
    entries = build_audio_entries(sandbox)
    return {
        "evaluation_id": "ULTRAVOX-AUDIO-LISTENING-REVIEW-001",
        "phase": "4J6",
        "status": "pending_manual_review",
        "source_sandbox_evaluation_id": sandbox.get("evaluation_id"),
        "source_quality_evaluation_id": quality.get("evaluation_id"),
        "source_sandbox_result_path": rel(SANDBOX_RESULT_PATH),
        "source_quality_result_path": rel(QUALITY_RESULT_PATH),
        "agent_audio_review_entries_count": len(entries),
        "agent_audio_review_entries": entries,
        "manual_review_template_json": rel(MANUAL_TEMPLATE_JSON),
        "manual_review_template_md": rel(MANUAL_TEMPLATE_MD),
        "manual_listening_required": True,
        "manual_listening_status": "pending_manual_review",
        "audio_files_copied": False,
        "audio_files_committed": False,
        "new_provider_call_made": False,
        "new_audio_generated": False,
        "outbound_phone_call_made": False,
        "real_customer_data_used": False,
        "raw_private_audio_or_transcripts_used": False,
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "real_customer_data_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }


def render_packet_report(packet: dict[str, Any]) -> str:
    lines = [
        "# ULTRAVOX-AUDIO-LISTENING-REVIEW-001",
        "",
        "Status: `pending_manual_review`",
        f"Agent audio review entries: `{packet['agent_audio_review_entries_count']}`",
        f"Manual review template JSON: `{packet['manual_review_template_json']}`",
        f"Manual review template MD: `{packet['manual_review_template_md']}`",
        "",
        "## Agent Audio Entries",
    ]
    for entry in packet["agent_audio_review_entries"]:
        lines.extend(
            [
                f"- Entry: `{entry['entry_id']}`",
                f"  - Local audio path: `{entry['local_audio_path']}`",
                f"  - Duration seconds: `{entry['duration_seconds']}`",
                f"  - Sample rate: `{entry['sample_rate']}`",
                f"  - File size bytes: `{entry['file_size_bytes']}`",
                f"  - Waveform hash: `{entry['waveform_hash']}`",
                f"  - Associated user prompt: `{entry['associated_user_prompt']}`",
                f"  - Agent transcript snippet: `{entry['agent_transcript_snippet']}`",
                f"  - First audio latency seconds: `{entry['first_audio_latency_seconds']}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Manual Listening Checklist",
            "- intelligibility 1-5",
            "- naturalness 1-5",
            "- voice quality 1-5",
            "- sales tone 1-5",
            "- pacing 1-5",
            "- artifact severity 1-5",
            "- interruption/turn-taking quality 1-5",
            "- thesis demo suitability 1-5",
            "- product fallback suitability 1-5",
            "- compared to ElevenLabs",
            "- notes",
            "",
            "## Boundaries",
            "Audio files copied: `false`",
            "Audio files committed: `false`",
            "New provider call made: `false`",
            "New audio generated: `false`",
            "Outbound phone call made: `false`",
            "Real customer data used: `false`",
            "Raw private audio or transcripts used: `false`",
            "Live wiring allowed: `false`",
            "Production call allowed: `false`",
            "Runtime behavior changed: `false`",
            "Response text changed: `false`",
            "",
        ]
    )
    return "\n".join(lines)


def render_manual_template_md(manual: dict[str, Any]) -> str:
    lines = [
        "# ULTRAVOX-AUDIO-LISTENING-REVIEW-MANUAL-001",
        "",
        "Status: `pending_manual_review`",
        "",
        "## Audio Outputs",
    ]
    for review in manual["per_audio_output_reviews"]:
        lines.extend(
            [
                f"- Entry: `{review['entry_id']}`",
                f"  - Local audio path: `{review['local_audio_path']}`",
                "  - Status: `pending_manual_review`",
            ]
        )
    lines.extend(
        [
            "",
            "## Checklist",
            "| Field | Rating / Notes |",
            "| --- | --- |",
        ]
    )
    for item in manual["manual_listening_checklist"]:
        lines.append(f"| {item['field']} | {item['scale']} |")
    lines.extend(
        [
            "",
            "Audio files copied: `false`",
            "Audio files committed: `false`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    sandbox = load_json(SANDBOX_RESULT_PATH)
    quality = load_json(QUALITY_RESULT_PATH)
    packet = build_packet(sandbox, quality)
    manual = build_manual_template(packet)
    write_json(PACKET_RESULT_PATH, packet)
    write_text(PACKET_REPORT_PATH, render_packet_report(packet))
    write_json(MANUAL_TEMPLATE_JSON, manual)
    write_text(MANUAL_TEMPLATE_MD, render_manual_template_md(manual))
    print(json.dumps({"status": packet["status"], "agent_audio_review_entries_count": packet["agent_audio_review_entries_count"]}, indent=2))


if __name__ == "__main__":
    main()
