#!/usr/bin/env python3
import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = ROOT / "runtime" / "config" / "local" / "ultravox.env"


def resolve_project_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and value and os.environ.get(key) is None:
            os.environ[key] = value


def api_request(url: str, api_key: str, method: str = "GET") -> tuple[int, str]:
    request = urllib.request.Request(
        url,
        method=method,
        headers={"X-API-Key": api_key},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.status, response.read().decode("utf-8", errors="replace")


def read_error(error: urllib.error.HTTPError) -> str:
    try:
        return " ".join(error.read(500).decode("utf-8", errors="replace").split())
    except Exception:
        return ""


def find_recent_call(api_key: str, suffix: str, page_size: int) -> str | None:
    query = urllib.parse.urlencode({"pageSize": page_size})
    _status, body = api_request(f"https://api.ultravox.ai/api/calls?{query}", api_key)
    payload = json.loads(body)
    for item in payload.get("results") or []:
        call_id = item.get("callId") or item.get("call_id") or item.get("id")
        if call_id and call_id.endswith(suffix):
            return call_id
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Delete a recent UltraVox call by redacted suffix.")
    parser.add_argument("--suffix", required=True, help="Last characters of the call ID from a redacted result.")
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE), help="Ignored env file with ULTRAVOX_API_KEY.")
    parser.add_argument("--page-size", type=int, default=20, help="Recent call page size.")
    parser.add_argument("--retries", type=int, default=5, help="Delete retries for unbilled/ongoing calls.")
    parser.add_argument("--sleep-seconds", type=float, default=3.0, help="Delay between 425 retries.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_env_file(resolve_project_path(args.env_file))
    api_key = os.environ.get("ULTRAVOX_API_KEY")
    if not api_key:
        raise SystemExit("missing ULTRAVOX_API_KEY")

    call_id = find_recent_call(api_key, args.suffix, args.page_size)
    print(f"matched_recent_call: {str(bool(call_id)).lower()}")
    if not call_id:
        return

    url = f"https://api.ultravox.ai/api/calls/{call_id}"
    for attempt in range(1, args.retries + 1):
        try:
            status, _body = api_request(url, api_key, method="DELETE")
            print(f"delete_attempt: {attempt} status: {status} deleted: {str(200 <= status < 300).lower()}")
            return
        except urllib.error.HTTPError as error:
            print(f"delete_attempt: {attempt} status: {error.code} deleted: false message: {read_error(error)}")
            if error.code != 425:
                return
            time.sleep(args.sleep_seconds)


if __name__ == "__main__":
    main()
