#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

import run_elevenlabs_040_tests as runner


class FakeProvider:
    def __init__(
        self,
        *,
        folders: list[dict[str, Any]] | None = None,
        tests: list[dict[str, Any]] | None = None,
        fail_on: tuple[str, str] | None = None,
        failure_message: str = "provider failed with contact details owner@example.com +1 212 555 0188",
        page_size: int | None = None,
        cycle_cursor: bool = False,
        readback_mutation: dict[str, Any] | None = None,
        list_items: list[dict[str, Any]] | None = None,
    ) -> None:
        self.folders = list(folders or [])
        self.tests = list(tests or [])
        self.list_items = list(list_items) if list_items is not None else None
        self.fail_on = fail_on
        self.failure_message = failure_message
        self.page_size = page_size
        self.cycle_cursor = cycle_cursor
        self.readback_mutation = readback_mutation
        self.calls: list[dict[str, Any]] = []
        self.created_counter = 0
        self.invocation_polls = 0
        self.last_run_test_ids: list[str] = []

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
            return {"status_code": 200, "response": self._list_entities(endpoint)}
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
        if method == "PUT" and endpoint.startswith("/v1/convai/agent-testing/"):
            provider_id = endpoint.rsplit("/", 1)[-1]
            for index, test in enumerate(self.tests):
                if test.get("id") == provider_id or test.get("test_id") == provider_id:
                    updated = {
                        **body,
                        "id": provider_id,
                        "test_id": provider_id,
                        "entity_type": test.get("entity_type", "simulation"),
                        "folder_parent_id": test.get("folder_parent_id"),
                    }
                    if self.readback_mutation:
                        updated.update(self.readback_mutation)
                    self.tests[index] = updated
                    return {"status_code": 200, "response": {"id": provider_id, "name": body["name"]}}
            raise RuntimeError(f"test not found for PUT: {provider_id}")
        if method == "GET" and endpoint.startswith("/v1/convai/agent-testing/"):
            provider_id = endpoint.rsplit("/", 1)[-1]
            for test in self.tests:
                if test.get("id") == provider_id or test.get("test_id") == provider_id:
                    return {"status_code": 200, "response": dict(test)}
            raise RuntimeError(f"test not found: {provider_id}")
        if method == "POST" and endpoint.endswith("/run-tests"):
            self.last_run_test_ids = [item["test_id"] for item in body["tests"]]
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
                        and (not self.last_run_test_ids or (item.get("id") or item.get("test_id")) in self.last_run_test_ids)
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
        source = self.folders if entity_type == "folder" else (self.list_items if self.list_items is not None else self.tests)
        items = []
        for item in source:
            if search and search not in str(item.get("name", "")):
                continue
            if parent and item.get("folder_parent_id") != parent:
                continue
            items.append(dict(item))
        if not self.page_size:
            return {"tests": items}
        cursor = params.get("cursor")
        start = int(cursor or "0")
        page = items[start : start + self.page_size]
        next_cursor = str(start) if self.cycle_cursor else str(start + self.page_size)
        has_more = start + self.page_size < len(items)
        return {
            "tests": page,
            "has_more": has_more,
            "next_cursor": next_cursor if has_more else None,
        }

    def _name_for_test_id(self, test_id: str) -> str:
        for test in self.tests:
            if test.get("id") == test_id or test.get("test_id") == test_id:
                return str(test["name"])
        return test_id


def expected_provider_tests(
    folder_id: str = "tfld_existing",
    *,
    expected_bodies: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    tests = []
    bodies = expected_bodies or runner.load_expected_bodies()
    for index, source_id in enumerate(runner.EXPECTED_TEST_IDS, start=1):
        body = bodies[source_id]
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


def without_repair_context(test: dict[str, Any]) -> dict[str, Any]:
    copy = json.loads(json.dumps(test))
    for key in runner.REPAIR_CONTEXT_KEYS:
        copy["dynamic_variables"].pop(key, None)
    return copy


def expected_pre_repair_tests(
    folder_id: str = "tfld_existing",
    *,
    expected_bodies: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    return [without_repair_context(test) for test in expected_provider_tests(folder_id=folder_id, expected_bodies=expected_bodies)]


def mapping_for_tests(
    tests: list[dict[str, Any]],
    *,
    folder_id: str = "tfld_existing",
    folder_name: str | None = None,
    created_in_this_run: bool = True,
    expected_bodies: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    by_source = {test["source_id"]: test for test in tests}
    bodies = expected_bodies or runner.load_expected_bodies()
    return {
        "checkpoint_id": runner.CHECKPOINT_ID,
        "folder": {
            "name": folder_name or runner.CHECKPOINT_ID,
            "folder_id": folder_id,
            "created_in_this_run": True,
            "reused_existing": False,
            "parent_folder_id": "root",
        },
        "tests": [
            {
                "source_test_id": source_id,
                "provider_test_name": by_source[source_id]["name"],
                "provider_test_id": by_source[source_id]["id"],
                "created_in_this_run": created_in_this_run,
                "reused_existing": not created_in_this_run,
                "body_canonical_sha256": runner.canonical_sha256(bodies[source_id]),
            }
            for source_id in runner.EXPECTED_TEST_IDS
        ],
    }


def repair_lineage_for_mapping(
    mapping: dict[str, Any],
    *,
    folder_id: str | None = None,
) -> dict[str, Any]:
    resolved_folder_id = folder_id or mapping["folder"]["folder_id"]
    repaired_tests = []
    attempts = []
    for item in mapping["tests"]:
        source_id = item["source_test_id"]
        provider_test_id = item["provider_test_id"]
        provider_test_name = item["provider_test_name"]
        repaired_tests.append(
            {
                "source_test_id": source_id,
                "provider_test_id": provider_test_id,
                "provider_test_name": provider_test_name,
                "provider_status_code": 200,
            }
        )
        attempts.append(
            {
                "request_id": f"repair_test::{source_id}",
                "operation": "repair-owned-context",
                "method": "PUT",
                "endpoint": f"/v1/convai/agent-testing/{provider_test_id}",
                "status": "succeeded",
                "status_code": 200,
            }
        )
    return {
        "checkpoint_id": runner.CHECKPOINT_ID,
        "status": "completed",
        "mode": "repair_owned_context",
        "folder_id": resolved_folder_id,
        "folder_membership_verified_count": len(mapping["tests"]),
        "repaired_test_count": len(mapping["tests"]),
        "repaired_tests": repaired_tests,
        "operation_ledger": {
            "attempt_count": len(attempts),
            "success_count": len(attempts),
            "failure_count": 0,
            "failed_request_id": None,
            "failed_error": None,
            "attempts": attempts,
        },
    }


def write_mapping(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="ascii")


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

    def test_page_two_exact_folder_is_reused_before_create(self) -> None:
        provider = FakeProvider(
            page_size=1,
            folders=[
                {"id": "tfld_other", "name": f"{runner.CHECKPOINT_ID}-other", "entity_type": "folder", "folder_parent_id": "root"},
                {"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"},
            ],
            tests=expected_provider_tests(),
        )
        result = self.run_with(provider)
        self.assertEqual(result["mapping"]["folder"]["folder_id"], "tfld_existing")
        self.assertFalse(any(call["endpoint"] == "/v1/convai/agent-testing/folders" for call in provider.calls))

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

    def test_page_two_test_reuse_and_drift_are_seen_before_create(self) -> None:
        filler = {
            "id": "test_filler",
            "test_id": "test_filler",
            "name": f"{runner.CHECKPOINT_ID}::unrelated",
            "entity_type": "simulation",
            "folder_parent_id": "tfld_existing",
        }
        provider = FakeProvider(
            page_size=1,
            folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
            tests=[filler, *expected_provider_tests()],
        )
        result = self.run_with(provider)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(provider.created_counter, 0)

        drifted = expected_provider_tests()
        drifted[0] = {**drifted[0], "success_condition": "weakened"}
        drift_provider = FakeProvider(
            page_size=1,
            folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
            tests=[filler, *drifted],
        )
        with self.assertRaises(runner.GuardError):
            self.run_with(drift_provider)
        self.assertEqual(drift_provider.created_counter, 0)

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

    def test_page_two_duplicate_folder_and_test_stop_before_mutation(self) -> None:
        duplicate_folders = FakeProvider(
            page_size=1,
            folders=[
                {"id": "tfld_1", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"},
                {"id": "tfld_2", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"},
            ],
        )
        with self.assertRaises(runner.GuardError):
            self.run_with(duplicate_folders)

        duplicate_tests = expected_provider_tests()
        duplicate_tests.append({**duplicate_tests[0], "id": "test_duplicate", "test_id": "test_duplicate"})
        provider = FakeProvider(
            page_size=10,
            folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
            tests=duplicate_tests,
        )
        with self.assertRaises(runner.GuardError):
            self.run_with(provider)
        self.assertEqual(provider.created_counter, 0)

    def test_cursor_cycle_and_page_cap_stop_before_mutation(self) -> None:
        cycle_provider = FakeProvider(
            page_size=1,
            cycle_cursor=True,
            folders=[
                {"id": "tfld_other", "name": f"{runner.CHECKPOINT_ID}-other", "entity_type": "folder", "folder_parent_id": "root"},
                {"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"},
            ],
        )
        with self.assertRaises(runner.GuardError):
            self.run_with(cycle_provider)

        with mock.patch.object(runner, "MAX_LIST_PAGES", 1):
            cap_provider = FakeProvider(
                page_size=1,
                folders=[
                    {"id": "tfld_other", "name": f"{runner.CHECKPOINT_ID}-other", "entity_type": "folder", "folder_parent_id": "root"},
                    {"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"},
                ],
            )
            with self.assertRaises(runner.GuardError):
                self.run_with(cap_provider)

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
        self.assertNotIn("api_failure_count", result)
        self.assertEqual(result["operation_ledger"]["attempt_count"], 2)
        self.assertEqual(result["operation_ledger"]["success_count"], 1)
        self.assertEqual(result["operation_ledger"]["failure_count"], 1)
        self.assertEqual(result["operation_ledger"]["failed_request_id"], "create_test::sim_040_capability_question_no_unprompted_price")
        self.assertNotIn("owner@example.com", rendered)
        self.assertNotIn("212 555 0188", rendered)

    def test_later_mutating_failure_preserves_attempt_success_failure_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            provider = FakeProvider(fail_on=("POST", "/v1/convai/agent-testing/bulk-move"))
            with self.assertRaises(RuntimeError):
                runner.execute_with_provider(
                    provider,
                    output_dir=output_dir,
                    live=True,
                    wait_timeout_seconds=1,
                    poll_interval_seconds=0,
                )
            result = json.loads((output_dir / "live_test_run_result.json").read_text(encoding="ascii"))
        ledger = result["operation_ledger"]
        self.assertEqual(ledger["attempt_count"], 12)
        self.assertEqual(ledger["success_count"], 11)
        self.assertEqual(ledger["failure_count"], 1)
        self.assertEqual(ledger["failed_request_id"], "move_created_tests::tfld_created")

    def test_dry_run_flag_forces_zero_provider_calls_even_with_confirmation(self) -> None:
        with mock.patch.dict("os.environ", {}, clear=True):
            with mock.patch.object(runner, "ElevenLabsProvider") as provider_class:
                with contextlib.redirect_stdout(io.StringIO()):
                    exit_code = runner.main(
                        [
                            "--dry-run",
                            "--confirm-test-creation-and-run",
                            runner.CONFIRMATION,
                        ]
                    )
        self.assertEqual(exit_code, 0)
        provider_class.assert_not_called()

    def test_validate_owned_mapping_accepts_created_mapping_without_lineage(self) -> None:
        mapping = mapping_for_tests(expected_provider_tests(), created_in_this_run=True)
        folder_id, provider_ids = runner.validate_owned_mapping(mapping)
        self.assertEqual(folder_id, "tfld_existing")
        self.assertEqual(
            provider_ids,
            {
                source_id: f"test_existing_{index:02d}"
                for index, source_id in enumerate(runner.EXPECTED_TEST_IDS, start=1)
            },
        )

    def test_validate_owned_mapping_accepts_reused_mapping_with_exact_repair_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            mapping_path = output_dir / "live_test_mapping.json"
            mapping = mapping_for_tests(expected_provider_tests(), created_in_this_run=False)
            write_mapping(mapping_path, mapping)
            (output_dir / "live_test_context_repair_result.json").write_text(
                json.dumps(repair_lineage_for_mapping(mapping), indent=2, ensure_ascii=True) + "\n",
                encoding="ascii",
            )

            folder_id, provider_ids = runner.validate_owned_mapping(mapping, mapping_path=mapping_path)

        self.assertEqual(folder_id, "tfld_existing")
        self.assertEqual(provider_ids["sim_040_basic_site_direct_price"], "test_existing_03")

    def test_validate_owned_mapping_reused_mapping_without_lineage_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            mapping_path = output_dir / "live_test_mapping.json"
            mapping = mapping_for_tests(expected_provider_tests(), created_in_this_run=False)
            write_mapping(mapping_path, mapping)

            with self.assertRaises(runner.GuardError):
                runner.validate_owned_mapping(mapping, mapping_path=mapping_path)

    def test_validate_owned_mapping_rejects_tampered_repair_lineage(self) -> None:
        mapping = mapping_for_tests(expected_provider_tests(), created_in_this_run=False)
        base_lineage = repair_lineage_for_mapping(mapping)
        tamper_cases = {
            "folder_id": lambda payload: payload.__setitem__("folder_id", "tfld_wrong"),
            "provider_id": lambda payload: payload["repaired_tests"][0].__setitem__("provider_test_id", "test_wrong"),
            "provider_name": lambda payload: payload["repaired_tests"][0].__setitem__("provider_test_name", "wrong-name"),
            "order": lambda payload: payload["repaired_tests"].insert(0, payload["repaired_tests"].pop()),
            "status": lambda payload: payload.__setitem__("status", "failed"),
            "mode": lambda payload: payload.__setitem__("mode", "wrong_mode"),
            "repaired_count": lambda payload: payload.__setitem__("repaired_test_count", 9),
            "membership_count": lambda payload: payload.__setitem__("folder_membership_verified_count", 9),
            "ledger_attempt_count": lambda payload: payload["operation_ledger"].__setitem__("attempt_count", 9),
            "ledger_request_id": lambda payload: payload["operation_ledger"]["attempts"][0].__setitem__("request_id", "repair_test::wrong"),
            "ledger_status": lambda payload: payload["operation_ledger"]["attempts"][0].__setitem__("status", "failed"),
        }
        for label, mutate in tamper_cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                output_dir = Path(tmp)
                mapping_path = output_dir / "live_test_mapping.json"
                write_mapping(mapping_path, mapping)
                lineage = json.loads(json.dumps(base_lineage))
                mutate(lineage)
                (output_dir / "live_test_context_repair_result.json").write_text(
                    json.dumps(lineage, indent=2, ensure_ascii=True) + "\n",
                    encoding="ascii",
                )

                with self.assertRaises(runner.GuardError):
                    runner.validate_owned_mapping(mapping, mapping_path=mapping_path)

    def test_full_reuse_write_preserves_durable_ownership_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            mapping_path = output_dir / "live_test_mapping.json"
            seeded_mapping = mapping_for_tests(expected_provider_tests(), created_in_this_run=False)
            write_mapping(mapping_path, seeded_mapping)
            (output_dir / "live_test_context_repair_result.json").write_text(
                json.dumps(repair_lineage_for_mapping(seeded_mapping), indent=2, ensure_ascii=True) + "\n",
                encoding="ascii",
            )
            provider = FakeProvider(
                folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
                tests=expected_provider_tests(),
            )

            first = runner.execute_with_provider(
                provider,
                output_dir=output_dir,
                live=True,
                wait_timeout_seconds=1,
                poll_interval_seconds=0,
            )
            first_mapping = json.loads(mapping_path.read_text(encoding="ascii"))
            second = runner.execute_with_provider(
                provider,
                output_dir=output_dir,
                live=True,
                wait_timeout_seconds=1,
                poll_interval_seconds=0,
            )
            second_mapping = json.loads(mapping_path.read_text(encoding="ascii"))

        self.assertEqual(first["status"], "completed")
        self.assertEqual(second["status"], "completed")
        self.assertIn("ownership", first_mapping)
        self.assertEqual(first_mapping["ownership"], second_mapping["ownership"])
        self.assertTrue(all(item["created_in_this_run"] is False for item in second_mapping["tests"]))

    def test_canary_validation_succeeds_after_reuse_mapping_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            mapping_path = output_dir / "live_test_mapping.json"
            seeded_mapping = mapping_for_tests(expected_provider_tests(), created_in_this_run=False)
            write_mapping(mapping_path, seeded_mapping)
            (output_dir / "live_test_context_repair_result.json").write_text(
                json.dumps(repair_lineage_for_mapping(seeded_mapping), indent=2, ensure_ascii=True) + "\n",
                encoding="ascii",
            )
            provider = FakeProvider(
                folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
                tests=expected_provider_tests(),
            )
            runner.execute_with_provider(
                provider,
                output_dir=output_dir,
                live=True,
                wait_timeout_seconds=1,
                poll_interval_seconds=0,
            )

            result = runner.execute_canary_run(
                provider,
                source_test_id="sim_040_capability_question_no_unprompted_price",
                mapping_path=mapping_path,
                output_dir=output_dir,
                live=True,
                wait_timeout_seconds=1,
                poll_interval_seconds=0,
            )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["selected_test_ids"], ["sim_040_capability_question_no_unprompted_price"])

    def test_repair_owned_context_puts_only_exact_missing_context_and_verifies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            mapping_path = output_dir / "live_test_mapping.json"
            tests = expected_pre_repair_tests()
            write_mapping(mapping_path, mapping_for_tests(tests))
            provider = FakeProvider(
                folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
                tests=tests,
            )
            result = runner.execute_repair_owned_context(
                provider,
                mapping_path=mapping_path,
                output_dir=output_dir,
                live=True,
            )

        self.assertEqual(result["status"], "completed")
        put_calls = [call for call in provider.calls if call["method"] == "PUT"]
        self.assertEqual(len(put_calls), 10)
        self.assertEqual(
            [call["endpoint"] for call in put_calls],
            [f"/v1/convai/agent-testing/test_existing_{index:02d}" for index in range(1, 11)],
        )
        self.assertEqual(put_calls[0]["body"]["dynamic_variables"]["business_name"], "Acme Dental")
        self.assertEqual(result["operation_ledger"]["attempt_count"], 10)
        self.assertEqual(result["operation_ledger"]["failure_count"], 0)

    def test_repair_refuses_any_extra_payload_drift_before_put(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            mapping_path = output_dir / "live_test_mapping.json"
            tests = expected_pre_repair_tests()
            tests[0]["success_condition"] = "weakened"
            write_mapping(mapping_path, mapping_for_tests(tests))
            provider = FakeProvider(
                folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
                tests=tests,
            )
            with self.assertRaises(runner.GuardError):
                runner.execute_repair_owned_context(provider, mapping_path=mapping_path, output_dir=output_dir, live=True)

        self.assertFalse(any(call["method"] == "PUT" for call in provider.calls))

    def test_repair_refuses_wrong_mapping_folder_or_not_owned_tests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            tests = expected_pre_repair_tests()
            wrong_folder = output_dir / "wrong_folder_mapping.json"
            write_mapping(wrong_folder, mapping_for_tests(tests, folder_name="not-the-040-folder"))
            provider = FakeProvider(
                folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
                tests=tests,
            )
            with self.assertRaises(runner.GuardError):
                runner.execute_repair_owned_context(provider, mapping_path=wrong_folder, output_dir=output_dir, live=True)

            reused_mapping = output_dir / "reused_mapping.json"
            write_mapping(reused_mapping, mapping_for_tests(tests, created_in_this_run=False))
            with self.assertRaises(runner.GuardError):
                runner.execute_repair_owned_context(provider, mapping_path=reused_mapping, output_dir=output_dir, live=True)

        self.assertFalse(any(call["method"] == "PUT" for call in provider.calls))

    def test_repair_refuses_missing_folder_membership_before_put(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            mapping_path = output_dir / "live_test_mapping.json"
            tests = expected_pre_repair_tests()
            for test in tests:
                test.pop("folder_parent_id", None)
            write_mapping(mapping_path, mapping_for_tests(tests))
            provider = FakeProvider(
                folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
                tests=tests,
            )
            with self.assertRaises(runner.GuardError):
                runner.execute_repair_owned_context(provider, mapping_path=mapping_path, output_dir=output_dir, live=True)

        self.assertFalse(any(call["method"] == "PUT" for call in provider.calls))

    def test_repair_refuses_list_get_folder_conflict_before_put(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            mapping_path = output_dir / "live_test_mapping.json"
            tests = expected_pre_repair_tests()
            list_items = [dict(test) for test in tests]
            tests[0]["folder_parent_id"] = "tfld_wrong"
            write_mapping(mapping_path, mapping_for_tests(list_items))
            provider = FakeProvider(
                folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
                tests=tests,
                list_items=list_items,
            )
            with self.assertRaises(runner.GuardError):
                runner.execute_repair_owned_context(provider, mapping_path=mapping_path, output_dir=output_dir, live=True)

        self.assertFalse(any(call["method"] == "PUT" for call in provider.calls))

    def test_repair_refuses_wrong_folder_membership_before_put(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            mapping_path = output_dir / "live_test_mapping.json"
            tests = expected_pre_repair_tests()
            list_items = [dict(test) for test in tests]
            list_items[0]["folder_parent_id"] = "tfld_wrong"
            write_mapping(mapping_path, mapping_for_tests(tests))
            provider = FakeProvider(
                folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
                tests=tests,
                list_items=list_items,
            )
            with self.assertRaises(runner.GuardError):
                runner.execute_repair_owned_context(provider, mapping_path=mapping_path, output_dir=output_dir, live=True)

        self.assertFalse(any(call["method"] == "PUT" for call in provider.calls))

    def test_repair_accepts_exact_folder_membership(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            mapping_path = output_dir / "live_test_mapping.json"
            tests = expected_pre_repair_tests()
            write_mapping(mapping_path, mapping_for_tests(tests))
            provider = FakeProvider(
                folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
                tests=tests,
            )
            result = runner.execute_repair_owned_context(provider, mapping_path=mapping_path, output_dir=output_dir, live=True)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(len([call for call in provider.calls if call["method"] == "PUT"]), 10)

    def test_repair_treats_omitted_expected_and_empty_current_history_as_equivalent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            mapping_path = output_dir / "live_test_mapping.json"
            tests = expected_pre_repair_tests()
            for test in tests:
                test["chat_history"] = []
            write_mapping(mapping_path, mapping_for_tests(tests))
            provider = FakeProvider(
                folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
                tests=tests,
            )
            result = runner.execute_repair_owned_context(provider, mapping_path=mapping_path, output_dir=output_dir, live=True)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(len([call for call in provider.calls if call["method"] == "PUT"]), 10)

    def test_repair_treats_empty_expected_and_omitted_current_history_as_equivalent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            mapping_path = output_dir / "live_test_mapping.json"
            expected_bodies = runner.load_expected_bodies()
            for body in expected_bodies.values():
                body["chat_history"] = []
            tests = expected_pre_repair_tests(expected_bodies=expected_bodies)
            for test in tests:
                test.pop("chat_history", None)
            write_mapping(mapping_path, mapping_for_tests(tests, expected_bodies=expected_bodies))
            provider = FakeProvider(
                folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
                tests=tests,
            )
            with mock.patch.object(runner, "load_expected_bodies", return_value=expected_bodies):
                result = runner.execute_repair_owned_context(provider, mapping_path=mapping_path, output_dir=output_dir, live=True)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(len([call for call in provider.calls if call["method"] == "PUT"]), 10)

    def test_repair_refuses_non_empty_current_history_when_expected_absent_before_put(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            mapping_path = output_dir / "live_test_mapping.json"
            tests = expected_pre_repair_tests()
            tests[0]["chat_history"] = [{"role": "user", "message": "history should remain strict"}]
            write_mapping(mapping_path, mapping_for_tests(tests))
            provider = FakeProvider(
                folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
                tests=tests,
            )
            with self.assertRaises(runner.GuardError):
                runner.execute_repair_owned_context(provider, mapping_path=mapping_path, output_dir=output_dir, live=True)

        self.assertFalse(any(call["method"] == "PUT" for call in provider.calls))

    def test_repair_refuses_non_empty_expected_history_when_current_is_empty_before_put(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            mapping_path = output_dir / "live_test_mapping.json"
            expected_bodies = runner.load_expected_bodies()
            expected_bodies[runner.EXPECTED_TEST_IDS[0]]["chat_history"] = [{"role": "assistant", "message": "expected history"}]
            tests = expected_pre_repair_tests(expected_bodies=expected_bodies)
            tests[0]["chat_history"] = []
            write_mapping(mapping_path, mapping_for_tests(tests, expected_bodies=expected_bodies))
            provider = FakeProvider(
                folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
                tests=tests,
            )
            with mock.patch.object(runner, "load_expected_bodies", return_value=expected_bodies):
                with self.assertRaises(runner.GuardError):
                    runner.execute_repair_owned_context(provider, mapping_path=mapping_path, output_dir=output_dir, live=True)

        self.assertFalse(any(call["method"] == "PUT" for call in provider.calls))

    def test_repair_refuses_wrong_type_current_history_before_put(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            mapping_path = output_dir / "live_test_mapping.json"
            tests = expected_pre_repair_tests()
            tests[0]["chat_history"] = {"role": "user", "message": "wrong type"}
            write_mapping(mapping_path, mapping_for_tests(tests))
            provider = FakeProvider(
                folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
                tests=tests,
            )
            with self.assertRaises(runner.GuardError):
                runner.execute_repair_owned_context(provider, mapping_path=mapping_path, output_dir=output_dir, live=True)

        self.assertFalse(any(call["method"] == "PUT" for call in provider.calls))

    def test_repair_finds_page_two_folder_membership_before_put(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            mapping_path = output_dir / "live_test_mapping.json"
            tests = expected_pre_repair_tests()
            filler = {
                "id": "test_filler",
                "test_id": "test_filler",
                "name": f"{runner.CHECKPOINT_ID}::unrelated",
                "entity_type": "simulation",
                "folder_parent_id": "tfld_existing",
            }
            write_mapping(mapping_path, mapping_for_tests(tests))
            provider = FakeProvider(
                page_size=1,
                folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
                tests=tests,
                list_items=[filler, *tests],
            )
            result = runner.execute_repair_owned_context(provider, mapping_path=mapping_path, output_dir=output_dir, live=True)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(len([call for call in provider.calls if call["method"] == "PUT"]), 10)

    def test_repair_partial_put_failure_records_accurate_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            mapping_path = output_dir / "live_test_mapping.json"
            tests = expected_pre_repair_tests()
            write_mapping(mapping_path, mapping_for_tests(tests))
            provider = FakeProvider(
                folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
                tests=tests,
                fail_on=("PUT", "/v1/convai/agent-testing/test_existing_03"),
            )
            with self.assertRaises(RuntimeError):
                runner.execute_repair_owned_context(provider, mapping_path=mapping_path, output_dir=output_dir, live=True)
            result = json.loads((output_dir / "live_test_context_repair_result.json").read_text(encoding="ascii"))

        ledger = result["operation_ledger"]
        self.assertEqual(ledger["attempt_count"], 3)
        self.assertEqual(ledger["success_count"], 2)
        self.assertEqual(ledger["failure_count"], 1)
        self.assertEqual(ledger["failed_request_id"], "repair_test::sim_040_basic_site_direct_price")

    def test_repair_readback_mismatch_fails_closed_after_put(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            mapping_path = output_dir / "live_test_mapping.json"
            tests = expected_pre_repair_tests()
            write_mapping(mapping_path, mapping_for_tests(tests))
            provider = FakeProvider(
                folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
                tests=tests,
                readback_mutation={"success_condition": "provider changed it"},
            )
            with self.assertRaises(runner.GuardError):
                runner.execute_repair_owned_context(provider, mapping_path=mapping_path, output_dir=output_dir, live=True)
            result = json.loads((output_dir / "live_test_context_repair_result.json").read_text(encoding="ascii"))

        self.assertEqual(result["status"], "failed")
        self.assertIn("readback", result["error"])
        self.assertEqual(result["operation_ledger"]["attempt_count"], 1)
        self.assertEqual(result["operation_ledger"]["failure_count"], 0)

    def test_canary_runs_one_mapped_provider_id_without_overwriting_suite_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            mapping_path = output_dir / "live_test_mapping.json"
            tests = expected_provider_tests()
            write_mapping(mapping_path, mapping_for_tests(tests))
            (output_dir / "live_test_run_result.json").write_text('{"status":"suite_evidence"}\n', encoding="ascii")
            provider = FakeProvider(
                folders=[{"id": "tfld_existing", "name": runner.CHECKPOINT_ID, "entity_type": "folder", "folder_parent_id": "root"}],
                tests=tests,
            )
            result = runner.execute_canary_run(
                provider,
                source_test_id="sim_040_basic_site_direct_price",
                mapping_path=mapping_path,
                output_dir=output_dir,
                live=True,
                wait_timeout_seconds=1,
                poll_interval_seconds=0,
            )
            suite_result = json.loads((output_dir / "live_test_run_result.json").read_text(encoding="ascii"))
            canary_result = json.loads((output_dir / "live_test_canary_result.json").read_text(encoding="ascii"))

        run_call = [call for call in provider.calls if call["endpoint"].endswith("/run-tests")][0]
        self.assertEqual(run_call["body"], {"tests": [{"test_id": "test_existing_03"}], "repeat_count": 1})
        self.assertEqual(result["status"], "completed")
        self.assertEqual(canary_result["selected_test_ids"], ["sim_040_basic_site_direct_price"])
        self.assertEqual(suite_result["status"], "suite_evidence")

    def test_mode_token_conflicts_fail_closed_and_dry_run_makes_no_provider(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                runner.parse_args(
                    [
                        "--repair-owned-context",
                        "--canary-test-id",
                        "sim_040_basic_site_direct_price",
                    ]
                )
        with mock.patch.dict("os.environ", {runner.API_KEY_ENV_VAR: "secret"}, clear=True):
            with mock.patch.object(runner, "ElevenLabsProvider") as provider_class:
                with contextlib.redirect_stdout(io.StringIO()):
                    exit_code = runner.main(
                        [
                            "--dry-run",
                            "--repair-owned-context",
                            "--confirm-owned-context-repair",
                            runner.REPAIR_CONFIRMATION,
                        ]
                    )
        self.assertEqual(exit_code, 0)
        provider_class.assert_not_called()

    def test_040_criteria_and_order_are_immutable_except_shared_context_variables(self) -> None:
        payload = json.loads(runner.TESTS_PATH.read_text(encoding="utf-8"))
        self.assertEqual([item["test_id"] for item in payload["tests"]], runner.EXPECTED_TEST_IDS)
        self.assertEqual(
            [
                (item["simulation_scenario"], item["success_condition"], item["simulated_user_model"], item["evaluation_model"], item["simulation_max_turns"])
                for item in payload["tests"]
            ],
            [
                ("Buyer asks whether Atlas can add booking, CRM, and payments but never asks cost.", "Pass: confident capability answer, no dollar amount, range, package, starting price, or care-plan price.", "gemini-2.5-flash", "gemini-2.5-flash", 8),
                ("Buyer asks whether the mockup is really free and whether there is a catch.", "Pass: process-risk answer only; no paid website price.", "gemini-2.5-flash", "gemini-2.5-flash", 8),
                ("Buyer explicitly asks what a basic three-to-five-page local-business site costs.", "Pass: one `$900-$1,500` whole-project range and one relevant driver at most.", "gemini-2.5-flash", "gemini-2.5-flash", 6),
                ("Buyer states they have an existing compatible site and asks the cost of adding a simple appointment-request form.", "Pass: one `$100-$250` add-on range; no whole-site package dump.", "gemini-2.5-flash", "gemini-2.5-flash", 6),
                ("Buyer asks what a new straightforward site with a simple request form costs, then asks about live calendar integration.", "Pass: `$900-$1,500` for simple request; later one higher relevant band for live integration; no add-on/whole-site confusion.", "gemini-2.5-flash", "gemini-2.5-flash", 10),
                ("Buyer asks for a new site with booking, CRM, payments, service-area pages, and a blog, then asks total cost.", "Pass: one likely whole-project band and scope driver; no arithmetic sum or feature-menu recital.", "gemini-2.5-flash", "gemini-2.5-flash", 8),
                ("Buyer has an existing compatible site and asks what a direct CRM integration costs.", "Pass: `$1,000-$2,500+`, an API/data-flow caveat, and no claim that every behavior is included.", "gemini-2.5-flash", "gemini-2.5-flash", 8),
                ("Buyer asks how much a parent portal with accounts and progress dashboards costs.", "Pass: no numeric quote or ceiling; scope accounts, data, permissions, security, and integrations.", "gemini-2.5-flash", "gemini-2.5-flash", 8),
                ("Buyer says the budget is `$1,200` and asks whether a basic site fits.", "Pass: direct fit answer against `$900-$1,500`; no unrelated package menu.", "gemini-2.5-flash", "gemini-2.5-flash", 6),
                ("Buyer first asks about ordinary site capability, then explicitly asks monthly hosting and maintenance cost.", "Pass: no care price before the ongoing-cost question; after it, one relevant `$79`, `$149`, or `$249` plan with scope.", "gemini-2.5-flash", "gemini-2.5-flash", 10),
            ],
        )
        self.assertEqual(
            {key: payload["dynamic_variables"].get(key) for key in runner.REPAIR_CONTEXT_KEYS},
            {"business_name": "Acme Dental", "business_type": "dental clinic", "city": "Phoenix"},
        )


if __name__ == "__main__":
    unittest.main()
