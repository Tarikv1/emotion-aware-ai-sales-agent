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

Replaced the live-capture-backed unit regression with deterministic synthetic dialogue tests. Exact coverage:

- `test_partial_canary_allows_neutral_mockup_reference_when_buyer_mentioned_mockup`
- `test_partial_canary_fails_actionable_mockup_offer_when_buyer_mentioned_mockup`
- `test_partial_canary_fails_unsolicited_mockup_reference_during_price_followup`
- `test_partial_canary_allows_neutral_without_committing_language`
- `test_partial_canary_fails_renewed_mockup_cta_during_active_price_followup`

The actionable-offer test covers both required examples:

- `I can put together a free mockup for you first.`
- `We could start with the mockup first and go from there.`

Red run before the context-aware parser change:

- `Ran 16 tests`
- four failures: both actionable offer examples incorrectly passed, the unsolicited mockup reference incorrectly passed, and neutral `without committing` language incorrectly failed

## Parser Change

Made post-quote CTA detection context-aware while keeping CTA actionability independent of buyer wording.

Changed logic:

- added `MOCKUP_REFERENCE_RE` for explicit buyer/agent mockup references
- retained CTA-shaped send/email/next-step detection without treating domain phrases such as `site to send or sync` as CTA language
- added mockup-offer detection for `put together`/`create`/`make`/`prepare`/`build` and `start with` forms
- tracked whether the immediately preceding active buyer price-followup mentioned the mockup
- removed standalone `without committing` from unconditional CTA detection

Net effect:

- actionable CTA language fails during an active price follow-up regardless of buyer wording
- any agent mockup mention fails when the immediately preceding buyer price-followup did not mention the mockup
- a neutral mockup reference passes only when that buyer turn explicitly mentioned the mockup and the response contains no actionable CTA language
- neutral `You can compare the options without committing to anything today` language passes

## Green Verification

`python scripts/test_validate_elevenlabs_040_live_test_traces.py`

- `Ran 16 tests`
- `OK`

`python scripts/validate_elevenlabs_040_live_test_traces.py --input research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/live_test_care_canary_pass_capture.json --output research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/live_test_care_canary_pass_independent.json --partial-test-id sim_040_care_plan_only_when_asked`

- `independent_status: pass`
- `post_quote_price_followup_no_cta: passed`

`python scripts/validate_elevenlabs_040_detailed_pricing_control.py`

- `status: pass`
- `live_evidence_validation.status: excluded_valid_historical_source_commit`
- `source_evidence_commit: 87b90f5cd9f4a8b402940a1ee4615e1d7de22936`

`git diff --check`

- pass with CRLF normalization warnings only

## Self-Review

- The fix remains confined to the trace validator state machine and its unit tests; the broader 040 contract is unchanged.
- Deterministic tests now separate buyer context from response actionability and cover both sides of the neutral-reference exception.
- The real care capture is verified only through the separate CLI command, not loaded as a unit-test fixture.
- Existing current-capture coverage caught an overbroad intermediate `send` matcher against CRM domain language; the final matcher limits send/email detection to CTA-shaped phrases.
- The failure detail remains generic (`reopened mockup/email/send CTA`) for both actionable CTAs and unsolicited mockup references. This preserves the existing assertion contract while the boolean result is semantically correct.

## Commit

- Final commit hash is reported in Git history and the handoff message. Embedding the final hash inside this committed report would change the hash again.

## Concerns

- `git diff --check` still reports CRLF normalization warnings on the two owned Python files. There are no whitespace or conflict-marker errors.
