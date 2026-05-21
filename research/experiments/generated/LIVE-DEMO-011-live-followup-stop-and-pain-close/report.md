# LIVE-DEMO-011 Live Follow-Up Stop And Pain Close Validator

- Passed: `true`
- Failure count: `0`
- Provider calls made: `false`

## Failures

- None

## Notes

- Checks that `never` after a callback-time request stops the call.
- Checks that explicit do-not-call wording stays plain.
- Checks that ASR-style `Leeds` pain still maps to missed leads.
- Checks that confirmed missed leads move directly to the appointment ask.