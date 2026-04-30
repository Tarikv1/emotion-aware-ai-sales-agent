# PROD-004 LLM vs Rule Baseline Comparison

This comparison uses the same sales difficulty gauntlet cases and campaign profiles for both runs.

## Runs Compared

- Initial rule baseline: first `PROD-004` rule run before LLM-informed fixes
- Improved rule baseline: `research/experiments/generated/PROD-004-rule-baseline-report.md`
- Original LLM agent: `research/experiments/generated/PROD-004-llm-agent-report.md`
- LLM model: `gpt-4o-mini`

## Aggregate Results

| Metric | Initial rule baseline | Original LLM agent | Improved rule baseline |
| --- | ---: | ---: | ---: |
| Turn emotion matches | 10 / 20 | 13 / 20 | 20 / 20 |
| Turn interest-state matches | 13 / 20 | 18 / 20 | 20 / 20 |
| Turn strategy matches | 13 / 20 | 7 / 20 | 20 / 20 |
| Final call-status matches | 6 / 14 | 10 / 14 | 14 / 14 |
| Final interest-state matches | 7 / 14 | 12 / 14 | 14 / 14 |
| Final strategy matches | 8 / 14 | 6 / 14 | 14 / 14 |
| Final appointment matches | 14 / 14 | 14 / 14 | 14 / 14 |

## Interpretation

The original LLM agent was better at reading nuanced lead state than the initial deterministic rule baseline. It improved emotion detection, turn-level interest classification, final call status, and final interest state while preserving appointment caution.

The main weakness is strategy-label alignment. The LLM often chooses a plausible sales move, but not the exact internal taxonomy label expected by the case set. This suggests the taxonomy/prompt contract needs to be made sharper before strategy-match scores can be interpreted as pure agent quality.

The improved rule baseline encodes the failure modes exposed by the LLM comparison as transparent control logic. It is not a claim that rules are more conversational than an LLM. It is the guardrail/control layer the LLM should now learn to match.

## Strong LLM Improvements

- Correctly escalates the competitor-comparison case instead of treating it as generic maybe-interest.
- Correctly escalates the outcome-guarantee request instead of over-selling.
- Correctly recognizes wrong-contact referral as `needs-human`.
- Better recognizes human-sensitive or specialist-sensitive cases than the rule baseline.

## Remaining LLM Risks

- Some final outcomes are internally inconsistent, especially when `interest_state` is `needs-human` but `call_status` remains `completed`.
- The LLM sometimes chooses `inquiry` where the reference expects `rapport`, or `evidence-or-benefit` where the reference expects `inquiry`.
- A few follow-up cases lack an explicit escalation or follow-up reason even when the reference expects one.

## Product Implication

The result supports the product architecture: a reusable sales-agent core can work across multiple campaign profiles and product types, but the agent needs a stricter output contract for final outcome consistency and strategy taxonomy selection.

Implemented improvement:

- Add a deterministic post-processor or validation layer that normalizes impossible combinations, such as `interest_state = needs-human` with `call_status = completed`.
- Tighten the prompt instructions for strategy labels with short definitions and examples.
- Improve the rule baseline so it covers competitor comparison, claim-boundary, human-request, authority-gap, timing-delay, and active-pain price objection cases.

Next evaluation target:

- Re-run the LLM agent with the stricter prompt and output contract.
- Compare the new LLM run against the improved deterministic baseline.
