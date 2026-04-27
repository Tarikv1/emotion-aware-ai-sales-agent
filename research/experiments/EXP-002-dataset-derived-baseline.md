# EXP-002: Dataset-Derived Prompt Baseline Comparison

## Status

Completed

## Source Label

`public-only`

## Date

2026-04-27

## Question

Does the adaptive baseline still outperform the non-adaptive baseline when the cases are grounded in observed dataset patterns rather than fully handcrafted scenarios?

## Hypothesis

The adaptive baseline will remain stronger on emotional appropriateness and strategy coherence, although the gap may narrow because the cases are less conveniently tailored than the synthetic seed set.

## Dataset

- Name: dataset-derived, domain-adapted case pack
- Source:
  - `MELD`
  - `Persuasion for Good`
- License/usage notes: case pack is a project-authored derivative artifact grounded in public datasets
- Size: 6 cases
- Language: English
- Labels:
  - compact emotion label
  - adaptive strategy label
- Notes:
  - cases are adapted into a sales context using emotional and strategic patterns drawn from the public datasets

## Scope

Editable files or modules:

- `packages/prompts/baseline-non-adaptive.txt`
- `packages/prompts/baseline-adaptive.txt`
- `research/experiments/EXP-002-dataset-derived-case-pack.md`

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

1. Use the case pack in `EXP-002-dataset-derived-case-pack.md`.
2. For each case, generate a non-adaptive response with the baseline non-adaptive prompt.
3. Generate an adaptive response with the baseline adaptive prompt using the specified emotion and strategy labels.
4. Evaluate both responses with `docs/thesis/EVALUATION_RUBRIC.md`.
5. Record results here.

## Results

### EXP-002-C01

- Emotion label: `positive`
- Adaptive strategy label: `direct-ask-or-commitment`

Non-adaptive response:

`That is exactly why teams usually feel more comfortable exploring it, because they do not need to rebuild everything at once. We can show you how a pilot would work so you can see whether the setup really fits your process.`

Adaptive response:

`That is a great point to test in a pilot. If you want, the next step would be a short walkthrough focused on how quickly your team could get a first use case live without disrupting the current process.`

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

The adaptive response turns positive surprise into a concrete commitment move.

### EXP-002-C02

- Emotion label: `positive`
- Adaptive strategy label: `direct-ask-or-commitment`

Non-adaptive response:

`That is usually the best place to start, because early wins make the rollout easier to evaluate. We can walk through a realistic first use case and show how the process would look before your team commits to anything larger.`

Adaptive response:

`That sounds like a good point to move to a concrete next step. We could map a first use case together and show you exactly what the initial rollout would look like so you can judge whether it is worth moving forward.`

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

The adaptive response better matches engaged agreement by advancing to a next step.

### EXP-002-C03

- Emotion label: `neutral`
- Adaptive strategy label: `evidence-or-benefit`

Non-adaptive response:

`On a normal workday, the biggest difference is that follow-ups and reminders are not left to memory or scattered across tools. That usually means less manual coordination and fewer missed opportunities.`

Adaptive response:

`In a normal workday, it would mainly reduce the manual work around tracking who needs a response, who is waiting, and what the next step is. The benefit is less time spent coordinating follow-ups and more visibility into where work is getting stuck.`

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

The adaptive response is slightly more concrete and operationally legible.

### EXP-002-C04

- Emotion label: `neutral`
- Adaptive strategy label: `evidence-or-benefit`

Non-adaptive response:

`The main reason is that teams often already have tools, but not a workflow that keeps follow-up consistent. What tends to matter is whether the system reduces missed handoffs and gives clearer visibility into what happens next.`

Adaptive response:

`The strongest case is usually not that it is another tool, but that it gives clearer visibility and more consistent follow-up than teams get from a fragmented setup. In practice, that means fewer dropped handoffs and a better view of which leads still need action.`

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

The adaptive response answers the confidence question more directly with a credibility-and-benefit frame.

### EXP-002-C05

- Emotion label: `skeptical-or-negative`
- Adaptive strategy label: `inquiry`

Non-adaptive response:

`I understand the frustration, and the reason some teams still adopt these systems is that the right setup reduces inconsistency instead of adding noise. When the workflow is well designed, it should make the process easier rather than more annoying.`

Adaptive response:

`That reaction usually means the real problem is not the idea of software, but the kind of friction it creates. What has made these tools feel annoying for your team before: setup effort, daily usage, or extra process overhead?`

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

The adaptive response reflects the frustration pattern and converts it into a diagnostic question.

### EXP-002-C06

- Emotion label: `skeptical-or-negative`
- Adaptive strategy label: `inquiry`

Non-adaptive response:

`That is fair, and there is no value in another long feature tour unless the system solves a clear operational problem. The real benefit should be whether it removes friction from the specific part of the process that is currently slowing your team down.`

Adaptive response:

`Understood. Instead of walking through features, what is the specific point in your process that causes the most friction right now: qualification, follow-up, or handoff?`

Scores:

- Non-adaptive:
  - Context fit: 5
  - Strategy coherence: 4
  - Emotional appropriateness: 3
  - Persuasive quality: 4
  - Human-likeness: 4
  - Total: 20
- Adaptive:
  - Context fit: 5
  - Strategy coherence: 5
  - Emotional appropriateness: 5
  - Persuasive quality: 5
  - Human-likeness: 5
  - Total: 25

Preferred: Adaptive

Why:

The adaptive response responds to overload by narrowing immediately to the user's real need.

### Aggregate summary

- Cases evaluated: 6
- Adaptive preferred: 6
- Non-adaptive preferred: 0

Average totals:

- Non-adaptive average total: 18.67
- Adaptive average total: 23.67

Most visible adaptive advantage:

- emotional appropriateness
- strategy coherence

Most stable dimension across both baselines:

- human-likeness

## Observations

The adaptive baseline remained stronger even when the cases were grounded in observed dataset patterns rather than only in purely handcrafted scenarios.

The skeptical cases again showed the largest benefit from adaptation. The main difference was not fancier wording, but switching from explanation to targeted inquiry.

The neutral cases remained closer, which continues to suggest that adaptation matters most when the user state is clearly directional.

The dataset-derived cases are still adapted into a sales domain, so they are more grounded than EXP-001 but not yet equivalent to a final benchmark.

## Decision

Keep

Reason:

The second pass reinforces the first result and gives the project a more defensible bridge from public datasets to sales-domain adaptation logic.

## Next Step

Build a repeatable execution path for prompt generation and scoring, then begin preparing a larger mixed case set with stronger dataset grounding.
