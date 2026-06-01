# Prospect Context Layer Overview

## Problem

Recent testing showed a structural issue: Emma sometimes asks outbound prospects for the business name or business type. For a cold call based on a prospect list, that is the wrong posture.

The agent should not discover everything from zero. It should use known context cautiously, confirm the right person, and ask only for missing details needed to make the free mockup useful.

## Principle

Known context should be confirmed, not re-asked.

Uncertain context should be hedged:

- "I had you down as..."
- "I may be wrong, but..."
- "Is that still accurate?"

Unsupported context should not be claimed.

## Boundaries

- Do not scrape leads in this phase.
- Do not invent lead data.
- Do not pretend to have inspected a website unless the prospect record supports it.
- Do not say "I saw your site" unless `inspected_website` is true.
- If the buyer corrects the context, accept the correction and continue.

## Output Shape

The V4 Atlas package adds:

- a schema for prospect context
- exact dynamic variables for first messages
- first-message templates
- prospect-context rules for the prompt and KB
- synthetic prospect examples
- context-aware regression tests
