# CONTEXTUAL-BUYER-SEMANTICS-011 Candidate Gap Mismatch Separate Report

## Status

fail

## Scope

This report is separate from Phase 4K5 runtime shadow JSONL write hardening. The failure is in `scripts/validate_contextual_buyer_semantics_011_campaign_adapter_runtime.py` and is not caused by the shadow logging changes.

## Exact Insurance/Telecom Candidate-Gap Mismatch

The failing permission-acknowledgement path selects a campaign-specific next-gap response, but does not carry the campaign core gap metadata into the outgoing semantic and memory fields.

| Vertical | Campaign core gaps | Expected | Actual outgoing fields |
| --- | --- | --- | --- |
| insurance | `coverage_fit`, `premium_or_budget`, `renewal_or_timing` | `outgoing_candidate_gaps` should be campaign core gaps or a valid subset; outgoing scope should identify campaign relevance | `outgoing_candidate_gaps=[]`, `outgoing_active_gap_scope="unknown"` |
| telecom | `coverage_or_availability`, `plan_fit`, `contract_or_switching` | `outgoing_candidate_gaps` should be campaign core gaps or a valid subset; outgoing scope should identify campaign relevance | `outgoing_candidate_gaps=[]`, `outgoing_active_gap_scope="unknown"` |

Concrete observed next-gap responses:

- insurance: `playbook_next_gap="coverage_fit"` and candidate response asks whether coverage fit is causing an issue.
- telecom: `playbook_next_gap="coverage_or_availability"` and candidate response asks whether coverage or availability is causing an issue.

The response text is campaign-aware, but the outgoing metadata remains empty/unknown. That is the mismatch.

## Failed Insurance/Telecom Assertions

- insurance: permission outgoing candidate gaps must be campaign core gaps.
- insurance: manager outgoing candidate gaps must be campaign core gaps.
- insurance: manager memory outgoing candidate gaps must be campaign core gaps.
- telecom: permission outgoing candidate gaps must be campaign core gaps.
- telecom: manager outgoing candidate gaps must be campaign core gaps.
- telecom: manager memory outgoing candidate gaps must be campaign core gaps.

## Additional Current Validator Failures

The rerun reported 13 total failures. In addition to the insurance/telecom candidate-gap failures, the current result also includes the same candidate-gap pattern for `home_services` and `b2b_saas`, plus one home-services semantic expectation mismatch:

- home_services: permission/manager/manager-memory outgoing candidate gaps are empty/unknown instead of campaign core gaps.
- b2b_saas: permission/manager/manager-memory outgoing candidate gaps are empty/unknown instead of campaign core gaps.
- home_services, "the estimate is unclear": expected `pain_confirmed`, got `gap_specific_unclear_context`.

## Safety

The validator run reports no provider calls, no local LLM calls, no email/calendar/CRM writes, no audio storage, and no prod-102 opening in the inspected synthetic campaign objects.
