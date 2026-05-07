#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import mimetypes
import re
import shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from private_speech_learning_queue import process_capture_record


ROOT = Path(__file__).resolve().parents[1]
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-030b-local-speech-capture.json"
PRIVATE_DATA_ROOT = ROOT / "data" / "private"
DEFAULT_PRIVATE_ROOT = PRIVATE_DATA_ROOT / "tarik-speech-samples"
DEFAULT_RAW_AUDIO_DIR = DEFAULT_PRIVATE_ROOT / "raw-audio"
DEFAULT_MANIFEST_PATH = DEFAULT_PRIVATE_ROOT / "derived" / "local-speech-capture-manifest.jsonl"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8791
MAX_UPLOAD_BYTES = 80 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".wav", ".webm", ".mp3", ".m4a", ".aac", ".ogg", ".opus", ".flac", ".wma", ".caf", ".amr"}
CONTENT_TYPE_EXTENSIONS = {
    "audio/wav": ".wav",
    "audio/wave": ".wav",
    "audio/x-wav": ".wav",
    "audio/webm": ".webm",
    "video/webm": ".webm",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/aac": ".aac",
    "audio/ogg": ".ogg",
    "audio/opus": ".opus",
    "audio/flac": ".flac",
}


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC).replace(microsecond=0)


def project_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def resolve_project_path(value: str | None, default: Path) -> Path:
    if not value:
        return default
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def is_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def sanitize_sample_id(value: str | None, *, language: str = "unknown") -> str:
    if value:
        base = value.strip().lower()
    else:
        timestamp = utc_now().strftime("%Y%m%d-%H%M%S")
        base = f"tarik-{language}-{timestamp}"
    base = re.sub(r"[^a-z0-9._-]+", "-", base)
    base = base.strip(".-_")
    return base[:80] or "speech-sample"


def normalize_language(value: str | None) -> str:
    language = (value or "unknown").strip().lower()
    if language in {"en", "english"}:
        return "en"
    if language in {"de", "german", "deutsch"}:
        return "de"
    return "unknown"


def guess_extension_from_content_type(content_type: str | None) -> str:
    if not content_type:
        return ".webm"
    media_type = content_type.split(";", 1)[0].strip().lower()
    return CONTENT_TYPE_EXTENSIONS.get(media_type) or mimetypes.guess_extension(media_type) or ".webm"


def ensure_private_paths(private_root: Path) -> tuple[Path, Path]:
    if not is_under(private_root, PRIVATE_DATA_ROOT):
        raise SystemExit("VOICE-030B private root must stay under data/private.")
    raw_audio_dir = private_root / "raw-audio"
    manifest_path = private_root / "derived" / "local-speech-capture-manifest.jsonl"
    raw_audio_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    return raw_audio_dir, manifest_path


def allocate_target_path(raw_audio_dir: Path, sample_id: str, extension: str) -> Path:
    extension = extension.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise SystemExit(f"Unsupported audio extension for capture/import: {extension}")
    base = sanitize_sample_id(sample_id)
    candidate = raw_audio_dir / f"{base}{extension}"
    if not candidate.exists():
        return candidate
    for index in range(2, 1000):
        candidate = raw_audio_dir / f"{base}-{index}{extension}"
        if not candidate.exists():
            return candidate
    raise SystemExit(f"Could not allocate a unique filename for sample ID: {base}")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_record(
    *,
    mode: str,
    sample_id: str,
    language: str,
    label: str,
    source_kind: str,
    target_path: Path,
    byte_count: int,
    content_sha256: str,
    content_type: str | None = None,
) -> dict[str, Any]:
    return {
        "voice_milestone": "VOICE-030B",
        "captured_at_utc": utc_now().isoformat().replace("+00:00", "Z"),
        "mode": mode,
        "sample_id": sample_id,
        "language": language,
        "label": label,
        "source_kind": source_kind,
        "stored_relative_path": project_relative(target_path),
        "file_extension": target_path.suffix.lower(),
        "byte_count": byte_count,
        "content_sha256": content_sha256,
        "content_type": content_type,
        "privacy_boundary": {
            "stored_under_data_private": is_under(target_path, PRIVATE_DATA_ROOT),
            "provider_calls_made": False,
            "transcription_created": False,
            "voice_cloning_used": False,
            "runtime_profile_applied": False,
            "public_artifact_created": False,
            "human_review_required_before_runtime_use": True,
        },
    }


def append_manifest(manifest_path: Path, record: dict[str, Any]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def payload_for_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "voice_milestone": "VOICE-030B",
        "mode": record["mode"],
        "sample": {
            "sample_id": record["sample_id"],
            "language": record["language"],
            "label": record["label"],
            "stored_relative_path": record["stored_relative_path"],
            "file_extension": record["file_extension"],
            "byte_count": record["byte_count"],
        },
        "privacy_boundary": record["privacy_boundary"],
    }


def payload_for_processed_record(record: dict[str, Any], *, private_root: Path) -> dict[str, Any]:
    payload = payload_for_record(record)
    payload["learning_queue"] = process_capture_record(record, private_root=private_root)
    return payload


def import_file(source_path: Path, *, sample_id: str, language: str, label: str, private_root: Path) -> dict[str, Any]:
    if not source_path.is_file():
        raise SystemExit(f"Import file does not exist: {source_path}")
    extension = source_path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise SystemExit(f"Unsupported import extension: {extension}")
    raw_audio_dir, manifest_path = ensure_private_paths(private_root)
    target_path = allocate_target_path(raw_audio_dir, sample_id, extension)
    shutil.copyfile(source_path, target_path)
    data = target_path.read_bytes()
    record = build_record(
        mode="import_file",
        sample_id=sample_id,
        language=language,
        label=label,
        source_kind="import_file",
        target_path=target_path,
        byte_count=len(data),
        content_sha256=sha256_bytes(data),
        content_type=mimetypes.guess_type(target_path.name)[0],
    )
    append_manifest(manifest_path, record)
    return payload_for_processed_record(record, private_root=private_root)


def store_upload(
    data: bytes,
    *,
    content_type: str | None,
    sample_id: str | None,
    language: str,
    label: str,
    private_root: Path,
) -> dict[str, Any]:
    if not data:
        raise ValueError("Upload body is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("Upload body exceeds the VOICE-030B local limit.")
    raw_audio_dir, manifest_path = ensure_private_paths(private_root)
    extension = guess_extension_from_content_type(content_type)
    sample_id = sanitize_sample_id(sample_id, language=language)
    target_path = allocate_target_path(raw_audio_dir, sample_id, extension)
    target_path.write_bytes(data)
    record = build_record(
        mode="localhost_browser_recorder",
        sample_id=sample_id,
        language=language,
        label=label,
        source_kind="localhost_browser_recorder",
        target_path=target_path,
        byte_count=len(data),
        content_sha256=sha256_bytes(data),
        content_type=content_type,
    )
    append_manifest(manifest_path, record)
    return payload_for_processed_record(record, private_root=private_root)


def render_recorder_html(port: int) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>VOICE-030B Local Speech Capture</title>
  <style>
    body {{
      font-family: Georgia, 'Times New Roman', serif;
      max-width: 760px;
      margin: 40px auto;
      padding: 0 20px;
      line-height: 1.5;
      color: #172019;
      background: #f6f2ea;
    }}
    .panel {{
      background: #fffaf0;
      border: 1px solid #d8cdb9;
      border-radius: 18px;
      padding: 22px;
      box-shadow: 0 14px 35px rgba(38, 31, 20, 0.08);
    }}
    button, select, input {{
      font: inherit;
      margin: 6px 8px 6px 0;
      padding: 10px 12px;
      border-radius: 10px;
      border: 1px solid #b8aa92;
    }}
    button {{
      cursor: pointer;
      background: #16251c;
      color: #fffaf0;
    }}
    button:disabled {{
      opacity: 0.45;
      cursor: not-allowed;
    }}
    code {{
      background: #eee3d1;
      padding: 2px 5px;
      border-radius: 5px;
    }}
    #status {{
      white-space: pre-wrap;
      background: #efe7d9;
      padding: 12px;
      border-radius: 10px;
    }}
  </style>
</head>
<body>
  <main class="panel">
    <h1>VOICE-030B Local Speech Capture</h1>
    <p>This page records only through <code>127.0.0.1:{port}</code>. Uploads are saved under <code>data/private/tarik-speech-samples/raw-audio</code>.</p>
    <p>No provider call, transcription, voice cloning, or runtime personalization happens here.</p>

    <label>Language:
      <select id="language">
        <option value="en">English</option>
        <option value="de">German</option>
        <option value="unknown">Unknown/mixed</option>
      </select>
    </label>
    <label>Label:
      <input id="label" value="tarik local speech sample" size="28">
    </label>
    <div>
      <button id="start">Start recording</button>
      <button id="stop" disabled>Stop and save</button>
    </div>
    <p id="status">Idle.</p>
  </main>
  <script>
    const startButton = document.getElementById('start');
    const stopButton = document.getElementById('stop');
    const statusBox = document.getElementById('status');
    let audioContext;
    let sourceNode;
    let processorNode;
    let activeStream;
    let recordedBuffers = [];
    let recordedFrameCount = 0;

    function setStatus(message) {{
      statusBox.textContent = message;
    }}

    function mergeBuffers(buffers, frameCount) {{
      const merged = new Float32Array(frameCount);
      let offset = 0;
      for (const buffer of buffers) {{
        merged.set(buffer, offset);
        offset += buffer.length;
      }}
      return merged;
    }}

    function writeAscii(view, offset, text) {{
      for (let index = 0; index < text.length; index += 1) {{
        view.setUint8(offset + index, text.charCodeAt(index));
      }}
    }}

    function encodeWav(samples, sampleRate) {{
      const bytesPerSample = 2;
      const buffer = new ArrayBuffer(44 + samples.length * bytesPerSample);
      const view = new DataView(buffer);
      writeAscii(view, 0, 'RIFF');
      view.setUint32(4, 36 + samples.length * bytesPerSample, true);
      writeAscii(view, 8, 'WAVE');
      writeAscii(view, 12, 'fmt ');
      view.setUint32(16, 16, true);
      view.setUint16(20, 1, true);
      view.setUint16(22, 1, true);
      view.setUint32(24, sampleRate, true);
      view.setUint32(28, sampleRate * bytesPerSample, true);
      view.setUint16(32, bytesPerSample, true);
      view.setUint16(34, 8 * bytesPerSample, true);
      writeAscii(view, 36, 'data');
      view.setUint32(40, samples.length * bytesPerSample, true);
      let offset = 44;
      for (const sample of samples) {{
        const clamped = Math.max(-1, Math.min(1, sample));
        view.setInt16(offset, clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff, true);
        offset += bytesPerSample;
      }}
      return new Blob([view], {{ type: 'audio/wav' }});
    }}

    async function uploadWav(blob) {{
      const language = encodeURIComponent(document.getElementById('language').value);
      const label = encodeURIComponent(document.getElementById('label').value);
      const response = await fetch(`/upload?language=${{language}}&label=${{label}}`, {{
        method: 'POST',
        headers: {{ 'Content-Type': 'audio/wav' }},
        body: blob
      }});
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || 'Upload failed');
      setStatus(`Saved WAV locally.\\n${{JSON.stringify(payload, null, 2)}}`);
    }}

    startButton.addEventListener('click', async () => {{
      recordedBuffers = [];
      recordedFrameCount = 0;
      activeStream = await navigator.mediaDevices.getUserMedia({{ audio: {{ channelCount: 1 }} }});
      audioContext = new AudioContext();
      sourceNode = audioContext.createMediaStreamSource(activeStream);
      processorNode = audioContext.createScriptProcessor(4096, 1, 1);
      processorNode.onaudioprocess = event => {{
        const input = event.inputBuffer.getChannelData(0);
        recordedBuffers.push(new Float32Array(input));
        recordedFrameCount += input.length;
      }};
      sourceNode.connect(processorNode);
      processorNode.connect(audioContext.destination);
      startButton.disabled = true;
      stopButton.disabled = false;
      setStatus('Recording local WAV audio. Speak naturally, then stop when done.');
    }});

    stopButton.addEventListener('click', async () => {{
      stopButton.disabled = true;
      startButton.disabled = false;
      setStatus('Encoding WAV locally and saving private audio...');
      try {{
        processorNode.disconnect();
        sourceNode.disconnect();
        activeStream.getTracks().forEach(track => track.stop());
        const samples = mergeBuffers(recordedBuffers, recordedFrameCount);
        const wavBlob = encodeWav(samples, audioContext.sampleRate);
        await audioContext.close();
        await uploadWav(wavBlob);
      }} catch (error) {{
        setStatus(`Could not save WAV: ${{error.message}}`);
      }}
    }});
  </script>
</body>
</html>
"""


class SpeechCaptureServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], private_root: Path):
        super().__init__(server_address, SpeechCaptureHandler)
        self.private_root = private_root


class SpeechCaptureHandler(BaseHTTPRequestHandler):
    server: SpeechCaptureServer

    def log_message(self, format: str, *args: object) -> None:
        return

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path not in {"/", "/index.html"}:
            self.send_json(404, {"error": "not_found"})
            return
        html_body = render_recorder_html(self.server.server_port).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html_body)))
        self.end_headers()
        self.wfile.write(html_body)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/upload":
            self.send_json(404, {"error": "not_found"})
            return
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0 or content_length > MAX_UPLOAD_BYTES:
            self.send_json(400, {"error": "invalid_upload_size"})
            return
        query = parse_qs(parsed.query)
        language = normalize_language(query.get("language", ["unknown"])[0])
        label = query.get("label", [""])[0][:120]
        sample_id = query.get("sample_id", [None])[0]
        data = self.rfile.read(content_length)
        try:
            payload = store_upload(
                data,
                content_type=self.headers.get("Content-Type"),
                sample_id=sample_id,
                language=language,
                label=label,
                private_root=self.server.private_root,
            )
        except ValueError as exc:
            self.send_json(400, {"error": str(exc)})
            return
        self.send_json(200, payload)


def serve(private_root: Path, *, port: int) -> None:
    ensure_private_paths(private_root)
    server = SpeechCaptureServer((DEFAULT_HOST, port), private_root)
    print("VOICE-030B local speech capture server")
    print(f"Open: http://{DEFAULT_HOST}:{port}/")
    print(f"Saving raw audio to: {project_relative(private_root / 'raw-audio')}")
    print("Provider calls: false")
    print("Transcription: false")
    print("Stop with Ctrl+C.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped VOICE-030B local speech capture server.")
    finally:
        server.server_close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture or import Tarik speech samples into data/private.")
    parser.add_argument("--case", default=str(CASE_PATH), help="VOICE-030B case/config JSON.")
    parser.add_argument("--private-root", default=str(DEFAULT_PRIVATE_ROOT), help="Private speech-sample workspace root.")
    parser.add_argument("--import-file", help="Copy an existing local audio file into the private raw-audio folder.")
    parser.add_argument("--serve", action="store_true", help="Run a localhost browser recorder.")
    parser.add_argument("--dry-run", action="store_true", help="Show server/import configuration without storing audio.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Localhost recorder port.")
    parser.add_argument("--sample-id", help="Optional safe sample ID. Defaults to timestamp when recording.")
    parser.add_argument("--language", default="unknown", help="Sample language: en, de, or unknown.")
    parser.add_argument("--label", default="", help="Private label for the sample manifest.")
    parser.add_argument("--print-json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    case_path = resolve_project_path(args.case, CASE_PATH)
    if not case_path.is_file():
        raise SystemExit(f"VOICE-030B case file is missing: {case_path}")
    private_root = resolve_project_path(args.private_root, DEFAULT_PRIVATE_ROOT)
    language = normalize_language(args.language)
    sample_id = sanitize_sample_id(args.sample_id, language=language)
    label = args.label.strip()[:120]

    if args.import_file and args.serve:
        raise SystemExit("Choose either --import-file or --serve, not both.")
    if not args.import_file and not args.serve:
        raise SystemExit("Choose --import-file <path> or --serve.")

    if args.dry_run:
        payload = {
            "voice_milestone": "VOICE-030B",
            "mode": "serve_dry_run" if args.serve else "import_dry_run",
            "server": {
                "host": DEFAULT_HOST,
                "port": args.port,
                "provider_calls_made": False,
            },
            "sample": {
                "sample_id": sample_id,
                "language": language,
                "label": label,
                "raw_audio_dir": project_relative(private_root / "raw-audio"),
            },
            "privacy_boundary": {
                "stores_uploads_under_data_private": is_under(private_root / "raw-audio", PRIVATE_DATA_ROOT),
                "provider_calls_made": False,
                "transcription_created": False,
                "voice_cloning_used": False,
                "runtime_profile_applied": False,
                "public_artifact_created": False,
            },
        }
        if args.print_json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(f"VOICE-030B dry run: {payload['mode']}")
            print(f"Local URL: http://{DEFAULT_HOST}:{args.port}/")
            print(f"Raw audio dir: {payload['sample']['raw_audio_dir']}")
        return

    if args.import_file:
        payload = import_file(
            resolve_project_path(args.import_file, Path("")),
            sample_id=sample_id,
            language=language,
            label=label,
            private_root=private_root,
        )
        if args.print_json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            sample = payload["sample"]
            print(f"Imported VOICE-030B sample: {sample['stored_relative_path']}")
        return

    serve(private_root, port=args.port)


if __name__ == "__main__":
    main()
