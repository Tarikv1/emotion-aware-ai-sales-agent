#!/usr/bin/env python3
"""Run existing ELEVENLABS-036 simulations with live-state guards."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import apply_elevenlabs_036_natural_sales_prompt_hardening as agent_guard
import apply_elevenlabs_039_independent_test_hardening as guards
from runtime.providers.elevenlabs_agents.automation import test_create_request


CHECKPOINT_ID = "ELEVENLABS-036-natural-sales-scenarios"
AGENT_ID = "agent_7801kt0g32zxf4f8x5zkykj7syty"
CONFIRMATION = "confirm-simulations"
API_KEY_ENV_VAR = "ELEVENLABS_API_KEY"
TESTS_PATH = ROOT / "runtime/providers/elevenlabs_agents/tests/web_design_natural_sales_scenarios_tests.json"
OUT_DIR = ROOT / "research/experiments/generated/ELEVENLABS-036-natural-sales-scenarios"
PROVIDER_TEST_IDS = {
    "sim_036_email_confirmation_spoken_email_two_step": "test_4201ktwzq7wpf589w4ypqbwwv6xk",
    "sim_036_email_plus_free_question_confirmation": "test_1301ktwzq879ex099m903r4f0gvt",
    "sim_036_future_price_ballpark_no_overpricing": "test_7101ktwzq8e5edm9bkmwe83tvcsw",
    "sim_036_scheduling_simple_request_vs_live_integration": "test_4601ktwzq8nyfcatm8a6mn58y7x6",
    "sim_036_crm_payment_capability_before_price": "test_4601ktwzq8xnfpbtry5qsepeprh3",
    "sim_036_custom_dashboard_scoped_separately": "test_9401ktwzq968e3bvmytqxg4exxc0",
    "sim_036_free_mockup_visual_not_working_site": "test_3301ktwzq9cnfzsa5dfjd9q61gq5",
    "sim_036_next_step_questions_no_cta_fatigue": "test_2001ktwzq9kbf92vdfttrgkvnr1x",
    "sim_036_guarantee_required_clean_disqualify": "test_7401ktwzq9txfkhs6ytstggj8k9y",
    "sim_036_goodbye_take_care_no_loop": "test_1901ktwzqa28f0mbk4rrt106d74d",
}
TARGETED_IDS = (
    "sim_036_future_price_ballpark_no_overpricing",
    "sim_036_guarantee_required_clean_disqualify",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def write_json(name: str, payload: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / name).write_text(
        json.dumps(guards.sanitize(payload), indent=2, ensure_ascii=True) + "\n",
        encoding="ascii",
    )


def expected_bodies() -> tuple[list[str], dict[str, dict[str, Any]]]:
    document = json.loads(TESTS_PATH.read_text(encoding="utf-8"))
    if document.get("package_id") != CHECKPOINT_ID:
        raise ValueError("repo test package ID mismatch")
    suite_variables = document.get("dynamic_variables", {})
    bodies: dict[str, dict[str, Any]] = {}
    ordered_ids: list[str] = []
    for item in document.get("tests", []):
        if not isinstance(item, dict):
            raise ValueError("repo test entry is not an object")
        source_id = str(item.get("test_id", ""))
        if source_id not in PROVIDER_TEST_IDS:
            raise ValueError(f"unexpected repo test ID {source_id!r}")
        ordered_ids.append(source_id)
        bodies[source_id] = test_create_request(
            item,
            package_id=CHECKPOINT_ID,
            suite_dynamic_variables=suite_variables,
        )["body"]
    if ordered_ids != list(PROVIDER_TEST_IDS):
        raise ValueError("repo test order or IDs differ from the fixed live map")
    return ordered_ids, bodies


def get_live_test(api_key: str, source_id: str) -> dict[str, Any]:
    provider_id = PROVIDER_TEST_IDS[source_id]
    result = guards.json_request(
        "GET",
        f"/v1/convai/agent-testing/{quote(provider_id, safe='')}",
        api_key=api_key,
    )
    response = result.get("response")
    if not isinstance(response, dict):
        raise ValueError(f"invalid live test response for {source_id}")
    expected_name = f"{CHECKPOINT_ID}::{source_id}"
    if response.get("id") != provider_id or response.get("name") != expected_name:
        raise ValueError(f"live test identity mismatch for {source_id}")
    return response


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Guard and run existing ELEVENLABS-036 tests.")
    parser.add_argument("--scope", choices=("guarantee", "scheduling", "crm", "cta", "crm-dashboard", "targeted", "full"), required=True)
    parser.add_argument("--label", required=True, help="Evidence filename prefix")
    parser.add_argument("--confirm-simulations", choices=(CONFIRMATION,), default=None)
    parser.add_argument("--wait-timeout-seconds", type=int, default=420)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_key = os.environ.get(API_KEY_ENV_VAR, "").strip()
    if not api_key:
        print(f"error: {API_KEY_ENV_VAR} is required", file=sys.stderr)
        return 2
    label = str(args.label).strip()
    if not label or not all(char.isalnum() or char in "_-" for char in label):
        print("error: --label must use only letters, digits, underscore, or hyphen", file=sys.stderr)
        return 2

    try:
        ordered_ids, bodies = expected_bodies()
        if args.scope == "guarantee":
            selected_ids = ["sim_036_guarantee_required_clean_disqualify"]
        elif args.scope == "scheduling":
            selected_ids = ["sim_036_scheduling_simple_request_vs_live_integration"]
        elif args.scope == "crm":
            selected_ids = ["sim_036_crm_payment_capability_before_price"]
        elif args.scope == "cta":
            selected_ids = ["sim_036_next_step_questions_no_cta_fatigue"]
        elif args.scope == "crm-dashboard":
            selected_ids = [
                "sim_036_crm_payment_capability_before_price",
                "sim_036_custom_dashboard_scoped_separately",
            ]
        elif args.scope == "targeted":
            selected_ids = list(TARGETED_IDS)
        else:
            selected_ids = ordered_ids
        live_tests = {source_id: get_live_test(api_key, source_id) for source_id in selected_ids}
        for source_id in selected_ids:
            if guards.test_semantics(live_tests[source_id]) != guards.test_semantics(bodies[source_id]):
                raise ValueError(f"live test semantics do not match repo for {source_id}")

        agent_result = guards.json_request(
            "GET", f"/v1/convai/agents/{quote(AGENT_ID, safe='')}", api_key=api_key
        )
        agent = agent_result.get("response")
        if not isinstance(agent, dict):
            raise ValueError("live agent response is invalid")
        agent_summary = agent_guard.preflight(agent)
        run_body = {
            "tests": [{"test_id": PROVIDER_TEST_IDS[source_id]} for source_id in selected_ids],
            "repeat_count": 1,
        }
        request_evidence = {
            "checkpoint_id": CHECKPOINT_ID,
            "captured_at_utc": utc_now(),
            "scope": args.scope,
            "agent": agent_summary,
            "test_ids": {source_id: PROVIDER_TEST_IDS[source_id] for source_id in selected_ids},
            "live_test_semantics_match_repo": True,
            "request": {
                "method": "POST",
                "endpoint": f"/v1/convai/agents/{AGENT_ID}/run-tests",
                "body": run_body,
            },
            "outbound_calls_made": False,
        }
        write_json(f"{label}_run_plan.json", request_evidence)
        if args.confirm_simulations is None:
            result = {
                "status": "dry_run",
                "post_performed": False,
                "scope": args.scope,
                "test_count": len(selected_ids),
                "outbound_calls_made": False,
            }
            print(json.dumps(result, indent=2))
            return 0

        write_json(f"{label}_run_request.json", request_evidence)
        run_result = guards.json_request(
            "POST",
            f"/v1/convai/agents/{quote(AGENT_ID, safe='')}/run-tests",
            api_key=api_key,
            body=run_body,
            timeout_seconds=60,
        )
        run_response = run_result.get("response")
        if not isinstance(run_response, dict):
            raise ValueError("run-tests response is invalid")
        invocation_id = run_response.get("id") or run_response.get("test_invocation_id")
        if not isinstance(invocation_id, str) or not invocation_id:
            raise ValueError("run-tests response did not include an invocation ID")

        deadline = time.monotonic() + max(1, args.wait_timeout_seconds)
        completed: dict[str, Any] | None = None
        while time.monotonic() < deadline:
            invocation_result = guards.json_request(
                "GET",
                f"/v1/convai/test-invocations/{quote(invocation_id, safe='')}",
                api_key=api_key,
            )
            invocation = invocation_result.get("response")
            if not isinstance(invocation, dict):
                raise ValueError("test invocation response is invalid")
            runs = invocation.get("test_runs")
            statuses = [
                str(item.get("status", ""))
                for item in runs
                if isinstance(item, dict)
            ] if isinstance(runs, list) else []
            if len(statuses) == len(selected_ids) and all(
                status not in {"", "pending", "running", "queued", "in_progress"}
                for status in statuses
            ):
                completed = invocation
                break
            time.sleep(2)
        if completed is None:
            raise TimeoutError(f"test invocation {invocation_id} did not finish before timeout")

        runs = completed.get("test_runs", [])
        run_summaries = [
            {
                "test_id": item.get("test_id"),
                "test_name": item.get("test_name"),
                "test_run_id": item.get("test_run_id") or item.get("id"),
                "status": item.get("status"),
            }
            for item in runs
            if isinstance(item, dict)
        ]
        result = {
            "checkpoint_id": CHECKPOINT_ID,
            "captured_at_utc": utc_now(),
            "status": "completed",
            "scope": args.scope,
            "invocation_id": invocation_id,
            "run_statuses": run_summaries,
            "provider_status_code": run_result.get("status_code"),
            "outbound_calls_made": False,
        }
        write_json(f"{label}_run_result.json", result)
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        error = guards.safe_error(exc)
        write_json(
            f"{label}_run_result.json",
            {
                "checkpoint_id": CHECKPOINT_ID,
                "status": "failed",
                "error": error,
                "outbound_calls_made": False,
            },
        )
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
