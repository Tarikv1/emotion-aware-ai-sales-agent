# Task 9 Neutral Mockup Reference Report

## Scope

Implemented the neutral mockup-reference trace-parser correction in the Atlas pricing worktree.

Owned files only:

- `scripts/validate_elevenlabs_040_live_test_traces.py`
- `scripts/test_validate_elevenlabs_040_live_test_traces.py`
- `.superpowers/sdd/task-9-neutral-mockup-reference-report.md`

No product prompt, KB, ElevenLabs dashboard test definition, criterion, provider state, API call, or browser action was changed or used.

## Red Evidence

Existing failed live capture before the parser correction:

`python scripts/validate_elevenlabs_040_live_test_traces.py --input research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/live_test_care_canary_pass_capture.json --output research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/live_test_care_canary_pass_independent.json --partial-test-id sim_040_care_plan_only_when_asked`

Result before the fix:

- `independent_status: fail`
- failure: `post_quote_price_followup_no_cta: agent response 12 reopened mockup/email/send CTA during active price follow-up`

Observed neutral response shape from the live capture:

- `If you decide to move forward with a new three to five page site, the build is usually nine hundred to fifteen hundred dollars, and ongoing care is typically seventy nine dollars per month after that. The mockup itself does not commit you to either one.`

That is a direct mockup/pricing answer, not a renewed CTA.

## Test-First Change

Added a regression in `scripts/test_validate_elevenlabs_040_live_test_traces.py` that validates the real `live_test_care_canary_pass_capture.json` fixture with `live_test_mapping.json` and requires `sim_040_care_plan_only_when_asked` to pass independently.

Preserved the existing renewed-CTA failure test:

- `test_partial_canary_fails_renewed_mockup_cta_during_active_price_followup`

## Parser Change

Narrowed the post-quote CTA detector from a broad mockup noun match to actionable follow-up language only.

Changed logic:

- replaced `MOCKUP_OR_SEND_CTA_RE`
- added `ACTIONABLE_POST_QUOTE_CTA_RE`
- removed standalone mockup-only triggers such as `mockup`, `homepage mockup`, and `free homepage`
- kept actionable CTA markers such as `send`, `email`, `best email`, `where should i send`, `take a look`, `would you be open`, `next step`, and the existing renewed-transition phrases

Net effect:

- neutral references to the mockup inside a price answer now pass
- renewed mockup/send/email/next-step CTAs during an active price follow-up still fail

## Green Verification

`python scripts/test_validate_elevenlabs_040_live_test_traces.py`

- `Ran 13 tests`
- `OK`

`python scripts/validate_elevenlabs_040_live_test_traces.py --input research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/live_test_care_canary_pass_capture.json --output research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/live_test_care_canary_pass_independent.json --partial-test-id sim_040_care_plan_only_when_asked`

- `independent_status: pass`
- `post_quote_price_followup_no_cta: passed`

`python scripts/validate_elevenlabs_040_detailed_pricing_control.py`

- `status: pass`
- `live_evidence_validation.status: validated_current_source_commit`

`git diff --check`

- pass with CRLF normalization warnings only

## Self-Review

- The fix is narrow: only the trace validator CTA parser changed, not the broader 040 checkpoint contract.
- The renewed CTA failure coverage is still present and unchanged at the test level.
- The new regression uses the real failing live capture plus mapping, which is the closest proof that the false positive is removed without weakening the care-plan rules.
- Risk remains limited to phrases that rely entirely on standalone mockup nouns without any actionable CTA wording. That tradeoff is intentional because the prior behavior was overbroad and contradicted the observed provider-passed trace.

## Commit

- Final commit hash is reported in Git history and the handoff message. Embedding the final hash inside this committed report would change the hash again.

## Concerns

- `git diff --check` still reports CRLF normalization warnings on the two owned Python files. There are no whitespace or conflict-marker errors.
