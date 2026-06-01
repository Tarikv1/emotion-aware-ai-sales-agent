# Black-Box Baseline Comparison Plan

## Purpose

RQ7 asks how the system compares to black-box LLM systems. The useful comparison is not provider branding; it is whether a generic hosted agent without campaign structure performs worse, equal, or better under the same cases and scoring.

## Variants

- Generic ElevenLabs baseline: generic website-sales prompt with no structured Atlas knowledge base
- Atlas structured package: 4N2 campaign package evaluated by the 4N3 case matrix
- Future iterated Atlas agent: revised package after evaluation findings, only compared if run on the same frozen rubric

## Controls

- same case matrix
- same evaluator instructions
- same scoring rubric
- same hard failure flags
- same result templates
- no real outbound calls
- no CRM, email, calendar, payment, account, or provider-side side effects

## Recommendation Rule

Prefer the generic baseline if it matches Atlas on sales outcomes while having fewer hard failures and lower complexity. Prefer Atlas only if it improves sales behavior while preserving safety, trust, and human-likeness boundaries.
