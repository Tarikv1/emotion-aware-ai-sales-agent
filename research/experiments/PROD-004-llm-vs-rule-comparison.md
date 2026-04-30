# PROD-004 LLM vs Rule Baseline Comparison

This comparison uses the same sales difficulty gauntlet cases and campaign profiles for both runs.

## Runs Compared

- Rule baseline: `research/experiments/generated/PROD-004-rule-baseline-report.md`
- LLM agent: `research/experiments/generated/PROD-004-llm-agent-report.md`
- LLM model: `gpt-4o-mini`

## Aggregate Results

| Metric | Rule baseline | LLM agent | Change |
| --- | ---: | ---: | ---: |
| Turn emotion matches | 10 / 20 | 13 / 20 | +3 |
| Turn interest-state matches | 13 / 20 | 18 / 20 | +5 |
| Turn strategy matches | 13 / 20 | 7 / 20 | -6 |
| Final call-status matches | 6 / 14 | 10 / 14 | +4 |
| Final interest-state matches | 7 / 14 | 12 / 14 | +5 |
| Final strategy matches | 8 / 14 | 6 / 14 | -2 |
| Final appointment matches | 14 / 14 | 14 / 14 | 0 |

## Interpretation

The LLM agent is better at reading nuanced lead state than the deterministic rule baseline. It improves emotion detection, turn-level interest classification, final call status, and final interest state while preserving appointment caution.

The main weakness is strategy-label alignment. The LLM often chooses a plausible sales move, but not the exact internal taxonomy label expected by the case set. This suggests the taxonomy/prompt contract needs to be made sharper before strategy-match scores can be interpreted as pure agent quality.

## Strong LLM Improvements

- Correctly escalates the competitor-comparison case instead of treating it as generic maybe-interest.
- Correctly escalates the outcome-guarantee request instead of over-selling.
- Correctly recognizes wrong-contact referral as `needs-human`.
- Better recognizes human-sensitive or specialist-sensitive cases than the rule baseline.

## Remaining Risks

- Some final outcomes are internally inconsistent, especially when `interest_state` is `needs-human` but `call_status` remains `completed`.
- The LLM sometimes chooses `inquiry` where the reference expects `rapport`, or `evidence-or-benefit` where the reference expects `inquiry`.
- A few follow-up cases lack an explicit escalation or follow-up reason even when the reference expects one.

## Product Implication

The result supports the product architecture: a reusable sales-agent core can work across multiple campaign profiles and product types, but the agent needs a stricter output contract for final outcome consistency and strategy taxonomy selection.

Next improvement target:

- Add a deterministic post-processor or validation layer that normalizes impossible combinations, such as `interest_state = needs-human` with `call_status = completed`.
- Tighten the prompt instructions for strategy labels with short definitions and examples.
- Re-run PROD-004 after the output contract is stricter.
