# Battle-Card Agent Blueprint

Source inspiration: the sales intelligence agent team pattern from `awesome-llm-apps`.

Goal: create evidence-backed competitive intelligence that helps a sales agent answer objections without inventing facts.

## Pipeline

1. Competitor research
   - company overview
   - target customers
   - pricing and packaging
   - recent news
   - customer review themes
   - source URLs

2. Feature analysis
   - core capabilities
   - integrations
   - technical constraints
   - pricing gotchas
   - known limitations

3. Positioning analysis
   - competitor messaging
   - target personas
   - how they compare themselves
   - analyst/review-site claims
   - case studies

4. SWOT
   - where we win
   - where they win
   - toss-ups
   - risks
   - landmines to avoid

5. Objection handling
   - likely buyer objection
   - short response
   - proof point
   - discovery question
   - source link

6. Artifact generation
   - Markdown battle card first
   - optional HTML/PDF later
   - optional comparison graphic only after the facts are stable

## Output Contract

Every battle card should include:

- competitor:
- our product:
- generated date:
- confidence:
- source list:
- executive summary:
- comparison table:
- top objections:
- proof-backed responses:
- open questions:
- do-not-claim list:

## Implementation Notes

- Use structured outputs so unsupported claims cannot sneak into prose.
- Store source URLs next to every claim.
- Flag stale cards for refresh after 30 days or after major competitor news.
- Keep human review before using externally.
- Treat emotional/persona adaptation as a second pass after factual grounding.

