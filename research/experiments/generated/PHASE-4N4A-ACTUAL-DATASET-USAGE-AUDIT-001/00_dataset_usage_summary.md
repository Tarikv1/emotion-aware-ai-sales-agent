# Dataset Usage Summary

## Correction

The current repo does not support a broad claim that all thesis-proposal datasets were used experimentally. The accurate statement is narrower:

- MELD: actual_public_dataset_downloaded_extracted
- Persuasion for Good: actual_public_dataset_downloaded_extracted
- IEMOCAP: actual_public_dataset_partial_or_unverified
- EASID: thesis_schema_only
- EXP-002 dataset-derived case pack: project_generated_eval_case_pack
- LOCAL-QWEN-SFT-DATASET-001, LOCAL-QWEN-BALANCED-SFT-DATASET-001, and NON-LLM-ACTION-SELECTOR-DATASET-001: project_generated_synthetic_sanitized_dataset
- NON-LLM-ACTION-SELECTOR-DATA-SOURCES-001: provenance_audit_artifact
- CallCenterEN / AIxBlock call-center scripts: reference_only_pattern_grounding
- Public OpenAI ChatGPT plan-fit fixture: product_source_bundle_claim_governance
- PHASE-4N3-WEBSITE-SALES-AGENT-EVALUATION-PROTOCOL-001: project_generated_eval_protocol
- PHASE-4N4-THESIS-EASID-ALIGNMENT-001: thesis_schema_only and proposal_placeholder_only for metrics

## Evidence Boundary

The thesis should not claim emotion accuracy, F1, persuasion lift, human-likeness, website-sales effectiveness, or live readiness until those values are computed from a documented protocol.

## Practical Recommendation

Use MELD and Persuasion for Good as public grounding sources, use project-generated sanitized/synthetic datasets for local planner/action-selection work, and treat EASID as the target schema for future collected/evaluated sales interactions.
