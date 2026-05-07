# VOICE-025 Filler Placement

## Purpose

VOICE-025 refines the shared speech-realism layer so English and German fillers are placed where they sound conversationally plausible.

The goal is not to make the sales agent "more casual." The goal is to avoid robotic delivery while keeping the agent professional, campaign-safe, and bilingual.

## Problem

VOICE-024 listening feedback showed that the speech-realism concept improved the audio, but some English fillers appeared in the wrong place.

Bad pattern:

```text
The important thing is, um, that...
Wichtig ist, ähm, dass...
```

This makes the agent sound uncertain inside a clean clause. It also risks damaging trust in the exact part of the answer where the agent should sound clear.

## Boundary-Aware Rule

Fillers may appear only in eligible freeform speech and should prefer:

- pre-answer or pre-planning-sentence placement
- sentence-boundary fallback
- discourse-transition placement
- repair or reformulation placement
- pause-only cues in future provider-level tests when a filler would sound forced

Fillers must not appear inside:

- campaign qualification questions
- required disclosures
- legal, medical, insurance, coverage, or payout boundaries
- hangup or do-not-call lines
- exact company scripts
- fluent clause frames such as `the important thing is that` or `Wichtig ist, dass`

## Language Profiles

English boundary markers:

- `well`
- `so`
- `um`
- `uh`

German boundary markers:

- `also`
- `ähm`
- `äh`
- `hm`

German is not treated as translated English. `also` is used as a German turn or transition marker, while `äh` and `ähm` are German filler-particle forms. `hm` remains available for bounded thinking moments.

## Runtime Position

VOICE-025 updates `scripts/speech_realism.py`, which is used after spoken-text normalization and before prosody/provider rendering.

The layer remains:

- local
- offline
- provider-neutral
- no API key required
- no customer audio upload
- no voice cloning

## Experiment

Run:

```powershell
python scripts\run_voice_025_filler_placement.py
```

Validate:

```powershell
python scripts\validate_voice_025_filler_placement.py
```

Generated outputs:

```text
research/experiments/generated/VOICE-025-filler-placement/results.json
research/experiments/generated/VOICE-025-filler-placement/report.md
```

## Current Result

The initial VOICE-025 offline packet covers five cases:

- English planning phrase boundary placement
- German planning phrase boundary placement
- English sentence-boundary fallback
- German sentence-boundary fallback
- German protected campaign question lock

Current validation status:

- cases: `5`
- English cases: `2`
- German cases: `3`
- provider calls: `false`
- customer audio upload: `false`
- protected segment changes: `0`

## Deep-Dive Follow-Up

After a deeper English/German speech-pattern review, VOICE-025 should be treated as the filler-placement checkpoint, not the whole speech-realism solution.

Evidence-backed distinction:

- Speaker fillers: planning and repair cues such as English `um`/`uh` or German `äh`/`ähm`.
- Discourse markers: turn-shaping words such as English `well`/`so`/`oh` and German `also`/`okay`/`ja`/`genau`.
- Backchannels: short listener feedback that acknowledges the customer without taking the floor too strongly.
- Provider prosody: speed, pitch, pauses, emotion, and break tags that should carry most rhythm variation when possible.

Immediate implication:

- Add `VOICE-026` before the next serious live audio comparison.
- `VOICE-026` should separate speaker fillers from listener backchannels and discourse markers.
- It should add English and German guardrails so acknowledgments do not imply unsafe agreement with customer claims.
- It should test faster sales-call pace and phrase-level prosody without changing protected campaign questions, disclosures, appointment details, handoff text, or regulated claims.

Why this matters:

- More fillers alone will not solve roboticness.
- Random `um`/`ähm` can make the voice sound less competent.
- German `ja`, `okay`, `genau`, and `also` are useful but risky if they accidentally validate something the agent must not promise.
- The next improvement should be interaction-aware timing and prosody, not just more text mutation.

## Thesis Relevance

VOICE-025 turns subjective listening feedback into a testable refinement:

- bad filler placement was observed in listening review
- sources were reviewed for filler/discourse-boundary behavior
- runtime rules were changed
- bilingual guardrails were preserved
- generated artifacts document the before-risk and after-rule
