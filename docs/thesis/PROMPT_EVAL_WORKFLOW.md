# Prompt And Evaluation Workflow

## Purpose

Describe how the first baseline responses should be produced and compared.

## Workflow

1. Select or create a test case with:
   - recent dialogue context
   - current user utterance
   - compact emotion label
   - adaptive strategy label
2. Generate a response with the non-adaptive baseline prompt.
3. Generate a response with the adaptive baseline prompt.
4. Evaluate both responses using `EVALUATION_RUBRIC.md`.
5. Record the result in an experiment note under `research/experiments/`.

For the first pass, use:

- `research/experiments/EXP-001-phase1-prompt-baseline.md`
- `research/experiments/EXP-001-case-pack.md`

For the second pass, use:

- `research/experiments/EXP-002-dataset-derived-baseline.md`
- `research/experiments/EXP-002-dataset-derived-case-pack.md`

## Prompt files

- `packages/prompts/baseline-non-adaptive.txt`
- `packages/prompts/baseline-adaptive.txt`

## Repeatable runner

Use:

`scripts/run_prompt_baseline.py`

This script takes a structured JSON case file and generates a repeatable markdown packet with:

- rendered non-adaptive prompts
- rendered adaptive prompts
- response slots
- rubric score placeholders

Current structured case files:

- `research/experiments/cases/exp-001-seed.json`
- `research/experiments/cases/exp-002-dataset-derived.json`

## Current adaptive policy

Use the phase-1 mapping:

- `positive` -> `direct-ask-or-commitment`
- `neutral` -> `evidence-or-benefit`
- `skeptical-or-negative` -> `inquiry`

## Output expectation

Each case should produce:

- one non-adaptive response
- one adaptive response
- one rubric-based comparison record

## Current Methodology Extension

The early prompt baseline remains historical thesis evidence. Current runtime work should not be evaluated only through prompt packets.

For post-baseline campaign/dialogue phases, use:

- source-grounded claim objects for product-specific facts
- deterministic replay for live-observed failures
- exact regression cases plus generalized variants and negative controls
- hosted speech-provider tool-boundary checks when a provider interface may call the project runtime
- cross-campaign contamination checks when campaign facts or selectors change
- universal isolation checks when real product fixtures are added
- human/live review for ASR, TTS, latency, voice naturalness, and sales-quality judgments

## Validation Budget

Do not run the full historical validator ring for every phase.

Default to:

- new focused validator(s)
- directly affected validators
- runtime manifest when runtime/manifest-owned docs change
- project drift guard when covered by the change
- `git diff --check`

Run the full ring only for broad universal runtime changes, major milestones, or release-readiness sweeps. If a reduced budget is used, record that scope instead of claiming all validators passed.

## Post-Checkpoint Workflow Rules

For current sales-dialogue work, do not treat exact scenario patching as enough. A useful evaluation packet should include:

- exact regression cases for observed defects
- paraphrase and spoken-variation cases
- semantic frame checks for buyer intent, objects, relations, negation, correction, and previous context
- negative controls that prove adjacent intents do not collapse into the same route
- loop-risk checks for repeated questions, "I already told you", terminal acceptance, and no-fit closes

Validator interpretation:

- evidence validators are regression tripwires and integrity checks
- quality gates can fail without blocking an honest evidence commit
- passing validators must not be written as live/product readiness
- manual live tests and listening reviews are required after architecture changes that affect sales flow, voice delivery, TTS, latency, or perceived naturalness
- provider sandbox passes must not be treated as live wiring approval unless tool ownership, product truth, side-effect safety, latency, and listening-review gates all pass

Operational workflow:

- use focused validators plus directly affected validators by default
- run shared-runtime or full historical validators only when shared/core runtime behavior changed
- avoid parallel Git/Codex sessions on the same repo when large commits are pending, because repeated Windows Git lock issues have occurred
- do not include `continue from commit X` in future phase prompts unless a fixed baseline is truly needed; the current local repo state and verified evidence baseline should be the source of truth
