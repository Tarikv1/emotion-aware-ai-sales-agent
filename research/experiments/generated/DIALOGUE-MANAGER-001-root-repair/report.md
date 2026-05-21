# DIALOGUE-MANAGER-001 Root Repair Validator

- Passed: `true`
- Failure count: `0`
- Provider calls made: `false`
- Local LLM calls made: `false`

## Failures

- None

## Notes

- Requires every tested final response to carry a manager action, template id, state trace, and call-control trace.
- Checks observed live failures as dialogue-manager routes rather than one-off policy exceptions.
- Keeps provider calls, local LLM calls, payment, contract closure, production promotion, and PROD-102 out of scope.