#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

import run_elevenlabs_040_tests as runner


class FakeProvider:
    def __init__(
        self,
        *,
        folders: list[dict[str, Any]] | None = None,
        tests: list[dict[str, Any]] | None = None,
        fail_on: tuple[str, str] | None = None,
        failure_message: str = "provider failed with xi-api-key=secret owner@example.com +1 212 555 0188",
    ) -> None:
        self.folders = list(folders or [])
        self.tests = list(tests or [])
        self.fail_on = fail_on
        self.failure_message = failure_message
        self.calls: list[dict[str, Any]] = []
        self.created_counter = 0
        self.invocation_polls = 0

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        body: dict[str, Any] | None = None,
        timeout_seconds: int = 20,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "method": method,
                "endpoint": endpoint,
                "body": body,
                "timeout_seconds": timeout_seconds,
            }
        )
        if self.fail_on == (method, endpoint.split("?", 1)[0]):
            raise RuntimeError(self.failure_message)

        if method == "GET" and endpoint.startswith("/v1/convai/agent-testing?"):
            return {"status_code": 200, "response": {"tests": self._list_entities(endpoint)}}
        if method == "POST" and endpoint == "/v1/convai/agent-testing/folders":
            folder = {
                "id": "tfld_created",
                "name": body["name"],
                "entity_type": "folder",
                "folder_parent_id": body.get("parent_folder_id", "root"),
            }
            self.folders.append(folder)
            return {"status_code": 200, "response": folder}
        if method == "POST" and endpoint == "/v1/convai/agent-testing/create":
            self.created_counter += 1
            test_id = f"test_created_{self.created_counter:02d}"
            test = {
                **body,
                "id": test_id,
                "test_id": test_id,
                "entity_type": "simulation",
                "folder_parent_id": "root",
            }
            self.tests.append(test)
            return {"status_code": 200, "response": {"id": test_id, "name": body["name"]}}
        if method == "POST" and endpoint == "/v1/convai/agent-testing/bulk-move":
            for entity_id in body["entity_ids"]:
                for test in self.tests:
                    if test.get("id") == entity_id or test.get("test_id") == entity_id:
                        test["folder_parent_id"] = body["move_to"]
            return {"status_code": 200, "response": {"moved": len(body["entity_ids"])}}
        if method == "GET" and endpoint.startswith("/v1/convai/agent-testing/"):
            provider_id = endpoint.rsplit("/", 1)[-1]
            for test in self.tests:
                if test.get("id") == provider_id or test.get("test_id") == provider_id:
                    return {"status_code": 200, "response": dict(test)}
            raise RuntimeError(f"test not found: {provider_id}")
        if method == "POST" and endpoint.endswith("/run-tests"):
            return {
                "status_code": 200,
                "response": {
                    "id": "suite_fake_040",
                    "status": "submitted",
                    "test_runs": [
                        {
                            "test_run_id": f"trun_{index:02d}",
                            "test_id": item["test_id"],
                            "test_name": self._name_for_test_id(item["test_id"]),
                            "status": "queued",
                        }
                        for index, item in enumerate(body["tests"], start=1)
                    ],
                },
            }
        if method == "GET" and endpoint.startswith("/v1/convai/test-invocations/"):
            self.invocation_polls += 1
            return {
                "status_code": 200,
                "response": {
                    "id": "suite_fake_040",
                    "agent_id": runner.AGENT_ID,
                    "test_runs": [
                        {
                            "test_run_id": f"trun_{index:02d}",
                            "test_id": item.get("id") or item.get("test_id"),
                            "test_name": item["name"],
                            "status": "passed",
                        }
                        for index, item in enumerate(self.tests, start=1)
                        if item.get("name") in runner.EXPECTED_NAMES
                    ],
                },
            }
        raise RuntimeError(f"unexpected request: {method} {endpoint}")

    def _list_entities(self, endpoint: str) -> list[dict[str, Any]]:
        query = endpoint.split("?", 1)[1]
        params = {}
        for pair in query.split("&"):
            key, _, value = pair.partition("=")
            params[key] = value.replace("+", " ")
        entity_type = params.get("types")
        parent = params.get("parent_folder_id")
        search = params.get("search", "")
        source = self.folders if entity_type == "folder" else self.tests
        items = []
        for item in source:
            if search and search not in str(item.get("name", "")):
                continue
            if parent and item.get("folder_parent_id") != parent:
                continue
            items.append(dict(item))
        return items

    def _name_for_test_id(self, test_id: str) -> str:
        for test in self.tests:
            if test.get("id") == test_id or test.get("test_id") == test_id:
                return str(test["name"])
        return test_id


def expected_provider_tests(folder_id: str = "tfld_existing") -> list[dict[str, Any]]:
    tests = []
    for index, (source_id, body) in enumerate(runner.load_expected_bodies().items(), start=1):
        tests.append(
            {
                **body,
                "id": f"test_existing_{index:02d}",
                "test_id": f"test_existing_{index:02d}",
                "entity_type": "simulation",
                "folder_parent_id": folder_id,
                "source_id": source_id,
            }
        )
    return tests


class RunnerTests(unittest.TestCase):
    def run_with(self, provider: FakeProvider) -> dict[str, Any]:
        with tempfile.TemporaryDirectory() as tmp:
            return runner.execute_with_provider(
                provider,
                output_dir=Path(tmp),
                live=True,
                wait_timeout_seconds=1,
                poll_interval_seconds=0,
            )

    def test_empty_state_creates_exact_folder_tests_moves_and_runs(self) -> None:
        provider = FakeProvider()
        result = self.run_with(provider)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(provider.created_counter, 10)
        move_calls = [call for call in provider.calls if call["endpoint"] == "/v1/convai/agent-testing/bulk-move"]
        self.assertEqual(len(move_calls), 1)
        self.assertEqual(len(move_calls[0]["body"]["entity_ids"]), 10)
        self.assertEqual(result["mapping"]["folder"]["created_in_this_run"], True)

    def test_exact_reuse_creates_nothing_and_runs_existing_ids(self) -> None:
        provider = FakeProvider(
            folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
            tests=expected_provider_tests(),
        )
        result = self.run_with(provider)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(provider.created_counter, 0)
        self.assertFalse(any(call["endpoint"] == "/v1/convai/agent-testing/bulk-move" for call in provider.calls))
        self.assertEqual(result["mapping"]["folder"]["reused_existing"], True)

    def test_partial_state_creates_only_missing_tests_and_moves_only_new_ids(self) -> None:
        partial = expected_provider_tests()[:4]
        provider = FakeProvider(
            folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
            tests=partial,
        )
        result = self.run_with(provider)
        move_call = [call for call in provider.calls if call["endpoint"] == "/v1/convai/agent-testing/bulk-move"][0]
        self.assertEqual(result["status"], "completed")
        self.assertEqual(provider.created_counter, 6)
        self.assertEqual(len(move_call["body"]["entity_ids"]), 6)

    def test_same_name_payload_drift_stops_before_create(self) -> None:
        drifted = expected_provider_tests()
        drifted[0] = {**drifted[0], "success_condition": "weakened"}
        provider = FakeProvider(
            folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
            tests=drifted,
        )
        with self.assertRaises(runner.GuardError):
            self.run_with(provider)
        self.assertEqual(provider.created_counter, 0)

    def test_duplicate_exact_folder_or_test_name_stops(self) -> None:
        duplicate_folders = FakeProvider(
            folders=[
                {"id": "tfld_1", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"},
                {"id": "tfld_2", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"},
            ]
        )
        with self.assertRaises(runner.GuardError):
            self.run_with(duplicate_folders)

        duplicate_tests = expected_provider_tests()
        duplicate_tests.append({**duplicate_tests[0], "id": "test_duplicate", "test_id": "test_duplicate"})
        provider = FakeProvider(
            folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
            tests=duplicate_tests,
        )
        with self.assertRaises(runner.GuardError):
            self.run_with(provider)

    def test_exact_test_outside_missing_folder_stops_before_folder_create(self) -> None:
        provider = FakeProvider(tests=expected_provider_tests(folder_id="root")[:1])
        with self.assertRaises(runner.GuardError):
            self.run_with(provider)
        self.assertFalse(any(call["endpoint"] == "/v1/convai/agent-testing/folders" for call in provider.calls))

    def test_run_payload_order_uses_exact_ten_provider_ids_once(self) -> None:
        tests = expected_provider_tests()
        provider = FakeProvider(
            folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
            tests=tests,
        )
        self.run_with(provider)
        run_call = [call for call in provider.calls if call["endpoint"].endswith("/run-tests")][0]
        self.assertEqual(run_call["body"]["repeat_count"], 1)
        self.assertEqual(
            [item["test_id"] for item in run_call["body"]["tests"]],
            [item["id"] for item in tests],
        )

    def test_api_failure_writes_sanitized_failed_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            provider = FakeProvider(fail_on=("POST", "/v1/convai/agent-testing/create"))
            with self.assertRaises(RuntimeError):
                runner.execute_with_provider(
                    provider,
                    output_dir=output_dir,
                    live=True,
                    wait_timeout_seconds=1,
                    poll_interval_seconds=0,
                )
            result = json.loads((output_dir / "live_test_run_result.json").read_text(encoding="ascii"))
        rendered = json.dumps(result, sort_keys=True)
        self.assertEqual(result["status"], "failed")
        self.assertGreaterEqual(result["api_failure_count"], 1)
        self.assertNotIn("secret", rendered)
        self.assertNotIn("owner@example.com", rendered)
        self.assertNotIn("212 555 0188", rendered)


if __name__ == "__main__":
    unittest.main()
