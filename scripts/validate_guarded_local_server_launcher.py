#!/usr/bin/env python3
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "start_guarded_local_server.py"
RUN_ID = f"{int(time.time() * 1000)}-{os.getpid()}"
TEST_DIR = ROOT / ".tmp" / "local-server-guarded" / RUN_ID
PID_OUT = TEST_DIR / f"LOCAL-SERVER-GUARDED-test-{RUN_ID}.pid"
STDOUT_LOG = TEST_DIR / f"LOCAL-SERVER-GUARDED-test-{RUN_ID}.stdout.log"
STDERR_LOG = TEST_DIR / f"LOCAL-SERVER-GUARDED-test-{RUN_ID}.stderr.log"
FAIL_PID_OUT = TEST_DIR / f"LOCAL-SERVER-GUARDED-failure-test-{RUN_ID}.pid"
FAIL_STDOUT_LOG = TEST_DIR / f"LOCAL-SERVER-GUARDED-failure-test-{RUN_ID}.stdout.log"
FAIL_STDERR_LOG = TEST_DIR / f"LOCAL-SERVER-GUARDED-failure-test-{RUN_ID}.stderr.log"


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def remove_if_exists(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except PermissionError:
        pass


def stop_process_tree(pid: int) -> None:
    try:
        os.kill(pid, signal_for_termination())
    except ProcessLookupError:
        pass
    except OSError:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"], text=True, capture_output=True)


def process_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def signal_for_termination() -> int:
    return 15 if os.name != "nt" else 9


def cleanup_artifacts(paths: list[Path]) -> None:
    for _attempt in range(10):
        remaining = []
        for path in paths:
            try:
                path.unlink()
            except FileNotFoundError:
                continue
            except PermissionError:
                remaining.append(path)
        if not remaining:
            return
        time.sleep(0.2)


def load_json_stdout(completed: subprocess.CompletedProcess) -> dict:
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Expected JSON stdout, got: {completed.stdout!r}") from exc


def main() -> None:
    assert_condition(LAUNCHER.exists(), "Guarded local server launcher is missing.")
    TEST_DIR.mkdir(parents=True, exist_ok=True)

    for path in [PID_OUT, STDOUT_LOG, STDERR_LOG, FAIL_PID_OUT, FAIL_STDOUT_LOG, FAIL_STDERR_LOG]:
        remove_if_exists(path)

    port = find_free_port()
    completed = subprocess.run(
        [
            sys.executable,
            str(LAUNCHER),
            "--name",
            "LOCAL-SERVER-GUARDED-TEST",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--startup-timeout",
            "5",
            "--pid-out",
            str(PID_OUT),
            "--stdout-log",
            str(STDOUT_LOG),
            "--stderr-log",
            str(STDERR_LOG),
            "--",
            sys.executable,
            "-m",
            "http.server",
            str(port),
            "--bind",
            "127.0.0.1",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    payload = load_json_stdout(completed)
    pid = int(PID_OUT.read_text(encoding="utf-8").strip())

    try:
        assert_condition(payload["status"] == "started", "Launcher should report started status.")
        assert_condition(payload["shell_used"] is False, "Launcher must not use shell=True.")
        assert_condition(payload["port"] == port, "Launcher should report the checked port.")
        assert_condition(payload["startup_timeout_seconds"] == 5.0, "Launcher should report startup timeout.")
        assert_condition(payload["pid"] == pid, "Launcher JSON should match pid file.")
        assert_condition(PID_OUT.exists(), "PID file should exist after successful startup.")
        assert_condition(STDOUT_LOG.exists(), "stdout log should exist after successful startup.")
        assert_condition(STDERR_LOG.exists(), "stderr log should exist after successful startup.")
        assert_condition(process_exists(pid), "Server process should remain running after launcher exits.")
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2) as response:
            assert_condition(response.status == 200, "Started HTTP server should respond successfully.")
    finally:
        stop_process_tree(pid)
        time.sleep(0.5)

    fail_port = find_free_port()
    start = time.perf_counter()
    failure = subprocess.run(
        [
            sys.executable,
            str(LAUNCHER),
            "--name",
            "LOCAL-SERVER-GUARDED-FAILURE-TEST",
            "--host",
            "127.0.0.1",
            "--port",
            str(fail_port),
            "--startup-timeout",
            "2",
            "--pid-out",
            str(FAIL_PID_OUT),
            "--stdout-log",
            str(FAIL_STDOUT_LOG),
            "--stderr-log",
            str(FAIL_STDERR_LOG),
            "--",
            sys.executable,
            "-c",
            "import time; time.sleep(30)",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    elapsed = time.perf_counter() - start
    assert_condition(failure.returncode != 0, "Launcher should fail when health check never opens.")
    assert_condition(elapsed < 8, "Launcher failure path should respect the bounded startup timeout.")
    failure_payload = load_json_stdout(failure)
    fail_pid = int(failure_payload["pid"])
    assert_condition(failure_payload["status"] == "startup-timeout", "Failure should report startup-timeout.")
    assert_condition(failure_payload["cleanup_attempted"] is True, "Failure should attempt child cleanup.")
    assert_condition(not process_exists(fail_pid), "Timed-out child process should be stopped.")

    cleanup_artifacts([PID_OUT, STDOUT_LOG, STDERR_LOG, FAIL_PID_OUT, FAIL_STDOUT_LOG, FAIL_STDERR_LOG])

    print("Guarded local server launcher validation passed.")


if __name__ == "__main__":
    main()
