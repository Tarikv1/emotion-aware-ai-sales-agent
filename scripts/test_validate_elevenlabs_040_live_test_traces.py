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

    def test_partial_canary_fails_mockup_cta_in_initial_price_answer(self) -> None:
        result = traces.validate_partial_canary_payload(
            canary_payload(
                ["A basic site is usually $900-$1,500 depending on content. I can send a free mockup first."],
                ["What does a basic website cost?"],
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

    def test_firm_quote_real_number_and_scoping_followups_keep_cta_locked(self) -> None:
        followups = [
            "Can you give me a firm quote?",
            "How do I get a real number?",
            "What does the scoping process involve?",
        ]

        for followup in followups:
            with self.subTest(followup=followup):
                result = traces.validate_partial_canary_payload(
                    canary_payload(
                        [
                            "A basic site is usually $900-$1,500 depending on content.",
                            "I can send a free mockup first and you can reply with the details.",
                        ],
                        ["What does a basic website cost?", followup],
                    )
                )

                self.assertEqual(result["independent_status"], "fail")
                self.assertIn("post_quote_price_followup_no_cta", canary_failure_names(result))

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

    def test_plural_prices_is_a_direct_price_trigger(self) -> None:
        self.assertIsNotNone(traces.PRICE_TRIGGER_RE.search("What are your website prices?"))
        self.assertIsNotNone(traces.PRICE_TRIGGER_RE.search("I need to know what a basic site costs."))

    def test_custom_business_logic_is_not_a_menu_dump(self) -> None:
        descriptive_phrases = [
            "That depends on the custom business logic and integrations.",
            "That depends on the custom business workflows and integrations.",
            "That depends on the custom business-logic and integrations.",
        ]

        for phrase in descriptive_phrases:
            with self.subTest(phrase=phrase):
                self.assertIsNone(traces.MENU_RE.search(phrase))
        self.assertIsNotNone(traces.MENU_RE.search("The Custom Business package is one option."))

    def test_negated_fixed_quote_language_is_not_an_unsupported_quote(self) -> None:
        refusals = [
            "That is not a real fixed price without scoping it.",
            "I can't give a fixed price yet.",
            "I cannot give an exact quote until the workflows are scoped.",
            "Not exactly. The combined project is usually $4,000-$6,500.",
        ]

        for refusal in refusals:
            with self.subTest(refusal=refusal):
                self.assertFalse(traces.has_unsupported_fixed_quote(refusal))

        self.assertTrue(traces.has_unsupported_fixed_quote("The fixed price is $1,200."))

    def test_negated_fixed_quote_passes_the_money_bearing_validator_path(self) -> None:
        payload = full_payload()
        payload["test_runs"][2]["agent_responses"] = [
            traces.make_event("user", "What does a basic website cost?"),
            traces.make_event("agent", "A basic site is usually $900-$1,500 depending on content. That is not a real fixed price without scoping it."),
        ]

        result = traces.validate_payload(payload)

        self.assertEqual(status_by_id(result)[traces.EXPECTED_TEST_ORDER[2]], "pass")

    def test_negated_ceiling_language_is_not_an_unsupported_ceiling(self) -> None:
        refusals = [
            "I can't honestly give a maximum without scope; the approved range is $1,000-$2,500+.",
            "I wouldn't want to invent a ceiling before scoping the API and data flow.",
        ]

        for refusal in refusals:
            with self.subTest(refusal=refusal):
                self.assertFalse(traces.has_unsupported_ceiling(refusal))

        self.assertTrue(traces.has_unsupported_ceiling("The maximum is $5,000."))
        self.assertFalse(traces.has_unsupported_ceiling("The $79 plan covers hosting; the domain stays under your ownership."))
        self.assertTrue(traces.has_unsupported_ceiling("Keep the project under $5,000."))
        self.assertTrue(traces.has_unsupported_ceiling("Keep the project under five thousand dollars."))

    def test_negated_ceiling_passes_the_money_bearing_validator_path(self) -> None:
        payload = full_payload()
        payload["test_runs"][6]["agent_responses"] = [
            traces.make_event("user", "What does direct CRM integration cost on our existing site?"),
            traces.make_event(
                "agent",
                "A direct CRM/API add-on is usually $1,000-$2,500+. I can't honestly give a maximum without scope because API data flow and field mapping can vary.",
            ),
        ]

        result = traces.validate_payload(payload)

        self.assertEqual(status_by_id(result)[traces.EXPECTED_TEST_ORDER[6]], "pass")

    def test_care_ongoing_costs_and_same_turn_mockup_question_pass(self) -> None:
        payload = full_payload()
        payload["test_runs"][9]["agent_responses"] = [
            traces.make_event("agent", "The mockup is a static homepage concept, not a working site."),
            traces.make_event("user", "So it's just a picture, basically? What about ongoing costs if I use it?"),
            traces.make_event(
                "agent",
                "Yes, the mockup is a static visual. For ongoing hosting and maintenance, the care plan is $79 per month for updates, backups, and monitoring.",
            ),
        ]

        result = traces.validate_payload(payload)

        self.assertEqual(status_by_id(result)[traces.EXPECTED_TEST_ORDER[9]], "pass")

    def test_care_same_turn_mockup_question_does_not_allow_send_cta(self) -> None:
        payload = full_payload()
        payload["test_runs"][9]["agent_responses"] = [
            traces.make_event("agent", "The mockup is a static homepage concept, not a working site."),
            traces.make_event("user", "So it's just a picture, basically? What about ongoing costs if I use it?"),
            traces.make_event(
                "agent",
                "Yes, the mockup is a static visual. The care plan is $79 per month for updates, backups, and monitoring. I can send the mockup over first.",
            ),
        ]

        result = traces.validate_payload(payload)

        self.assertEqual(status_by_id(result)[traces.EXPECTED_TEST_ORDER[9]], "fail")
        self.assertIn("post_quote_price_followup_no_cta", traces.failure_names(result, traces.EXPECTED_TEST_ORDER[9]))

    def test_portal_scope_chain_fails_mockup_cta_without_numeric_price(self) -> None:
        payload = full_payload()
        payload["test_runs"][7]["agent_responses"] = [
            traces.make_event("user", "How much does a parent portal with accounts and a dashboard cost?"),
            traces.make_event("agent", "That needs scope around accounts, database, permissions, security, and integrations. I can send a free homepage mockup first."),
        ]

        result = traces.validate_payload(payload)

        self.assertEqual(status_by_id(result)[traces.EXPECTED_TEST_ORDER[7]], "fail")
        self.assertIn("portal_no_mockup_cta", traces.failure_names(result, traces.EXPECTED_TEST_ORDER[7]))

    def test_actionable_mockup_offers_are_detected_without_broad_language_false_positives(self) -> None:
        offers = [
            "I can show you a mockup first.",
            "I can share the mockup if useful.",
            "We could walk through a mockup first.",
            "Where should I send the mockup?",
            "What is the best email for the mockup?",
        ]
        neutral_price_language = [
            "Would you be open to the lower end if content is ready?",
            "Take a look at the service count and page count.",
            "You can compare the options without committing today.",
            "Send the scope notes over and I can tell you which range fits.",
            "Send the photos over and I can tell you whether the lower end fits.",
        ]

        for offer in offers:
            with self.subTest(offer=offer):
                self.assertTrue(traces.has_actionable_post_quote_cta(offer))
        for response in neutral_price_language:
            with self.subTest(response=response):
                self.assertFalse(traces.has_actionable_post_quote_cta(response))

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

    def test_between_and_spoken_basic_range_is_normalized(self) -> None:
        payload = full_payload()
        payload["test_runs"][2]["agent_responses"] = [
            traces.make_event("user", "What does a basic three-to-five-page site cost?"),
            traces.make_event("agent", "A basic site usually falls between nine hundred dollars and fifteen hundred dollars, depending on content."),
        ]

        result = traces.validate_payload(payload)

        self.assertEqual(status_by_id(result)[traces.EXPECTED_TEST_ORDER[2]], "pass")

    def test_that_can_fit_is_an_affirmative_budget_answer(self) -> None:
        payload = full_payload()
        payload["test_runs"][8]["agent_responses"] = [
            traces.make_event("user", "I need a basic website, and my budget is about $1,200."),
            traces.make_event("agent", "That can fit a basic three to five page new site. The usual range is nine hundred to fifteen hundred dollars."),
        ]

        result = traces.validate_payload(payload)

        self.assertEqual(status_by_id(result)[traces.EXPECTED_TEST_ORDER[8]], "pass")

    def test_budget_within_range_and_fit_within_that_budget_are_affirmative(self) -> None:
        payload = full_payload()
        payload["test_runs"][8]["agent_responses"] = [
            traces.make_event("agent", "A free mockup shows what a cleaner homepage could look like."),
            traces.make_event("user", "How much would a basic site cost? My budget is around $1,200."),
            traces.make_event("agent", "A basic site is usually nine hundred to fifteen hundred dollars, so twelve hundred is within the normal range."),
            traces.make_event("user", "Would that cover a simple appointment request form?"),
            traces.make_event("agent", "Yes, that light option can usually fit within that twelve hundred dollar budget."),
        ]

        result = traces.validate_payload(payload)

        self.assertEqual(status_by_id(result)[traces.EXPECTED_TEST_ORDER[8]], "pass")
        self.assertEqual(result["independent_status"], "pass")

    def test_that_is_within_usual_range_is_an_affirmative_budget_answer(self) -> None:
        payload = full_payload()
        payload["test_runs"][8]["agent_responses"] = [
            traces.make_event("user", "I was thinking about a basic site, maybe around $1,200?"),
            traces.make_event("agent", "For a new three to five page site, that is within the usual range, which is $900-$1,500."),
        ]

        result = traces.validate_payload(payload)

        self.assertEqual(status_by_id(result)[traces.EXPECTED_TEST_ORDER[8]], "pass")
        self.assertFalse(traces.contains_affirmative_budget_fit("That is not within the usual range."))
        self.assertFalse(traces.contains_affirmative_budget_fit("That might be within the usual range."))
        self.assertTrue(traces.contains_affirmative_budget_fit("That's within the usual range."))
        self.assertTrue(traces.contains_affirmative_budget_fit("That’s within the normal range."))

    def test_budget_advanced_price_followup_can_move_to_whole_project_band(self) -> None:
        payload = full_payload()
        payload["test_runs"][8]["agent_responses"] = [
            traces.make_event("user", "Would a basic site fit a $1,200 budget?"),
            traces.make_event("agent", "Yes, $1,200 fits within the $900-$1,500 basic-site range."),
            traces.make_event("user", "How much more would booking, payments, or those extra things usually cost?"),
            traces.make_event("agent", "For a new site with standard integration work, the whole project is usually $4,000-$6,500 depending on the workflow."),
        ]

        result = traces.validate_payload(payload)

        self.assertEqual(status_by_id(result)[traces.EXPECTED_TEST_ORDER[8]], "pass")

    def test_budget_advanced_band_before_extra_price_ask_still_fails(self) -> None:
        payload = full_payload()
        payload["test_runs"][8]["agent_responses"] = [
            traces.make_event("user", "Would a basic site fit a $1,200 budget?"),
            traces.make_event("agent", "Yes, $1,200 fits within the $900-$1,500 range, and integration work is usually $4,000-$6,500."),
        ]

        result = traces.validate_payload(payload)

        self.assertEqual(status_by_id(result)[traces.EXPECTED_TEST_ORDER[8]], "fail")
        self.assertIn("approved_ranges_only_in_relevant_scenarios", traces.failure_names(result, traces.EXPECTED_TEST_ORDER[8]))

    def test_budget_advanced_band_requires_explicit_price_language(self) -> None:
        payload = full_payload()
        payload["test_runs"][8]["agent_responses"] = [
            traces.make_event("user", "Would a basic site fit a $1,200 budget?"),
            traces.make_event("agent", "Yes, $1,200 fits within the $900-$1,500 basic-site range."),
            traces.make_event("user", "Those extra things for booking sound useful."),
            traces.make_event("agent", "For a new site with standard integration work, the whole project is usually $4,000-$6,500."),
        ]

        result = traces.validate_payload(payload)

        self.assertEqual(status_by_id(result)[traces.EXPECTED_TEST_ORDER[8]], "fail")
        self.assertIn("approved_ranges_only_in_relevant_scenarios", traces.failure_names(result, traces.EXPECTED_TEST_ORDER[8]))

    def test_budget_advanced_band_requires_a_later_price_followup(self) -> None:
        payload = full_payload()
        payload["test_runs"][8]["agent_responses"] = [
            traces.make_event("user", "Would a basic site fit a $1,200 budget, and how much more would booking and payments cost?"),
            traces.make_event("agent", "Yes, $1,200 fits within the $900-$1,500 range. For integrated booking and payments, the whole project is usually $4,000-$6,500."),
        ]

        result = traces.validate_payload(payload)

        self.assertEqual(status_by_id(result)[traces.EXPECTED_TEST_ORDER[8]], "fail")
        self.assertIn("budget_advanced_price_followup_is_later", traces.failure_names(result, traces.EXPECTED_TEST_ORDER[8]))

    def test_canonical_end_call_mirrors_do_not_make_dialogue_ambiguous(self) -> None:
        payload = full_payload()
        payload["test_runs"][6]["agent_responses"].extend(
            [
                {
                    "role": "agent",
                    "message": None,
                    "tool_calls": [{"type": "system", "tool_name": "end_call", "tool_has_been_called": True}],
                    "tool_results": [],
                },
                {
                    "role": "agent",
                    "message": None,
                    "tool_calls": [],
                    "tool_results": [{"type": "system", "tool_name": "end_call", "tool_has_been_called": True}],
                },
            ]
        )

        result = traces.validate_payload(payload)

        self.assertEqual(status_by_id(result)[traces.EXPECTED_TEST_ORDER[6]], "pass")

    def test_generic_empty_agent_event_remains_ambiguous(self) -> None:
        payload = full_payload()
        payload["test_runs"][6]["agent_responses"].append(
            {"role": "agent", "message": None, "tool_calls": [], "tool_results": []}
        )

        result = traces.validate_payload(payload)

        self.assertEqual(status_by_id(result)[traces.EXPECTED_TEST_ORDER[6]], "fail")
        self.assertIn("ordered_dialogue_extractable", traces.failure_names(result, traces.EXPECTED_TEST_ORDER[6]))

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

    def test_synthetic_mixed_suite_classifies_fail_and_incomplete_without_live_fixtures(self) -> None:
        payload = full_payload()
        payload["test_runs"][5]["agent_responses"] = [
            traces.make_event("user", "I need a new site with booking, CRM, payments, service-area pages, and a blog."),
            traces.make_event("agent", "That is a broader connected workflow, so the scope depends on what needs to sync."),
        ]
        payload["test_runs"][9]["agent_responses"] = [
            traces.make_event("user", "Can you build the site and help keep it updated?"),
            traces.make_event("agent", "Yes, we can build the site and keep it updated."),
            traces.make_event("user", "What do hosting and maintenance cost each month?"),
            traces.make_event("agent", "Essential Care is seventy nine dollars per month, Business Care is one hundred forty nine dollars per month, and Growth Care is two hundred forty nine dollars per month."),
        ]

        result = traces.validate_payload(payload)
        statuses = status_by_id(result)

        self.assertEqual(result["independent_status"], "fail")
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
