# Agent Variants

## Fixed Setup Rules

All variants use the same 36 evaluation cases, the same buyer turns, the same scoring rubric, and the same manual review sheet. No variant may use real outbound calls, CRM, email, calendar, payment, account actions, or provider-side tools.

## VARIANT-A: Generic Baseline

Label: Generic baseline

Configuration:

- simple generic website-sales prompt
- no structured KB
- no vertical playbooks
- no Atlas-specific playbook
- same safety constraints as the Atlas runs
- no tools

Purpose:

This establishes whether a simple prompt already handles the cases well enough. If the baseline performs similarly, the structured package is not justified.

## VARIANT-B: Atlas 4N2 Agent

Label: Atlas 4N2 agent

Configuration:

- Atlas Web Studio system prompt from 4N2
- 4N2 KB files uploaded as knowledge
- no tools
- same safety constraints as the baseline
- same manual case matrix

Purpose:

This tests whether the structured Atlas package improves sales progression, relevance, objection handling, and buyer-state adaptation.

## VARIANT-C: Iterated Atlas Agent

Label: Iterated Atlas agent

Configuration:

- future improved version after first test results
- same safety constraints
- same case matrix unless a new experiment is declared
- no live actions or provider-side tools

Purpose:

This variant is not used to claim improvement until Variant A and Variant B are scored. It is reserved for a second controlled pass where one editable surface is changed based on observed failures.

## Comparison Logic

Do not compare a revised Atlas agent against a different case set. Freeze cases, score the baseline and Atlas 4N2 first, then decide whether the iteration is worth testing.
