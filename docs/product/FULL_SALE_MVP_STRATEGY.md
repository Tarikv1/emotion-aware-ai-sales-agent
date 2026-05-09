# Full-Sale MVP Strategy

Status: product strategy and experiment boundary.

This document updates the product direction from appointment-setting only toward a generic autonomous sales agent that can close eligible calls itself. The first implementation target remains simulation, not live deployment.

## Goal

Build a client-usable sales-agent core that can move a call from discovery through objection handling to a safe close when the campaign allows it.

The first full-sale target is a low-risk consumer-product campaign for SD cards and storage accessories. This is a proof campaign, not the product boundary.

## Full Sale V1

`full_sale_v1` means:

- the buyer gives a clear verbal commitment
- the product or package intent is confirmed
- required campaign disclosure is satisfied
- the agent avoids forbidden claims
- compatibility, warranty, and delivery uncertainty are handled safely
- the call logs `sale_ready=true`

`full_sale_v1` does not include:

- real payment handling
- real checkout
- contracts
- real customer data
- regulated product advice
- live deployment
- commercial model training on non-commercial datasets

## Scenario Grounding Source

The first scenario bank should use the Hugging Face `AIxBlock/92k-real-world-call-center-scripts-english` dataset and its paper as pattern-grounding sources.

The dataset is not clean commercial product fuel. It is licensed `cc-by-nc-4.0`, the dataset card says commercial use, resale, or redistribution is prohibited, and the paper frames it as non-commercial research use.

Allowed use in this project:

- source domain and call-flow analysis
- objection-pattern analysis
- escalation and refusal pattern analysis
- scenario-pattern extraction
- locally rewritten simulation scenarios

Blocked use:

- copying transcript lines into tracked scenarios
- high-similarity paraphrases of source transcript lines
- generating a scenario from only one transcript
- putting transcript-derived text into commercial runtime prompts
- training or fine-tuning a commercial runtime model on the dataset without separate license clearance
- redistributing the dataset or transcript-derived text

Raw downloaded ZIP files, if later approved, must stay under ignored local storage such as `data/external/callcenteren/raw/`.

## Metrics

Primary metric:

- `safe_close_rate`: eligible simulated calls ending with `sale_ready=true` and no hard failure.

Required sub-metrics:

- `hard_failure_rate`: share of calls with any safety, leakage, refusal, claim, checkout, or prompt-contamination failure. Release candidate target is `0.0`.
- `non_sale_correctness`: share of non-sale calls where the agent correctly refuses to close and logs the right outcome.
- `close_attempt_quality`: close attempts are clear, low-pressure, and based on confirmed fit.
- `scenario_diversity`: scenario bank covers multiple domains and call shapes.
- `latency_readiness`: scenario grounding does not add slow lookup to the live critical path.

`non_sale_correctness` must stay strong before optimizing close rate further.

## Leakage Tests

Every generated scenario bank must pass:

- no exact transcript sentence appears in generated scenarios
- no high-similarity paraphrase appears in generated scenarios
- no scenario is generated from only one source transcript
- no transcript-derived text enters prompts used by the commercial runtime

The implementation may scan raw local ZIP contents transiently in memory, but it must not write raw transcript text to tracked files, reports, prompts, or runtime artifacts.

## Product Architecture

The reusable core remains:

```text
SalesCampaign
  -> short-term call state
  -> buyer-state and emotion uncertainty
  -> strategy selection
  -> call-control decision
  -> response draft
  -> output contract
  -> voice delivery profile
```

The SD-card campaign supplies:

- product options
- price bands
- compatibility caveats
- warranty boundaries
- allowed claims
- forbidden claims
- required disclosure
- close criteria
- sale-ready outcome fields

The core must not hard-code SD-card behavior. The same full-sale mechanism should later support other campaign-defined closes.

## Safety Rules

The agent must not close when:

- the buyer refuses
- the buyer asks not to continue
- compatibility is unclear
- warranty or performance certainty is requested beyond approved facts
- the buyer asks for a human
- a forbidden claim would be needed to close
- the buyer is angry or confused enough that a close would be pressure
- payment, contract, or private-data handling would be required

In those cases, the correct outcome is `non_sale_correct`, `escalate`, or `end_call`, not `sale_ready`.

## Current Implementation Slice

`PROD-006` implements the first safe slice:

- no dataset download by default
- no provider calls
- no real customer data
- no raw transcript storage
- source-provenance registry entry
- pattern-grounded scenario-bank fixture
- leakage guard shape
- full-sale metrics
- SD-card full-sale simulation scenarios

`BRAIN-002` then defines the per-turn runtime state packet needed to score full-sale behavior:

- buyer state
- strategy
- safety
- call control
- retrieval status
- voice profile
- response outcome
- evidence log

`PROD-007` adds the first fixed full-call gauntlet:

- compares the old core against the BRAIN-002/full-sale candidate on the same calls
- scores safe close rate, hard failure rate, non-sale correctness, close quality, call-control correctness, retrieval default-off, and latency readiness
- keeps no provider calls, no private data reads, no dataset download, no payment handling, no checkout handling, and no live runtime change

`PROD-008` then removes the fixture-scored packet shortcut:

- creates one BRAIN-002 state packet from each turn with local runtime-style logic
- preserves the PROD-007 gains on the same fixed calls
- adds state packet completeness as a first-class gate
- keeps retrieval disabled by default and does not change live runtime behavior

`PROD-009` expands the generated gauntlet across domains:

- covers retail product, telecom, B2B software, insurance, medical equipment, home service, membership, and automotive-style calls
- requires at least three source-pattern IDs per call
- preserves generated safe close rate, hard failure rate, non-sale correctness, call-control correctness, and state packet completeness targets
- keeps retrieval disabled by default and still does not change live runtime behavior

`PROD-010` adds longer universal-objection calls:

- uses at least seven turns per call
- carries the call-level objection stack through every generated BRAIN-002 packet
- scores objection boundary correctness and long-call state continuity
- preserves safe close, hard failure, non-sale, call-control, and packet-completeness targets

`PROD-011` hardens the dialogue-policy layer:

- derives one policy action per PROD-010 turn
- preserves the source packet reference, turn position, and objection stack
- scores policy action correctness, blocked action avoidance, objection stack preservation, and state-reference completeness
- keeps retrieval disabled by default and still does not change live runtime behavior

This prepares the project for live-shaped transcript simulation before any client-facing full-sale claim.
