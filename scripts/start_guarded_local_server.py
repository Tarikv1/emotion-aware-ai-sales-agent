#!/usr/bin/env python3
import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def resolve_project_path(path_text: str | None) -> Path | None:
    if path_text is None:
        return None
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def can_connect(host: str, port: int, timeout_seconds: float = 0.25) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True
    except OSError:
        return False


def wait_for_port(host: str, port: int, startup_timeout_seconds: float) -> bool:
    deadline = time.perf_counter() + startup_timeout_seconds
    while time.perf_counter() < deadline:
        if can_connect(host, port):
            return True
        time.sleep(0.1)
    return can_connect(host, port)


def stop_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    if os.name != "nt":
        try:
            os.killpg(process.pid, signal.SIGTERM)
            return
        except OSError:
            process.terminate()
            return
    process.kill()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/PID", str(process.pid), "/F", "/T"], text=True, capture_output=True)


def build_payload(
    *,
    name: str,
    status: str,
    host: str,
    port: int,
    startup_timeout_seconds: float,
    pid: int | None,
    stdout_log: Path,
    stderr_log: Path,
    pid_out: Path,
    command: list[str],
    started_at: float,
    cleanup_attempted: bool = False,
    message: str | None = None,
) -> dict:
    payload = {
        "name": name,
        "status": status,
        "host": host,
        "port": port,
        "url": f"http://{host}:{port}/",
        "startup_timeout_seconds": startup_timeout_seconds,
        "pid": pid,
        "pid_out": str(pid_out),
        "stdout_log": str(stdout_log),
        "stderr_log": str(stderr_log),
        "command": command,
        "shell_used": False,
        "cleanup_attempted": cleanup_attempted,
        "elapsed_ms": int((time.perf_counter() - started_at) * 1000),
    }
    if message is not None:
        payload["message"] = message
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start a local server with bounded startup health-checks, PID tracking, and cleanup on failure."
    )
    parser.add_argument("--name", required=True, help="Human-readable server name for logs and JSON output.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to check for the local server.")
    parser.add_argument("--port", required=True, type=int, help="Port to check for the local server.")
    parser.add_argument("--startup-timeout", type=float, default=8.0, help="Seconds to wait for the port to listen.")
    parser.add_argument("--pid-out", required=True, help="Path to write the child process PID.")
    parser.add_argument("--stdout-log", required=True, help="Path to write child process stdout.")
    parser.add_argument("--stderr-log", required=True, help="Path to write child process stderr.")
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to start after `--`. Example: -- python scripts/run_browser_speech_demo.py",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    started_at = time.perf_counter()
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise SystemExit("A server command is required after `--`.")
    if args.startup_timeout <= 0:
        raise SystemExit("--startup-timeout must be greater than zero.")

    pid_out = resolve_project_path(args.pid_out)
    stdout_log = resolve_project_path(args.stdout_log)
    stderr_log = resolve_project_path(args.stderr_log)
    stdout_log.parent.mkdir(parents=True, exist_ok=True)
    stderr_log.parent.mkdir(parents=True, exist_ok=True)
    pid_out.parent.mkdir(parents=True, exist_ok=True)

    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    start_new_session = os.name != "nt"

    with stdout_log.open("w", encoding="utf-8") as stdout_handle, stderr_log.open("w", encoding="utf-8") as stderr_handle:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            stdout=stdout_handle,
            stderr=stderr_handle,
            stdin=subprocess.DEVNULL,
            text=True,
            shell=False,
            creationflags=creationflags,
            start_new_session=start_new_session,
        )

    write_text(pid_out, f"{process.pid}\n")
    if wait_for_port(args.host, args.port, args.startup_timeout):
        payload = build_payload(
            name=args.name,
            status="started",
            host=args.host,
            port=args.port,
            startup_timeout_seconds=args.startup_timeout,
            pid=process.pid,
            stdout_log=stdout_log,
            stderr_log=stderr_log,
            pid_out=pid_out,
            command=command,
            started_at=started_at,
        )
        print(json.dumps(payload, indent=2))
        return

    cleanup_attempted = process.poll() is None
    stop_process(process)
    payload = build_payload(
        name=args.name,
        status="startup-timeout",
        host=args.host,
        port=args.port,
        startup_timeout_seconds=args.startup_timeout,
        pid=process.pid,
        stdout_log=stdout_log,
        stderr_log=stderr_log,
        pid_out=pid_out,
        command=command,
        started_at=started_at,
        cleanup_attempted=cleanup_attempted,
        message="The child process did not open the expected TCP port before the startup timeout.",
    )
    print(json.dumps(payload, indent=2))
    raise SystemExit(1)


if __name__ == "__main__":
    main()
