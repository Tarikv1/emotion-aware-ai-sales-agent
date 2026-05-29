#!/usr/bin/env python3
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from runtime.audio_backends.ultravox_sales_brain_mock import (
    handle_project_sales_brain_next_move,
    validate_ultravox_tool_response,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_local_tool_endpoint_config.json"
CONTRACT_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_sales_brain_tool_contract.json"


class LocalToolHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(self, server_address: tuple[str, int], request_handler: type[BaseHTTPRequestHandler], *, config: dict[str, Any], auth_token: str):
        super().__init__(server_address, request_handler)
        self.config = config
        self.auth_token = auth_token
        self.sanitized_events: list[dict[str, Any]] = []


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def validate_request_schema(request: dict[str, Any]) -> list[str]:
    contract = load_contract()
    errors: list[str] = []
    for field_name, spec in contract["request_fields"].items():
        if spec.get("required") is True and field_name not in request:
            errors.append(f"missing required request field: {field_name}")
    if not isinstance(request.get("turn_index"), int):
        errors.append("turn_index must be an integer")
    for field_name in (
        "session_id",
        "buyer_utterance_text",
        "ultravox_session_summary",
        "project_memory_summary",
        "current_campaign_id",
        "detected_emotion_hint",
        "requested_action_context",
    ):
        if not isinstance(request.get(field_name), str) or not request.get(field_name, "").strip():
            errors.append(f"{field_name} must be non-empty text")
    return errors


def validate_response_schema(response: dict[str, Any]) -> list[str]:
    errors = validate_ultravox_tool_response(response)
    if response.get("side_effects_allowed") is not False:
        errors.append("side_effects_allowed must be false")
    return errors


def handle_request(request: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    request_errors = validate_request_schema(request)
    if request_errors:
        return 400, {
            "allowed_to_speak": False,
            "buyer_facing_response": "I need to clarify that before answering.",
            "next_action_id": "bad_request",
            "project_memory_updates": [],
            "prosody_hints": {"tone": "calm", "pace": "steady", "emphasis": []},
            "must_not_say": [],
            "source_boundary": {"grounded_in_campaign_truth": False, "unsupported_claims_allowed": False, "raw_urls_allowed": False},
            "side_effects_allowed": False,
            "call_should_end": False,
            "verifier_status": "blocked",
            "safety_warnings": request_errors,
        }

    response = handle_project_sales_brain_next_move(request)
    response_errors = validate_response_schema(response)
    if response_errors:
        response["allowed_to_speak"] = False
        response["buyer_facing_response"] = "I need to clarify that before answering."
        response["verifier_status"] = "blocked"
        response["safety_warnings"] = response_errors
    return 200, response


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class ProjectSalesBrainToolHandler(BaseHTTPRequestHandler):
    server: LocalToolHTTPServer

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_POST(self) -> None:
        config = self.server.config
        if self.path != config["path"]:
            _json_response(self, 404, {"error": "not_found"})
            return

        expected_token = self.server.auth_token
        received_token = self.headers.get(config["auth_header_name"], "")
        if config.get("auth_required") is True and received_token != expected_token:
            self.server.sanitized_events.append({"event": "auth_rejected", "path": self.path})
            _json_response(self, 401, {"error": "unauthorized"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            _json_response(self, 400, {"error": "bad_content_length"})
            return
        if length <= 0 or length > 32768:
            _json_response(self, 400, {"error": "bad_request_size"})
            return

        try:
            request = json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            _json_response(self, 400, {"error": "invalid_json"})
            return
        if not isinstance(request, dict):
            _json_response(self, 400, {"error": "json_object_required"})
            return

        status, response = handle_request(request)
        self.server.sanitized_events.append(
            {
                "event": "tool_request",
                "status": status,
                "turn_index": request.get("turn_index"),
                "request_field_count": len(request),
                "side_effects_allowed": response.get("side_effects_allowed"),
                "verifier_status": response.get("verifier_status"),
            }
        )
        _json_response(self, status, response)


def build_server(*, host: str | None = None, port: int | None = None, auth_token: str) -> LocalToolHTTPServer:
    config = load_config()
    server_host = host or config["host"]
    server_port = int(port if port is not None else config["port"])
    if server_host != "127.0.0.1":
        raise ValueError("local prototype server must bind only to 127.0.0.1")
    if not auth_token:
        raise ValueError("auth_token is required")
    return LocalToolHTTPServer((server_host, server_port), ProjectSalesBrainToolHandler, config=config, auth_token=auth_token)


def run_local_server_once_for_tests(*, auth_token: str) -> LocalToolHTTPServer:
    return build_server(auth_token=auth_token)
