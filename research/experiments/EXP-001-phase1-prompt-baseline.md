# EXP-001: Phase 1 Prompt Baseline Comparison

## Status

Completed

## Source Label

`public-only`

## Date

2026-04-27

## Question

Does a simple emotion-aware adaptive prompt produce more appropriate persuasive responses than a non-adaptive baseline prompt when both are evaluated on the same dialogue cases?

## Hypothesis

The adaptive baseline will outperform the non-adaptive baseline on emotional appropriateness and strategy coherence, while staying competitive on context fit, persuasive quality, and human-likeness.

## Dataset

- Name: curated seed test cases for phase 1
- Source: project-authored synthetic cases derived from the current thesis baseline design
- License/usage notes: internal thesis experiment artifact
- Size: 6 cases
- Language: English
- Labels:
  - compact emotion label
  - adaptive strategy label
- Notes:
  - cases are synthetic and should be treated as seed evaluation material, not final benchmark data
  - later experiments should add dataset-derived or mixed-source cases

## Scope

Editable files or modules:

- `packages/prompts/baseline-non-adaptive.txt`
- `packages/prompts/baseline-adaptive.txt`
- `research/experiments/EXP-001-case-pack.md`

Fixed constraints:

- use the phase-1 compact emotion taxonomy
- use the phase-1 adaptive policy
- compare paired responses with the shared evaluation rubric

Out of scope:

- speech/audio processing
- real-time execution
- private data
- learned policy selection

## Metrics

Primary metric:

- rubric-based preference between adaptive and non-adaptive responses

Secondary metrics:

- total rubric score by response
- emotional appropriateness score
- strategy coherence score

## Method

1. Use the curated case pack in `EXP-001-case-pack.md`.
2. For each case, generate a non-adaptive response with the baseline non-adaptive prompt.
3. Generate an adaptive response with the baseline adaptive prompt using the specified emotion and strategy labels.
4. Evaluate both responses with `docs/thesis/EVALUATION_RUBRIC.md`.
5. Record results in this file or a follow-up result note.

## Results

### EXP-001-C01

- Emotion label: `positive`
- Adaptive strategy label: `direct-ask-or-commitment`

Non-adaptive response:

`That is exactly where teams usually see value first, because setup is designed to be lightweight and the reporting wins show up quickly. We can walk you through a simple example based on your current workflow so you can see what the rollout would actually look like.`

Adaptive response:

`That sounds like a strong fit for a trial. If you are open to it, the next step would be a short walkthrough so we can show you how setup would work with your current reporting flow and decide whether it is worth testing with your team.`

Scores:

- Non-adaptive:
  - Context fit: 4
  - Strategy coherence: 3
  - Emotional appropriateness: 3
  - Persuasive quality: 4
  - Human-likeness: 4
  - Total: 18
- Adaptive:
  - Context fit: 5
  - Strategy coherence: 5
  - Emotional appropriateness: 5
  - Persuasive quality: 5
  - Human-likeness: 4
  - Total: 24

Preferred: Adaptive

Why:

The adaptive response turns willingness into a concrete next step instead of staying in value explanation mode.

### EXP-001-C02

- Emotion label: `positive`
- Adaptive strategy label: `direct-ask-or-commitment`

Non-adaptive response:

`That is one of the biggest benefits teams mention, because faster replies usually mean fewer missed opportunities and less manual chasing. In a demo, we can show how the system brings messages into one place and helps your team respond more consistently.`

Adaptive response:

`That makes sense, and a demo would be the right next step here. We could show you exactly how messages are captured and routed so you can quickly judge whether it would help your team respond faster in practice.`

Scores:

- Non-adaptive:
  - Context fit: 4
  - Strategy coherence: 3
  - Emotional appropriateness: 3
  - Persuasive quality: 4
  - Human-likeness: 4
  - Total: 18
- Adaptive:
  - Context fit: 5
  - Strategy coherence: 5
  - Emotional appropriateness: 5
  - Persuasive quality: 5
  - Human-likeness: 4
  - Total: 24

Preferred: Adaptive

Why:

The adaptive response capitalizes on the user's interest and moves decisively toward commitment.

### EXP-001-C03

- Emotion label: `neutral`
- Adaptive strategy label: `evidence-or-benefit`

Non-adaptive response:

`The main difference is that a spreadsheet can track information, but it does not actively help your team follow through. This gives you reminders, visibility into the pipeline, and structured follow-up so fewer leads slip through the cracks.`

Adaptive response:

`A spreadsheet can store names and notes, but it usually depends on people remembering the next step themselves. The difference here is that follow-ups, reminders, and visibility are built into the workflow, which makes it much easier to see who needs attention and when.`

Scores:

- Non-adaptive:
  - Context fit: 5
  - Strategy coherence: 4
  - Emotional appropriateness: 4
  - Persuasive quality: 4
  - Human-likeness: 4
  - Total: 21
- Adaptive:
  - Context fit: 5
  - Strategy coherence: 5
  - Emotional appropriateness: 4
  - Persuasive quality: 4
  - Human-likeness: 4
  - Total: 22

Preferred: Adaptive

Why:

Both responses work, but the adaptive version is slightly clearer and more comparative.

### EXP-001-C04

- Emotion label: `neutral`
- Adaptive strategy label: `evidence-or-benefit`

Non-adaptive response:

`That depends on the team, but the biggest gains usually come from reducing manual follow-up and eliminating tool-switching. Companies tend to save time by centralizing the first response and keeping the next steps more consistent.`

Adaptive response:

`The practical savings usually come from two places: less time spent switching between tools and less manual effort in the early follow-up stage. Teams often do not just save time, they also gain a clearer view of where inquiries are getting stuck.`

Scores:

- Non-adaptive:
  - Context fit: 4
  - Strategy coherence: 4
  - Emotional appropriateness: 4
  - Persuasive quality: 4
  - Human-likeness: 4
  - Total: 20
- Adaptive:
  - Context fit: 5
  - Strategy coherence: 5
  - Emotional appropriateness: 4
  - Persuasive quality: 4
  - Human-likeness: 4
  - Total: 22

Preferred: Adaptive

Why:

The adaptive response feels slightly more concrete and informative without getting pushy.

### EXP-001-C05

- Emotion label: `skeptical-or-negative`
- Adaptive strategy label: `inquiry`

Non-adaptive response:

`That is fair, and the reason some teams still move forward is that the right system reduces manual follow-up instead of adding more admin overhead. When it is set up well, it can actually simplify the process rather than complicate it.`

Adaptive response:

`That sounds like the real issue is whether a tool actually reduces effort instead of adding another layer to manage. Where have systems created extra work for your team in the past: setup, daily usage, or reporting?`

Scores:

- Non-adaptive:
  - Context fit: 4
  - Strategy coherence: 3
  - Emotional appropriateness: 2
  - Persuasive quality: 3
  - Human-likeness: 4
  - Total: 16
- Adaptive:
  - Context fit: 5
  - Strategy coherence: 5
  - Emotional appropriateness: 5
  - Persuasive quality: 5
  - Human-likeness: 5
  - Total: 25

Preferred: Adaptive

Why:

The adaptive response explores the objection instead of trying to talk through it.

### EXP-001-C06

- Emotion label: `skeptical-or-negative`
- Adaptive strategy label: `inquiry`

Non-adaptive response:

`That concern makes sense, and adoption is exactly why teams look for something that is easier to use and easier to fit into existing routines. The value is not just the software itself, but whether it simplifies the work enough that people actually stick with it.`

Adaptive response:

`That is a reasonable concern. When adoption fails, is it usually because the tool is too complex, because the workflow does not fit the team, or because people do not see enough value to change their habits?`

Scores:

- Non-adaptive:
  - Context fit: 4
  - Strategy coherence: 3
  - Emotional appropriateness: 2
  - Persuasive quality: 3
  - Human-likeness: 4
  - Total: 16
- Adaptive:
  - Context fit: 5
  - Strategy coherence: 5
  - Emotional appropriateness: 5
  - Persuasive quality: 4
  - Human-likeness: 5
  - Total: 24

Preferred: Adaptive

Why:

The adaptive response narrows the concern into something discussable, which is a better fit for resistance.

### Aggregate summary

- Cases evaluated: 6
- Adaptive preferred: 6
- Non-adaptive preferred: 0

Average totals:

- Non-adaptive average total: 18.17
- Adaptive average total: 23.50

Most visible adaptive advantage:

- emotional appropriateness
- strategy coherence

Most stable dimension across both baselines:

- human-likeness

## Observations

The adaptive baseline showed the strongest advantage in skeptical cases, where shifting from explanation to inquiry changed the tone of the exchange in a meaningful way.

For positive cases, the main gain was momentum. The adaptive baseline advanced toward commitment, while the non-adaptive baseline often kept explaining.

For neutral cases, both baselines produced acceptable answers. The difference was smaller, which suggests that adaptation may matter most when user state is clearly favorable or clearly resistant.

The non-adaptive baseline was not intentionally weak. That makes the adaptive wins more useful as early evidence for the thesis direction.

## Decision

Keep

Reason:

The first prompt comparison supports the core thesis idea well enough to continue. The adaptive baseline consistently produced more emotionally appropriate and strategy-coherent responses without losing fluency.

## Next Step

Create a repeatable execution path for these comparisons and expand the case set with dataset-derived examples.
