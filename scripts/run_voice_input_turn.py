#!/usr/bin/env python3
import argparse
import hashlib
import html
import json
import wave
from pathlib import Path

from generate_voice_response import build_voice_packet, resolve_project_path
from realtime_turn_cli import build_turn_case, find_campaign, run_turn_decision
from run_realtime_turn_simulation import load_realtime_cases


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES_PATH = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
VOICE_INPUT_MILESTONE = "VOICE-002"


def project_relative_string(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def sha256_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wav_metadata(path: Path) -> dict:
    with wave.open(str(path), "rb") as wav_file:
        frames = wav_file.getnframes()
        frame_rate = wav_file.getframerate()
        return {
            "channels": wav_file.getnchannels(),
            "sample_rate_hz": frame_rate,
            "sample_width_bytes": wav_file.getsampwidth(),
            "frame_count": frames,
            "duration_seconds": round(frames / frame_rate, 3) if frame_rate else None,
        }


def audio_metadata(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Audio file does not exist: {path}")
    if not path.is_file():
        raise SystemExit(f"Audio path is not a file: {path}")

    suffix = path.suffix.lower().lstrip(".") or "unknown"
    metadata = {
        "path": str(path),
        "project_relative_path": project_relative_string(path),
        "format": suffix,
        "byte_size": path.stat().st_size,
        "sha256": sha256_digest(path),
        "duration_seconds": None,
        "channels": None,
        "sample_rate_hz": None,
    }
    if suffix == "wav":
        wav = wav_metadata(path)
        metadata.update(wav)
    return metadata


def load_transcript(transcript: str | None, transcript_file: str | None) -> tuple[str, str]:
    if transcript:
        return transcript, "cli"
    if transcript_file:
        path = resolve_project_path(transcript_file)
        if path is None or not path.exists():
            raise SystemExit(f"Transcript file does not exist: {transcript_file}")
        return path.read_text(encoding="utf-8").strip(), "file"
    raise SystemExit("manual-transcript provider requires --transcript or --transcript-file.")


def build_voice_input_packet(
    campaign: dict,
    stage: str,
    input_type: str,
    silence_count: int,
    audio: dict,
    transcript: str,
    transcript_source: str,
    response_packet: dict,
    listener_out: Path | None,
) -> dict:
    return {
        "voice_input_run_id": f"{VOICE_INPUT_MILESTONE}-manual-transcript",
        "voice_milestone": VOICE_INPUT_MILESTONE,
        "provider": "manual-transcript",
        "campaign_id": campaign["campaign_id"],
        "campaign": response_packet["campaign"],
        "stage": stage,
        "input_type": input_type,
        "audio_input": audio,
        "consent": {
            "confirmed": True,
            "scope": "recorded-audio experiment only",
            "private_customer_audio_allowed": False,
            "synthetic_placeholder_recommended": True,
        },
        "transcription": {
            "provider": "manual-transcript",
            "transcript_source": transcript_source,
            "transcript": transcript,
            "confidence": None,
            "language": campaign.get("language"),
            "requires_api_key": False,
        },
        "response_packet": response_packet,
        "listener_output_path": str(listener_out) if listener_out is not None else None,
        "trace": {
            "source": "scripts/run_voice_input_turn.py",
            "realtime_source": "scripts/realtime_turn_cli.py",
            "response_packet_source": "scripts/generate_voice_response.py",
            "case_file": project_relative_string(Path(campaign.get("_case_file", DEFAULT_CASES_PATH))),
        },
    }


def render_listener(packet: dict) -> str:
    transcript = packet["transcription"]["transcript"]
    response = packet["response_packet"]["tts_text"]
    audio_path = packet["audio_input"]["project_relative_path"]
    utterance_language = "de-DE" if packet["transcription"].get("language") == "de" else "en-US"
    transcript_html = html.escape(transcript)
    response_html = html.escape(response)
    audio_path_html = html.escape(audio_path)
    response_json = json.dumps(response)
    utterance_language_json = json.dumps(utterance_language)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>VOICE-002 Audio Input Listener</title>
  <style>
    :root {{
      --ink: #18211f;
      --muted: #5d6965;
      --card: #fffaf2;
      --line: #dbcdb8;
      --accent: #a24f2f;
      --accent-dark: #74341f;
      --wash: #f4eadb;
    }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background:
        radial-gradient(circle at 78% 18%, rgba(162, 79, 47, 0.18), transparent 34%),
        linear-gradient(145deg, #f7efe3 0%, #dfd1bd 100%);
      color: var(--ink);
      font-family: Georgia, "Times New Roman", serif;
    }}
    main {{
      width: min(820px, calc(100vw - 32px));
      padding: 32px;
      border: 1px solid var(--line);
      border-radius: 30px;
      background: rgba(255, 250, 242, 0.94);
      box-shadow: 0 28px 80px rgba(55, 38, 25, 0.16);
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(2rem, 5vw, 4rem);
      line-height: 0.96;
      letter-spacing: -0.04em;
    }}
    p, li {{
      color: var(--muted);
      font-size: 1.03rem;
      line-height: 1.6;
    }}
    section {{
      margin-top: 24px;
      padding: 20px;
      border: 1px solid var(--line);
      border-radius: 20px;
      background: white;
    }}
    h2 {{
      margin: 0 0 10px;
      font-size: 1.05rem;
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }}
    blockquote {{
      margin: 0;
      font-size: 1.22rem;
      line-height: 1.55;
    }}
    button {{
      margin-top: 22px;
      border: 0;
      border-radius: 999px;
      padding: 14px 22px;
      background: var(--accent);
      color: white;
      font: 700 1rem Georgia, "Times New Roman", serif;
      cursor: pointer;
      box-shadow: 0 10px 24px rgba(162, 79, 47, 0.24);
    }}
    button:hover {{
      background: var(--accent-dark);
    }}
  </style>
</head>
<body>
  <main>
    <h1>VOICE-002 Audio Input Listener</h1>
    <p>Recorded-audio input was paired with a human-approved transcript, then routed through the realtime sales-agent core.</p>
    <section>
      <h2>Audio Input</h2>
      <p>{audio_path_html}</p>
    </section>
    <section>
      <h2>Transcript</h2>
      <blockquote>{transcript_html}</blockquote>
    </section>
    <section>
      <h2>Agent Response</h2>
      <blockquote id="ttsText">{response_html}</blockquote>
      <button type="button" id="speakButton">Play agent response</button>
    </section>
  </main>
  <script>
    const text = {response_json};
    document.querySelector("#speakButton").addEventListener("click", () => {{
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = {utterance_language_json};
      utterance.rate = 0.95;
      utterance.pitch = 1;
      window.speechSynthesis.speak(utterance);
    }});
  </script>
</body>
</html>
"""


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a VOICE-002 recorded-audio input turn.")
    parser.add_argument("--campaign", required=True, help="Campaign ID to use.")
    parser.add_argument("--stage", required=True, help="Current call stage.")
    parser.add_argument("--audio", required=True, help="Path to recorded audio.")
    parser.add_argument("--transcript", help="Human-approved transcript text for manual-transcript provider.")
    parser.add_argument("--transcript-file", help="Path to human-approved transcript text file.")
    parser.add_argument("--provider", default="manual-transcript", choices=["manual-transcript"], help="STT provider.")
    parser.add_argument(
        "--input-type",
        default="speech-final",
        choices=["speech-final", "voicemail-detected", "silence-timeout"],
        help="Runtime input type.",
    )
    parser.add_argument("--silence-count", type=int, default=0, help="Silence retry count for silence-timeout input.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES_PATH), help="Campaign wrapper case file to load.")
    parser.add_argument("--consent-confirmed", action="store_true", help="Confirm this audio is permitted for testing.")
    parser.add_argument("--out-json", help="Optional path to write the VOICE-002 packet JSON.")
    parser.add_argument("--listener-out", help="Optional path to write a local browser listener.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.consent_confirmed:
        raise SystemExit("--consent-confirmed is required before recorded-audio experiments can run.")

    audio_path = resolve_project_path(args.audio)
    if audio_path is None:
        raise SystemExit("--audio is required.")
    transcript, transcript_source = load_transcript(args.transcript, args.transcript_file)

    cases_path = resolve_project_path(args.cases)
    if cases_path is None:
        raise SystemExit("--cases is required.")
    campaigns, _cases = load_realtime_cases(cases_path)
    campaign = find_campaign(campaigns, args.campaign)
    campaign["_case_file"] = cases_path

    case = build_turn_case(args.campaign, args.stage, transcript, args.input_type, args.silence_count)
    decision = run_turn_decision(case, campaign)
    response_packet = build_voice_packet(
        campaign=campaign,
        stage=args.stage,
        input_type=args.input_type,
        transcript=transcript,
        silence_count=args.silence_count,
        decision=decision,
        provider="dry-run",
        voice_name=None,
        audio_output_path=None,
    )

    listener_out = resolve_project_path(args.listener_out)
    packet = build_voice_input_packet(
        campaign=campaign,
        stage=args.stage,
        input_type=args.input_type,
        silence_count=args.silence_count,
        audio=audio_metadata(audio_path),
        transcript=transcript,
        transcript_source=transcript_source,
        response_packet=response_packet,
        listener_out=listener_out,
    )

    out_json = resolve_project_path(args.out_json)
    if out_json is not None:
        write_json(out_json, packet)
    if listener_out is not None:
        listener_out.parent.mkdir(parents=True, exist_ok=True)
        listener_out.write_text(render_listener(packet), encoding="utf-8")

    print(json.dumps(packet, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
