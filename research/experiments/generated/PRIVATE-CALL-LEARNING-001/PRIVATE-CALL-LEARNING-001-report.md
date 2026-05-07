# PRIVATE-CALL-LEARNING-001 Report

- Status: `pass`
- Network calls made: false
- Raw private content read: false
- Secret values logged: false
- Private root: `data/private`
- Required private workspace folders: 8
- Checks: 12
- Failures: 0

## Boundary

- Raw private audio stays local and is not provider-uploaded by default.
- Customer identifiers and sensitive personal facts are not learning signal.
- Fine-tuning remains disabled until a separate reviewed checkpoint.
- Safe export requires redaction plus human review.

## Pipeline Stages

1. `ingest_raw_audio_local_only` -> `data/private/raw-audio`
2. `local_transcription` -> `data/private/transcripts-raw`
3. `speaker_segmentation` -> `data/private/speaker-segments`
4. `pii_sensitive_redaction` -> `data/private/transcripts-redacted`
5. `outcome_labeling` -> `data/private/outcome-labels`
6. `pattern_mining` -> `data/private/pattern-notes`
7. `human_review` -> `data/private/pattern-notes`
8. `safe_learning_export` -> `data/processed`
9. `retention_or_deletion` -> `data/private/deletion-manifests`

## Learning Outputs

- `positive_sales_pattern`
- `negative_sales_pattern`
- `customer_objection_pattern`
- `human_agent_success_pattern`
- `human_agent_failure_pattern`
- `safety_or_compliance_constraint`
- `emotion_transition_pattern`
- `interest_state_transition`
- `handoff_or_escalation_pattern`
- `timing_or_pacing_pattern`

## Checks

- `pass` `case_file.safe`: Pipeline case file is present and uses the expected id.
- `pass` `pipeline.stage_order`: Pipeline preserves local ingest, redaction, review, export, and deletion order.
- `pass` `pipeline.good_and_bad_patterns`: Pipeline includes successful, unsuccessful, customer, human-agent, and safety pattern outputs.
- `pass` `policy_doc.exists`: Private call learning policy document exists.
- `pass` `policy_doc.boundary`: Policy document records pattern-first learning, private audio boundary, identifier exclusion, negative examples, and export gates.
- `pass` `private_root.exists`: Local-only private data root exists.
- `pass` `private_root.gitignored`: Root and private .gitignore rules keep private contents out of Git.
- `pass` `pipeline.no_provider_upload`: Raw private audio upload to providers is disabled by default.
- `pass` `pipeline.no_identifier_learning`: Customer identifiers are excluded from learning signal.
- `pass` `pipeline.redaction_before_export`: Safe export requires redaction first.
- `pass` `pipeline.human_review_before_export`: Safe export requires human review first.
- `pass` `pipeline.retention_or_deletion`: Retention/deletion handling records deletion manifests without private content.
