# HUMAN-REVIEW-FINDINGS-001

## Summary

- Status: pass
- Initial red replay reproduced failure count: 20
- Current reproduced failure count: 0
- Stale or already-fixed findings: The direct 'what happens next?' process question already passed current-runtime replay for automotive, insurance, telecom, and B2B SaaS., Retail order-support boundary already passed current-runtime replay., RouteSignal preservation cases already passed current-runtime replay and were not patched.
- Runtime behavior changed by targeted patch: True
- Phase 1/2/3 backpatch required: False

## Findings Covered

- generic RouteSignal-concept leakage beyond exact forbidden terms
- uncertainty should not jump to appointment/review
- what happens next should answer process
- out-of-scope support/account requests must not become sales next-step
- right-person contact capture wording
- callback confirmation wording
- RouteSignal preservation

## Initial Red Replay Reproductions

- Automotive uncertainty repair leaked RouteSignal/B2B-demo concepts: inbound leads, asks for a demo, demo or more information, next reply.
- Automotive repeated uncertainty moved to an appointment/review bridge instead of clarification or polite stop.
- B2B SaaS and telecom password/account-support requests fell back to sales diagnostics.
- Membership cancellation request implied a fake cancellation-team transfer.
- B2B SaaS handoff-state account-support boundary kept the right-person state but used a sales review target phrase.
- B2B SaaS right-person email capture sounded like a dead end rather than a human follow-up path.
- Insurance, healthcare, and membership callback confirmations used generic 'the specialist' wording instead of campaign owner/target wording.

## Patches Made

- Made generic tentative/uncertain qualification repair campaign-aware and free of RouteSignal/B2B-demo concepts.
- Changed generic next-step wording to explain the if-issue/if-no-issue process before asking another diagnostic.
- Added a generic account/support boundary for password, order, and cancellation requests without fake support actions.
- Kept 'talk to support' as a right-person routing phrase rather than treating it as an account-support request.
- Changed right-person email capture wording to note human follow-up through the right path without claiming to send anything.
- Made send-info callback confirmation campaign-aware by naming the campaign owner/appointment target instead of 'the specialist'.

## Failures

- None.

## Safety

- Synthetic campaigns only.
- RouteSignal live-demo path used only for preservation checks.
- Provider calls false.
- Local LLM calls false.
- Email/calendar/CRM writes false.
- PROD-102 false.
- Raw synthetic emails redacted in public evidence.
