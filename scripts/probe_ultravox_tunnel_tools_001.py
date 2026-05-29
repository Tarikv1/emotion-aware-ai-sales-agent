#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TUNNEL-TOOLS-PROBE-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"


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


def executable_probe(name: str, version_args: list[str]) -> dict[str, Any]:
    path = shutil.which(name)
    return {
        "name": name,
        "available": bool(path),
        "path_present": bool(path),
        "version": run_version([path, *version_args]) if path else None,
        "tunnel_opened": False,
    }


def build_result() -> dict[str, Any]:
    cloudflared = executable_probe("cloudflared", ["--version"])
    ngrok = executable_probe("ngrok", ["version"])
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
    usable = []
    if cloudflared["available"]:
        usable.append("cloudflared")
    if ngrok["available"]:
        usable.append("ngrok")
    if localtunnel["available"]:
        usable.append("localtunnel")
    elif lt["available"]:
        usable.append("lt")
    selected = next((tool for tool in ("cloudflared", "ngrok", "localtunnel", "lt") if tool in usable), None)
    return {
        "evaluation_id": "ULTRAVOX-TUNNEL-TOOLS-PROBE-001",
        "phase": "4J3",
        "probe_only": True,
        "tunnel_opened": False,
        "provider_calls_made": False,
        "ultravox_hosted_call_made": False,
        "outbound_phone_call_made": False,
        "real_customer_data_used": False,
        "raw_private_audio_or_transcripts_used": False,
        "secrets_logged": False,
        "candidate_tunnel_tools": {
            "cloudflared": cloudflared,
            "ngrok": ngrok,
            "localtunnel": localtunnel,
            "lt": lt,
            "npx": npx,
        },
        "usable_tunnel_tools": usable,
        "preferred_order": ["cloudflared", "ngrok", "localtunnel"],
        "selected_if_gated": selected,
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
