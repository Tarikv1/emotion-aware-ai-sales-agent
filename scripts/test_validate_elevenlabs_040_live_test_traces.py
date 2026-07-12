#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_elevenlabs_040_live_test_traces as traces


def canary_payload(agent_messages: list[str], user_messages: list[str]) -> dict[str, object]:
    return traces.make_payload(
        [
            traces.make_run(
                "sim_040_basic_site_direct_price",
                agent_messages,
                user_messages,
            )
        ]
    )


def canary_failure_names(result: dict[str, object]) -> set[str]:
    tests = result.get("tests")
    if not isinstance(tests, list) or not tests:
        return set()
    return {item.get("name") for item in tests[0].get("assertions", []) if item.get("passed") is False}


class DetailedPricingTraceCanaryTests(unittest.TestCase):
    def test_default_full_suite_validation_still_rejects_one_test_canary(self) -> None:
        result = traces.validate_payload(
            canary_payload(
                ["A basic site is usually in the $900-$1,500 range, depending on content."],
                ["What does a basic website cost?"],
            )
        )

        self.assertEqual(result["independent_status"], "fail")
        self.assertTrue(any("expected exact 040 test ids/order" in failure for failure in result["global_failures"]))

    def test_partial_canary_fails_renewed_mockup_cta_during_active_price_followup(self) -> None:
        result = traces.validate_partial_canary_payload(
            canary_payload(
                [
                    "A basic site is usually in the $900-$1,500 range, depending on content.",
                    "The lower end is when content is ready. The free mockup is a good next step, and I can send it over first.",
                ],
                [
                    "What does a basic website cost?",
                    "What makes it cost more or less?",
                ],
            )
        )

        self.assertEqual(result["independent_status"], "fail")
        self.assertIn("post_quote_price_followup_no_cta", canary_failure_names(result))

    def test_partial_canary_allows_direct_price_driver_answer_without_cta(self) -> None:
        result = traces.validate_partial_canary_payload(
            canary_payload(
                [
                    "A basic site is usually in the $900-$1,500 range, depending on content.",
                    "The lower end is when your copy and photos are ready; it moves higher when we need to write, organize, or polish more pages.",
                ],
                [
                    "What does a basic website cost?",
                    "What makes it cost more or less?",
                ],
            )
        )

        self.assertEqual(result["independent_status"], "pass")

    def test_existing_live_post_fix_canary_remains_failed_for_cta_reason(self) -> None:
        path = SCRIPT_DIR.parent / "research" / "experiments" / "generated" / traces.CHECKPOINT_ID / "live_test_canary_post_fix_capture.json"
        payload = traces.capture_payload(traces.read_json(path))

        result = traces.validate_partial_canary_payload(payload)

        self.assertEqual(result["independent_status"], "fail")
        self.assertIn("post_quote_price_followup_no_cta", canary_failure_names(result))


if __name__ == "__main__":
    unittest.main()
