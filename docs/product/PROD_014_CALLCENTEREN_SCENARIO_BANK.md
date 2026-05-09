# PROD-014 CallCenterEN Scenario Bank

## Purpose

PROD-014 turns the abstract `PROD-013` CallCenterEN pattern bank into a clean scenario bank for later runtime evaluation.

It does not copy transcript wording, train on the dataset, promote retrieval, or change runtime behavior. The output is a set of project-owned scenario packets with synthetic customer prompts, expected agent response requirements, safe-close boundaries, non-sale boundaries, source-pattern IDs, and leakage checks.

## Source Boundary

- Input: `research/experiments/generated/PROD-013-callcenteren-pattern-extraction/pattern-bank.json`
- Dataset reference: https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english
- Paper: https://arxiv.org/abs/2507.02958
- License observed: `cc-by-nc-4.0`
- Reuse label: `abstract_scenario_bank_only`
- Commercial runtime prompt use: `false`
- Commercial model training use: `false`

The generator consumes only abstract labels and pattern IDs from `PROD-013`. If local CallCenterEN ZIPs are available under `data/external/callcenteren/raw/`, it may scan source sentences transiently in memory for leakage checks without writing raw transcript text into tracked artifacts.

## Scenario Packet Shape

Each scenario includes:

- `scenario_label`, such as `sale_eligible`, `price_objection`, `callback_request`, `cancellation_boundary`, `support_handoff`, or `trust_repair`
- at least five abstract `source_pattern_ids`
- multiple `source_pattern_categories`
- synthetic `customer_prompt` turns
- `expected_agent_response_requirements`
- `bad_tactics_to_avoid`
- `expected_outcome`
- `safe_close_definition`
- leakage flags proving no copied transcript text, no single-source transcript generation, and no transcript-derived runtime prompt text

Safe close means verbal commitment or sale-ready outcome without payment collection.

## Commands

Run the expanded default bank:

```powershell
python scripts\run_prod_014_callcenteren_scenario_bank.py
```

Run a smaller bank:

```powershell
python scripts\run_prod_014_callcenteren_scenario_bank.py --scenario-count 8
```

Validate:

```powershell
python scripts\validate_prod_014_callcenteren_scenario_bank.py
```

Default output:

```text
research/experiments/generated/PROD-014-callcenteren-scenario-bank/scenario-bank.json
research/experiments/generated/PROD-014-callcenteren-scenario-bank/report.md
```

## Generated Result

The 2026-05-09 run generated:

- `240` scenarios
- `720` customer turns
- `240` unique scenario recipes
- `2,502` abstract source-pattern references
- `10` source-pattern categories
- `0` leakage findings after a transient scan of `5,000` local source sentences
- scenario quality score `1.0`
- leakage failure rate `0.0`
- safe-close coverage `0.3375`
- non-sale boundary coverage `0.6625`
- emotion-label coverage `1.0`

The default is intentionally an evaluation bank, not one scenario per source call. It expands `7` scenario templates, `8` domains, `5,000` objection patterns, `5,000` emotion-transition patterns, `5,000` persuasion-strategy patterns, `9` discovery-question patterns, and `5,000` close-attempt patterns into configurable abstract recipes.

The generated labels are `sale_eligible`, `price_objection`, `callback_request`, `cancellation_boundary`, `support_handoff`, and `trust_repair`.

## Runtime Decision

PROD-014 is not a runtime promotion. It creates the scenario input bank for `PROD-015`, where old runtime and retrieval runtime should answer the same generated customer prompts under safe-close, hard-failure, non-sale correctness, leakage, and emotional handling metrics.
