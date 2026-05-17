# PROD-060 Runtime Promotion Path Decision

`PROD-060` records the path decision after human acceptance of `PROD-059`.

This is a path decision only. It changes no runtime behavior or response text.

## Decision

- Decision: `select_internal_guarded_english_baseline_only`
- Selected path: `internal_guarded_english_baseline_only`
- Allowed scope: `local_offline_synthetic_internal_regression_reference`
- Plain-language scope: local offline synthetic internal regression reference
- Source readiness status: `ready_with_exclusions`
- Blocked path count: `8`
- Still-blocked blocker count: `14`
- Review HTML: `research/experiments/generated/PROD-060-runtime-promotion-path-decision/prod_060_review.html`
- Recommended next checkpoint: `PROD-061-english-product-policy-gate-prioritization`
- Production runtime promotion allowed: `false`

## Selected Path

The selected path is not production and not public demo use. It only allows the bounded English deterministic surface to be used as a local offline synthetic internal regression reference.

## Rejected Paths

### public_demo_path

- Label: Public demo path
- Status: `blocked`
- Why: Public demo use remains explicitly excluded by PROD-059 and needs its own public-demo, polish, safety, and legal review.
- Blocked by: `public_demo_use, legal_compliance_review`

### real_customer_path

- Label: Real customer path
- Status: `blocked`
- Why: Real customer use remains blocked; the current evidence is synthetic and local.
- Blocked by: `real_customer_use, legal_compliance_review, provider_or_private_data_use`

### provider_or_private_data_path

- Label: Provider or private-data path
- Status: `blocked`
- Why: PROD-059 did not approve provider calls, LLM use, or private-data reads.
- Blocked by: `provider_or_private_data_use`

### retrieval_default_path

- Label: Retrieval default path
- Status: `blocked`
- Why: Runtime retrieval remains disabled by default and must reopen through RAG gates.
- Blocked by: `retrieval_default`

### voice_playback_path

- Label: Voice playback path
- Status: `blocked`
- Why: Voice playback quality remains a separate listening gate and is not proven by English text readiness.
- Blocked by: `voice_playback_quality`

### german_language_path

- Label: German language path
- Status: `blocked`
- Why: Native German review remains parked until the corrected reviewer export exists.
- Blocked by: `native_german_review`

### payment_or_contract_path

- Label: Payment or contract path
- Status: `blocked`
- Why: Payment collection and contract signing are legal/deployment actions, not runtime wording readiness.
- Blocked by: `payment_collection, contract_signing, legal_compliance_review`

### production_runtime_path

- Label: Production runtime path
- Status: `blocked`
- Why: Production runtime promotion remains explicitly blocked by PROD-059 exclusions.
- Blocked by: `production_runtime_promotion, legal_compliance_review, real_customer_use`

## Source Evidence

- Source checkpoint: `PROD-059-final-english-only-runtime-readiness-review`
- Source readiness decision: `english_only_runtime_ready_with_exclusions`
- Source stable guard command: `python scripts\validate_english_multi_turn_regression_guard.py`
- Source stable guard passed: `true`
- Source review HTML: `research/experiments/generated/PROD-059-final-english-only-runtime-readiness-review/prod_059_review.html`

## Still Blocked

- `customer_move_classification_outside_selected_non_refusal_groups`
- `voicemail_action_only_behavior`
- `coverage_knowledge_policy_behavior`
- `context_sensitive_autonomy_behavior`
- `native_german_review`
- `voice_playback_quality`
- `retrieval_default`
- `provider_or_private_data_use`
- `legal_compliance_review`
- `public_demo_use`
- `real_customer_use`
- `payment_collection`
- `contract_signing`
- `production_runtime_promotion`

## Boundary

- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- No provider calls.
- No LLM or LLM judging.
- No private data reads.
- Retrieval remains default-off.
- Voice playback remains blocked.
- German exact-phrase promotion remains blocked.
- Public demo use remains blocked.
- Real customer use remains blocked.
- Payment collection remains blocked.
- Contract signing remains blocked.
- Production runtime promotion allowed: `false`

## Next Checkpoint

`PROD-061-english-product-policy-gate-prioritization` should prioritize the four English product-policy gates that still block broader English runtime promotion: customer-move classification, voicemail action-only behavior, coverage knowledge-policy behavior, and context-sensitive autonomy behavior.
