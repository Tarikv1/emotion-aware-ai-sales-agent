# LANG-001 Bilingual Realtime Core

## Experiment Goal

Verify that the reusable realtime sales core can answer in German or English based on `SalesCampaign` language configuration.

This is not a separate German product and English product. It is one response core with campaign-aware language routing.

## Command

```powershell
python scripts\validate_lang_001_bilingual_realtime_core.py
```

The validator calls:

```powershell
python scripts\run_realtime_turn_simulation.py `
  --cases research\experiments\cases\lang-001-bilingual-realtime-core.json `
  --out research/experiments/generated/LANG-001/LANG-001-bilingual-realtime-results.json `
  --report-out research/experiments/generated/LANG-001/LANG-001-bilingual-realtime-report.md
```

## Case Design

LANG-001 uses `16` paired realtime cases:

- German cases: `8`
- English cases: `8`

Covered scenarios:

- price objection
- product detail lookup
- do-not-call / stop request
- human request
- claim or guarantee boundary
- scheduling confirmation
- vague callback timing
- repeated silence

## Current Result

Generated summary:

- cases: `16`
- response-mode matches: `16 / 16`
- call-control matches: `16 / 16`
- response-language matches: `16 / 16`
- response-marker matches: `16 / 16`
- live-path sub-agent violations: `0`
- language counts: `{"de": 8, "en": 8}`
- RESP-001 guarded response preserves German wording for the German price-objection path.

## Interpretation

LANG-001 closes the gap after VOICE-006:

- VOICE-006 decides when the agent should stop or pause while speaking.
- LANG-001 verifies that the realtime response core answers in the configured campaign language.

The same policy labels remain shared across languages. Only the customer-facing wording changes.

The checkpoint also guards the response-generation layer: RESP-001 may improve wording, but it must preserve the campaign language.

## Safety Boundary

This is still deterministic prototype wording. It does not yet prove high-quality natural German or English sales language from an LLM.

Future work should add:

- LLM wording generation under RESP-001 guardrails
- locale-specific tone and formality controls
- code-switching policy
- broader multilingual sales-dialogue simulations
