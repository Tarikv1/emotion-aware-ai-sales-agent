# COMMERCIAL-SALES-PERFORMANCE-GATE-001

- Status: `pass`
- Scenario count: `18`
- Multi-turn count: `18`
- Average score: `98.28`
- Minimum score: `89`
- Critical failure count: `0`
- Zero-dimension-score count: `0`
- Strict enough to catch previous live failures: `true`

## Score By Dimension

```json
{
  "buyer_specificity_score": 10.0,
  "close_progression_score": 10.0,
  "direct_answer_score": 10.0,
  "momentum_score": 10.0,
  "naturalness_score": 10.0,
  "no_loop_score": 10.0,
  "objection_handling_score": 10.0,
  "recommendation_strength_score": 8.61,
  "safety_grounding_score": 10.0,
  "value_framing_score": 9.67
}
```

## Critical Failure Rules

```json
[
  "no_loop_score == 0",
  "direct buying question is not answered",
  "enough context exists but no recommendation is made",
  "buyer gives buying signal but no close/decision step follows",
  "buyer asks price but response gives no value frame",
  "buyer asks is X enough but response dodges or over-qualifies",
  "response repeats same caveat after buyer gives new information",
  "response only provides information and no next commercial action",
  "buyer asks which tier/version and agent answers earlier plan comparison",
  "price objection receives repeated price info with no value reframe",
  "buyer gives tool usage and agent prematurely disqualifies without explicit no-fit signal",
  "signup close ignores current decision stage",
  "response asks another qualifier when recommendation is already possible",
  "unsupported claim / fake side effect / internal policy language / product leakage",
  "source-note wording in normal sales answer",
  "same response after follow-up question",
  "terminal acceptance followed by a new sales pitch",
  "buyer asks plan-change timing and agent repeats tier-selection answer",
  "state downgrades Pro-tier buyer to Plus without buyer preference for lower cost",
  "blank final_response marked pass",
  "explanation question routed to recommendation/team/close",
  "plan label question treated as plan-selection/team intent",
  "buyer conjunction fidelity changed",
  "stability guard owns recognized commercial turn",
  "state mutates from explanation into recommendation/no-fit/team intent",
  "same response used for different sub-intents requiring a specific answer"
]
```

## Why Each Critical Failure Is Critical

```json
{
  "buyer asks is X enough but response dodges or over-qualifies": "An is-enough question requests a direct plan decision, not another qualifier.",
  "buyer asks plan-change timing and agent repeats tier-selection answer": "A billing/timing question must be answered directly without inventing terms.",
  "buyer asks price but response gives no value frame": "Price without value creates sticker-shock instead of a commercial decision.",
  "buyer asks which tier/version and agent answers earlier plan comparison": "A later-stage tier decision must not be answered with an earlier Plus-vs-Pro frame.",
  "buyer gives buying signal but no close/decision step follows": "Buying signals must be converted into a next decision, comparison, or close.",
  "buyer gives tool usage and agent prematurely disqualifies without explicit no-fit signal": "Mere tool usage is discovery evidence, not a no-fit signal.",
  "direct buying question is not answered": "A buyer asking what to buy is a high-intent moment; dodging it loses trust and momentum.",
  "enough context exists but no recommendation is made": "When fit evidence is available, more discovery is friction rather than selling.",
  "no_loop_score == 0": "Looping proves the seller ignored new buyer information, so a high aggregate score is misleading.",
  "price objection receives repeated price info with no value reframe": "Repeating prices after sticker shock reinforces the objection instead of resolving it.",
  "response asks another qualifier when recommendation is already possible": "Unneeded qualification stalls high-intent buyers.",
  "response only provides information and no next commercial action": "Information is not selling unless it advances the buyer toward a decision.",
  "response repeats same caveat after buyer gives new information": "Repeated caveats show the dialogue is not adapting to the buyer.",
  "same response after follow-up question": "A follow-up indicates confusion or a new detail, so repeating the same answer is a live-call failure.",
  "signup close ignores current decision stage": "A close must match the buyer's active decision, otherwise the next step is generic and weak.",
  "source-note wording in normal sales answer": "Sales speech should use grounded facts silently; source-note narration sounds like reading notes.",
  "state downgrades Pro-tier buyer to Plus without buyer preference for lower cost": "A buyer choosing between Pro tiers is already past the Plus-vs-Pro stage.",
  "terminal acceptance followed by a new sales pitch": "Once the buyer accepts the next step, more selling creates friction and weakens the close.",
  "unsupported claim / fake side effect / internal policy language / product leakage": "These create trust, legal, privacy, or campaign-boundary failures."
}
```

## Failure Examples

```json
[]
```

## Low-Score Examples

```json
[
  {
    "critical_failures": [],
    "dimension_scores": {
      "buyer_specificity_score": 10,
      "close_progression_score": 10,
      "direct_answer_score": 10,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 10,
      "objection_handling_score": 10,
      "recommendation_strength_score": 5,
      "safety_grounding_score": 10,
      "value_framing_score": 4
    },
    "failures": [
      "recommendation was present but weak",
      "decision frame 'current_tool_vs_chatgpt' missing"
    ],
    "final_response_hash": "6462d5ab2985",
    "group": "objection_handling",
    "id": "commercial-ai-tool-usage-no-premature-nofit-001",
    "score": 89
  },
  {
    "critical_failures": [],
    "dimension_scores": {
      "buyer_specificity_score": 10,
      "close_progression_score": 10,
      "direct_answer_score": 10,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 10,
      "objection_handling_score": 10,
      "recommendation_strength_score": 5,
      "safety_grounding_score": 10,
      "value_framing_score": 10
    },
    "failures": [
      "recommendation was present but weak"
    ],
    "final_response_hash": "8aab91f0b6cb",
    "group": "decision_stage",
    "id": "commercial-pro-tier-selection-001",
    "score": 95
  },
  {
    "critical_failures": [],
    "dimension_scores": {
      "buyer_specificity_score": 10,
      "close_progression_score": 10,
      "direct_answer_score": 10,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 10,
      "objection_handling_score": 10,
      "recommendation_strength_score": 5,
      "safety_grounding_score": 10,
      "value_framing_score": 10
    },
    "failures": [
      "recommendation was present but weak"
    ],
    "final_response_hash": "7104eb1d01dc",
    "group": "decision_stage",
    "id": "commercial-pro-tier-midmonth-followup-001",
    "score": 95
  },
  {
    "critical_failures": [],
    "dimension_scores": {
      "buyer_specificity_score": 10,
      "close_progression_score": 10,
      "direct_answer_score": 10,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 10,
      "objection_handling_score": 10,
      "recommendation_strength_score": 5,
      "safety_grounding_score": 10,
      "value_framing_score": 10
    },
    "failures": [
      "recommendation was present but weak"
    ],
    "final_response_hash": "7104eb1d01dc",
    "group": "decision_stage",
    "id": "commercial-pro-tier-start-lower-upgrade-001",
    "score": 95
  },
  {
    "critical_failures": [],
    "dimension_scores": {
      "buyer_specificity_score": 10,
      "close_progression_score": 10,
      "direct_answer_score": 10,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 10,
      "objection_handling_score": 10,
      "recommendation_strength_score": 5,
      "safety_grounding_score": 10,
      "value_framing_score": 10
    },
    "failures": [
      "recommendation was present but weak"
    ],
    "final_response_hash": "da1a77147a2e",
    "group": "self_serve_close",
    "id": "commercial-signup-after-pro-tier-001",
    "score": 95
  },
  {
    "critical_failures": [],
    "dimension_scores": {
      "buyer_specificity_score": 10,
      "close_progression_score": 10,
      "direct_answer_score": 10,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 10,
      "objection_handling_score": 10,
      "recommendation_strength_score": 10,
      "safety_grounding_score": 10,
      "value_framing_score": 10
    },
    "failures": [],
    "final_response_hash": "437593def519",
    "group": "direct_recommendation",
    "id": "commercial-plus-enough-after-use-case-001",
    "score": 100
  },
  {
    "critical_failures": [],
    "dimension_scores": {
      "buyer_specificity_score": 10,
      "close_progression_score": 10,
      "direct_answer_score": 10,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 10,
      "objection_handling_score": 10,
      "recommendation_strength_score": 10,
      "safety_grounding_score": 10,
      "value_framing_score": 10
    },
    "failures": [],
    "final_response_hash": "dfd4e4ed4934",
    "group": "direct_recommendation",
    "id": "commercial-heavy-plus-enough-001",
    "score": 100
  },
  {
    "critical_failures": [],
    "dimension_scores": {
      "buyer_specificity_score": 10,
      "close_progression_score": 10,
      "direct_answer_score": 10,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 10,
      "objection_handling_score": 10,
      "recommendation_strength_score": 10,
      "safety_grounding_score": 10,
      "value_framing_score": 10
    },
    "failures": [],
    "final_response_hash": "c4d37e9f9f02",
    "group": "momentum_close",
    "id": "commercial-pro-agreement-close-001",
    "score": 100
  },
  {
    "critical_failures": [],
    "dimension_scores": {
      "buyer_specificity_score": 10,
      "close_progression_score": 10,
      "direct_answer_score": 10,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 10,
      "objection_handling_score": 10,
      "recommendation_strength_score": 10,
      "safety_grounding_score": 10,
      "value_framing_score": 10
    },
    "failures": [],
    "final_response_hash": "668def6d152c",
    "group": "price_value_frame",
    "id": "commercial-price-known-heavy-001",
    "score": 100
  },
  {
    "critical_failures": [],
    "dimension_scores": {
      "buyer_specificity_score": 10,
      "close_progression_score": 10,
      "direct_answer_score": 10,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 10,
      "objection_handling_score": 10,
      "recommendation_strength_score": 10,
      "safety_grounding_score": 10,
      "value_framing_score": 10
    },
    "failures": [],
    "final_response_hash": "f97566014c66",
    "group": "self_serve_close",
    "id": "commercial-signup-known-heavy-001",
    "score": 100
  }
]
```

## Critical Rule Probes

```json
[
  {
    "actual_status": "fail",
    "critical_failures": [
      "information-only response without commercial action",
      "repeated same response after buyer gives new info",
      "same response after follow-up question",
      "zero dimension score",
      "no_loop_score == 0"
    ],
    "dimension_scores": {
      "buyer_specificity_score": 10,
      "close_progression_score": 0,
      "direct_answer_score": 10,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 0,
      "objection_handling_score": 10,
      "recommendation_strength_score": 5,
      "safety_grounding_score": 10,
      "value_framing_score": 4
    },
    "expected_status": "fail",
    "failure_count": 8,
    "id": "probe-no-loop-zero",
    "response_hash": "f2a22ca5b568",
    "rule": "no_loop_score == 0",
    "score": 69
  },
  {
    "actual_status": "fail",
    "critical_failures": [
      "direct buying question dodged",
      "enough context exists but no recommendation",
      "information-only response without commercial action",
      "zero dimension score",
      "no_loop_score == 0"
    ],
    "dimension_scores": {
      "buyer_specificity_score": 6,
      "close_progression_score": 0,
      "direct_answer_score": 0,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 0,
      "objection_handling_score": 10,
      "recommendation_strength_score": 0,
      "safety_grounding_score": 10,
      "value_framing_score": 4
    },
    "expected_status": "fail",
    "failure_count": 12,
    "id": "probe-direct-question-dodged",
    "response_hash": "5c13194081c3",
    "rule": "direct buying question is not answered",
    "score": 50
  },
  {
    "actual_status": "fail",
    "critical_failures": [
      "direct buying question dodged",
      "enough context exists but no recommendation",
      "information-only response without commercial action",
      "zero dimension score"
    ],
    "dimension_scores": {
      "buyer_specificity_score": 6,
      "close_progression_score": 0,
      "direct_answer_score": 0,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 10,
      "objection_handling_score": 10,
      "recommendation_strength_score": 2,
      "safety_grounding_score": 10,
      "value_framing_score": 4
    },
    "expected_status": "fail",
    "failure_count": 8,
    "id": "probe-no-recommendation-after-context",
    "response_hash": "5e8e29721248",
    "rule": "enough context exists but no recommendation is made",
    "score": 62
  },
  {
    "actual_status": "fail",
    "critical_failures": [
      "close opportunity missed",
      "information-only response without commercial action",
      "zero dimension score"
    ],
    "dimension_scores": {
      "buyer_specificity_score": 6,
      "close_progression_score": 0,
      "direct_answer_score": 10,
      "momentum_score": 5,
      "naturalness_score": 10,
      "no_loop_score": 10,
      "objection_handling_score": 10,
      "recommendation_strength_score": 5,
      "safety_grounding_score": 10,
      "value_framing_score": 5
    },
    "expected_status": "fail",
    "failure_count": 8,
    "id": "probe-buying-signal-no-close",
    "response_hash": "0a8b8a2ada32",
    "rule": "buyer gives buying signal but no close/decision step follows",
    "score": 71
  },
  {
    "actual_status": "fail",
    "critical_failures": [
      "direct buying question dodged",
      "enough context exists but no recommendation",
      "price asked without value frame",
      "information-only response without commercial action",
      "zero dimension score"
    ],
    "dimension_scores": {
      "buyer_specificity_score": 6,
      "close_progression_score": 0,
      "direct_answer_score": 0,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 10,
      "objection_handling_score": 10,
      "recommendation_strength_score": 2,
      "safety_grounding_score": 10,
      "value_framing_score": 0
    },
    "expected_status": "fail",
    "failure_count": 8,
    "id": "probe-price-no-value-frame",
    "response_hash": "94af412fcfa9",
    "rule": "buyer asks price but response gives no value frame",
    "score": 58
  },
  {
    "actual_status": "fail",
    "critical_failures": [
      "direct buying question dodged",
      "is-enough question dodged",
      "enough context exists but no recommendation",
      "zero dimension score"
    ],
    "dimension_scores": {
      "buyer_specificity_score": 6,
      "close_progression_score": 10,
      "direct_answer_score": 0,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 10,
      "objection_handling_score": 10,
      "recommendation_strength_score": 2,
      "safety_grounding_score": 10,
      "value_framing_score": 5
    },
    "expected_status": "fail",
    "failure_count": 7,
    "id": "probe-enough-overqualified",
    "response_hash": "b57a81840b54",
    "rule": "buyer asks is X enough but response dodges or over-qualifies",
    "score": 73
  },
  {
    "actual_status": "fail",
    "critical_failures": [
      "enough context exists but no recommendation",
      "repeated same response after buyer gives new info",
      "same response after follow-up question",
      "repeated same caveat after buyer gives new info",
      "zero dimension score",
      "no_loop_score == 0"
    ],
    "dimension_scores": {
      "buyer_specificity_score": 6,
      "close_progression_score": 10,
      "direct_answer_score": 10,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 0,
      "objection_handling_score": 10,
      "recommendation_strength_score": 2,
      "safety_grounding_score": 10,
      "value_framing_score": 10
    },
    "expected_status": "fail",
    "failure_count": 7,
    "id": "probe-repeated-caveat",
    "response_hash": "792c795ac5b2",
    "rule": "response repeats same caveat after buyer gives new information",
    "score": 78
  },
  {
    "actual_status": "fail",
    "critical_failures": [
      "information-only response without commercial action",
      "zero dimension score"
    ],
    "dimension_scores": {
      "buyer_specificity_score": 6,
      "close_progression_score": 0,
      "direct_answer_score": 10,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 10,
      "objection_handling_score": 10,
      "recommendation_strength_score": 5,
      "safety_grounding_score": 10,
      "value_framing_score": 5
    },
    "expected_status": "fail",
    "failure_count": 6,
    "id": "probe-information-only",
    "response_hash": "d5e241047986",
    "rule": "response only provides information and no next commercial action",
    "score": 76
  },
  {
    "actual_status": "fail",
    "critical_failures": [
      "buyer asks which tier/version and agent answers earlier plan comparison",
      "zero dimension score",
      "direct buying question dodged"
    ],
    "dimension_scores": {
      "buyer_specificity_score": 6,
      "close_progression_score": 10,
      "direct_answer_score": 0,
      "momentum_score": 0,
      "naturalness_score": 10,
      "no_loop_score": 10,
      "objection_handling_score": 10,
      "recommendation_strength_score": 10,
      "safety_grounding_score": 10,
      "value_framing_score": 0
    },
    "expected_status": "fail",
    "failure_count": 5,
    "id": "probe-pro-tier-reset-to-plus-vs-pro",
    "response_hash": "f89ab4eca91f",
    "rule": "buyer asks which tier/version and agent answers earlier plan comparison",
    "score": 66
  },
  {
    "actual_status": "fail",
    "critical_failures": [
      "price asked without value frame",
      "price objection receives repeated price info with no value reframe",
      "information-only response without commercial action",
      "zero dimension score",
      "no_loop_score == 0",
      "objection not reframed"
    ],
    "dimension_scores": {
      "buyer_specificity_score": 6,
      "close_progression_score": 0,
      "direct_answer_score": 10,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 0,
      "objection_handling_score": 0,
      "recommendation_strength_score": 5,
      "safety_grounding_score": 10,
      "value_framing_score": 0
    },
    "expected_status": "fail",
    "failure_count": 10,
    "id": "probe-price-objection-repeated-price",
    "response_hash": "5724e2a9285a",
    "rule": "price objection receives repeated price info with no value reframe",
    "score": 51
  },
  {
    "actual_status": "fail",
    "critical_failures": [
      "buyer gives tool usage and agent prematurely disqualifies without explicit no-fit signal",
      "zero dimension score"
    ],
    "dimension_scores": {
      "buyer_specificity_score": 6,
      "close_progression_score": 10,
      "direct_answer_score": 10,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 10,
      "objection_handling_score": 0,
      "recommendation_strength_score": 10,
      "safety_grounding_score": 10,
      "value_framing_score": 10
    },
    "expected_status": "fail",
    "failure_count": 3,
    "id": "probe-tool-usage-premature-no-fit",
    "response_hash": "1cac2fc2e742",
    "rule": "buyer gives tool usage and agent prematurely disqualifies without explicit no-fit signal",
    "score": 86
  },
  {
    "actual_status": "fail",
    "critical_failures": [
      "direct buying question dodged",
      "buyer asks which tier/version and agent answers earlier plan comparison",
      "state downgrades Pro-tier buyer to Plus without buyer preference for lower cost",
      "signup close ignores current decision stage",
      "zero dimension score",
      "close opportunity missed"
    ],
    "dimension_scores": {
      "buyer_specificity_score": 6,
      "close_progression_score": 0,
      "direct_answer_score": 0,
      "momentum_score": 0,
      "naturalness_score": 10,
      "no_loop_score": 10,
      "objection_handling_score": 10,
      "recommendation_strength_score": 0,
      "safety_grounding_score": 10,
      "value_framing_score": 0
    },
    "expected_status": "fail",
    "failure_count": 8,
    "id": "probe-signup-ignores-pro-tier-stage",
    "response_hash": "c46f3e215c7d",
    "rule": "signup close ignores current decision stage",
    "score": 46
  },
  {
    "actual_status": "fail",
    "critical_failures": [
      "direct buying question dodged",
      "enough context exists but no recommendation",
      "zero dimension score",
      "no_loop_score == 0"
    ],
    "dimension_scores": {
      "buyer_specificity_score": 6,
      "close_progression_score": 10,
      "direct_answer_score": 0,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 0,
      "objection_handling_score": 10,
      "recommendation_strength_score": 0,
      "safety_grounding_score": 10,
      "value_framing_score": 5
    },
    "expected_status": "fail",
    "failure_count": 9,
    "id": "probe-extra-qualifier",
    "response_hash": "f5d4e1cf7806",
    "rule": "response asks another qualifier when recommendation is already possible",
    "score": 61
  },
  {
    "actual_status": "fail",
    "critical_failures": [
      "direct buying question dodged",
      "enough context exists but no recommendation",
      "close opportunity missed",
      "information-only response without commercial action",
      "fake side effect",
      "zero dimension score"
    ],
    "dimension_scores": {
      "buyer_specificity_score": 6,
      "close_progression_score": 0,
      "direct_answer_score": 0,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 10,
      "objection_handling_score": 10,
      "recommendation_strength_score": 2,
      "safety_grounding_score": 0,
      "value_framing_score": 5
    },
    "expected_status": "fail",
    "failure_count": 10,
    "id": "probe-fake-side-effect",
    "response_hash": "9115e02f624f",
    "rule": "unsupported claim / fake side effect / internal policy language / product leakage",
    "score": 53
  },
  {
    "actual_status": "fail",
    "critical_failures": [
      "direct buying question dodged",
      "source-note wording in normal sales answer",
      "zero dimension score"
    ],
    "dimension_scores": {
      "buyer_specificity_score": 6,
      "close_progression_score": 10,
      "direct_answer_score": 0,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 10,
      "objection_handling_score": 10,
      "recommendation_strength_score": 5,
      "safety_grounding_score": 0,
      "value_framing_score": 5
    },
    "expected_status": "fail",
    "failure_count": 7,
    "id": "probe-source-note-wording",
    "response_hash": "0aba24bd7257",
    "rule": "source-note wording in normal sales answer",
    "score": 66
  },
  {
    "actual_status": "fail",
    "critical_failures": [
      "buyer asks plan-change timing and agent repeats tier-selection answer",
      "same response after follow-up question",
      "repeated same response after buyer gives new info",
      "zero dimension score",
      "no_loop_score == 0",
      "direct buying question dodged"
    ],
    "dimension_scores": {
      "buyer_specificity_score": 6,
      "close_progression_score": 10,
      "direct_answer_score": 0,
      "momentum_score": 10,
      "naturalness_score": 10,
      "no_loop_score": 0,
      "objection_handling_score": 10,
      "recommendation_strength_score": 5,
      "safety_grounding_score": 3,
      "value_framing_score": 5
    },
    "expected_status": "fail",
    "failure_count": 11,
    "id": "probe-plan-change-repeats-tier-answer",
    "response_hash": "b21c561467f9",
    "rule": "buyer asks plan-change timing and agent repeats tier-selection answer",
    "score": 59
  },
  {
    "actual_status": "fail",
    "critical_failures": [
      "terminal acceptance followed by a new sales pitch",
      "zero dimension score",
      "no_loop_score == 0"
    ],
    "dimension_scores": {
      "buyer_specificity_score": 10,
      "close_progression_score": 0,
      "direct_answer_score": 10,
      "momentum_score": 10,
      "naturalness_score": 0,
      "no_loop_score": 0,
      "objection_handling_score": 10,
      "recommendation_strength_score": 10,
      "safety_grounding_score": 10,
      "value_framing_score": 5
    },
    "expected_status": "fail",
    "failure_count": 5,
    "id": "probe-terminal-acceptance-pitched-again",
    "response_hash": "a9946419c8e4",
    "rule": "terminal acceptance followed by a new sales pitch",
    "score": 65
  },
  {
    "actual_status": "fail",
    "critical_failures": [
      "enough context exists but no recommendation",
      "buyer asks which tier/version and agent answers earlier plan comparison",
      "state downgrades Pro-tier buyer to Plus without buyer preference for lower cost",
      "zero dimension score",
      "direct buying question dodged"
    ],
    "dimension_scores": {
      "buyer_specificity_score": 10,
      "close_progression_score": 10,
      "direct_answer_score": 0,
      "momentum_score": 0,
      "naturalness_score": 10,
      "no_loop_score": 10,
      "objection_handling_score": 10,
      "recommendation_strength_score": 0,
      "safety_grounding_score": 10,
      "value_framing_score": 0
    },
    "expected_status": "fail",
    "failure_count": 8,
    "id": "probe-pro-tier-downgraded-to-plus",
    "response_hash": "078b1642536a",
    "rule": "state downgrades Pro-tier buyer to Plus without buyer preference for lower cost",
    "score": 60
  }
]
```
