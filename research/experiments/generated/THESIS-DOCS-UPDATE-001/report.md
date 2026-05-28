# THESIS-DOCS-UPDATE-001

## Baseline Verification

- Verified thesis-doc baseline commit: `09228e0c23548ae799ca7baf7ede9ced7aea83ad`
- Commit message: `docs(thesis): update project methodology and decision records`
- Commit date: `2026-05-25 01:29:50 +0200`
- Verification command: `git log --format="%H`t%ci`t%s" -- docs/thesis`
- Result: no later commit touching `docs/thesis` was found before thesis documentation edits.
- Baseline status: using the known 2026-05-25 thesis checkpoint, not the older 2026-05-22 checkpoint.

## Thesis Files Discovered

- `docs/thesis/AI_USAGE_NOTE.md`
- `docs/thesis/BASELINE_SPEC.md`
- `docs/thesis/COLLABORATION_NOTE.md`
- `docs/thesis/DECISION_LOG.md`
- `docs/thesis/EVALUATION_RUBRIC.md`
- `docs/thesis/FIRST_EXPERIMENT_PLAN.md`
- `docs/thesis/METHODOLOGY_LOG.md`
- `docs/thesis/PROJECT_BRIEF.md`
- `docs/thesis/PROMPT_EVAL_WORKFLOW.md`
- `docs/thesis/ROADMAP.md`
- `docs/thesis/SPEECH_REALISM_REFERENCES.md`
- `docs/thesis/THESIS_OUTLINE.md`
- `docs/thesis/THESIS_REFERENCE_REGISTRY.md`
- `docs/thesis/THESIS_WRITING_GUIDE.md`

## Files Updated

All discovered thesis files were updated where needed:

- decision log: added post-baseline decisions for OpenAI sales behavior, sales-ready definition, semantic mapping, ElevenLabs voice resolution, LLM role, local LLM rejection for live use, Liquid retirement, Fish-inspired prosody taxonomy, ElevenLabs mapping readiness, and validator/quality-gate separation.
- roadmap: shifted current work toward prosody cleanup, no-provider ElevenLabs mapping prototype planning, non-LLM/action-selector research, and thesis evidence consolidation.
- methodology log: added entries for OpenAI semantic sales readiness, local LLM research, Liquid retirement, prosody taxonomy/audit, and this thesis update.
- reference registry and speech realism references: added Liquid, Fish, Kokoro, PyTorch, local LLM/Ollama benchmark evidence, and prosody-control boundaries.
- rubric, prompt workflow, baseline spec, project brief, outline, writing guide, AI usage note, collaboration note, and first experiment plan: updated current methodology and limitation framing.

Docs checker support files were updated narrowly:

- `scripts/check_thesis_reference_registry.py`: allowed `example.invalid` as reserved synthetic non-reference test data.
- `scripts/validate_thesis_reference_registry.py`: raised the wrapper timeout from 30 to 90 seconds because the current repo reference scan exceeded the stale 30-second budget.

## Files Intentionally Not Updated

- No discovered `docs/thesis` file was intentionally skipped.
- Runtime, campaign, model, adapter, checkpoint, and audio files were intentionally not edited because this phase is documentation/evidence only.

## Evidence Reviewed

The update used committed/generated evidence after `09228e0c23548ae799ca7baf7ede9ced7aea83ad`, including:

- OpenAI live/sales chain: `ELEVENLABS-VOICE-RESOLUTION-AUDIT-001`, `PUBLIC-OPENAI-LIVE-SALES-FLOW-001`, `PUBLIC-OPENAI-LIVE-SALES-READINESS-001`, `PUBLIC-OPENAI-DECISION-STAGE-SELLING-001`, `PUBLIC-OPENAI-MEMORY-PROGRESSION-001`, `PUBLIC-OPENAI-INTENT-PRIORITY-001`, `PUBLIC-OPENAI-SPOKEN-SALES-NATURALNESS-001`, `PUBLIC-OPENAI-COMMERCIAL-CLOSING-001`, `PUBLIC-OPENAI-SEMANTIC-UNDERSTANDING-001`, and `PUBLIC-OPENAI-LIVE-SEMANTIC-PIPELINE-001`.
- Local LLM chain: `LOCAL-LLM-CONVERSATION-BRAIN-FEASIBILITY-001`, `LOCAL-QWEN-GOLDSET-EVAL-001`, Qwen SFT/QLoRA/tiny/curriculum/mixed-replay evidence, `LOCAL-QWEN-TWO-HEAD-ARCHITECTURE-001`, Qwen/Ollama latency decisions, and `LOCAL-OLLAMA-SMALL-LIVE-ACTION-MODEL-DECISION-001`.
- Audio/prosody chain: `LOCAL-AUDIO-BACKEND-REGISTRY-001`, Liquid feasibility/listening/retirement evidence, `FISH-INSPIRED-PROSODY-TAXONOMY-001`, `PROSODY-TAXONOMY-QUALITY-DECISION-001`, and `ELEVENLABS-PROSODY-MAPPING-READINESS-001`.

## Major Decisions Reflected

- Sales-ready means active selling, not only product explanation.
- Scenario-specific patches are not enough; semantic frame mapping and buyer-state tracking are now core methodology.
- Future LLM role is conversation planner only; deterministic layers own memory, verification, source/fact boundaries, side-effect safety, and anti-loop checks.
- Qwen2.5-7B and tested local small models are not live-ready; action-id-only selector and non-LLM selector paths remain future research.
- Liquid is retired as TTS/voice backend after failed manual listening review.
- Fish-inspired prosody labels are internal, backend-neutral, sales-safe, and not live-wired.
- ElevenLabs remains the current live voice path.
- Evidence validators and quality gates are separate; manual live/listening review remains necessary.

## Side Effects

- Provider/model/audio calls made: false
- OpenAI API calls made: false
- Local LLM/Ollama generation made: false
- Liquid/Fish/Kokoro inference made: false
- ElevenLabs/live TTS calls made: false
- Model downloads/training made: false
- Audio generation made: false
- Raw private transcript copied: false
- Runtime behavior changed: false
- Response text changed: false
- Live runtime wiring changed: false
