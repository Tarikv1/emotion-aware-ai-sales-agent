# VOICE-014 Provider Listening Comparison

## Objective

Create a structured side-by-side listening comparison between the successful Cartesia and ElevenLabs voice outputs.

## Method

VOICE-014 reads existing local artifacts:

```text
VOICE-011 Cartesia WebSocket result
VOICE-013 ElevenLabs streaming result
```

It pairs the matching German and English cases, records timing differences, and generates:

- a JSON comparison packet
- a Markdown report
- a local HTML listening page with audio controls and rating tables

No provider calls are made.

## Generated Artifacts

```text
research/experiments/generated/VOICE-014-provider-listening-comparison.json
research/experiments/generated/VOICE-014-provider-listening-comparison-report.md
research/experiments/generated/VOICE-014-provider-listening-comparison.html
```

## Current Result

- comparison pairs: `4`
- German pairs: `2`
- English pairs: `2`
- complete audio pairs: `4 / 4`
- Cartesia files available: `4`
- ElevenLabs files available: `4`
- provider calls made: `false`
- customer audio uploaded: `false`
- human ratings recorded: `false`
- quality claim allowed: `false`

## Timing Observations

ElevenLabs had lower total latency in all four pairs.

First-audio timing was mixed:

- `VOICE-014-C01`: Cartesia faster by `106.921 ms`
- `VOICE-014-C02`: ElevenLabs faster by `71.719 ms`
- `VOICE-014-C03`: ElevenLabs faster by `108.763 ms`
- `VOICE-014-C04`: ElevenLabs faster by `46.416 ms`

## Listening Rubric

The listening page asks for `1-5` ratings for:

- naturalness
- clarity
- language pronunciation
- sales-call pacing
- low muffling or artifacts
- emotional appropriateness
- trustworthiness
- overall preference

## Interpretation

VOICE-014 should be used before making a stronger provider claim.

The current informal impression favors ElevenLabs for human-likeness, but structured ratings are still needed before deciding whether ElevenLabs should become the primary TTS adapter.

## Next Work

After provider ratings are recorded, synthesize VOICE-012 naturalized text through the stronger provider and compare:

- plain provider output
- naturalized provider output
- whether fillers improve human-likeness
- whether fillers reduce trust in German or regulated contexts
