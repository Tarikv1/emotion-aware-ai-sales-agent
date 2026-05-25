#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.providers.tts_provider_clients import resolve_voice_id, voice_env_for_language  # noqa: E402
from runtime.voice.runtime_tts_delivery import provider_for_key  # noqa: E402


CHECKPOINT_ID = "ELEVENLABS-VOICE-RESOLUTION-AUDIT-001"
CURRENT_COMMIT = "729d06e"
FIXTURE_RELATIVE = "runtime/campaigns/examples/public-openai-chatgpt-plans.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
PRIVATE_ROOT = ROOT / "data" / "private"

SCAN_ROOTS = [ROOT / "runtime", ROOT / "scripts", ROOT / "docs", ROOT / "research" / "experiments" / "generated"]
LOCAL_VOICE_CONFIG_PATHS = {
    ROOT / "runtime" / "config" / "local" / "voice_ids.json",
    ROOT / "config" / "local" / "voice_ids.json",
}
LOCAL_VOICE_CONFIG_PRECEDENCE = [
    ROOT / "runtime" / "config" / "local" / "voice_ids.json",
    ROOT / "config" / "local" / "voice_ids.json",
]

VOICE_TOKEN_RE = re.compile(r"^[A-Za-z0-9]{20}$")
VOICE_CONTEXT_RE = re.compile(r"voice|elevenlabs|tts", re.I)
RAW_LOG_RE = re.compile(r"\b(print|logger\.|logging\.|write_text|json\.dumps)\b.*\bvoice_id\b", re.I)
ASSIGNMENT_LITERAL_RE = re.compile(
    r"(?:voice_id|ELEVENLABS_VOICE_ID|\"(?:en|de|default|english_sales_voice_v1|german_sales_voice_v1)\")\s*[:=]\s*[\"']([^\"']+)[\"']",
    re.I,
)


def project_relative(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def sha8(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def selected_config(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("selected_campaign_config") if isinstance(payload.get("selected_campaign_config"), dict) else {}


def campaign_path(payload: dict[str, Any]) -> str:
    selected = selected_config(payload)
    return str(payload.get("campaign_config_path") or selected.get("config_path") or "").replace("\\", "/")


def packet(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("packet") if isinstance(payload.get("packet"), dict) else {}


def summary(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("summary") if isinstance(payload.get("summary"), dict) else {}


def tts(payload: dict[str, Any]) -> dict[str, Any]:
    body = packet(payload)
    return body.get("tts_delivery") if isinstance(body.get("tts_delivery"), dict) else {}


def generated_at(payload: dict[str, Any]) -> str | None:
    value = payload.get("generated_at_utc") or payload.get("generated_at")
    return str(value) if value else None


def sort_dt(record: dict[str, Any]) -> datetime:
    parsed = parse_dt(generated_at(record["payload"]))
    if parsed:
        return parsed
    return datetime.fromtimestamp(record["mtime"], tz=timezone.utc)


def provider_calls(payload: dict[str, Any]) -> bool:
    delivery = tts(payload)
    sumry = summary(payload)
    return bool(delivery.get("provider_calls_made") or sumry.get("tts_provider_calls_made"))


def audio_created(payload: dict[str, Any]) -> bool:
    delivery = tts(payload)
    sumry = summary(payload)
    return bool(delivery.get("audio_file_created") or sumry.get("tts_audio_file_created"))


def live_tts_used(payload: dict[str, Any]) -> bool:
    return bool(payload.get("live_tts_used") or (provider_calls(payload) and audio_created(payload)))


def private_openai_packets() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not PRIVATE_ROOT.exists():
        return records
    for root in PRIVATE_ROOT.glob("live-demo-*"):
        if not root.is_dir():
            continue
        for path in root.rglob("*.json"):
            payload = load_json(path)
            if not payload or campaign_path(payload) != FIXTURE_RELATIVE:
                continue
            records.append({"path": path, "payload": payload, "mtime": path.stat().st_mtime})
    return sorted(records, key=sort_dt, reverse=True)


def current_threshold(records: list[dict[str, Any]]) -> datetime | None:
    current_times = [sort_dt(record) for record in records if str(record["payload"].get("git_head_short") or "") == CURRENT_COMMIT]
    if current_times:
        return min(current_times)
    live_times = [sort_dt(record) for record in records if live_tts_used(record["payload"])]
    return min(live_times) if live_times else None


def is_current(record: dict[str, Any], threshold: datetime | None) -> bool:
    payload = record["payload"]
    if str(payload.get("git_head_short") or "") == CURRENT_COMMIT:
        return True
    if payload.get("git_head_short"):
        return False
    return bool(threshold and sort_dt(record) >= threshold and live_tts_used(payload))


def latest_current_voice_packet(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    threshold = current_threshold(records)
    current = [record for record in records if is_current(record, threshold)]
    live = [record for record in current if live_tts_used(record["payload"]) and provider_calls(record["payload"])]
    return (live or current or [None])[0]


def voice_diag_from_packet(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {
            "voice_id_source": None,
            "voice_id_present": False,
            "voice_id_length": 0,
            "voice_id_hash": None,
            "raw_value_logged": False,
        }
    delivery = tts(payload)
    diag = delivery.get("voice_id_diagnostics") if isinstance(delivery.get("voice_id_diagnostics"), dict) else {}
    return {
        "voice_id_source": delivery.get("selected_voice_id_source") or delivery.get("selected_voice_id_env_var") or diag.get("source") or diag.get("voice_id_source"),
        "voice_id_present": bool(delivery.get("voice_id_present") or diag.get("present") or diag.get("voice_id_present")),
        "voice_id_length": int(diag.get("length") or diag.get("voice_id_length") or 0),
        "voice_id_hash": diag.get("sha256_8") or diag.get("voice_id_hash"),
        "raw_value_logged": bool(diag.get("raw_value_logged") or delivery.get("voice_id_value_logged")),
    }


def safe_voice_diag(value: str | None, source: str | None) -> dict[str, Any]:
    return {
        "voice_id_source": source,
        "voice_id_present": bool(value),
        "voice_id_length": len(value) if value else 0,
        "voice_id_hash": sha8(value),
        "raw_value_logged": False,
    }


def parse_env_file(path: Path) -> dict[str, Any]:
    keys: list[str] = []
    if not path.is_file():
        return {"path": project_relative(path), "present": False, "keys_present": []}
    for line in path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip().startswith("ELEVENLABS_") and value.strip():
            keys.append(key.strip())
    return {"path": project_relative(path), "present": True, "keys_present": sorted(set(keys))}


def active_local_voice_config_path() -> Path | None:
    for path in LOCAL_VOICE_CONFIG_PRECEDENCE:
        if path.is_file():
            return path
    return None


def safe_local_voice_file_diag(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"resolved_voice_config_source_path": None, "voice_config_file_present": False, "voice_alias_or_label": None}
    payload = load_json(path) or {}
    provider_data = payload.get("elevenlabs") if isinstance(payload, dict) else None
    labels: list[str] = []
    if isinstance(provider_data, dict):
        aliases = provider_data.get("aliases")
        if isinstance(aliases, dict):
            labels.extend(str(key) for key in aliases)
        for key in ("en", "de", "default"):
            if provider_data.get(key):
                labels.append(key)
    return {
        "resolved_voice_config_source_path": project_relative(path),
        "voice_config_file_present": True,
        "voice_alias_or_label": sorted(set(labels)) or None,
    }


def looks_like_raw_voice_id(token: str) -> bool:
    token = str(token or "").strip()
    if token.startswith(("ELEVENLABS_", "paste-", "local_voice_ids")):
        return False
    return bool(VOICE_TOKEN_RE.fullmatch(token) and any(ch.islower() for ch in token) and any(ch.isupper() for ch in token) and any(ch.isdigit() for ch in token))


def iter_scan_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            if path.resolve() in {item.resolve() for item in LOCAL_VOICE_CONFIG_PATHS}:
                continue
            if path.suffix.lower() not in {".py", ".json", ".md", ".txt", ".env", ".example"}:
                continue
            files.append(path)
    return files


def raw_voice_findings() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    hardcoded: list[dict[str, Any]] = []
    logging_findings: list[dict[str, Any]] = []
    for path in iter_scan_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if RAW_LOG_RE.search(line) and "raw_value_logged" not in line and "voice_id_value_logged" not in line:
                logging_findings.append(
                    {
                        "path": project_relative(path),
                        "line": line_number,
                        "line_hash": sha8(line.strip()),
                    }
                )
            if not (VOICE_CONTEXT_RE.search(line) or "voice_ids" in str(path).lower()):
                continue
            for match in ASSIGNMENT_LITERAL_RE.finditer(line):
                token = match.group(1).strip()
                if not looks_like_raw_voice_id(token):
                    continue
                hardcoded.append(
                    {
                        "path": project_relative(path),
                        "line": line_number,
                        "value_length": len(token),
                        "value_hash": sha8(token),
                        "raw_value_logged": False,
                    }
                )
    return hardcoded, logging_findings


def write_evidence(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = "\n".join(
        [
            f"# {CHECKPOINT_ID}",
            "",
            f"- Status: `{result['status']}`",
            f"- Active evidence source: `{result['active_evidence_source']}`",
            f"- Voice ID source: `{result['voice_id_source']}`",
            f"- Voice ID present: `{str(result['voice_id_present']).lower()}`",
            f"- Voice ID length: `{result['voice_id_length']}`",
            f"- Voice ID hash: `{result['voice_id_hash']}`",
            f"- Raw value logged: `{str(result['raw_value_logged']).lower()}`",
            f"- Hardcoded voice findings: `{len(result['hardcoded_voice_id_findings'])}`",
            f"- Raw logging findings: `{len(result['raw_voice_id_logging_findings'])}`",
            f"- Voice source expectation: `{result['voice_source_expectation_status']}`",
            "",
            "## Current Packet Voice Diagnostics",
            "",
            "```json",
            json.dumps(result["current_packet_voice_diagnostics"], indent=2, sort_keys=True),
            "```",
            "",
            "## Precedence",
            "",
            *[f"{index}. {item}" for index, item in enumerate(result["precedence_chain"], start=1)],
            "",
        ]
    )
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    provider = provider_for_key("elevenlabs")
    language = "en"
    expected_env_source = voice_env_for_language(provider, language)
    current_process_voice_id, current_process_source = resolve_voice_id(provider, language, force_key_missing=False)
    current_process_diag = safe_voice_diag(current_process_voice_id, current_process_source)
    records = private_openai_packets()
    latest = latest_current_voice_packet(records)
    packet_diag = voice_diag_from_packet(latest["payload"] if latest else None)
    active_diag = packet_diag if packet_diag["voice_id_present"] else current_process_diag
    active_evidence_source = "latest_current_private_openai_live_packet" if packet_diag["voice_id_present"] else "current_codex_process_resolver"
    active_config = active_local_voice_config_path()
    local_diag = safe_local_voice_file_diag(active_config)
    hardcoded, logging_findings = raw_voice_findings()
    raw_logged_count = len(hardcoded) + len(logging_findings) + int(bool(active_diag["raw_value_logged"]))
    voice_source_expectation_status = (
        "env_source_confirmed"
        if active_diag["voice_id_source"] == expected_env_source
        else "non_env_source_observed_review_operator_environment"
    )
    failures: list[str] = []
    if not active_diag["voice_id_present"]:
        failures.append("voice_id_missing")
    if int(active_diag["voice_id_length"] or 0) != 20:
        failures.append("voice_id_length_not_20")
    if not active_diag["voice_id_hash"]:
        failures.append("voice_id_hash_missing")
    if raw_logged_count:
        failures.append("raw_voice_id_logged_or_hardcoded")

    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "active_evidence_source": active_evidence_source,
        "latest_current_packet_path": project_relative(latest["path"]) if latest else None,
        "latest_current_packet_hash": sha_file(latest["path"]) if latest else None,
        "latest_current_packet_generated_at": generated_at((latest or {}).get("payload", {})) if latest else None,
        "voice_id_source": active_diag["voice_id_source"],
        "voice_id_present": active_diag["voice_id_present"],
        "voice_id_length": active_diag["voice_id_length"],
        "voice_id_hash": active_diag["voice_id_hash"],
        "raw_value_logged": active_diag["raw_value_logged"],
        "raw_voice_id_logged_count": raw_logged_count,
        "expected_env_voice_source": expected_env_source,
        "voice_source_expectation_status": voice_source_expectation_status,
        "current_packet_voice_diagnostics": packet_diag,
        "current_codex_process_voice_diagnostics": current_process_diag,
        **local_diag,
        "language": language,
        "effective_provider_model": provider.get("model_id"),
        "env_variables_used": [
            provider["api_key_env_var"],
            provider["language_voice_id_env_vars"]["en"],
            provider["default_voice_id_env_var"],
        ],
        "env_file": parse_env_file(ROOT / "runtime" / "config" / "local" / "elevenlabs.env"),
        "legacy_env_file_note": "The live demo process uses its active process environment first, then local voice config fallback. This audit does not print raw values.",
        "cli_voice_override_supported": False,
        "campaign_specific_voice_override_present": False,
        "route_signal_vs_generic_resolution": "same resolver; generic voice_consistency_mode changes settings, not voice id precedence",
        "stale_env_can_override_config": bool(os.environ.get(expected_env_source) or os.environ.get(provider["default_voice_id_env_var"])),
        "server_restart_required_for_env_changes": True,
        "precedence_chain": [
            f"{provider['language_voice_id_env_vars']['en']} from active process environment",
            f"{provider['default_voice_id_env_var']} from active process environment",
            "runtime/config/local/voice_ids.json if present",
            "config/local/voice_ids.json legacy local fallback if runtime local file is absent",
            "no documented fallback voice id if no env/config exists",
        ],
        "hardcoded_voice_id_findings": hardcoded,
        "raw_voice_id_logging_findings": logging_findings,
        "provider_calls_made_by_audit": False,
        "live_tts_calls_made_by_audit": False,
        "raw_private_transcript_copied_to_public_evidence": False,
    }
    write_evidence(result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "voice_id_source": result["voice_id_source"],
                "voice_id_present": result["voice_id_present"],
                "voice_id_length": result["voice_id_length"],
                "voice_id_hash": result["voice_id_hash"],
                "raw_voice_id_logged_count": result["raw_voice_id_logged_count"],
                "voice_source_expectation_status": result["voice_source_expectation_status"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    if result["status"] != "pass":
        sys.exit(1)


if __name__ == "__main__":
    main()
