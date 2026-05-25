#!/usr/bin/env python3
from __future__ import annotations

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

from runtime.config import local_voice_config  # noqa: E402
from runtime.providers.tts_provider_clients import resolve_voice_id, voice_env_for_language  # noqa: E402
from runtime.voice.runtime_tts_delivery import provider_for_key  # noqa: E402


CHECKPOINT_ID = "ELEVENLABS-VOICE-RESOLUTION-AUDIT-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
RUNTIME_SCAN_ROOTS = [ROOT / "runtime", ROOT / "scripts"]
SAFE_RELATIVE_CONFIG_PATHS = [
    ROOT / "runtime" / "config" / "local" / "voice_ids.json",
    ROOT / "config" / "local" / "voice_ids.json",
]

VOICE_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{20,}$")
VOICE_CONTEXT_RE = re.compile(r"voice|elevenlabs|tts", re.I)
RAW_LOG_RE = re.compile(r"\b(print|logger\.|logging\.|write_text|json\.dumps)\b.*\bvoice_id\b", re.I)
ASSIGNMENT_LITERAL_RE = re.compile(r"(?:voice_id|ELEVENLABS_VOICE_ID|\"(?:en|de|default|english_sales_voice_v1|german_sales_voice_v1)\")\s*[:=]\s*[\"']([^\"']+)[\"']", re.I)


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


def safe_voice_diag(value: str | None, source: str | None) -> dict[str, Any]:
    return {
        "voice_id_source": source,
        "voice_id_present": bool(value),
        "voice_id_length": len(value) if value else 0,
        "voice_id_hash": sha8(value),
        "raw_value_logged": False,
    }


def looks_like_raw_voice_id(token: str) -> bool:
    token = str(token or "").strip()
    if token.startswith(("ELEVENLABS_", "paste-")):
        return False
    if not VOICE_TOKEN_RE.fullmatch(token):
        return False
    if not token.isalnum():
        return False
    return any(char.islower() for char in token) and any(char.isupper() for char in token) and any(char.isdigit() for char in token)


def parse_env_file(path: Path) -> dict[str, Any]:
    keys: list[str] = []
    if not path.is_file():
        return {"path": project_relative(path), "present": False, "keys_present": []}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip().startswith("ELEVENLABS_") and value.strip():
            keys.append(key.strip())
    return {"path": project_relative(path), "present": True, "keys_present": sorted(set(keys))}


def active_local_voice_config_path() -> Path | None:
    for path in SAFE_RELATIVE_CONFIG_PATHS:
        if path.is_file():
            return path
    return None


def safe_local_voice_file_diag(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"resolved_voice_config_source_path": None, "voice_config_file_present": False}
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    provider_data = payload.get("elevenlabs") if isinstance(payload, dict) else None
    labels: list[str] = []
    if isinstance(provider_data, dict):
        aliases = provider_data.get("aliases")
        if isinstance(aliases, dict):
            labels.extend(str(key) for key in aliases)
    return {
        "resolved_voice_config_source_path": project_relative(path),
        "voice_config_file_present": True,
        "voice_alias_or_label": sorted(labels) or None,
    }


def iter_scan_files() -> list[Path]:
    files: list[Path] = []
    for root in RUNTIME_SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
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
            f"- Voice ID source: `{result['voice_id_source']}`",
            f"- Voice ID present: `{str(result['voice_id_present']).lower()}`",
            f"- Voice ID length: `{result['voice_id_length']}`",
            f"- Voice ID hash: `{result['voice_id_hash']}`",
            f"- Raw value logged: `{str(result['raw_value_logged']).lower()}`",
            f"- Hardcoded voice findings: `{len(result['hardcoded_voice_id_findings'])}`",
            f"- Raw logging findings: `{len(result['raw_voice_id_logging_findings'])}`",
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
    voice_id, source = resolve_voice_id(provider, language, force_key_missing=False)
    active_config = active_local_voice_config_path()
    local_diag = safe_local_voice_file_diag(active_config)
    hardcoded, logging_findings = raw_voice_findings()
    expected_source = voice_env_for_language(provider, language)
    diag = safe_voice_diag(voice_id, source)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not hardcoded and not logging_findings else "fail",
        **diag,
        **local_diag,
        "language": language,
        "effective_provider_model": provider.get("model_id"),
        "env_variables_used": [
            provider["api_key_env_var"],
            provider["language_voice_id_env_vars"]["en"],
            provider["default_voice_id_env_var"],
        ],
        "env_file": parse_env_file(ROOT / "runtime" / "config" / "local" / "elevenlabs.env"),
        "legacy_env_file_note": "The running server process reads its active process environment plus the configured env file loaded at startup; it does not read every .env file on disk.",
        "cli_voice_override_supported": False,
        "campaign_specific_voice_override_present": False,
        "route_signal_vs_generic_resolution": "same resolver; different voice_consistency_mode affects settings, not voice id source",
        "stale_env_can_override_config": bool(os.environ.get(expected_source) or os.environ.get(provider["default_voice_id_env_var"])),
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
        "raw_value_logged": False,
        "provider_calls_made": False,
        "live_tts_calls_made": False,
    }
    write_evidence(result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "voice_id_source": result["voice_id_source"],
                "voice_id_present": result["voice_id_present"],
                "voice_id_hash": result["voice_id_hash"],
                "hardcoded_voice_findings": len(hardcoded),
                "raw_logging_findings": len(logging_findings),
            },
            indent=2,
            sort_keys=True,
        )
    )
    if result["status"] != "pass":
        sys.exit(1)


if __name__ == "__main__":
    main()
