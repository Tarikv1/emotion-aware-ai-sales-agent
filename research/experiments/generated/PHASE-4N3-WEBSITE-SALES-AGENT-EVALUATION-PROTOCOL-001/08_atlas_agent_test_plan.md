# Atlas Agent Test Plan

## Purpose

Test the Atlas 4N2 agent against the generic baseline using the same manual case matrix, scoring rubric, and review sheet.

## Source Package

Use:
`research/experiments/generated/PHASE-4N2-FINAL-ATLAS-WEB-STUDIO-ELEVENLABS-UPLOAD-001/`

Use the 4N2 system prompt and the 4N2 KB files exactly as created. Do not modify the 4N2 upload package for this evaluation protocol.

## Controlled Comparison

1. Run VARIANT-A on all 36 cases.
2. Export sanitized transcripts.
3. Score all transcripts using the same review sheet.
4. Run VARIANT-B on the same 36 cases.
5. Export sanitized transcripts.
6. Score all transcripts using the same review sheet.
7. Compare metrics by variant.
8. Record whether Atlas improves outcomes without increasing hard failure flags.

## Atlas-Specific Checks

The Atlas agent should show:

- better vertical_relevance than the baseline
- stronger objection_handling on price, spam concern, guarantee, SEO, partner approval, and bad-agency-experience cases
- better buyer_state_adaptation for busy, annoyed, low-intent, skeptical, and high-intent buyers
- no fake identity, fake guarantee, or pressure after stop requests
- no internal-test wording in buyer-facing responses

## Iteration Gate

Do not create VARIANT-C until the first comparison identifies a specific failure pattern. The iteration must change one editable surface only and must be re-run on the same frozen cases.
