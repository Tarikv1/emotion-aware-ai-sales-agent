# PROD-042 CallCenterEN Turn-Level Sales Pattern Playbook

## Summary

`PROD-042-callcenteren-turn-pattern-playbook` creates an offline, deterministic, leakage-safe turn-level sales playbook from CallCenterEN raw zip files and existing abstract checkpoints (`PROD-013` and `PROD-014`).

This checkpoint does not generate synthetic scenarios or interaction traces. It extracts reusable pattern layers:

- customer move patterns
- agent response tactics
- response quality patterns
- customer reaction patterns
- customer state transition patterns
- next-best-action patterns
- failure patterns
- recovery patterns
- sales playbook rules
- deterministic evaluation rules

## Local Commands

```powershell
python scripts\run_prod_042_callcenteren_turn_pattern_playbook.py
python scripts\validate_prod_042_callcenteren_turn_pattern_playbook.py
```

## Raw Source Path

- `data\external\callcenteren\raw`

## Output Artifacts

- `research/experiments/generated/PROD-042-callcenteren-turn-pattern-playbook/result.json`
- `research/experiments/generated/PROD-042-callcenteren-turn-pattern-playbook/report.md`
- `research/experiments/generated/PROD-042-callcenteren-turn-pattern-playbook/source_pattern_index.json`
- `research/experiments/generated/PROD-042-callcenteren-turn-pattern-playbook/raw_parse_summary.json`
- `research/experiments/generated/PROD-042-callcenteren-turn-pattern-playbook/customer_move_patterns.json`
- `research/experiments/generated/PROD-042-callcenteren-turn-pattern-playbook/agent_response_tactics.json`
- `research/experiments/generated/PROD-042-callcenteren-turn-pattern-playbook/agent_response_quality_patterns.json`
- `research/experiments/generated/PROD-042-callcenteren-turn-pattern-playbook/customer_reaction_patterns.json`
- `research/experiments/generated/PROD-042-callcenteren-turn-pattern-playbook/customer_state_transition_patterns.json`
- `research/experiments/generated/PROD-042-callcenteren-turn-pattern-playbook/next_best_action_patterns.json`
- `research/experiments/generated/PROD-042-callcenteren-turn-pattern-playbook/failure_patterns.json`
- `research/experiments/generated/PROD-042-callcenteren-turn-pattern-playbook/recovery_patterns.json`
- `research/experiments/generated/PROD-042-callcenteren-turn-pattern-playbook/sales_playbook_rules.json`
- `research/experiments/generated/PROD-042-callcenteren-turn-pattern-playbook/evaluation_rules.json`
- `research/experiments/generated/PROD-042-callcenteren-turn-pattern-playbook/pattern_review_data.json`
- `research/experiments/generated/PROD-042-callcenteren-turn-pattern-playbook/pattern_review.html`

## Source Boundary

- Primary source: raw CallCenterEN zip files under `data\external\callcenteren\raw`.
- Secondary source: existing abstract artifacts from `PROD-013` and `PROD-014` for cross-check/fallback enrichment.
- Conflict rule: raw-derived aggregate patterns are preferred over existing abstract artifacts when inconsistent.

## Commercial-Safety Boundary

- Abstract pattern outputs only.
- No raw transcript text in generated artifacts.
- No exact source sequence storage.
- No dataset-specific phrasing in core machine-readable outputs.
- No provider/API calls.
- No LLM usage.
- No dataset download step.
- No runtime agent modification.
- Retrieval remains disabled.

## Validation Gates

- Raw parsing must succeed for at least one zip file and one supported inner file.
- All required artifacts must exist.
- Every pattern must include source support and confidence.
- Coverage gaps are required for unsupported target categories instead of hallucinated patterns.
- No synthetic conversation trace artifacts are allowed in PROD-042 outputs.
- Leakage checks block phone numbers, email addresses, address-like strings, raw placeholder tokens, and long quoted snippets.
- Review HTML must include all pattern sections, filters, coverage gaps, and safety boundary summary.

## Result Metrics

Use `result.json` summary values for:

- parse coverage (`raw_zip_file_count`, `parsed_zip_file_count`, `parsed_inner_file_count`, `estimated_record_count`)
- pattern counts per artifact
- coverage gap count
- supported/unsupported tactic split (`supported_agent_response_tactic_count`, `unsupported_agent_response_tactic_count`, `unsupported_target_tactic_ids`)
- next-best-action and playbook quality (`unsafe_next_best_action_count`, `most_common_playbook_sequence_rate`)
- boundary booleans for no-leakage/no-runtime/no-provider/no-LLM guarantees

Support-count interpretation:

- `support_count_method`: heuristic aggregate signal count from parsed raw CallCenterEN files plus abstract cross-check artifacts.
- `support_count_limitations`: not a verified labeled success count; counts can reflect broad lexical/category matches.

## Review HTML

`pattern_review.html` is a static inspection surface for:

- customer move taxonomy and recommended/avoid tactics
- tactic-to-reaction and tactic-to-state-delta relationships
- next best actions
- failure-to-recovery mapping
- playbook priority rules
- deterministic evaluation rules
- source support and confidence
- coverage gaps
- safety boundary status

Sanitized generalized examples are review-only and marked:

- `example_type: sanitized_generalized_paraphrase`
- `source_quote: false`
- `from_single_transcript: false`

## Relationship To PROD-041A

Further synthetic scenario expansion is paused. `PROD-042` supersedes additional `PROD-041A` simulator expansion as the next turn-level sales intelligence layer.

`PROD-041A` artifacts remain preserved and unchanged.

## Next Recommended Checkpoint

`PROD-043-sales-playbook-runtime-adapter`

Purpose of `PROD-043` (not implemented here):

- apply/evaluate `PROD-042` playbook rules against real agent outputs in offline mode
- keep transcript text blocked
- keep runtime defaults unchanged until a separate promotion gate
