# COMMERCIAL-SALES-PERFORMANCE-GATE-001

- Status: `pass`
- Scenario count: `11`
- Multi-turn count: `11`
- Average score: `100.0`
- Minimum score: `100`
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
  "recommendation_strength_score": 10.0,
  "safety_grounding_score": 10.0,
  "value_framing_score": 10.0
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
  "response asks another qualifier when recommendation is already possible",
  "unsupported claim / fake side effect / internal policy language / product leakage"
]
```

## Why Each Critical Failure Is Critical

```json
{
  "buyer asks is X enough but response dodges or over-qualifies": "An is-enough question requests a direct plan decision, not another qualifier.",
  "buyer asks price but response gives no value frame": "Price without value creates sticker-shock instead of a commercial decision.",
  "buyer gives buying signal but no close/decision step follows": "Buying signals must be converted into a next decision, comparison, or close.",
  "direct buying question is not answered": "A buyer asking what to buy is a high-intent moment; dodging it loses trust and momentum.",
  "enough context exists but no recommendation is made": "When fit evidence is available, more discovery is friction rather than selling.",
  "no_loop_score == 0": "Looping proves the seller ignored new buyer information, so a high aggregate score is misleading.",
  "response asks another qualifier when recommendation is already possible": "Unneeded qualification stalls high-intent buyers.",
  "response only provides information and no next commercial action": "Information is not selling unless it advances the buyer toward a decision.",
  "response repeats same caveat after buyer gives new information": "Repeated caveats show the dialogue is not adapting to the buyer.",
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
    "final_response_hash": "29e68776c62e",
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
    "final_response_hash": "f09571a999b4",
    "group": "objection_reframe",
    "id": "commercial-competitor-gap-001",
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
    "final_response_hash": "61cccbea609b",
    "group": "no_fit_close",
    "id": "commercial-no-fit-001",
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
    "final_response_hash": "6133667e2577",
    "group": "objection_handling",
    "id": "commercial-objection-001",
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
    "final_response_hash": "3f75851e172f",
    "group": "objection_handling",
    "id": "commercial-objection-002",
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
    "final_response_hash": "1175535a8eec",
    "group": "objection_handling",
    "id": "commercial-objection-003",
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
    "failure_count": 7,
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
    "failure_count": 6,
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
  }
]
```
