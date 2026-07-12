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


def status_by_id(result: dict[str, object]) -> dict[str, str]:
    tests = result.get("tests")
    if not isinstance(tests, list):
        return {}
    return {str(test.get("test_id")): str(test.get("independent_status")) for test in tests if isinstance(test, dict)}


def full_payload() -> dict[str, object]:
    return traces.make_payload(traces.valid_runs())


class DetailedPricingTraceCanaryTests(unittest.TestCase):
    def test_default_full_suite_validation_still_rejects_one_test_canary(self) -> None:
        result = traces.validate_payload(
            canary_payload(
                ["A basic site is usually in the $900-$1,500 range, depending on content."],
                ["What does a basic website cost?"],
            )
        )

        self.assertEqual(result["independent_status"], "fail")
        self.assertTrue(any("missing test ids" in failure for failure in result["global_failures"]))

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

    def test_partial_canary_allows_neutral_mockup_reference_when_buyer_mentioned_mockup(self) -> None:
        result = traces.validate_partial_canary_payload(
            canary_payload(
                [
                    "A basic site is usually in the $900-$1,500 range, depending on content.",
                    "The mockup itself does not commit you to the site or ongoing care.",
                ],
                [
                    "What does a basic website cost?",
                    "If I like the mockup, what makes the site cost more or less?",
                ],
            )
        )

        self.assertEqual(result["independent_status"], "pass")

    def test_partial_canary_fails_actionable_mockup_offer_when_buyer_mentioned_mockup(self) -> None:
        offers = [
            "I can put together a free mockup for you first.",
            "We could start with the mockup first and go from there.",
        ]

        for offer in offers:
            with self.subTest(offer=offer):
                result = traces.validate_partial_canary_payload(
                    canary_payload(
                        [
                            "A basic site is usually in the $900-$1,500 range, depending on content.",
                            offer,
                        ],
                        [
                            "What does a basic website cost?",
                            "If I like the mockup, what makes the site cost more or less?",
                        ],
                    )
                )

                self.assertEqual(result["independent_status"], "fail")
                self.assertIn("post_quote_price_followup_no_cta", canary_failure_names(result))

    def test_partial_canary_fails_unsolicited_mockup_reference_during_price_followup(self) -> None:
        result = traces.validate_partial_canary_payload(
            canary_payload(
                [
                    "A basic site is usually in the $900-$1,500 range, depending on content.",
                    "The mockup itself does not commit you to the site or ongoing care.",
                ],
                [
                    "What does a basic website cost?",
                    "What makes the site cost more or less?",
                ],
            )
        )

        self.assertEqual(result["independent_status"], "fail")
        self.assertIn("post_quote_price_followup_no_cta", canary_failure_names(result))

    def test_partial_canary_allows_neutral_without_committing_language(self) -> None:
        result = traces.validate_partial_canary_payload(
            canary_payload(
                [
                    "A basic site is usually in the $900-$1,500 range, depending on content.",
                    "You can compare the options without committing to anything today.",
                ],
                [
                    "What does a basic website cost?",
                    "What makes the site cost more or less?",
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

    def test_swapped_run_order_passes_after_canonicalization(self) -> None:
        payload = full_payload()
        runs = list(payload["test_runs"])
        runs[5], runs[6] = runs[6], runs[5]
        payload["test_runs"] = runs

        result = traces.validate_payload(payload)

        self.assertEqual(result["independent_status"], "pass")
        self.assertEqual(result["input_test_ids"], traces.EXPECTED_TEST_ORDER)

    def test_duplicate_or_missing_run_id_fails_exact_suite(self) -> None:
        duplicate_payload = full_payload()
        duplicate_runs = list(duplicate_payload["test_runs"])
        duplicate_runs[6] = dict(duplicate_runs[5])
        duplicate_payload["test_runs"] = duplicate_runs

        duplicate_result = traces.validate_payload(duplicate_payload)

        self.assertEqual(duplicate_result["independent_status"], "fail")
        self.assertTrue(any("duplicate test ids" in failure for failure in duplicate_result["global_failures"]))

        missing_payload = full_payload()
        missing_payload["test_runs"] = list(missing_payload["test_runs"])[:-1]

        missing_result = traces.validate_payload(missing_payload)

        self.assertEqual(missing_result["independent_status"], "fail")
        self.assertTrue(any("missing test ids" in failure for failure in missing_result["global_failures"]))

    def test_spoken_budget_trace_passes_normalized_money_checks(self) -> None:
        payload = full_payload()
        payload["test_runs"][8]["agent_responses"] = [
            traces.make_event("user", "Our budget is twelve hundred dollars. Does that fit a basic site?"),
            traces.make_event("agent", "Yes, twelve hundred dollars fits within nine hundred to fifteen hundred dollars if the content is straightforward."),
        ]

        result = traces.validate_payload(payload)

        self.assertEqual(status_by_id(result)[traces.EXPECTED_TEST_ORDER[8]], "pass")
        self.assertEqual(result["independent_status"], "pass")

    def test_spoken_three_care_plan_transcript_fails_one_plan_rule(self) -> None:
        payload = full_payload()
        payload["test_runs"][9]["agent_responses"] = [
            traces.make_event("user", "Can you build the site and help keep it updated?"),
            traces.make_event("agent", "Yes, we can build the site and keep it updated."),
            traces.make_event("user", "What do hosting and maintenance cost each month?"),
            traces.make_event("agent", "Essential Care is seventy nine dollars per month, Business Care is one hundred forty nine dollars per month, and Growth Care is two hundred forty nine dollars per month depending on support."),
        ]

        result = traces.validate_payload(payload)

        self.assertEqual(status_by_id(result)[traces.EXPECTED_TEST_ORDER[9]], "fail")
        self.assertIn("care_plan_single_relevant_plan", traces.failure_names(result, traces.EXPECTED_TEST_ORDER[9]))

    def test_missing_required_price_trigger_marks_run_incomplete_not_product_failure(self) -> None:
        payload = full_payload()
        payload["test_runs"][5]["agent_responses"] = [
            traces.make_event("user", "I need a new site with booking, CRM, payments, service-area pages, and a blog."),
            traces.make_event("agent", "That is a broader connected workflow, so the scope depends on what needs to sync."),
        ]

        result = traces.validate_payload(payload)

        self.assertEqual(result["independent_status"], "incomplete")
        self.assertEqual(status_by_id(result)[traces.EXPECTED_TEST_ORDER[5]], "incomplete")

    def test_current_capture_classifies_as_eight_pass_one_fail_one_incomplete(self) -> None:
        root = SCRIPT_DIR.parent / "research" / "experiments" / "generated" / traces.CHECKPOINT_ID
        payload = traces.capture_payload(traces.read_json(root / "live_test_capture.json"))
        mapping = traces.provider_test_id_mapping(traces.read_json(root / "live_test_mapping.json"))

        result = traces.validate_payload(payload, mapping)
        statuses = status_by_id(result)

        self.assertEqual(result["independent_status"], "fail")
        self.assertEqual(list(statuses.values()).count("pass"), 8)
        self.assertEqual(statuses["sim_040_care_plan_only_when_asked"], "fail")
        self.assertEqual(statuses["sim_040_multi_feature_no_price_stacking"], "incomplete")

    def test_partial_validation_accepts_exactly_one_known_expected_test(self) -> None:
        care_payload = traces.make_payload([traces.valid_runs()[9]])
        care_result = traces.validate_partial_test_payload(care_payload, partial_test_id="sim_040_care_plan_only_when_asked")

        self.assertEqual(care_result["validation_mode"], "partial_test")
        self.assertEqual(care_result["input_test_ids"], ["sim_040_care_plan_only_when_asked"])
        self.assertEqual(care_result["independent_status"], "pass")

        multi_payload = traces.make_payload([traces.valid_runs()[5]])
        multi_result = traces.validate_partial_test_payload(multi_payload, partial_test_id="sim_040_multi_feature_no_price_stacking")

        self.assertEqual(multi_result["validation_mode"], "partial_test")
        self.assertEqual(multi_result["input_test_ids"], ["sim_040_multi_feature_no_price_stacking"])
        self.assertEqual(multi_result["independent_status"], "pass")

    def test_partial_validation_rejects_unknown_or_mismatched_test(self) -> None:
        care_payload = traces.make_payload([traces.valid_runs()[9]])

        mismatch_result = traces.validate_partial_test_payload(care_payload, partial_test_id="sim_040_multi_feature_no_price_stacking")
        unknown_result = traces.validate_partial_test_payload(care_payload, partial_test_id="unknown")

        self.assertEqual(mismatch_result["independent_status"], "fail")
        self.assertTrue(any("partial validation expects exactly" in failure for failure in mismatch_result["global_failures"]))
        self.assertEqual(unknown_result["independent_status"], "fail")
        self.assertTrue(any("known expected test" in failure for failure in unknown_result["global_failures"]))


if __name__ == "__main__":
    unittest.main()
