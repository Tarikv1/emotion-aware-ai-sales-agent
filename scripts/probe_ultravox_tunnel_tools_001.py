#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.load_local_ultravox_env_001 import (  # noqa: E402
    API_KEY_ENV,
    UnsafeUltravoxEnvFile,
    load_local_ultravox_env,
)

OUT_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TUNNEL-TOOLS-PROBE-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
TUNNEL_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TUNNEL-SANDBOX-001" / "result.json"
CLOUDFLARED_PATH_ENV = "ULTRAVOX_TUNNEL_CLOUDFLARED_PATH"
NGROK_PATH_ENV = "ULTRAVOX_TUNNEL_NGROK_PATH"
LOCALTUNNEL_GATE = "LOCAL_ULTRAVOX_ALLOW_LOCALTUNNEL"
KNOWN_CLOUDFLARED_PATHS = [
    Path(r"C:\Program Files (x86)\cloudflared\cloudflared.exe"),
    Path(r"C:\Program Files\cloudflared\cloudflared.exe"),
]
KNOWN_NGROK_PATHS = [
    Path(r"C:\Program Files\ngrok\ngrok.exe"),
    Path(r"C:\Program Files (x86)\ngrok\ngrok.exe"),
    Path.home() / "AppData" / "Local" / "ngrok" / "ngrok.exe",
    Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages" / "Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe" / "ngrok.exe",
    Path.home() / "scoop" / "shims" / "ngrok.exe",
]
KNOWN_NGROK_CONFIG_PATHS = [
    Path.home() / "AppData" / "Local" / "ngrok" / "ngrok.yml",
    Path.home() / ".ngrok2" / "ngrok.yml",
]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_version(command: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return None
    text = " ".join((completed.stdout + " " + completed.stderr).split())
    return text[:240] or None


def path_is_safe_to_record(path: str | None) -> bool:
    if not path:
        return True
    lowered = path.lower()
    if any(token in lowered for token in ("api_key", "apikey", "token", "secret", "password", "key=")):
        return False
    for value in (os.environ.get(API_KEY_ENV), os.environ.get("PROJECT_ULTRAVOX_TOOL_TOKEN")):
        if value and value in path:
            return False
    return True


def evidence_path(path: str | None) -> str | None:
    if not path:
        return None
    return path if path_is_safe_to_record(path) else "<redacted_path>"


def first_existing_config_path() -> str | None:
    explicit = os.environ.get("NGROK_CONFIG", "").strip()
    candidates = [Path(explicit)] if explicit else []
    candidates.extend(KNOWN_NGROK_CONFIG_PATHS)
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return evidence_path(explicit) if explicit else None


def executable_probe(name: str, version_args: list[str], *, explicit_path: str | None = None, source: str = "PATH") -> dict[str, Any]:
    if explicit_path:
        resolved = explicit_path
        exists = Path(explicit_path).is_file()
    else:
        resolved = shutil.which(name)
        exists = bool(resolved)
    version = run_version([resolved, *version_args]) if resolved and exists else None
    return {
        "name": name,
        "available": bool(exists and version),
        "path_present": bool(resolved),
        "path_exists": bool(exists),
        "source": source,
        "executable": evidence_path(resolved),
        "_executable_for_run": resolved,
        "version": version,
        "version_ok": bool(version),
        "tunnel_opened": False,
    }


def evidence_probe(probe: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in probe.items() if not key.startswith("_")}


def evidence_cloudflared_discovery(discovery: dict[str, Any]) -> dict[str, Any]:
    return {
        **{key: value for key, value in discovery.items() if key not in {"path_lookup", "known_windows_paths"}},
        "path_lookup": evidence_probe(discovery["path_lookup"]) if discovery.get("path_lookup") else {},
        "known_windows_paths": [evidence_probe(item) for item in discovery.get("known_windows_paths", [])],
    }


def load_env_metadata() -> tuple[dict[str, bool], bool]:
    try:
        return load_local_ultravox_env(), False
    except UnsafeUltravoxEnvFile:
        return {
            "env_file_exists": True,
            "env_file_ignored_by_git": False,
            "env_file_loaded": False,
            "api_key_present": bool(os.environ.get(API_KEY_ENV)),
            "gates_enabled": False,
        }, True


def empty_probe(name: str, source: str = "explicit_env") -> dict[str, Any]:
    return {
        "name": name,
        "available": False,
        "path_present": False,
        "path_exists": False,
        "source": source,
        "executable": None,
        "version": None,
        "version_ok": False,
        "tunnel_opened": False,
    }


def discover_executable(
    name: str,
    version_args: list[str],
    *,
    env_var: str,
    known_paths: list[Path],
) -> tuple[dict[str, Any], dict[str, Any]]:
    explicit_value = os.environ.get(env_var, "").strip()
    explicit = (
        executable_probe(name, version_args, explicit_path=explicit_value or None, source="explicit_env")
        if explicit_value
        else empty_probe(name)
    )
    path_lookup = executable_probe(name, version_args, source="PATH")
    known_results = []
    for candidate in known_paths:
        known_results.append(executable_probe(name, version_args, explicit_path=str(candidate), source="known_windows_path"))

    selected = None
    selected_source = None
    for source_name, candidate in [
        ("explicit_env", explicit),
        ("PATH", path_lookup),
        *[("known_windows_path", item) for item in known_results],
    ]:
        if candidate["available"]:
            selected = candidate
            selected_source = source_name
            break

    selected_probe = dict(selected or explicit or path_lookup)
    if selected is None:
        selected_probe = path_lookup if path_lookup["path_present"] else explicit
    selected_probe["name"] = name
    selected_probe["available"] = bool(selected)
    selected_probe["source"] = selected_source or selected_probe.get("source")
    return selected_probe, {
        f"explicit_{name}_path_present": bool(explicit_value),
        f"explicit_{name}_path_exists": bool(explicit.get("path_exists")),
        f"explicit_{name}_version_ok": bool(explicit.get("version_ok")),
        f"explicit_{name}_executable": evidence_path(explicit_value) if explicit_value else None,
        "path_lookup": path_lookup,
        "known_windows_paths": known_results,
    }


def discover_cloudflared() -> tuple[dict[str, Any], dict[str, Any]]:
    return discover_executable(
        "cloudflared",
        ["--version"],
        env_var=CLOUDFLARED_PATH_ENV,
        known_paths=KNOWN_CLOUDFLARED_PATHS,
    )


def discover_ngrok() -> tuple[dict[str, Any], dict[str, Any]]:
    ngrok, discovery = discover_executable(
        "ngrok",
        ["version"],
        env_var=NGROK_PATH_ENV,
        known_paths=KNOWN_NGROK_PATHS,
    )
    config_path = first_existing_config_path()
    check = check_ngrok_config(ngrok.get("_executable_for_run"))
    ngrok.update(
        {
            "config_check_attempted": check["attempted"],
            "config_check_succeeded": check["succeeded"],
            "config_path": evidence_path(config_path),
            "auth_configured": check["auth_configured"],
        }
    )
    discovery.update(
        {
            "ngrok_config_check_attempted": check["attempted"],
            "ngrok_config_check_succeeded": check["succeeded"],
            "ngrok_config_path": evidence_path(config_path),
            "ngrok_auth_configured": check["auth_configured"],
        }
    )
    return ngrok, discovery


def check_ngrok_config(executable: str | None) -> dict[str, Any]:
    if not executable:
        return {"attempted": False, "succeeded": False, "auth_configured": "unknown"}
    try:
        completed = subprocess.run(
            [executable, "config", "check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return {"attempted": True, "succeeded": False, "auth_configured": "unknown"}
    output = " ".join((completed.stdout + " " + completed.stderr).lower().split())
    if completed.returncode == 0:
        auth_configured: bool | str = True
    elif "authtoken" in output or "authentication" in output or "no configuration" in output:
        auth_configured = False
    else:
        auth_configured = "unknown"
    return {"attempted": True, "succeeded": completed.returncode == 0, "auth_configured": auth_configured}


def load_prior_tunnel_state() -> dict[str, Any]:
    if not TUNNEL_RESULT_PATH.is_file():
        return {
            "prior_tunnel_evidence_exists": False,
            "cloudflared_dns_failed_before": False,
            "cloudflared_passed_before": False,
        }
    try:
        prior = json.loads(TUNNEL_RESULT_PATH.read_text(encoding="utf-8"))
    except Exception:
        prior = {}
    used_cloudflared = prior.get("tunnel_tool_used") == "cloudflared"
    cloudflared_dns_failed_before = bool(
        prior.get("cloudflared_dns_failed_before") is True
        or (
            used_cloudflared
            and prior.get("tunnel_url_created") is True
            and prior.get("dns_success") is False
        )
    )
    return {
        "prior_tunnel_evidence_exists": True,
        "cloudflared_dns_failed_before": cloudflared_dns_failed_before,
        "cloudflared_passed_before": bool(
            prior.get("cloudflared_passed_before") is True
            or
            used_cloudflared
            and prior.get("dns_success") is True
            and prior.get("http_success") is True
            and prior.get("auth_preflight_success") is True
        ),
        "prior_tunnel_tool_used": prior.get("tunnel_tool_used"),
        "prior_dns_success": prior.get("dns_success"),
        "prior_http_success": prior.get("http_success"),
        "prior_auth_preflight_success": prior.get("auth_preflight_success"),
    }


def discover_tunnel_tools() -> dict[str, Any]:
    cloudflared, cloudflared_discovery = discover_cloudflared()
    ngrok, ngrok_discovery = discover_ngrok()
    localtunnel = executable_probe("localtunnel", ["--version"])
    lt = executable_probe("lt", ["--version"])
    npx_path = shutil.which("npx")
    npx = {
        "name": "npx",
        "available": bool(npx_path),
        "path_present": bool(npx_path),
        "version": run_version([npx_path, "--version"]) if npx_path else None,
        "localtunnel_via_npx_candidate": bool(npx_path),
        "runner_uses_npx": False,
        "reason_runner_uses_npx_false": "npx may install packages or hit the network, so Phase 4J3 only uses already-installed tunnel executables.",
        "tunnel_opened": False,
    }
    prior_state = load_prior_tunnel_state()
    localtunnel_explicitly_enabled = os.environ.get(LOCALTUNNEL_GATE) == "1"
    usable = []
    if cloudflared["available"] and prior_state["cloudflared_passed_before"]:
        usable.append("cloudflared")
    if ngrok["available"]:
        usable.append("ngrok")
    if localtunnel_explicitly_enabled and localtunnel["available"]:
        usable.append("localtunnel")
    elif localtunnel_explicitly_enabled and lt["available"]:
        usable.append("lt")
    selected = next((tool for tool in ("cloudflared", "ngrok", "localtunnel", "lt") if tool in usable), None)
    selected_details = {
        "cloudflared": cloudflared,
        "ngrok": ngrok,
        "localtunnel": localtunnel,
        "lt": lt,
    }.get(selected or "", {})
    return {
        "cloudflared": cloudflared,
        "ngrok": ngrok,
        "localtunnel": localtunnel,
        "lt": lt,
        "npx": npx,
        "cloudflared_discovery": cloudflared_discovery,
        "ngrok_discovery": ngrok_discovery,
        **prior_state,
        "localtunnel_explicitly_enabled": localtunnel_explicitly_enabled,
        "usable_tunnel_tools": usable,
        "selected_tunnel_tool": selected,
        "selected_preferred_tool": selected,
        "selected_tunnel_executable": selected_details.get("executable"),
        "selected_tunnel_executable_for_run": selected_details.get("_executable_for_run"),
    }


def build_result() -> dict[str, Any]:
    env_metadata, unsafe_secret_file = load_env_metadata()
    discovery = discover_tunnel_tools() if not unsafe_secret_file else {
        "cloudflared": {"name": "cloudflared", "available": False, "path_present": False, "path_exists": False, "source": None, "executable": None, "version": None, "version_ok": False, "tunnel_opened": False},
        "ngrok": {"name": "ngrok", "available": False, "path_present": False, "path_exists": False, "source": None, "executable": None, "version": None, "version_ok": False, "tunnel_opened": False},
        "localtunnel": {"name": "localtunnel", "available": False, "path_present": False, "path_exists": False, "source": None, "executable": None, "version": None, "version_ok": False, "tunnel_opened": False},
        "lt": {"name": "lt", "available": False, "path_present": False, "path_exists": False, "source": None, "executable": None, "version": None, "version_ok": False, "tunnel_opened": False},
        "npx": {"name": "npx", "available": False, "path_present": False, "version": None, "localtunnel_via_npx_candidate": False, "runner_uses_npx": False, "tunnel_opened": False},
        "cloudflared_discovery": {
            "explicit_cloudflared_path_present": False,
            "explicit_cloudflared_path_exists": False,
            "explicit_cloudflared_version_ok": False,
            "explicit_cloudflared_executable": None,
            "path_lookup": {},
            "known_windows_paths": [],
        },
        "ngrok_discovery": {
            "explicit_ngrok_path_present": False,
            "explicit_ngrok_path_exists": False,
            "explicit_ngrok_version_ok": False,
            "explicit_ngrok_executable": None,
            "path_lookup": {},
            "known_windows_paths": [],
        },
        "prior_tunnel_evidence_exists": False,
        "cloudflared_dns_failed_before": False,
        "cloudflared_passed_before": False,
        "localtunnel_explicitly_enabled": False,
        "usable_tunnel_tools": [],
        "selected_tunnel_tool": None,
        "selected_preferred_tool": None,
        "selected_tunnel_executable": None,
        "selected_tunnel_executable_for_run": None,
    }
    cloudflared_discovery = evidence_cloudflared_discovery(discovery["cloudflared_discovery"])
    ngrok_discovery = evidence_cloudflared_discovery(discovery["ngrok_discovery"])
    return {
        "evaluation_id": "ULTRAVOX-TUNNEL-TOOLS-PROBE-001",
        "phase": "4J3",
        "phase_detail": "4J3G",
        "env_file_exists": env_metadata["env_file_exists"],
        "env_file_ignored_by_git": env_metadata["env_file_ignored_by_git"],
        "env_file_loaded": env_metadata["env_file_loaded"],
        "unsafe_secret_file": unsafe_secret_file,
        "probe_only": True,
        "tunnel_opened": False,
        "provider_calls_made": False,
        "ultravox_hosted_call_made": False,
        "outbound_phone_call_made": False,
        "real_customer_data_used": False,
        "raw_private_audio_or_transcripts_used": False,
        "secrets_logged": False,
        "explicit_cloudflared_path_present": cloudflared_discovery["explicit_cloudflared_path_present"],
        "explicit_cloudflared_path_exists": cloudflared_discovery["explicit_cloudflared_path_exists"],
        "explicit_cloudflared_version_ok": cloudflared_discovery["explicit_cloudflared_version_ok"],
        "explicit_cloudflared_executable": cloudflared_discovery["explicit_cloudflared_executable"],
        "cloudflared_available": discovery["cloudflared"]["available"],
        "cloudflared_dns_failed_before": discovery["cloudflared_dns_failed_before"],
        "cloudflared_passed_before": discovery["cloudflared_passed_before"],
        "ngrok_available": discovery["ngrok"]["available"],
        "ngrok_version_ok": discovery["ngrok"].get("version_ok", False),
        "ngrok_version": discovery["ngrok"].get("version"),
        "ngrok_path_source": discovery["ngrok"].get("source"),
        "ngrok_config_check_attempted": discovery["ngrok"].get("config_check_attempted", False),
        "ngrok_config_check_succeeded": discovery["ngrok"].get("config_check_succeeded", False),
        "ngrok_config_path": discovery["ngrok"].get("config_path"),
        "ngrok_auth_configured": discovery["ngrok"].get("auth_configured", "unknown"),
        "explicit_ngrok_path_present": ngrok_discovery["explicit_ngrok_path_present"],
        "explicit_ngrok_path_exists": ngrok_discovery["explicit_ngrok_path_exists"],
        "explicit_ngrok_version_ok": ngrok_discovery["explicit_ngrok_version_ok"],
        "selected_tunnel_tool": discovery["selected_tunnel_tool"],
        "selected_preferred_tool": discovery["selected_preferred_tool"],
        "selected_tunnel_executable": discovery["selected_tunnel_executable"],
        "candidate_tunnel_tools": {
            "cloudflared": evidence_probe(discovery["cloudflared"]),
            "ngrok": evidence_probe(discovery["ngrok"]),
            "localtunnel": evidence_probe(discovery["localtunnel"]),
            "lt": evidence_probe(discovery["lt"]),
            "npx": evidence_probe(discovery["npx"]),
        },
        "cloudflared_discovery": cloudflared_discovery,
        "ngrok_discovery": ngrok_discovery,
        "prior_tunnel_evidence_exists": discovery["prior_tunnel_evidence_exists"],
        "localtunnel_explicitly_enabled": discovery["localtunnel_explicitly_enabled"],
        "usable_tunnel_tools": discovery["usable_tunnel_tools"],
        "preferred_order": ["cloudflared", "ngrok", "localtunnel"],
        "selected_if_gated": discovery["selected_tunnel_tool"],
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# ULTRAVOX-TUNNEL-TOOLS-PROBE-001 Report",
        "",
        "This probe checks local tunnel CLI availability only. It does not open a tunnel and does not call Ultravox.",
        "",
        f"Env file ignored by Git: `{str(result['env_file_ignored_by_git']).lower()}`",
        f"Explicit cloudflared path present: `{str(result['explicit_cloudflared_path_present']).lower()}`",
        f"Explicit cloudflared path exists: `{str(result['explicit_cloudflared_path_exists']).lower()}`",
        f"Explicit cloudflared version ok: `{str(result['explicit_cloudflared_version_ok']).lower()}`",
        f"Cloudflared available: `{str(result['cloudflared_available']).lower()}`",
        f"Cloudflared DNS failed before: `{str(result['cloudflared_dns_failed_before']).lower()}`",
        f"Ngrok available: `{str(result['ngrok_available']).lower()}`",
        f"Ngrok auth configured: `{result['ngrok_auth_configured']}`",
        f"Ngrok config check succeeded: `{str(result['ngrok_config_check_succeeded']).lower()}`",
        f"Ngrok config path: `{result['ngrok_config_path']}`",
        f"Ngrok path source: `{result['ngrok_path_source']}`",
        f"Selected tunnel tool: `{result['selected_tunnel_tool']}`",
        f"Selected preferred tool: `{result['selected_preferred_tool']}`",
        f"Selected tunnel executable: `{result['selected_tunnel_executable']}`",
        f"Selected if gated: `{result['selected_if_gated']}`",
        f"Tunnel opened: `{str(result['tunnel_opened']).lower()}`",
        f"Provider calls made: `{str(result['provider_calls_made']).lower()}`",
        "",
        "## Tools",
        "",
    ]
    for name, details in result["candidate_tunnel_tools"].items():
        lines.append(f"- {name}: available `{str(details['available']).lower()}`, version `{details.get('version')}`")
    lines.extend(
        [
            "",
            f"Live wiring allowed: `{str(result['live_wiring_allowed']).lower()}`",
            f"Production call allowed: `{str(result['production_call_allowed']).lower()}`",
            f"Runtime behavior changed: `{str(result['runtime_behavior_changed']).lower()}`",
            f"Response text changed: `{str(result['response_text_changed']).lower()}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    result = build_result()
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, render_report(result))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
