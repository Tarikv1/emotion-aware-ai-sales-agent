# PROD-048A Native German Review HTML Packet

## Summary

PROD-048A creates a German-only, non-technical, browser-openable review packet for a native German reviewer.

This checkpoint prepares review material only. No native German approval is claimed. No legal compliance is claimed. Runtime behavior is not changed, retrieval is not enabled, providers and LLMs are not called, private data is not read, and voice/demo/customer use remains blocked.

## Source Inputs

- `research/experiments/generated/PROD-046-core-sales-policy-human-review/german_response_quality_findings.json`
- `research/experiments/generated/PROD-046-core-sales-policy-human-review/call_control_findings.json`
- `research/experiments/generated/PROD-046D-german-source-informed-wording-quality-guard/german_source_informed_results.json`
- `runtime/campaigns/examples/campaign-prod-047-valid-de-source-informed.json`
- `research/experiments/generated/PROD-047-campaign-profile-contract-validator/result.json`

## Local Commands

```powershell
python scripts\run_prod_048a_native_german_review_html_packet.py
python scripts\validate_prod_048a_native_german_review_html_packet.py
```

## Outputs

Generated output directory:

```text
research\experiments\generated\PROD-048A-native-german-review-html-packet\
```

Artifacts:

- `result.json`
- `report.md`
- `native_german_review_packet.json`
- `native_german_review.html`
- `native_german_review_export_schema.json`
- `native_german_review_readme_de.md`
- `native_german_review_table.csv`

## Review HTML

`native_german_review.html` is self-contained and can be opened directly in a browser. It has no external JavaScript or CSS dependencies.

The visible review UI is German-only and intended for a non-technical native German reviewer. It lets the reviewer:

- read a short customer utterance and assistant response;
- rate naturalness, clarity, friendliness, spoken-language quality, abruptness, internal/technical tone, phone acceptability, and revision need;
- flag pressure, legal-risk-sounding wording, medical/coverage advice, payment, contract, unclear, or impolite wording;
- add a better German formulation and comments;
- save progress in browser local storage;
- export JSON and CSV locally with Blob downloads;
- print the packet.

## Boundaries

- No native German approval is claimed.
- No legal compliance is claimed.
- Runtime behavior changed: `false`
- Retrieval enabled: `false`
- Provider calls made: `false`
- LLM used: `false`
- Private data read: `false`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`
- Payment collection allowed: `false`
- Contract signing allowed: `false`
- Production runtime promotion allowed: `false`

## Validation Gates

The PROD-048A validator checks that the HTML exists, is self-contained, includes all German review cases, has required rating fields and textareas for every review item, supports JSON/CSV export and localStorage save/load, keeps visible reviewer labels German, avoids native-approval and legal-compliance claims, and keeps PROD-046 and PROD-047 validation sources passing.

## Next Checkpoint

Recommended next checkpoint: `PROD-048B-native-german-review-import`.

Purpose: import the reviewer-returned JSON/CSV, summarize decisions, and decide whether wording revisions are needed before any voice/demo/customer-facing promotion.
