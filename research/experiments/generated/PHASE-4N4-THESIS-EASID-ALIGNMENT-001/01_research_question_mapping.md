# Research Question Mapping

## RQ1: Emotion Detection

Question: How accurately can emotions be detected from multi-modal inputs?

Current and future measurable artifacts:

- manual emotion labels on each buyer turn
- text emotion cues extracted from the buyer utterance
- optional audio/prosody features if transcript/audio is available
- automatic model output only if actually implemented
- metrics: accuracy/F1 only after labeled data exists

No accuracy, F1, or model-performance result is claimed in this checkpoint.

## RQ2: EASID Preservation

Question: Does EASID preserve emotional and conversational features effectively?

Measurable artifacts:

- schema completeness against required conversation, emotion, persuasion, buyer-state, safety, and outcome fields
- field coverage across scored turns
- reproducibility from case id, agent variant, campaign id, and evaluator fields
- privacy-safe storage
- ability to reconstruct feature-level conversation state without raw private audio

## RQ3: Success/Failure Differentiation

Question: Can features differentiate successful vs unsuccessful calls?

Measurement plan:

- compare features between free_mockup_yes/review_call_yes and disqualified/failed/no_interest outcomes
- compare buyer state, objection type, persuasion strategy, vertical, hard failure flags, and call outcome
- test whether feature patterns explain success/failure before claiming predictive value

## RQ4: Emotion-Aware Persuasion

Question: Does emotion-aware persuasion improve outcomes?

Measurement plan:

- compare generic baseline vs Atlas structured agent vs future emotion-aware variant
- require strategy selection to respond to buyer state
- evaluate outcome movement only on the same frozen case matrix
- prohibit fake manipulation or dark patterns

## RQ5: Human-Likeness

Question: How human-like is the system?

Measurement plan:

- manual rating rubric
- spoken naturalness
- concise call control
- trust
- buyer-state adaptation
- no robotic/internal wording

## RQ6: EASID Insights

Question: What insights does EASID enable?

Expected insight categories:

- common objections
- buyer states linked to success/failure
- vertical-specific patterns
- persuasion strategy effectiveness
- safety failure modes

These are analysis targets, not current findings.

## RQ7: Black-Box LLM Comparison

Question: How does it compare to black-box LLM systems?

Comparison plan:

- generic ElevenLabs baseline
- Atlas structured package
- future iterated Atlas agent
- compare using the same case matrix and rubric

The black-box baseline is useful only if it is evaluated under identical cases, scoring dimensions, and safety flags.
