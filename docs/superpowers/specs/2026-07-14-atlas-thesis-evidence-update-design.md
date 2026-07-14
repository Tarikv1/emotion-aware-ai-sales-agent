# Atlas Thesis Evidence Update Design

## Goal

Bring the thesis-facing project state forward from the last recorded `ELEVENLABS-018` checkpoint to the completed Atlas 036/039/040 natural-sales, terminal-control, and detailed-pricing evidence without rewriting historical phase-one documents or overstating production readiness.

## Baseline

- Latest pre-update thesis commit: `7ad0a1a` (`Add ElevenLabs 018 sales value control repair`).
- The branch contains 174 later commits through `8d9898702e29090460e2312d8aaa8b22c05e517b`.
- `METHODOLOGY_LOG.md` stops at 2026-06-07.
- `ROADMAP.md` still identifies the already-built Universal Sales RAG skeleton as current work.
- `PROJECT_BRIEF.md` and `BASELINE_SPEC.md` describe the 2026-05-29 state.
- The reference registry gate reports eight existing unregistered sales/pricing URLs.

## Evidence Contract

The update may claim:

- the final guarded 040 provider patch succeeded and was read back structurally;
- the active Atlas configuration preserved 17 ordered KB attachments, 30 Analysis criteria, one built-in `end_call`, zero custom/server duplicates, inactive Procedures, and unrelated tool/configuration state;
- paid pricing is buyer-triggered and scoped into one applicable pricing lane;
- hard-stop, delivery-timing, gatekeeper, capability, portal, and CRM behavior were hardened through 036/039/040;
- targeted multi-feature, CRM, and portal repair traces passed independent validation;
- manual transcript review separated product defects from stale evaluator or test-contract expectations;
- no outbound call was placed.

The update must also preserve these limitations:

- full-suite capture files include historical failures and must not be described as universally green;
- broad readiness is limited to the covered hosted Atlas text/simulation contract;
- PSTN audio, ASR, latency, interruption handling, buyer perception, conversion impact, and real-customer performance remain unproven;
- no dashboard criterion or Analysis definition was weakened to manufacture a pass, but new 040 regression tests were added;
- the product is not production-deployed or generally production-validated.

## Document Scope

- `ROADMAP.md`: replace stale current checkpoint/status with thesis consolidation of the Atlas 019-040 arc and next evidence gaps.
- `PROJECT_BRIEF.md`: distinguish global non-production status from covered Atlas configuration readiness.
- `BASELINE_SPEC.md`: update the current runtime baseline while preserving the historical phase-one baseline.
- `METHODOLOGY_LOG.md`: prepend one consolidated Atlas 019-040 methodology entry with evidence and limitations.
- `DECISION_LOG.md`: add decisions for independent trace review over provider labels and buyer-triggered pricing/state-lane control.
- `PROMPT_EVAL_WORKFLOW.md`: add provider-hosted trace reconciliation, failure classification, targeted rerun, and structural readback steps.
- `EVALUATION_RUBRIC.md`: add price-intent, atomic terminal, state continuity, evaluator-conflict, and credit-aware evidence dimensions.
- `THESIS_OUTLINE.md`: map 036/039/040 evidence into simulations, validation gates, results, and threats to validity.
- `THESIS_REFERENCE_REGISTRY.md`: register the eight existing sales/pricing context sources as product-context references, not peer-reviewed evidence.
- `research/experiments/generated/THESIS-DOCS-UPDATE-002/`: record the reviewed range, files, claims, limitations, side effects, and validator results.

## Non-Goals

- No runtime, prompt, KB, test, Analysis, Procedure, live agent, or provider change.
- No new simulation, outbound call, model run, audio generation, or browser action.
- No rewrite of `FIRST_EXPERIMENT_PLAN.md`, collaboration notes, AI-usage disclosure, or speech-realism bibliography.
- No claim that market-pricing pages establish scientific validity or exact Atlas pricing.

## Validation

Run:

```powershell
python scripts\check_thesis_reference_registry.py
python scripts\validate_thesis_reference_registry.py
python scripts\check_thesis_update_gate.py
python scripts\validate_thesis_update_gate.py
python scripts\validate_runtime_manifest.py
python scripts\validate_project_drift_guard.py
git diff --check
```

Also run the thesis update gate with every file in `7ad0a1a..HEAD` supplied through repeated `--changed-file` arguments so the committed branch range, not only the working tree, is covered.

