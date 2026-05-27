# LOCAL-QWEN-SFT-DATASET-001

## Summary

- Rows: 80
- Train: 60
- Validation: 10
- Test: 10
- Target format: compact JSON
- Target compact contract valid: true
- Deprecated target labels: 0
- Case-ID-like target labels: 0
- Generic target labels: 0
- Failed Qwen outputs used as targets: false
- Local model calls made: false
- Provider/API/TTS calls made: false
- Runtime behavior changed: false
- Response text changed: false

## Split Method

Rows preserve gold-set order. Every 8th row is validation, the following row is test, and the other 6 rows are train, producing the expected 60/10/10 split.

## Dataset Notes

- `target_compact_json` is the supervised target.
- `target_full_json` is the compact-to-full adapter expansion used for verifier validation.
- Qwen failed outputs are summarized only in `negative_example_metadata`.
- Privacy is `sanitized_only`; raw private transcripts are not included.

## Target Repairs

- `safe_price_reframe`: 2
