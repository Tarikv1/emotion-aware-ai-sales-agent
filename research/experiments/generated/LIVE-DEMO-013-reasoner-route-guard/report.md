# LIVE-DEMO-013 Reasoner Route Guard Validator

- Passed: `true`
- Failure count: `0`
- Provider calls made: `false`
- Local LLM calls made: `false`

## Failures

- None

## Notes

- Checks that CRM replacement questions use public product wording, not internal fixture labels.
- Checks that ASR-shaped clarification such as `who is harder` explains the previous question.
- Checks that deterministic reasoner labels are present before async enrichment and match the spoken route.