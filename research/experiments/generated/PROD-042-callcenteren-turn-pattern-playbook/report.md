# PROD-042-callcenteren-turn-pattern-playbook

## Why This Checkpoint Exists

PROD-042 replaces additional synthetic scenario generation with turn-level sales intelligence extraction from CallCenterEN raw files.
Synthetic scenario expansion from PROD-041A is paused for this lane. This checkpoint extracts reusable customer-move, tactic, quality, reaction, transition, next-action, failure, recovery, playbook, and deterministic evaluation patterns.

## Sources Used

- Primary raw source directory: `data/external/callcenteren/raw`
- Parsed zip files: `11/11`
- Parsed inner files: `16003`
- Estimated record count: `95953`
- Cross-check artifact availability: PROD-013=`True`, PROD-014=`True`

## What Was Extracted

- customer_move_patterns: `28`
- agent_response_tactics: `22`
- agent_response_quality_patterns: `245`
- customer_reaction_patterns: `246`
- customer_state_transition_patterns: `246`
- next_best_action_patterns: `679`
- failure_patterns: `18`
- recovery_patterns: `18`
- sales_playbook_rules: `28`
- evaluation_rules: `28`
- supported_agent_response_tactic_count: `12`
- unsupported_agent_response_tactic_count: `10`
- recovery_patterns_using_unsupported_tactics_count: `13`
- unsafe_next_best_action_count: `0`
- most_common_playbook_sequence_rate: `0.0357`

## Support Count Method And Limitations

- support_count_method: `heuristic aggregate signal count from parsed raw CallCenterEN files and abstract cross-check artifacts`
- support_count_limitations: `Not a verified labeled success count; counts may reflect broad lexical/category matches.`
- unsupported target tactics may appear in recovery guidance as desired taxonomy entries, but they are not source-backed extracted tactics.

## Commercial-Safety And Leakage Boundary

- Output artifacts are abstract-pattern-only and do not store raw transcript text.
- No transcript quotes, no copied source sequence, and no dataset-specific phrasing are written into core machine-readable artifacts.
- HTML includes only sanitized generalized examples marked as review-only paraphrases.
- No provider call, LLM call, private-data read, dataset download, runtime behavior change, retrieval enablement, or runtime-agent modification was performed.

## Why Outputs Exclude Full Conversations

PROD-042 intentionally avoids synthetic conversation scripts. It stores turn-level aggregates and deterministic rules so the playbook can later guide offline evaluation without copying CallCenterEN source wording.

## Pattern Structure Summary

- customer_move_patterns: customer intent, emotional signal, risks, preferred tactics, avoid tactics, and source support.
- agent_response_tactics: when to use each tactic, abstract response structure, and safety constraints.
- response_quality_patterns: directness/specificity/low-pressure/empathy/relevance/brevity/safety/progression dimensions.
- customer_reaction_patterns: reaction tendency after move+tactic and approximate outcome tendencies.
- customer_state_transition_patterns: trust/patience/clarity/interest/friction delta and emotion-shift tendency.
- next_best_action_patterns: recommended next tactic sequence by move+tactic+reaction state.
- failure_patterns and recovery_patterns: deterministic failure detection and bounded recovery tactics.
- sales_playbook_rules: prioritized, RAG-friendly abstract guidance with runtime disabled now.
- evaluation_rules: deterministic checks only; no LLM judging required.

## Coverage Gaps

Total coverage gaps recorded: `13`. Gaps are reported instead of hallucinating unsupported patterns.

| Artifact | Target | Reason | Action |
|---|---|---|---|
| agent_response_tactics | time_respectful | Insufficient source support found in parsed raw zip files. | left unsupported rather than hallucinating pattern |
| agent_response_tactics | one_concrete_relevance_point | Insufficient source support found in parsed raw zip files. | left unsupported rather than hallucinating pattern |
| agent_response_tactics | trust_repair | Insufficient source support found in parsed raw zip files. | left unsupported rather than hallucinating pattern |
| agent_response_tactics | safe_social_proof | Insufficient source support found in parsed raw zip files. | left unsupported rather than hallucinating pattern |
| agent_response_tactics | manager_review_offer | Insufficient source support found in parsed raw zip files. | left unsupported rather than hallucinating pattern |
| agent_response_tactics | support_boundary_route | Insufficient source support found in parsed raw zip files. | left unsupported rather than hallucinating pattern |
| agent_response_tactics | qualify_out | Insufficient source support found in parsed raw zip files. | left unsupported rather than hallucinating pattern |
| agent_response_tactics | proof_without_unsupported_claim | Insufficient source support found in parsed raw zip files. | left unsupported rather than hallucinating pattern |
| agent_response_tactics | payment_safety_boundary | Insufficient source support found in parsed raw zip files. | left unsupported rather than hallucinating pattern |
| agent_response_tactics | stop_after_refusal | Insufficient source support found in parsed raw zip files. | left unsupported rather than hallucinating pattern |
| failure_patterns | ignored_customer_input | No direct aggregate signal observed in parsed sample. | left unsupported rather than hallucinating pattern |
| failure_patterns | premature_price_discussion | No direct aggregate signal observed in parsed sample. | left unsupported rather than hallucinating pattern |
| failure_patterns | overpromised_results | No direct aggregate signal observed in parsed sample. | left unsupported rather than hallucinating pattern |

## Runtime Boundary

- Runtime behavior was not changed.
- Retrieval remains disabled by default.
- Real sales-agent runtime code was not modified.

## Guard Script Substitutions

- Requested `python scripts\setup_guard.py` -> used `python scripts\check_setup.py` (setup_guard.py not present in repo; check_setup.py is the local equivalent)
- Requested `python scripts\project_drift_guard.py` -> used `python scripts\check_project_drift.py` (project_drift_guard.py not present in repo; check_project_drift.py is the local equivalent)
- Requested `python scripts\thesis_update_gate.py` -> used `python scripts\check_thesis_update_gate.py` (thesis_update_gate.py not present in repo; check_thesis_update_gate.py is the local equivalent)
- Requested `python scripts\thesis_reference_registry_guard.py` -> used `python scripts\check_thesis_reference_registry.py` (thesis_reference_registry_guard.py not present in repo; check_thesis_reference_registry.py is the local equivalent)

## Next Recommended Checkpoint

`PROD-043-sales-playbook-runtime-adapter`
