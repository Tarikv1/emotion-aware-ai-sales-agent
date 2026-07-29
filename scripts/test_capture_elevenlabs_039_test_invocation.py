#!/usr/bin/env python3
from __future__ import annotations

import unittest

import capture_elevenlabs_039_test_invocation as capture


def base_run(**overrides):
    run = {
        "test_run_id": "trun_test",
        "test_invocation_id": "suite_test",
        "agent_id": capture.EXPECTED_AGENT_ID,
        "test_id": "test_provider_001",
        "test_name": f"{capture.CHECKPOINT_ID}::sim_test",
        "status": "failed",
        "condition_result": {"result": "fail"},
    }
    run.update(overrides)
    return run


class CaptureResponsesTests(unittest.TestCase):
    def test_empty_agent_responses_list_is_preserved(self) -> None:
        result = capture.sanitize_run(base_run(agent_responses=[]), result_rationale_by_test_id={})
        self.assertEqual(result["agent_responses"], [])

    def test_missing_agent_responses_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "agent_responses must be present"):
            capture.sanitize_run(base_run(), result_rationale_by_test_id={})

    def test_non_list_agent_responses_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "agent_responses must be a list"):
            capture.sanitize_run(base_run(agent_responses="timeout"), result_rationale_by_test_id={})

    def test_ordinary_agent_responses_are_unchanged(self) -> None:
        responses = [
            {"role": "user", "message": "Hello", "time_in_call_secs": 1},
            {"role": "assistant", "message": "Hi there", "time_in_call_secs": 2},
        ]
        result = capture.sanitize_run(base_run(agent_responses=responses), result_rationale_by_test_id={})
        self.assertEqual(result["agent_responses"][0]["role"], "user")
        self.assertEqual(result["agent_responses"][0]["message"], "Hello")
        self.assertEqual(result["agent_responses"][0]["time"], 1)
        self.assertEqual(result["agent_responses"][1]["role"], "assistant")
        self.assertEqual(result["agent_responses"][1]["message"], "Hi there")
        self.assertEqual(result["agent_responses"][1]["time"], 2)


if __name__ == "__main__":
    unittest.main()
