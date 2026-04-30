#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
from pathlib import Path

from realtime_turn_cli import build_turn_case, find_campaign, run_turn_decision
from run_realtime_turn_simulation import load_realtime_cases


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES_PATH = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
DEFAULT_VOICE_LABEL = "Neutral Synthetic Test Voice"
VOICE_STYLE = "neutral-synthetic-test"
VOICE_RUN_PREFIX = "VOICE-001"


def resolve_project_path(path_text: str | None) -> Path | None:
    if not path_text:
        return None
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def project_relative_string(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def campaign_summary(campaign: dict) -> dict:
    return {
        "product_name": campaign.get("product_name"),
        "product_category": campaign.get("product_category"),
        "customer_type": campaign.get("customer_type"),
        "language": campaign.get("language"),
    }


def build_voice_packet(
    campaign: dict,
    stage: str,
    input_type: str,
    transcript: str,
    silence_count: int,
    decision: dict,
    provider: str,
    voice_name: str | None,
    audio_output_path: Path | None,
) -> dict:
    dry_run = provider == "dry-run"
    tts_text = decision["agent_response"]
    return {
        "voice_run_id": f"{VOICE_RUN_PREFIX}-{'dry-run' if dry_run else provider}",
        "voice_milestone": VOICE_RUN_PREFIX,
        "provider": provider,
        "mode": "metadata-only" if dry_run else "audio-file",
        "campaign_id": campaign["campaign_id"],
        "campaign": campaign_summary(campaign),
        "stage": stage,
        "input_type": input_type,
        "silence_count": silence_count if input_type == "silence-timeout" else None,
        "transcript": transcript,
        "decision": decision,
        "tts_text": tts_text,
        "voice": {
            "name": voice_name or DEFAULT_VOICE_LABEL,
            "style": VOICE_STYLE,
            "consent_boundary": "synthetic-test-voice-only",
            "cloned_voice": False,
        },
        "latency_contract": {
            "first_response_target_ms": 2000,
            "tts_start_target_ms": 500,
            "source_decision_latency_ms": decision.get("first_response_latency_ms"),
            "source_decision_latency_bucket": decision.get("first_response_latency_observed_bucket"),
        },
        "audio_output_path": str(audio_output_path) if audio_output_path is not None else None,
        "trace": {
            "source": "scripts/realtime_turn_cli.py",
            "case_file": project_relative_string(Path(campaign.get("_case_file", DEFAULT_CASES_PATH))),
            "synthetic_output": True,
            "requires_api_key": False,
        },
    }


def synthesize_with_windows_sapi(text: str, audio_path: Path, voice_name: str | None) -> None:
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["VOICE_001_TEXT"] = text
    env["VOICE_001_OUT"] = str(audio_path)
    env["VOICE_001_NAME"] = voice_name or ""
    command = r"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
if ($env:VOICE_001_NAME) {
  $synth.SelectVoice($env:VOICE_001_NAME)
}
$synth.SetOutputToWaveFile($env:VOICE_001_OUT)
$synth.Speak($env:VOICE_001_TEXT)
$synth.Dispose()
"""
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            env=env,
            text=True,
            capture_output=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise SystemExit("Windows SAPI provider requires PowerShell on Windows.") from exc
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        raise SystemExit(f"Windows SAPI synthesis failed: {message}") from exc


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a VOICE-001 TTS packet from a realtime sales-agent turn.")
    parser.add_argument("--campaign", required=True, help="Campaign ID to use.")
    parser.add_argument("--stage", required=True, help="Current call stage.")
    parser.add_argument("--transcript", default="", help="Customer transcript for this turn.")
    parser.add_argument(
        "--input-type",
        default="speech-final",
        choices=["speech-final", "voicemail-detected", "silence-timeout"],
        help="Runtime input type.",
    )
    parser.add_argument("--silence-count", type=int, default=0, help="Silence retry count for silence-timeout input.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES_PATH), help="Campaign wrapper case file to load.")
    parser.add_argument(
        "--provider",
        default="dry-run",
        choices=["dry-run", "windows-sapi"],
        help="TTS provider. Dry-run writes metadata only.",
    )
    parser.add_argument("--voice-name", help="Optional Windows SAPI voice name. Dry-run uses a neutral test label.")
    parser.add_argument("--out-json", help="Optional path to write the voice packet JSON.")
    parser.add_argument("--out-audio", help="Path to write WAV audio when using windows-sapi.")
    parser.add_argument("--dry-run", action="store_true", help="Force metadata-only dry-run mode.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    provider = "dry-run" if args.dry_run else args.provider
    out_audio = resolve_project_path(args.out_audio)

    if provider == "windows-sapi" and out_audio is None:
        raise SystemExit("--out-audio is required when --provider windows-sapi is used without --dry-run.")

    cases_path = resolve_project_path(args.cases)
    if cases_path is None:
        raise SystemExit("--cases is required.")
    campaigns, _cases = load_realtime_cases(cases_path)
    campaign = find_campaign(campaigns, args.campaign)
    campaign["_case_file"] = cases_path
    case = build_turn_case(args.campaign, args.stage, args.transcript, args.input_type, args.silence_count)
    decision = run_turn_decision(case)

    if provider == "windows-sapi" and out_audio is not None:
        synthesize_with_windows_sapi(decision["agent_response"], out_audio, args.voice_name)

    packet = build_voice_packet(
        campaign=campaign,
        stage=args.stage,
        input_type=args.input_type,
        transcript=args.transcript,
        silence_count=args.silence_count,
        decision=decision,
        provider=provider,
        voice_name=args.voice_name,
        audio_output_path=out_audio if provider != "dry-run" else None,
    )

    out_json = resolve_project_path(args.out_json)
    if out_json is not None:
        write_json(out_json, packet)

    print(json.dumps(packet, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
