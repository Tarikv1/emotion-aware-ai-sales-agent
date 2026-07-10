#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import io
import json
import sys
import urllib.error
from pathlib import Path
from types import ModuleType
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def fail(message: str) -> None:
    raise AssertionError(message)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert_condition(spec is not None and spec.loader is not None, f"Could not load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


APPLY_038 = load_module(
    "apply_elevenlabs_038_end_call_terminal_control",
    ROOT / "scripts" / "apply_elevenlabs_038_end_call_terminal_control.py",
)
RUN_036 = load_module(
    "run_elevenlabs_036_tests",
    ROOT / "scripts" / "run_elevenlabs_036_tests.py",
)


def schema_without_description(tool: dict[str, object]) -> dict[str, object]:
    value = json.loads(json.dumps(tool))
    value.pop("description", None)
    return value


def canonical_kb(count: int = 17) -> list[dict[str, str]]:
    return [
        {
            "type": "file",
            "name": f"doc_{index:02d}.md",
            "id": f"kb_{index:02d}",
        }
        for index in range(count)
    ]


def fake_agent_for_patch() -> dict[str, object]:
    kb = canonical_kb()
    return {
        "agent_id": "agent_7801kt0g32zxf4f8x5zkykj7syty",
        "name": "web design",
        "conversation_config": {
            "agent": {
                "prompt": {
                    "prompt": "Atlas Web Studio\nMission: earn permission",
                    "knowledge_base": kb,
                    "tools": [
                        {"name": "calendar", "type": "webhook"},
                        {
                            "name": "end_call",
                            "type": "system",
                            "params": {"system_tool_type": "end_call"},
                        },
                        {"name": "end_call", "type": "webhook", "url": "https://example.invalid"},
                    ],
                    "built_in_tools": {
                        "end_call": {
                            "type": "system",
                            "name": "end_call",
                            "description": "old description",
                            "response_timeout_secs": 47,
                            "disable_interruptions": True,
                            "force_pre_tool_speech": True,
                            "pre_tool_speech": "manual",
                            "assignments": [{"channel": "ops"}],
                            "tool_call_sound": "beep",
                            "tool_call_sound_behavior": "always",
                            "tool_error_handling_mode": "strict",
                            "params": {
                                "system_tool_type": "end_call",
                                "custom_flag": "keep-me",
                            },
                            "extra_nested": {"keep": ["this", "shape"]},
                        },
                        "transfer": {"type": "system", "name": "transfer"},
                    },
                    "tool_ids": ["tool_live_1"],
                    "mcp_server_ids": ["mcp_live_1"],
                    "native_mcp_server_ids": ["native_live_1"],
                    "llm": {"model": "gpt"},
                }
            },
            "tts": {"voice_id": "voice_live_1"},
        },
        "platform_settings": {"evaluation": {"criteria": [{"id": "criterion_1"}]}},
        "workflow": {"steps": ["one"]},
        "tags": ["atlas"],
        "phone_numbers": [{"label": "sales", "phone_number": "+1 555 010 9999"}],
        "whatsapp_accounts": [],
        "procedures": [],
    }


def test_preserve_live_end_call_schema() -> None:
    agent = fake_agent_for_patch()
    before_tool = json.loads(json.dumps(agent["conversation_config"]["agent"]["prompt"]["built_in_tools"]["end_call"]))
    patch = APPLY_038.build_agent_patch(
        agent,
        canonical_kb(),
        "Atlas Web Studio\nMission: earn permission\npatched",
    )
    patched_prompt = patch["conversation_config"]["agent"]["prompt"]
    after_tool = patched_prompt["built_in_tools"]["end_call"]

    assert_condition(
        schema_without_description(after_tool) == schema_without_description(before_tool),
        "build_agent_patch must preserve the entire live built-in end_call schema outside description",
    )
    assert_condition(
        after_tool["description"] == APPLY_038.END_CALL_DESCRIPTION,
        "build_agent_patch must update only the description",
    )
    assert_condition(
        [item["name"] for item in patched_prompt["tools"]] == ["calendar"],
        "legacy end_call entries must be removed while unrelated tools remain",
    )


def test_verification_rejects_name_only_kb_match() -> None:
    canonical = canonical_kb()
    mismatched = canonical_kb()
    mismatched[5] = dict(mismatched[5], id="kb_wrong_05")
    agent = fake_agent_for_patch()
    prompt = agent["conversation_config"]["agent"]["prompt"]
    prompt["prompt"] = "prompt exact"
    prompt["knowledge_base"] = mismatched
    prompt["tools"] = [{"name": "calendar", "type": "webhook"}]
    prompt["built_in_tools"]["end_call"]["description"] = APPLY_038.END_CALL_DESCRIPTION

    payload = APPLY_038.verification(agent, "prompt exact", canonical)
    try:
        APPLY_038.assert_verification(payload)
    except ValueError:
        return
    fail("assert_verification must fail when KB names match but canonical IDs/order do not")


def test_message_and_error_sanitization() -> None:
    sanitized = APPLY_038.sanitize(
        {
            "message": "Contact jane@example.com or +1 (555) 222-3333 with token=abc123 and api_key=topsecret",
        }
    )
    serialized = json.dumps(sanitized, ensure_ascii=False).lower()
    for leaked in ("jane@example.com", "555", "abc123", "topsecret"):
        assert_condition(leaked not in serialized, f"sanitize leaked sensitive value: {leaked}")

    body = b'{"message":"call jane@example.com or +1 (555) 222-3333","token":"abc123","api_key":"topsecret"}'

    def raise_http_error(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise urllib.error.HTTPError(
            url="https://api.elevenlabs.io/v1/test",
            code=400,
            msg="Bad Request",
            hdrs=None,
            fp=io.BytesIO(body),
        )

    with patch.object(APPLY_038.urllib.request, "urlopen", side_effect=raise_http_error):
        try:
            APPLY_038.json_request("GET", "/v1/test", api_key="fake")
        except RuntimeError as exc:
            text = str(exc).lower()
            for leaked in ("jane@example.com", "555", "abc123", "topsecret"):
                assert_condition(leaked not in text, f"json_request leaked sensitive value: {leaked}")
        else:
            fail("json_request should raise on HTTP errors")


def test_runner_repeat_failures_write_evidence_and_exit_nonzero() -> None:
    writes: dict[str, dict[str, object]] = {}
    ordered_ids = list(RUN_036.PROVIDER_TEST_IDS)
    bodies = {source_id: {"name": source_id} for source_id in ordered_ids}
    monotonic_values = iter([0.0, 0.1, 0.2, 0.3, 0.4])

    def fake_write_json(name: str, payload: dict[str, object]) -> None:
        writes[name] = json.loads(json.dumps(payload))

    def fake_json_request(method: str, endpoint: str, *, api_key: str, body=None, timeout_seconds=30):  # type: ignore[no-untyped-def]
        if method == "GET" and endpoint.endswith("/agents/agent_7801kt0g32zxf4f8x5zkykj7syty"):
            return {"status_code": 200, "response": {"agent_id": RUN_036.AGENT_ID, "name": "web design"}}
        if method == "POST" and endpoint.endswith("/run-tests"):
            return {"status_code": 200, "response": {"id": "inv_123"}}
        if method == "GET" and endpoint.endswith("/test-invocations/inv_123"):
            return {
                "status_code": 200,
                "response": {
                    "test_runs": [
                        {"test_id": "test_one", "test_name": "crm repeat 1", "status": "passed"},
                        {"test_id": "test_one", "test_name": "crm repeat 2", "status": "failed"},
                    ]
                },
            }
        raise AssertionError(f"unexpected request: {method} {endpoint}")

    argv = [
        "run_elevenlabs_036_tests.py",
        "--scope",
        "crm",
        "--label",
        "repeat-failure",
        "--confirm-simulations",
        RUN_036.CONFIRMATION,
        "--repeat-count",
        "2",
        "--wait-timeout-seconds",
        "1",
    ]
    with patch.object(RUN_036, "expected_bodies", return_value=(ordered_ids, bodies)), patch.object(
        RUN_036, "get_live_test", side_effect=lambda api_key, source_id: {"name": source_id}
    ), patch.object(RUN_036.guards, "test_semantics", side_effect=lambda value: value), patch.object(
        RUN_036.guards, "json_request", side_effect=fake_json_request
    ), patch.object(RUN_036.agent_guard, "preflight", return_value={"status": "ok"}), patch.object(
        RUN_036, "write_json", side_effect=fake_write_json
    ), patch.object(
        RUN_036.time, "sleep", return_value=None
    ), patch.object(
        RUN_036.time, "monotonic", side_effect=lambda: next(monotonic_values)
    ), patch.object(
        sys, "argv", argv
    ), patch.dict(
        RUN_036.os.environ, {RUN_036.API_KEY_ENV_VAR: "fake-key"}, clear=False
    ):
        exit_code = RUN_036.main()

    assert_condition(exit_code == 1, "runner must exit nonzero when any repeated terminal run fails")
    request = writes.get("repeat-failure_run_request.json") or {}
    result = writes.get("repeat-failure_run_result.json") or {}
    assert_condition(request.get("request", {}).get("body", {}).get("repeat_count") == 2, "repeat_count must be forwarded to run-tests")
    assert_condition(result.get("status") == "failed", "runner must still write failed evidence")
    statuses = result.get("final_run_statuses") or []
    assert_condition(len(statuses) == 2, "runner evidence must record one terminal status per repeated run")


def test_runner_supports_new_single_test_scopes() -> None:
    ordered_ids = list(RUN_036.PROVIDER_TEST_IDS)
    scope_map = {
        "email-plus": ["sim_036_email_plus_free_question_confirmation"],
        "visual": ["sim_036_free_mockup_visual_not_working_site"],
        "goodbye": ["sim_036_goodbye_take_care_no_loop"],
    }
    for scope, expected in scope_map.items():
        selected = RUN_036.selected_ids_for_scope(scope, ordered_ids)
        assert_condition(selected == expected, f"{scope} did not resolve to the expected test id")


def test_runner_fails_closed_on_unknown_terminal_status() -> None:
    assert_condition(
        not RUN_036.is_successful_terminal_status("provider_new_terminal_state"),
        "unknown provider terminal statuses must not be treated as successful",
    )


def main() -> None:
    test_preserve_live_end_call_schema()
    test_verification_rejects_name_only_kb_match()
    test_message_and_error_sanitization()
    test_runner_repeat_failures_write_evidence_and_exit_nonzero()
    test_runner_supports_new_single_test_scopes()
    test_runner_fails_closed_on_unknown_terminal_status()
    print("Patch utility safety fix validation passed.")


if __name__ == "__main__":
    main()
