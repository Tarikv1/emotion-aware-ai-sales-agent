# RQ To Dataset Evidence Mapping

## RQ1 Emotion Detection

- MELD sentiment/emotion labels can ground initial emotion/sentiment categories.
- IEMOCAP only pending verification for official audio-corpus use.
- Manual/annotated labels for website-sales calls can support later evaluation if collected.
- Emotion detection accuracy/F1 is not computed in the inspected evidence.

## RQ2 EASID Preservation

- EASID schema, example rows, field coverage, privacy-safe storage are defined in 4N4.
- EASID is schema-only until actual sanitized interaction rows are collected and coverage is measured.

## RQ3 Features Differentiate Success/Failure

- 4N3/4N4A evaluation outputs can support this once manual scoring exists.
- The project-generated eval protocol defines cases, variants, scoring dimensions, and hard failure flags.
- Current row/split counts are not evidence that success/failure features have been statistically separated.

## RQ4 Emotion-Aware Persuasion Improves Outcomes

- Compare generic baseline vs Atlas package vs iterated Atlas after manual runs.
- Use buyer-state/persuasion labels from EASID rows and 4N3 scoring.
- Persuasion for Good supports strategy taxonomy only; it does not prove commercial sales improvement.

## RQ5 Human-Like System

- Manual evaluator scores and spoken naturalness rubric are required.
- 4N4 has placeholder tables, not scored human-likeness results.

## RQ6 EASID Insights

- Aggregate buyer states, objections, strategies, outcomes, failures after EASID rows exist.
- 4N4A clarifies which source fields are available now and which remain future work.

## RQ7 Black-Box LLM Comparison

- Generic ElevenLabs baseline vs structured Atlas package is the planned comparison.
- The comparison is valid only after both are scored against the same frozen 4N3 case matrix and rubric.
