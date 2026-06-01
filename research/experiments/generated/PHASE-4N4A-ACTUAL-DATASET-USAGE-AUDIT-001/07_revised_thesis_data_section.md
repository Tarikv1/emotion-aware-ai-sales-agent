# Revised Thesis Data Section

The proposal introduced EASID as a schema for emotion-aware sales interaction data. In the current implementation, EASID should be described as the target structure for future sanitized turn-level records, not as a pre-existing external dataset.

The implementation used MELD and Persuasion for Good for public emotion/persuasion grounding. MELD provides dialogue-level sentiment and emotion labels that support emotion/sentiment grounding, while Persuasion for Good supports persuasion strategy grounding and success/failure pattern analysis. These sources are useful for grounding labels and strategy design, but neither source is evidence of real commercial outbound sales performance.

IEMOCAP was inspected/planned but not relied on as official full audio corpus evidence unless later provenance verification proves official corpus access and use. The current repo evidence treats the local IEMOCAP artifact as partial or unverified for audio-emotion experiments.

Project-generated sanitized/synthetic datasets supported planner/action-selection/evaluation work. These include Qwen SFT datasets, the balanced Qwen dataset, the non-LLM action-selector dataset, and the dataset-derived EXP-002 case pack. They are useful implementation artifacts, not substitutes for measured thesis outcomes.

Placeholder proposal metrics are not experimental results. Final thesis results must be computed from the defined evaluation protocol, with evidence paths for data collection, annotation, scoring, and aggregation.

For the website-sales campaign, PHASE-4N3 defines the evaluation protocol and PHASE-4N4 defines the EASID schema and placeholder result tables. The next step is to collect or manually score controlled conversations before reporting sales effectiveness, human-likeness, emotion accuracy/F1, or hosted voice latency.
